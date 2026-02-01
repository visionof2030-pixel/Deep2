import os
import jwt
import random
import datetime
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware

# ======================
# Environment Variables
# ======================

JWT_SECRET = os.getenv("JWT_SECRET")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

if not JWT_SECRET or not ADMIN_TOKEN:
    raise RuntimeError("JWT_SECRET or ADMIN_TOKEN not set")

# ===== Gemini API Keys =====
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
    raise RuntimeError("No Gemini API keys found")

# ======================
# FastAPI App
# ======================

app = FastAPI(title="Educational AI Tool")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
# Models
# ======================

class AskRequest(BaseModel):
    prompt: str

# ======================
# Helpers
# ======================

def pick_gemini():
    key = random.choice(GEMINI_KEYS)
    genai.configure(api_key=key)
    return genai.GenerativeModel("models/gemini-2.5-flash-lite")


# ---------- JWT (Activation) ----------
def verify_activation_jwt(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "activation":
            raise HTTPException(status_code=401, detail="Invalid activation token")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Activation code expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid activation code")


# ---------- JWT (Access) ----------
def create_access_jwt():
    payload = {
        "type": "access",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=12)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_access_jwt(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid access token")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ======================
# Routes
# ======================

@app.get("/")
def health():
    return {
        "status": "ok",
        "time": datetime.datetime.utcnow().isoformat()
    }

# ---------- توليد كود التفعيل (للأدمن فقط) ----------
@app.get("/easy-code")
def generate_activation_code(key: str):
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

# ---------- تسجيل الدخول (تحويل التفعيل إلى Access Token) ----------
@app.post("/login")
def login(activation_code: str = Header(...)):
    verify_activation_jwt(activation_code)
    access_token = create_access_jwt()
    return {
        "access_token": access_token,
        "expires_in": "12 hours"
    }

# ---------- استخدام الذكاء الاصطناعي ----------
@app.post("/generate")
def generate(
    data: AskRequest,
    authorization: str = Header(...)
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization.replace("Bearer ", "").strip()
    verify_access_jwt(token)

    try:
        model = pick_gemini()
        response = model.generate_content(data.prompt)
        return {
            "answer": response.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))