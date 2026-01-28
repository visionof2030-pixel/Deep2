import uuid
from datetime import datetime, timedelta
from database import get_connection

def create_key(days=30, usage_limit=100):
    code = uuid.uuid4().hex[:16].upper()
    expires_at = datetime.utcnow() + timedelta(days=days)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO activation_codes (code, expires_at, usage_limit)
        VALUES (%s, %s, %s)
    """, (code, expires_at, usage_limit))

    conn.commit()
    conn.close()
    return code