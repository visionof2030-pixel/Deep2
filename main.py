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

# =====================
# Environment
# =====================
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

if not ADMIN_TOKEN:
    raise RuntimeError("ADMIN_TOKEN is not set")

# =====================
# Database
# =====================
def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS activation_codes (
            id SERIAL PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            device_id TEXT,
            activated_at TIMESTAMP,
            last_seen TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# =====================
# Models
# =====================
class ActivateReq(BaseModel):
    code: str
    device_id: str

class AskReq(BaseModel):
    prompt: str
    device_id: str

# =====================
# Gemini API Keys
# =====================
api_keys = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 8)]
api_keys = [k for k in api_keys if k]
key_cycle = itertools.cycle(api_keys)

def get_api_key():
    return next(key_cycle)

# =====================
# Routes
# =====================
@app.get("/")
def root():
    return {"status": "server running"}

@app.get("/login.html")
def login_page():
    return FileResponse("login.html")

@app.get("/app.html")
def app_page():
    return FileResponse("app.html")

# =====================
# Admin - Generate Code
# =====================
@app.post("/admin/generate")
def admin_generate(request: Request, days: int = 30):
    token = request.headers.get("x-admin-token")
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")

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

    return {
        "code": code,
        "expires_at": expires_at.isoformat()
    }

# =====================
# Admin - Disable Code
# =====================
@app.post("/admin/disable")
def admin_disable(request: Request, code: str):
    token = request.headers.get("x-admin-token")
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE activation_codes SET is_active = false WHERE code = %s",
        (code,)
    )
    conn.commit()
    conn.close()

    return {"status": "disabled"}

# =====================
# Activate Code
# =====================
@app.post("/activate")
def activate(req: ActivateReq):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """SELECT expires_at, is_active, device_id 
           FROM activation_codes WHERE code = %s""",
        (req.code,)
    )
    row = cur.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=401, detail="invalid_code")

    expires_at, is_active, device_id = row

    if not is_active:
        conn.close()
        raise HTTPException(status_code=401, detail="disabled")

    if datetime.utcnow() > expires_at:
        conn.close()
        raise HTTPException(status_code=401, detail="expired")

    # First activation
    if device_id is None:
        cur.execute("""
            UPDATE activation_codes
            SET device_id = %s,
                activated_at = %s,
                last_seen = %s
            WHERE code = %s
        """, (req.device_id, datetime.utcnow(), datetime.utcnow(), req.code))
        conn.commit()
        conn.close()
        return {"status": "activated"}

    # Same device
    if device_id == req.device_id:
        cur.execute("""
            UPDATE activation_codes
            SET last_seen = %s
            WHERE code = %s
        """, (datetime.utcnow(), req.code))
        conn.commit()
        conn.close()
        return {"status": "activated"}

    # Different device
    conn.close()
    raise HTTPException(status_code=401, detail="device_mismatch")

# =====================
# Ask AI (Protected)
# =====================
@app.post("/ask")
def ask(req: AskReq):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT is_active, expires_at, device_id
        FROM activation_codes
        WHERE device_id = %s
    """, (req.device_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="not_activated")

    is_active, expires_at, device_id = row

    if not is_active or datetime.utcnow() > expires_at:
        raise HTTPException(status_code=401, detail="subscription_invalid")

    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
    response = model.generate_content(req.prompt)

    return {"answer": response.text}