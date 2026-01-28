from fastapi import Header, HTTPException
from database import get_connection
from datetime import datetime

def activation_required(x_activation_code: str = Header(...)):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, is_active, expires_at, usage_limit, usage_count
        FROM activation_codes
        WHERE code=%s
    """, (x_activation_code,))
    row = cur.fetchone()

    if not row:
        raise HTTPException(401, "Invalid code")

    code_id, active, expires, limit, used = row

    if not active:
        raise HTTPException(401, "Code disabled")

    if expires and datetime.utcnow() > expires:
        raise HTTPException(401, "Code expired")

    if limit and used >= limit:
        raise HTTPException(401, "Usage limit reached")

    cur.execute(
        "UPDATE activation_codes SET usage_count = usage_count + 1 WHERE id=%s",
        (code_id,)
    )
    conn.commit()
    conn.close()