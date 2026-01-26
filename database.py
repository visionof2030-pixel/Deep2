import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    if not DATABASE_URL:
        raise Exception("DATABASE_URL not set")
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS activation_codes (
            id SERIAL PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            name TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            expires_at TIMESTAMP NULL,
            usage_limit INTEGER NULL,
            usage_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()