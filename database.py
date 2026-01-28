import sqlite3
from datetime import datetime

DB = "data.db"

def get_connection():
    return sqlite3.connect(DB)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS passwords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        password TEXT UNIQUE,
        expires_at TEXT
    )
    """)
    conn.commit()
    conn.close()

def is_valid_password(pw: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT expires_at FROM passwords WHERE password=?",
        (pw,)
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return False

    return datetime.utcnow() < datetime.fromisoformat(row[0])