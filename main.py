from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from datetime import datetime, timedelta
import os, uuid, itertools
import psycopg2
import google.generativeai as genai

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS frontend_passwords (
        id SERIAL PRIMARY KEY,
        password TEXT UNIQUE,
        expires_at TIMESTAMP,
        used BOOLEAN DEFAULT FALSE
    )
    """)
    conn.commit()
    conn.close()

init_db()

class AskReq(BaseModel):
    prompt: str

class PasswordReq(BaseModel):
    password: str

api_keys = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 8)]
api_keys = [k for k in api_keys if k]
key_cycle = itertools.cycle(api_keys)

def get_api_key():
    return next(key_cycle)

@app.get("/")
def root():
    return {"status": "server is running"}

@app.post("/ask")
def ask(req: AskReq):
    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
    r = model.generate_content(req.prompt)
    return {"answer": r.text}

@app.post("/admin/generate")
def generate_password(days: int = 7, x_admin_token: str = Header(None)):
    if x_admin_token != os.getenv("ADMIN_TOKEN"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    password = uuid.uuid4().hex[:16].upper()
    expires_at = datetime.utcnow() + timedelta(days=days)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO frontend_passwords (password, expires_at) VALUES (%s, %s)",
        (password, expires_at)
    )
    conn.commit()
    conn.close()

    return {
        "password": password,
        "expires_at": expires_at.isoformat()
    }

@app.post("/check-password")
def check_password(req: PasswordReq):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, expires_at, used FROM frontend_passwords WHERE password=%s",
        (req.password,)
    )
    row = cur.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=400, detail="INVALID")

    pid, expires_at, used = row

    if used:
        conn.close()
        raise HTTPException(status_code=400, detail="USED")

    if datetime.utcnow() > expires_at:
        conn.close()
        raise HTTPException(status_code=400, detail="EXPIRED")

    cur.execute(
        "UPDATE frontend_passwords SET used=TRUE WHERE id=%s",
        (pid,)
    )
    conn.commit()
    conn.close()

    return {"status": "OK"}