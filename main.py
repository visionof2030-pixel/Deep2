from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import init_db, validate_code

app = FastAPI()

# ⚠️ تُنفذ مرة واحدة عند تشغيل السيرفر
init_db()

class AskRequest(BaseModel):
    prompt: str
    code: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ask")
def ask(data: AskRequest):
    if not validate_code(data.code):
        raise HTTPException(status_code=403, detail="كود التفعيل غير صالح أو منتهي")

    return {
        "answer": (
            "1. الذكاء الاصطناعي يساهم في تطوير التعليم.\n"
            "2. يساعد المعلم على تحسين أساليب التدريس.\n"
            "3. يرفع تفاعل الطلاب داخل الصف.\n"
            "4. يدعم التقييم والمتابعة بدقة.\n"
            "5. يمثل مستقبل التعليم الحديث."
        )
    }