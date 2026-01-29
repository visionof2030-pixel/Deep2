# key_logic.py
from datetime import datetime
from fastapi import HTTPException
from database import get_connection

def verify_code(code: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, is_active, expires_at, usage_limit, usage_count
        FROM activation_codes
        WHERE code = %s
        """,
        (code,)
    )

    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid activation code")

    # ✅ لأننا نستخدم RealDictCursor
    is_active = row["is_active"]
    expires_at = row["expires_at"]
    usage_limit = row["usage_limit"]
    usage_count = row["usage_count"]
    code_id = row["id"]

    if not is_active:
        raise HTTPException(status_code=401, detail="Activation code disabled")

    if expires_at and datetime.utcnow() > expires_at:
        raise HTTPException(status_code=401, detail="Activation code expired")

    if usage_limit is not None and usage_count >= usage_limit:
        raise HTTPException(status_code=401, detail="Usage limit reached")

    # تحديث الاستخدام
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE activation_codes
        SET usage_count = usage_count + 1,
            last_used_at = %s
        WHERE id = %s
        """,
        (datetime.utcnow(), code_id)
    )
    conn.commit()
    conn.close()