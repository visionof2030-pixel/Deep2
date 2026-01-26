from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from pathlib import Path
import os, itertools
import google.generativeai as genai
from database import init_db, get_connection
from create_key import create_key
from security import activation_required

init_db()

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
)

class GenerateKeyReq(BaseModel):
    days: int | None = None
    usage_limit: int | None = None
    customer_name: str | None = None

def admin_auth(x_admin_token: str = Header(...)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/admin/generate", dependencies=[Depends(admin_auth)])
def generate(req: GenerateKeyReq):
    return {
        "code": create_key(req.days, req.usage_limit, req.customer_name)
    }

@app.get("/admin/codes", dependencies=[Depends(admin_auth)])
def codes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT id, code, customer_name, is_active, expires_at, usage_limit, usage_count
    FROM activation_codes ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

@app.put("/admin/code/{id}/toggle", dependencies=[Depends(admin_auth)])
def toggle(id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    UPDATE activation_codes 
    SET is_active = CASE WHEN is_active=1 THEN 0 ELSE 1 END
    WHERE id=?
    """, (id,))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.delete("/admin/code/{id}", dependencies=[Depends(admin_auth)])
def delete(id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM activation_codes WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return {"deleted": True}

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return Path("admin.html").read_text(encoding="utf-8")

@app.get("/manifest.json")
def manifest():
    return FileResponse("manifest.json")

@app.get("/sw.js")
def sw():
    return FileResponse("sw.js")