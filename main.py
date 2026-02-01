import os
import random
from datetime import datetime
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import jwt

# ======================
# إعدادات عامة
# ======================

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
SECRET_KEY = os.getenv("SECRET_KEY")

if not ADMIN_TOKEN or not SECRET_KEY:
    raise RuntimeError("ADMIN_TOKEN or SECRET_KEY not set")

JWT_ALGORITHM = "HS256"

# ===== مفاتيح Gemini (7 فقط) =====
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
# FastAPI
# ======================

app = FastAPI(title="Gemini Gateway with JWT")

# ======================
# Models
# ======================

class GenerateRequest(BaseModel):
    prompt: str

class CodeRequest(BaseModel):
    expires_at: str  # YYYY-MM-DD

class VerifyRequest(BaseModel):
    token: str

# ======================
# Helpers
# ======================

def check_admin(token: str):
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

def pick_gemini():
    key = random.choice(GEMINI_KEYS)
    genai.configure(api_key=key)
    return genai.GenerativeModel("gemini-2.5-flash-lite")

def create_jwt(expires_at: str):
    exp = datetime.strptime(expires_at, "%Y-%m-%d")
    payload = {
        "type": "activation",
        "exp": exp,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)

# ======================
# Routes
# ======================

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/generate")
def generate(data: GenerateRequest):
    try:
        model = pick_gemini()
        response = model.generate_content(data.prompt)
        return {"answer": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/create-code")
def create_code(
    data: CodeRequest,
    x_admin_token: str = Header(...)
):
    check_admin(x_admin_token)
    token = create_jwt(data.expires_at)
    return {
        "activation_code": token,
        "expires_at": data.expires_at
    }

@app.post("/verify-code")
def verify_code(data: VerifyRequest):
    try:
        decoded = jwt.decode(
            data.token,
            SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        return {
            "valid": True,
            "expires_at": decoded["exp"]
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Code expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid code")