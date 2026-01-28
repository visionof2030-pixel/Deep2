from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from datetime import datetime, timedelta
import os, uuid, itertools
import psycopg2
import google.generativeai as genai

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS frontend_passwords (
        id SERIAL PRIMARY KEY,
        password TEXT UNIQUE NOT NULL,
        expires_at TIMESTAMP NOT NULL
    )
    """)
    conn.commit()
    conn.close()

init_db()

class AskReq(BaseModel):
    prompt: str

class ActivateReq(BaseModel):
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
def admin_generate(days: int = 7, x_admin_token: str = Header(None)):
    if x_admin_token != os.getenv("ADMIN_TOKEN"):
        raise HTTPException(status_code=401, detail="unauthorized")

    password = uuid.uuid4().hex[:16].upper()
    expires_at = datetime.utcnow() + timedelta(days=days)

    conn = get_connection()
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

@app.post("/activate")
def activate(req: ActivateReq):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT expires_at FROM frontend_passwords WHERE password = %s",
        (req.password,)
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=400, detail="invalid_code")

    if row[0] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="expired_code")

    return {"status": "activated"}