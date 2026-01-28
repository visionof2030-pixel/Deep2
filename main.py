from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
import os, itertools, uuid
import psycopg2
import google.generativeai as genai

DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

app = FastAPI()

class AskReq(BaseModel):
    prompt: str

api_keys = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 8)]
api_keys = [k for k in api_keys if k]
key_cycle = itertools.cycle(api_keys)

def get_api_key():
    return next(key_cycle)

@app.on_event("startup")
def startup():
    conn = get_conn()
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

@app.get("/")
def root():
    return {"status": "server running"}

@app.post("/ask")
def ask(req: AskReq):
    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
    r = model.generate_content(req.prompt)
    return {"answer": r.text}

@app.post("/admin/generate")
def generate(days: int = 7, x_admin_token: str = None):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")

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

@app.get("/activate/{password}")
def activate_by_link(password: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT expires_at FROM frontend_passwords WHERE password=%s",
        (password,)
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return {"status": "invalid"}

    if row[0] < datetime.utcnow():
        return {"status": "expired"}

    return RedirectResponse(url="/?activated=1")