from fastapi import FastAPI, HTTPException, Depends, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import itertools
import google.generativeai as genai
from datetime import datetime, timedelta
from database import init_db, get_connection
from create_key import create_key
from security import activation_required

try:
    init_db()
except Exception as e:
    print("DB INIT ERROR:", e)

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
    expires_at: int | None = None
    usage_limit: int | None = None
    name: str | None = None

api_keys = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
    os.getenv("GEMINI_API_KEY_5"),
    os.getenv("GEMINI_API_KEY_6"),
    os.getenv("GEMINI_API_KEY_7"),
]
api_keys = [k for k in api_keys if k]
key_cycle = itertools.cycle(api_keys) if api_keys else None

def get_api_key():
    if not key_cycle:
        raise HTTPException(status_code=500, detail="No Gemini API key configured")
    return next(key_cycle)

def admin_auth(x_admin_token: str = Header(...)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/")
def root():
    return {"status": "running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/activate")
def activate(code: str = Body(..., embed=True)):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, is_active, expires_at, usage_limit, usage_count
        FROM activation_codes WHERE code=?
    """, (code,))
    row = cur.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid code")

    code_id, active, expires, limit, used = row

    if not active:
        conn.close()
        raise HTTPException(status_code=401, detail="Disabled")

    if expires and datetime.fromisoformat(expires) < datetime.utcnow():
        conn.close()
        raise HTTPException(status_code=401, detail="Expired")

    if limit and used >= limit:
        conn.close()
        raise HTTPException(status_code=401, detail="Limit reached")

    cur.execute(
        "UPDATE activation_codes SET usage_count=usage_count+1 WHERE id=?",
        (code_id,)
    )
    conn.commit()
    conn.close()

    return {"status": "activated"}

@app.post("/ask")
def ask(req: Req, _: None = Depends(activation_required)):
    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
    response = model.generate_content(req.prompt)
    return {"answer": response.text}

@app.post("/admin/generate", dependencies=[Depends(admin_auth)])
def admin_generate(req: GenerateKeyReq):
    days = req.expires_at
    expires = None
    if days:
        expires = (datetime.utcnow() + timedelta(days=days)).isoformat()

    conn = get_connection()
    cur = conn.cursor()

    code = create_key(days, req.usage_limit)

    if req.name:
        cur.execute(
            "UPDATE activation_codes SET name=? WHERE code=?",
            (req.name, code)
        )
        conn.commit()

    conn.close()
    return {"code": code}

@app.get("/admin/codes", dependencies=[Depends(admin_auth)])
def admin_codes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, code, is_active, expires_at, usage_limit, usage_count
        FROM activation_codes
        ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "name": r[1],
            "code": r[2],
            "active": bool(r[3]),
            "expires_at": r[4],
            "usage_limit": r[5],
            "usage_count": r[6],
        }
        for r in rows
    ]

@app.put("/admin/code/{code_id}/toggle", dependencies=[Depends(admin_auth)])
def admin_toggle(code_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE activation_codes SET is_active = CASE WHEN is_active=1 THEN 0 ELSE 1 END WHERE id=?",
        (code_id,),
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.delete("/admin/code/{code_id}", dependencies=[Depends(admin_auth)])
def admin_delete(code_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM activation_codes WHERE id=?", (code_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return "<h3>Admin Panel Ready</h3>"