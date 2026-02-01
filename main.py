import os
import random
import datetime
import jwt
import google.generativeai as genai

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ======================
# ENV
# ======================
JWT_SECRET = os.getenv("JWT_SECRET")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

if not JWT_SECRET or not ADMIN_TOKEN:
    raise RuntimeError("JWT_SECRET or ADMIN_TOKEN missing")

GEMINI_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
    os.getenv("GEMINI_API_KEY_5"),
    os.getenv("GEMINI_API_KEY_6"),
    os.getenv("GEMINI_API_KEY_7"),
]

GEMINI_KEYS = [k for k in GEMINI_KEYS if k]

if not GEMINI_KEYS:
    raise RuntimeError("No Gemini API Keys found")

# ======================
# APP
# ======================
app = FastAPI(title="Educational AI Tool")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
# MODELS
# ======================
class AskRequest(BaseModel):
    prompt: str

# ======================
# HELPERS
# ======================
def pick_gemini_model():
    key = random.choice(GEMINI_KEYS)
    genai.configure(api_key=key)
    return genai.GenerativeModel("models/gemini-2.5-flash-lite")

def verify_jwt(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "activation":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Activation code expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid access token")

# ======================
# ROUTES
# ======================
@app.get("/")
def health():
    return {
        "status": "ok",
        "time": datetime.datetime.utcnow().isoformat()
    }

# -------- توليد كود تفعيل (للإدارة فقط) --------
@app.get("/easy-code")
def easy_code(key: str):
    if key != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    payload = {
        "type": "activation",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    return {
        "activation_code": token,
        "expires_in": "30 days"
    }

# -------- التحقق من التفعيل (لصفحة التفعيل) --------
@app.post("/verify")
def verify_token(x_token: str = Header(..., alias="X-Token")):
    verify_jwt(x_token)
    return {"valid": True}

# -------- توليد محتوى الذكاء الاصطناعي --------
@app.post("/generate")
def generate(
    data: AskRequest,
    x_token: str = Header(..., alias="X-Token")
):
    verify_jwt(x_token)

    try:
        model = pick_gemini_model()
        response = model.generate_content(data.prompt)

        return {
            "success": True,
            "result": response.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))