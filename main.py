# main.py
import os
import itertools
import google.generativeai as genai
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import init_db, get_connection
from create_key import create_key
from security import activation_required

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⚠️ تشغيل مرة واحدة فقط
init_db()

class AskReq(BaseModel):
    prompt: str

class KeyReq(BaseModel):
    expires_at: str | None = None
    usage_limit: int | None = None

# Gemini keys
api_keys = [os.getenv("GEMINI_API_KEY_1")]
api_keys = [k for k in api_keys if k]

key_cycle = itertools.cycle(api_keys)

def get_api_key():
    return next(key_cycle)

def admin_auth(x_admin_token: str = Header(...)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ask")
def ask(req: AskReq, _: None = Depends(activation_required)):
    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    r = model.generate_content(req.prompt)
    return {"answer": r.text}

@app.post("/admin/generate", dependencies=[Depends(admin_auth)])
def admin_generate(req: KeyReq):
    return {"code": create_key(req.expires_at, req.usage_limit)}