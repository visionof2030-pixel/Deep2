from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlite3, uuid, os, itertools
import google.generativeai as genai

app = FastAPI()

DB = "data.db"

def conn():
    return sqlite3.connect(DB)

def init_db():
    c = conn()
    cur = c.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS frontend_passwords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        password TEXT UNIQUE,
        expires_at TEXT
    )
    """)
    c.commit()
    c.close()

init_db()

class LoginReq(BaseModel):
    password: str

class AskReq(BaseModel):
    prompt: str

api_keys = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 8)]
api_keys = [k for k in api_keys if k]
key_cycle = itertools.cycle(api_keys)

def get_api_key():
    return next(key_cycle)

@app.get("/")
def login_page():
    return FileResponse("login.html")

@app.get("/app")
def app_page():
    return FileResponse("app.html")

@app.post("/login")
def login(req: LoginReq):
    c = conn()
    cur = c.cursor()
    cur.execute(
        "SELECT expires_at FROM frontend_passwords WHERE password=?",
        (req.password,)
    )
    row = cur.fetchone()
    c.close()

    if not row:
        raise HTTPException(401, "wrong password")

    if datetime.utcnow() > datetime.fromisoformat(row[0]):
        raise HTTPException(401, "expired")

    return {"ok": True}

@app.post("/admin/create-password")
def create_password(days: int = 7):
    pw = uuid.uuid4().hex[:8]
    exp = datetime.utcnow() + timedelta(days=days)

    c = conn()
    cur = c.cursor()
    cur.execute(
        "INSERT INTO frontend_passwords (password, expires_at) VALUES (?,?)",
        (pw, exp.isoformat())
    )
    c.commit()
    c.close()

    return {"password": pw, "expires_at": exp.isoformat()}

@app.post("/ask")
def ask(req: AskReq):
    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
    r = model.generate_content(req.prompt)
    return {"answer": r.text}