import uuid
from datetime import datetime, timedelta
from database import get_connection

def create_key(days=None, usage_limit=None):
    code = str(uuid.uuid4()).upper().replace("-", "")[:16]
    expires_at = None

    if days:
        expires_at = datetime.utcnow() + timedelta(days=days)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO activation_codes
        (code, is_active, expires_at, usage_limit, usage_count)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (code, True, expires_at, usage_limit, 0)
    )
    conn.commit()
    conn.close()
    return code