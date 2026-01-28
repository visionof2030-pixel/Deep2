from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
import os, uuid, psycopg2, itertools
import google.generativeai as genai

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

if not DATABASE_URL or not ADMIN_TOKEN:
    raise RuntimeError("Missing env vars")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

# ---------- Models ----------
class ActivateReq(BaseModel):
    code: str
    device_id: str

class AskReq(BaseModel):
    prompt: str
    device_id: str

# ---------- Gemini ----------
api_keys = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 8)]
api_keys = [k for k in api_keys if k]
key_cycle = itertools.cycle(api_keys)

def get_api_key():
    return next(key_cycle)

# ---------- Routes ----------
@app.get("/")
def root():
    return {"status": "server running"}

@app.get("/login.html")
def login_page():
    return FileResponse("login.html")

@app.get("/app.html")
def app_page():
    return FileResponse("app.html")

# ---------- Admin ----------
@app.post("/admin/generate")
def admin_generate(request: Request, days: int = 30):
    if request.headers.get("x-admin-token") != ADMIN_TOKEN:
        raise HTTPException(status_code=401)

    code = uuid.uuid4().hex[:16].upper()
    expires_at = datetime.utcnow() + timedelta(days=days)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO activation_codes (code, expires_at) VALUES (%s, %s)",
        (code, expires_at)
    )
    conn.commit()
    conn.close()

    return {"code": code, "expires_at": expires_at.isoformat()}

@app.post("/admin/disable")
def admin_disable(request: Request, code: str):
    if request.headers.get("x-admin-token") != ADMIN_TOKEN:
        raise HTTPException(status_code=401)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE activation_codes SET is_active=false WHERE code=%s",
        (code,)
    )
    conn.commit()
    conn.close()
    return {"status": "disabled"}

# ---------- Activate ----------
@app.post("/activate")
def activate(req: ActivateReq):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT device_id, expires_at, is_active FROM activation_codes WHERE code=%s",
        (req.code,)
    )
    row = cur.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=401, detail="invalid")

    device_id, expires_at, is_active = row

    if not is_active or datetime.utcnow() > expires_at:
        conn.close()
        raise HTTPException(status_code=401, detail="expired_or_disabled")

    if device_id is None:
        cur.execute(
            """UPDATE activation_codes
               SET device_id=%s, last_used=%s
               WHERE code=%s""",
            (req.device_id, datetime.utcnow(), req.code)
        )
        conn.commit()
        conn.close()
        return {"status": "activated"}

    if device_id != req.device_id:
        conn.close()
        raise HTTPException(status_code=401, detail="device_mismatch")

    cur.execute(
        "UPDATE activation_codes SET last_used=%s WHERE code=%s",
        (datetime.utcnow(), req.code)
    )
    conn.commit()
    conn.close()
    return {"status": "activated"}

# ---------- Ask (Protected) ----------
@app.post("/ask")
def ask(req: AskReq):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """SELECT expires_at, is_active
           FROM activation_codes
           WHERE device_id=%s""",
        (req.device_id,)
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401)

    expires_at, is_active = row
    if not is_active or datetime.utcnow() > expires_at:
        raise HTTPException(status_code=401)

    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
    r = model.generate_content(req.prompt)
    return {"answer": r.text}