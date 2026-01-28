# main.py
from fastapi import FastAPI
from pydantic import BaseModel
import os
import google.generativeai as genai

app = FastAPI()

class Req(BaseModel):
    prompt: str

@app.get("/")
def root():
    return {"status": "server is running"}

@app.post("/ask")
def ask(req: Req):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
    r = model.generate_content(req.prompt)
    return {"answer": r.text}