import os
import random
from datetime import datetime
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

# ======================
# إعدادات عامة
# ======================

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
SECRET_KEY = os.getenv("SECRET_KEY")

if not ADMIN_TOKEN or not SECRET_KEY:
    raise RuntimeError("ADMIN_TOKEN or SECRET_KEY not set")

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

app = FastAPI(title="Gemini API Gateway")

# ======================
# Models
# ======================

class GenerateRequest(BaseModel):
    prompt: str

class CodeRequest(BaseModel):
    expires_at: str  # مثال: 2026-12-31

# ======================
# Helpers
# ======================

def check_admin(x_admin_token: str):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

def pick_gemini():
    key = random.choice(GEMINI_KEYS)
    genai.configure(api_key=key)
    return genai.GenerativeModel("gemini-pro")

# ======================
# Routes
# ======================

@app.get("/")
def health():
    return {
        "status": "ok",
        "time": datetime.utcnow().isoformat()
    }

@app.post("/generate")
def generate(data: GenerateRequest):
    try:
        model = pick_gemini()
        response = model.generate_content(data.prompt)
        return {
            "success": True,
            "result": response.text
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/admin/create-code")
def create_code(
    data: CodeRequest,
    x_admin_token: str = Header(...)
):
    check_admin(x_admin_token)

    return {
        "message": "Endpoint جاهز — سيتم ربط JWT لاحقًا",
        "expires_at": data.expires_at
    }