import uuid
from datetime import datetime, timedelta
from database import get_connection

def create_key(days=None, usage_limit=None):
    code = uuid.uuid4().hex[:16].upper()
    expires_at = None

    if days:
        expires_at = datetime.utcnow() + timedelta(days=int(days))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO activation_codes
        (code, is_active, expires_at, usage_limit, usage_count)
        VALUES (%s, true, %s, %s, 0)
    """, (code, expires_at, usage_limit))
    conn.commit()
    conn.close()
    return code