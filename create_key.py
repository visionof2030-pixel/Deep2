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
        (code, created_at, expires_at, usage_limit)
        VALUES (%s, %s, %s, %s)
        """,
        (
            code,
            datetime.utcnow(),
            expires_at,
            usage_limit
        )
    )
    conn.commit()
    conn.close()
    return code