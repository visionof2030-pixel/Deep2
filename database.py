# database.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS frontend_passwords (
        id SERIAL PRIMARY KEY,
        password TEXT UNIQUE NOT NULL,
        expires_at TIMESTAMP NOT NULL
    );
    """)

    conn.commit()
    conn.close()