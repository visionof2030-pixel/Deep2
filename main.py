# main.py
from fastapi import FastAPI
from pydantic import BaseModel
import os
import itertools
import google.generativeai as genai
from database import init_db, get_connection
import uuid

app = FastAPI()
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
    return {"status": "server is running"}

@app.post("/ask")
def ask(req: AskReq):
    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
    r = model.generate_content(req.prompt)
    return {"answer": r.text}

@app.post("/admin/generate")
def admin_generate():
    code = uuid.uuid4().hex[:8].upper()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO codes (code) VALUES (?)", (code,))
    conn.commit()
    conn.close()
    return {"code": code}

@app.get("/admin/codes")
def admin_codes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT code FROM codes ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return {"codes": [r[0] for r in rows]}