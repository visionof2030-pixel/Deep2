# create_key.py
import uuid
from datetime import datetime
from database import get_connection

def create_key(expires_at=None, usage_limit=None):
    code = str(uuid.uuid4())
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO activation_codes
        (code, is_active, created_at, expires_at, usage_limit, usage_count)
        VALUES (?, 1, ?, ?, ?, 0)
        """,
        (
            code,
            datetime.utcnow().isoformat(),
            expires_at,
            usage_limit
        )
    )
    conn.commit()
    conn.close()
    return code
