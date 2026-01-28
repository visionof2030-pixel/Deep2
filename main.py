from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import os, uuid, itertools
import psycopg2
import google.generativeai as genai

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

class AskReq(BaseModel):
    prompt: str

class PasswordReq(BaseModel):
    password: str

api_keys = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 8)]
api_keys = [k for k in api_keys if k]
key_cycle = itertools.cycle(api_keys)

def get_api_key():
    return next(key_cycle)

@app.get("/")
def root():
    return {"status": "server is running"}

@app.post("/ask")
def ask(req: AskReq