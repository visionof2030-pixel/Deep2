from fastapi import FastAPI, Header, HTTPException
from datetime import datetime, timedelta
import jwt
import os

# ===== إعدادات =====
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_THIS_SECRET")
ALGORITHM = "HS256"

app = FastAPI()

# ===== دالة توليد كود تفعيل (لك أنت فقط) =====
def generate_activation_code(days: int):
    payload = {
        "type": "activation",
        "exp": datetime.utcnow() + timedelta(days=days)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

# مثال استخدام (احذفه بعد ما تأخذ الكود)
print("Activation code (30 days):")
print(generate_activation_code(30))


# ===== فحص الكود =====
def verify_code(code: str):
    try:
        jwt.decode(code, SECRET_KEY, algorithms=[ALGORITHM])
        return True
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Activation expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid activation code")


# ===== endpoint للفحص (الفرونت يستخدمه) =====
@app.get("/health")
def health(x_activation_code: str = Header(None)):
    if not x_activation_code:
        raise HTTPException(status_code=401, detail="Missing activation code")

    verify_code(x_activation_code)
    return {"status": "ok"}


# ===== endpoint الذكاء الاصطناعي (اختياري الآن) =====
@app.post("/ask")
def ask_ai(
    payload: dict,
    x_activation_code: str = Header(None)
):
    if not x_activation_code:
        raise HTTPException(status_code=401, detail="Missing activation code")

    verify_code(x_activation_code)

    # هنا لاحقًا تحط Gemini / AI logic
    return {
        "answer": "تم التحقق من الكود بنجاح، الذكاء الاصطناعي يعمل."
    }