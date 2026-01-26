from fastapi import Header, HTTPException
from datetime import datetime
from database import get_connection

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
        conn.close()
        raise HTTPException(401, "Invalid code")

    code_id, active, expires, limit, used = row

    if not active:
        conn.close()
        raise HTTPException(401, "Code disabled")

    if expires and expires < datetime.utcnow():
        conn.close()
        raise HTTPException(401, "Code expired")

    if limit and used >= limit:
        conn.close()
        raise HTTPException(401, "Usage limit reached")

    cur.execute(
        "UPDATE activation_codes SET usage_count = usage_count + 1 WHERE id=%s",
        (code_id,)
    )
    conn.commit()
    conn.close()