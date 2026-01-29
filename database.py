# database.py
import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS activation_codes (
        id SERIAL PRIMARY KEY,
        code TEXT UNIQUE,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP,
        expires_at TIMESTAMP,
        usage_limit INTEGER,
        usage_count INTEGER DEFAULT 0,
        last_used_at TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()