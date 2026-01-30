from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import os
import uuid
import psycopg2

# ================== إعداد التطبيق ==================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

# ================== قاعدة البيانات ==================
def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS activation_codes (
        code TEXT PRIMARY KEY,
        used BOOLEAN DEFAULT FALSE,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

# تُنفَّذ مرة عند تشغيل السيرفر
init_db()

# ================== الحماية (أدمن) ==================
def admin_required(x_admin_token: str = Header(...)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

# ================== نماذج ==================
class GenerateReq(BaseModel):
    days_valid: int = 1  # عدد أيام الصلاحية

class ActivateReq(BaseModel):
    code: str

# ================== اختبار السيرفر ==================
@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now()}

# ================== توليد كود (أدمن) ==================
@app.post("/admin/generate", dependencies=[Depends(admin_required)])
def generate_code(data: GenerateReq):
    code = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(days=data.days_valid)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO activation_codes (code, expires_at) VALUES (%s, %s)",
        (code, expires_at)
    )
    conn.commit()
    cur.close()
    conn.close()

    return {
        "code": code,
        "expires_at": expires_at
    }

# ================== تفعيل الكود (مستخدم) ==================
@app.post("/activate")
def activate_code(data: ActivateReq):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT used, expires_at FROM activation_codes WHERE code = %s",
        (data.code,)
    )
    row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=400, detail="كود غير موجود")

    used, expires_at = row

    if used:
        raise HTTPException(status_code=400, detail="الكود مستخدم")

    if expires_at < datetime.now():
        raise HTTPException(status_code=400, detail="الكود منتهي")

    cur.execute(
        "UPDATE activation_codes SET used = TRUE WHERE code = %s",
        (data.code,)
    )
    conn.commit()
    cur.close()
    conn.close()

    return {"status": "activated"}