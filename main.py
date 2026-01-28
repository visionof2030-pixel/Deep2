from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid
import os, itertools
import google.generativeai as genai

from database import init_db, get_connection, is_valid_password

app = FastAPI()
init_db()

class AskReq(BaseModel):
    prompt: str

class PasswordReq(BaseModel):
    days: int

api_keys = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 8)]
api_keys = [k for k in api_keys if k]
key_cycle = itertools.cycle(api_keys)

def get_api_key():
    return next(key_cycle)

@app.get("/")
def root():
    return {"status": "server is running"}

@app.post("/admin/create-password")
def create_password(req: PasswordReq):
    pw = uuid.uuid4().hex[:10]
    expires = datetime.utcnow() + timedelta(days=req.days)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO passwords (password, expires_at) VALUES (?, ?)",
        (pw, expires.isoformat())
    )
    conn.commit()
    conn.close()

    return {
        "password": pw,
        "expires_at": expires.isoformat()
    }

@app.post("/ask")
def ask(req: AskReq, x_password: str = Header(...)):
    if not is_valid_password(x_password):
        raise HTTPException(401, "Password expired or invalid")

    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
    r = model.generate_content(req.prompt)
    return {"answer": r.text}