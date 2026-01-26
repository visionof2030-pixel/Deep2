from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pathlib import Path
import os
import itertools
import google.generativeai as genai
from database import init_db, get_connection
from create_key import create_key
from security import activation_required

init_db()

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Req(BaseModel):
    prompt: str

class GenerateKeyReq(BaseModel):
    name: str | None = None
    days: int | None = None
    usage_limit: int | None = None

api_keys = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1,8)]
api_keys = [k for k in api_keys if k]
key_cycle = itertools.cycle(api_keys) if api_keys else None

def get_api_key():
    if not key_cycle:
        raise HTTPException(status_code=500, detail="No API key")
    return next(key_cycle)

def admin_auth(x_admin_token: str = Header(...)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/")
def root():
    return {"status": "running"}

@app.post("/activate")
def activate(_: None = Depends(activation_required)):
    return {"status": "ok"}

@app.post("/ask")
def ask(req: Req, _: None = Depends(activation_required)):
    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
    r = model.generate_content(req.prompt)
    return {"answer": r.text}

@app.post("/admin/generate", dependencies=[Depends(admin_auth)])
def admin_generate(req: GenerateKeyReq):
    return create_key(req.days, req.usage_limit, req.name)

@app.get("/admin/codes", dependencies=[Depends(admin_auth)])
def admin_codes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, code, name, is_active, expires_at, usage_limit, usage_count
        FROM activation_codes
        ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "code": r[1],
            "name": r[2],
            "active": bool(r[3]),
            "expires_at": r[4],
            "usage_limit": r[5],
            "usage_count": r[6],
        } for r in rows
    ]

@app.put("/admin/code/{code_id}/toggle", dependencies=[Depends(admin_auth)])
def toggle(code_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE activation_codes SET is_active=1-is_active WHERE id=?", (code_id,))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.delete("/admin/code/{code_id}", dependencies=[Depends(admin_auth)])
def delete(code_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM activation_codes WHERE id=?", (code_id,))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return Path("admin.html").read_text(encoding="utf-8")