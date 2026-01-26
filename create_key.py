import uuid
from datetime import datetime, timedelta
from database import get_connection

def create_key(days=None, usage_limit=None, name=None):
    code = uuid.uuid4().hex[:16].upper()
    expires_at = None

    if days:
        expires_at = datetime.utcnow() + timedelta(days=int(days))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO activation_codes
        (code, name, is_active, expires_at, usage_limit, usage_count)
        VALUES (%s, %s, true, %s, %s, 0)
        RETURNING code
    """, (code, name, expires_at, usage_limit))

    conn.commit()
    conn.close()
    return code