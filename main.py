# main.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
import os, itertools, uuid
import google.generativeai as genai
from database import init_db, get_connection

app = FastAPI()
init_db()

class AskReq(BaseModel):
    prompt: str
    password: str

class CreatePasswordReq(BaseModel):
    days: int

api_keys = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 8)]
api_keys = [k for k in api_keys if k]
key_cycle = itertools.cycle(api_keys)

def get_api_key():
    return next(key_cycle)

def check_password(password: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT expires_at FROM frontend_passwords
        WHERE password=%s
    """, (password,))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(401, "Invalid password")

    if row["expires_at"] < datetime.utcnow():
        raise HTTPException(401, "Password expired")

@app.get("/")
def root():
    return {"status": "server is running"}

@app.post("/ask")
def ask(req: AskReq):
    check_password(req.password)
    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
    r = model.generate_content(req.prompt)
    return {"answer": r.text}

@app.post("/admin/create-password")
def create_password(req: CreatePasswordReq):
    password = uuid.uuid4().hex[:10]
    expires_at = datetime.utcnow() + timedelta(days=req.days)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO frontend_passwords (password, expires_at)
        VALUES (%s, %s)
    """, (password, expires_at))
    conn.commit()
    conn.close()

    return {
        "password": password,
        "expires_at": expires_at.isoformat()
    }