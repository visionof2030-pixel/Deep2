from fastapi import FastAPI, Depends
from pydantic import BaseModel
from database import init_db
from create_key import create_key
from security import activation_required

app = FastAPI()

try:
    init_db()
except Exception as e:
    print("DB ERROR:", e)

class GenReq(BaseModel):
    days: int | None = None
    usage_limit: int | None = None

class AskReq(BaseModel):
    text: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/generate")
def generate(req: GenReq):
    code = create_key(req.days, req.usage_limit)
    return {"code": code}

@app.post("/ask")
def ask(req: AskReq, _: None = Depends(activation_required)):
    return {"answer": "system works"}