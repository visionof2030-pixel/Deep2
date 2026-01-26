from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
import os
import itertools
import google.generativeai as genai
from database import init_db, get_connection
from security import activation_required

init_db()

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Models
# =========================

class AskReq(BaseModel):
    prompt: str

class GenerateKeyReq(BaseModel):
    days: int | None = None
    usage_limit: int | None = None
    name: str | None = None

# =========================
# Gemini API rotation
# =========================

api_keys = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
    os.getenv("GEMINI_API_KEY_5"),
]

api_keys = [k for k in api_keys if k]
key_cycle = itertools.cycle(api_keys)

def get_api_key():
    return next(key_cycle)

# =========================
# Admin Auth
# =========================

def admin_auth(x_admin_token: str = Header(...)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

# =========================
# Routes
# =========================

@app.get("/")
def root():
    return {"status": "running"}

@app.post("/activate")
def activate(_: None = Depends(activation_required)):
    return {"status": "activated"}

@app.post("/ask")
def ask(req: AskReq, _: None = Depends(activation_required)):
    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
    res = model.generate_content(req.prompt)
    return {"answer": res.text}

# =========================
# Admin APIs
# =========================

@app.post("/admin/generate", dependencies=[Depends(admin_auth)])
def admin_generate(req: GenerateKeyReq):
    code = os.urandom(8).hex().upper()
    expires_at = None

    if req.days:
        expires_at = datetime.utcnow() + timedelta(days=req.days)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO activation_codes
        (code, name, is_active, expires_at, usage_limit, usage_count)
        VALUES (%s, %s, true, %s, %s, 0)
        """,
        (code, req.name, expires_at, req.usage_limit),
    )
    conn.commit()
    conn.close()

    return {"code": code}

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

    data = []
    now = datetime.utcnow()

    for r in rows:
        expires = r[4]
        remaining = None
        if expires:
            remaining = max(0, (expires - now).days)

        data.append({
            "id": r[0],
            "code": r[1],
            "name": r[2],
            "active": r[3],
            "expires_at": r[4],
            "remaining_days": remaining,
            "usage_limit": r[5],
            "usage_count": r[6],
        })

    return data

@app.put("/admin/code/{code_id}/toggle", dependencies=[Depends(admin_auth)])
def toggle_code(code_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE activation_codes
        SET is_active = NOT is_active
        WHERE id = %s
    """, (code_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.delete("/admin/code/{code_id}", dependencies=[Depends(admin_auth)])
def delete_code(code_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM activation_codes WHERE id = %s", (code_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return open("admin.html", encoding="utf-8").read()