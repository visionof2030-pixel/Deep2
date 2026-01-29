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
        VALUES (%s, TRUE, %s, %s, %s, 0)
        RETURNING code
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