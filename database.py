import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
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
            usage_count INTEGER DEFAULT 0,
            last_used_at TIMESTAMP NULL
        )
    """)

    conn.commit()
    conn.close()