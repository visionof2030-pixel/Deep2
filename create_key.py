import uuid
from datetime import datetime, timedelta
from database import get_connection

def create_key(days=None, usage_limit=None, customer_name=None):
    code = str(uuid.uuid4()).upper().replace("-", "")[:16]
    expires_at = None

    if days:
        expires_at = (datetime.utcnow() + timedelta(days=days)).isoformat()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO activation_codes 
        (code, customer_name, is_active, expires_at, usage_limit, usage_count)
        VALUES (?, ?, 1, ?, ?, 0)
        """,
        (code, customer_name, expires_at, usage_limit)
    )
    conn.commit()
    conn.close()
    return code