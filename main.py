from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

# ====== CORS ======
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== نموذج الطلب ======
class AskRequest(BaseModel):
    prompt: str

# ====== اختبار أن السيرفر يعمل ======
@app.get("/health")
def health():
    return {
        "status": "OK",
        "message": "Server is running",
        "time": datetime.now()
    }

# ====== نقطة اختبار الذكاء الاصطناعي ======
@app.post("/ask")
def ask(data: AskRequest):
    return {
        "answer": (
            "1. يهدف هذا الموضوع إلى توضيح أهمية الذكاء الاصطناعي في تطوير التعليم.\n"
            "2. يساعد الذكاء الاصطناعي المعلم على تحسين أساليب التدريس.\n"
            "3. يسهم في رفع مستوى تفاعل الطلاب داخل الصف.\n"
            "4. يدعم عمليات التقييم والمتابعة بشكل دقيق.\n"
            "5. يمثل الذكاء الاصطناعي مستقبل التعليم الحديث."
        )
    }