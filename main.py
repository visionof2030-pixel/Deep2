from fastapi import FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
import os, uuid
import psycopg2
import google.generativeai as genai
import itertools

app = FastAPI()

app.mount("/", StaticFiles(directory=".", html=True), name="static")

DATABASE_URL = os.getenv("DATABASE_URL")

def db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    c = db()
    cur = c.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS frontend_passwords (
        id SERIAL PRIMARY KEY,
        password TEXT UNIQUE,
        expires_at TIMESTAMP
    )
    """)
    c.commit()
    c.close()

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
    return {"status": "server running"}

@app.post("/ask")
def ask(req: AskReq):
    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
    r = model.generate_content(req.prompt)
    return {"answer": r.text}

@app.post("/admin/generate")
def generate_code(x_admin_token: str = Header(None)):
    if x_admin_token != os.getenv("ADMIN_TOKEN"):
        raise HTTPException(status_code=401, detail="unauthorized")

    password = uuid.uuid4().hex[:16].upper()
    expires_at = datetime.utcnow() + timedelta(days=7)

    c = db()
    cur = c.cursor()
    cur.execute(
        "INSERT INTO frontend_passwords (password, expires_at) VALUES (%s, %s)",
        (password, expires_at)
    )
    c.commit()
    c.close()

    return {
        "password": password,
        "expires_at": expires_at.isoformat()
    }

@app.post("/activate")
def activate(req: ActivateReq):
    c = db()
    cur = c.cursor()
    cur.execute(
        "SELECT expires_at FROM frontend_passwords WHERE password=%s",
        (req.password,)
    )
    row = cur.fetchone()
    c.close()

    if not row:
        return {"status": "invalid"}

    if datetime.utcnow() > row[0]:
        return {"status": "expired"}

    return {"status": "ok"}

@app.get("/activate/{code}")
def activate_link(code: str):
    c = db()
    cur = c.cursor()
    cur.execute(
        "SELECT expires_at FROM frontend_passwords WHERE password=%s",
        (code,)
    )
    row = cur.fetchone()
    c.close()

    if not row:
        return {"status": "invalid"}

    if datetime.utcnow() > row[0]:
        return {"status": "expired"}

    return {"status": "ok"}