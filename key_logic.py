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

    if not row:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid activation code")

    code_id, is_active, expires_at, usage_limit, usage_count = row

    if not is_active:
        conn.close()
        raise HTTPException(status_code=401, detail="Activation code disabled")

    if expires_at and datetime.utcnow() > expires_at:
        cur.execute(
            "UPDATE activation_codes SET is_active = FALSE WHERE id = %s",
            (code_id,)
        )
        conn.commit()
        conn.close()
        raise HTTPException(status_code=401, detail="Activation code expired")

    if usage_limit is not None and usage_count >= usage_limit:
        cur.execute(
            "UPDATE activation_codes SET is_active = FALSE WHERE id = %s",
            (code_id,)
        )
        conn.commit()
        conn.close()
        raise HTTPException(status_code=401, detail="Usage limit reached")

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