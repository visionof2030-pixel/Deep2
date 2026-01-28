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

DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "fahadlassa14661436")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
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

init_db()

class AskReq(BaseModel):
    prompt: str

api_keys = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 8)]
api_keys = [k for k in api_keys if k]
key_cycle = itertools.cycle(api_keys)

def get_api_key():
    return next(key_cycle)

@app.get("/")
def root():
    return {"status": "server running"}

@app.get("/login.html")
def login_page():
    return FileResponse("login.html")

@app.get("/app.html")
def app_page():
    return FileResponse("app.html")

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
        "INSERT INTO frontend_passwords (password, expires_at) VALUES (%s, %s)",
        (password, expires_at)
    )
    conn.commit()
    conn.close()

    return {"password": password, "expires_at": expires_at.isoformat()}

@app.get("/activate/{code}")
def activate(code: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT expires_at FROM frontend_passwords WHERE password = %s",
        (code,)
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return {"status": "invalid"}

    expires_at = row[0]
    if datetime.utcnow() > expires_at:
        return {"status": "expired"}

    return {"status": "ok"}

@app.post("/ask")
def ask(req: AskReq):
    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
    r = model.generate_content(req.prompt)
    return {"answer": r.text}