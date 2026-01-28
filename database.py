import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS activation_codes (
            id SERIAL PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            device_id TEXT,
            activated_at TIMESTAMP,
            last_seen TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()