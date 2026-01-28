from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
import os
import uuid
import psycopg2
import itertools
import google.generativeai as genai

app = FastAPI()

# ================== ENV ==================
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "FahadJassar14061436")

# ================== DB ==================
def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS frontend_passwords (
        id SERIAL PRIMARY KEY,
        password TEXT UNIQUE NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        device_fingerprint TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ================== MODELS ==================
class AskReq(BaseModel):
    prompt: str

# ================== GEMINI ==================
api_keys = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 8)]
api_keys = [k for k in api_keys if k]
key_cycle = itertools.cycle(api_keys)

def get_api_key():
    return next(key_cycle)

# ================== ROUTES ==================
@app.get("/")
def root():
    return {"status": "server running"}

@app.get("/login.html")
def login_page():
    return FileResponse("login.html")

@app.get("/app.html")
def app_page():
    return FileResponse("app.html")

# ================== ADMIN ==================
@app.post("/admin/generate")
def admin_generate(request: Request, days: int = 7):
    token = request.headers.get("x-admin-token")
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")

    password = uuid.uuid4().hex[:16].upper()
    expires_at = datetime.utcnow() + timedelta(days=days)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO frontend_passwords (password, expires_at)
        VALUES (%s, %s)
        """,
        (password.strip(), expires_at)
    )
    conn.commit()
    conn.close()

    return {
        "code": password,
        "expires_at": expires_at.isoformat()
    }

# ================== ACTIVATE ==================
@app.post("/activate")
def activate(request: Request):
    code = request.headers.get("x-activation-code")
    device = request.headers.get("x-device-id")

    if not code:
        raise HTTPException(status_code=400, detail="missing code")

    clean_code = code.strip().upper()

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT expires_at, is_active, device_fingerprint
        FROM frontend_passwords
        WHERE TRIM(password) = %s
        """,
        (clean_code,)
    )
    row = cur.fetchone()

    if not row:
        conn.close()
        return {"status": "invalid"}

    expires_at, is_active, stored_device = row

    if not is_active:
        conn.close()
        return {"status": "revoked"}

    if datetime.utcnow() > expires_at:
        conn.close()
        return {"status": "expired"}

    # ربط الجهاز أول مرة
    if stored_device is None and device:
        cur.execute(
            """
            UPDATE frontend_passwords
            SET device_fingerprint = %s
            WHERE TRIM(password) = %s
            """,
            (device, clean_code)
        )
        conn.commit()

    # منع جهاز آخر
    if stored_device and device and stored_device != device:
        conn.close()
        return {"status": "device_mismatch"}

    conn.close()
    return {"status": "activated"}

# ================== ASK ==================
@app.post("/ask")
def ask(req: AskReq):
    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
    r = model.generate_content(req.prompt)
    return {"answer": r.text}