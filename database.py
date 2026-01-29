import sqlite3

DATABASE = "/data/database.db"

def get_connection():
    return sqlite3.connect(DATABASE, check_same_thread=False)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS activation_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        is_active INTEGER,
        created_at TEXT,
        expires_at TEXT,
        usage_limit INTEGER,
        usage_count INTEGER,
        last_used_at TEXT
    )
    """)
    conn.commit()
    conn.close()