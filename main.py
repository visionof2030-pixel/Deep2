from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, itertools
import google.generativeai as genai
from database import init_db, get_connection
from create_key import create_key
from security import activation_required

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"]
)

init_db()

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

api_keys = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 8)]
api_keys = [k for k in api_keys if k]

if not api_keys:
    raise RuntimeError("No Gemini API keys found")

key_cycle = itertools.cycle(api_keys)

def get_api_key():
    return next(key_cycle)

def admin_auth(x_admin_token: str = Header(...)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

class Req(BaseModel):
    prompt: str

class GenerateKeyReq(BaseModel):
    expires_at: str | None = None
    usage_limit: int | None = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ask")
def ask(req: Req, _: None = Depends(activation_required)):
    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
    res = model.generate_content(req.prompt)
    return {"answer": res.text}

@app.post("/admin/generate", dependencies=[Depends(admin_auth)])
def admin_generate(req: GenerateKeyReq):
    return {"code": create_key(req.expires_at, req.usage_limit)}