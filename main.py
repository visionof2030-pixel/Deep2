from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import psycopg2
import os
import uuid

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

# ================== اتصال قاعدة البيانات ==================
def get_db():
    return psycopg2.connect(DATABASE_URL)

# ================== نماذج الطلب ==================
class GenerateReq(BaseModel):
    days_valid: int

class UseReq(BaseModel):
    code: str
    prompt: str

# ================== اختبار السيرفر ==================
@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now()}

# ================== توليد كود تفعيل ==================
@app.post("/admin/generate")
def generate_code(
    data: GenerateReq,
    x_admin_token: str = Header(None)
):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    code = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(days=data.days_valid)

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO activation_codes (code, expires_at)
        VALUES (%s, %s)
        """,
        (code, expires_at)
    )
    conn.commit()
    cur.close()
    conn.close()

    return {
        "code": code,
        "expires_at": expires_at
    }

# ================== استخدام الأداة بالكود ==================
@app.post("/use")
def use_tool(data: UseReq):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT used, expires_at
        FROM activation_codes
        WHERE code = %s
        """,
        (data.code,)
    )

    row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=400, detail="كود غير موجود")

    used, expires_at = row

    if used:
        raise HTTPException(status_code=400, detail="الكود مستخدم مسبقًا")

    if expires_at < datetime.now():
        raise HTTPException(status_code=400, detail="الكود منتهي")

    # 🔒 يمكن جعله يُستهلك مرة واحدة (اختياري)
    cur.execute(
        "UPDATE activation_codes SET used = TRUE WHERE code = %s",
        (data.code,)
    )
    conn.commit()

    cur.close()
    conn.close()

    # ====== منطق الأداة (تجربة فقط) ======
    answer = (
        "تم قبول الكود بنجاح ✅\n\n"
        f"سؤالك:\n{data.prompt}\n\n"
        "هذا رد تجريبي من الأداة المقفلة."
    )

    return {"answer": answer}