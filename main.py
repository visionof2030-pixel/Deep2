from database import init_db
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import psycopg2, os, uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL)

# ===== Models =====
class AskRequest(BaseModel):
    code: str

# ===== Health =====
@app.get("/health")
def health():
    return {"status": "OK"}

# ===== Generate Code (admin) =====
@app.post("/admin/generate")
def generate_code():
    code = str(uuid.uuid4())
    expires = datetime.now() + timedelta(minutes=10)

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO activation_codes (code, expires_at)
        VALUES (%s, %s)
    """, (code, expires))
    conn.commit()
    conn.close()

    return {"code": code, "expires_at": expires}

# ===== Use Code =====
@app.post("/use")
def use_code(data: AskRequest):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT used, expires_at FROM activation_codes WHERE code=%s",
        (data.code,)
    )
    row = cur.fetchone()

    if not row:
        raise HTTPException(401, "كود غير موجود")

    used, expires_at = row

    if used:
        raise HTTPException(401, "الكود مستخدم")

    if datetime.now() > expires_at:
        raise HTTPException(401, "الكود منتهي")

    cur.execute(
        "UPDATE activation_codes SET used=true WHERE code=%s",
        (data.code,)
    )
    conn.commit()
    conn.close()

    return {"message": "تم التفعيل بنجاح ✅"}