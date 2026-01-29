from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid

app = FastAPI()

# ===== CORS =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== تخزين الأكواد في الذاكرة =====
activation_codes = {}  # code: used(True/False)

# ===== نماذج الطلب =====
class AskRequest(BaseModel):
    prompt: str
    code: str

# ===== توليد كود تفعيل =====
@app.post("/admin/generate")
def generate_code():
    code = str(uuid.uuid4())
    activation_codes[code] = False  # لم يُستخدم
    return {"code": code}

# ===== الأداة المقفلة =====
@app.post("/ask")
def ask(data: AskRequest):
    if data.code not in activation_codes:
        raise HTTPException(status_code=401, detail="كود تفعيل غير صالح")

    if activation_codes[data.code]:
        raise HTTPException(status_code=401, detail="كود التفعيل مستخدم")

    # تعليم الكود كمستخدم
    activation_codes[data.code] = True

    return {
        "answer": (
            "الأداة تعمل بنجاح.\n"
            "تم التحقق من كود التفعيل.\n"
            "هذا رد تجريبي.\n"
            "النظام يعمل كما هو متوقع.\n"
            "جاهزون للخطوة التالية."
        )
    }

# ===== فحص السيرفر =====
@app.get("/health")
def health():
    return {"status": "ok"}