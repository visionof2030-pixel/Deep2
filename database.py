import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS activation_codes (
        code TEXT PRIMARY KEY,
        used BOOLEAN DEFAULT FALSE,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def validate_code(code: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM activation_codes
        WHERE code=%s AND used=false AND expires_at > NOW()
    """, (code,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE activation_codes SET used=true WHERE code=%s", (code,))
        conn.commit()
    cur.close()
    conn.close()
    return row is not None