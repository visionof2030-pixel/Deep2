from fastapi import FastAPI
from pydantic import BaseModel
import os
import itertools
import google.generativeai as genai
from database import init_db
import traceback

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
    try:
        genai.configure(api_key=get_api_key())
        model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
        r = model.generate_content(req.prompt)
        return {"answer": r.text}

    except Exception as e:
        return {
            "error": "Gemini failed",
            "detail": str(e)
        }