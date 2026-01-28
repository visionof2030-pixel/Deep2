from fastapi import FastAPI, Depends
from pydantic import BaseModel
import os, itertools
import google.generativeai as genai

from database import init_db
from create_key import create_key
from security import activation_required

app = FastAPI()
init_db()

# ===== Gemini Keys =====
api_keys = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 8)]
api_keys = [k for k in api_keys if k]
key_cycle = itertools.cycle(api_keys)

def get_api_key():
    return next(key_cycle)

# ===== Models =====
class AskReq(BaseModel):
    prompt: str

# ===== Routes =====
@app.get("/")
def root():
    return {"status": "server running"}

@app.post("/ask")
def ask(req: AskReq, _: None = Depends(activation_required)):
    genai.configure(api_key=get_api_key())
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
    r = model.generate_content(req.prompt)
    return {"answer": r.text}

@app.post("/generate")
def generate():
    code = create_key(days=30, usage_limit=200)
    return {"code": code}