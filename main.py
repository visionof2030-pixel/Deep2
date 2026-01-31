from fastapi import FastAPI, Header, HTTPException
from datetime import datetime, timedelta
import jwt
import os

# ================== إعدادات أساسية ==================
app = FastAPI()

SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME_SECRET")
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "ADMIN123")
ALGORITHM = "HS256"

# ================== دالة التحقق من كود التفعيل ==================
def verify_activation_code(code: str):
    try:
        payload = jwt.decode(code, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "activation":
            raise HTTPException(status_code=401, detail="Invalid code type")
        return True
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Activation code expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid activation code")

# ================== endpoint فحص التفعيل ==================
@app.get("/health")
def health_check(x_activation_code: str = Header(...)):
    verify_activation_code(x_activation_code)
    return {"status": "ok"}

# ================== توليد كود تفعيل (للمالك فقط) ==================
@app.get("/admin/generate")
def generate_activation_code(days: int, secret: str):
    if secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    payload = {
        "type": "activation",
        "exp": datetime.utcnow() + timedelta(days=days),
        "created_at": datetime.utcnow().isoformat()
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "valid_days": days,
        "activation_code": token
    }

# ================== endpoint الذكاء الاصطناعي ==================
@app.post("/ask")
def ask_ai(
    data: dict,
    x_activation_code: str = Header(...)
):
    # التحقق من كود التفعيل
    verify_activation_code(x_activation_code)

    prompt = data.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    # 🔴 هنا مكان ربط Gemini أو أي AI لاحقًا
    # حالياً رد تجريبي حتى يشتغل المشروع بدون أخطاء
    return {
        "answer": "تم استلام الطلب بنجاح. هذا رد تجريبي من الخادم."
    }