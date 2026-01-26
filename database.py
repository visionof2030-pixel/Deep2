import sqlite3

DB_PATH = "data.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS activation_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            name TEXT,
            is_active INTEGER,
            expires_at TEXT,
            usage_limit INTEGER,
            usage_count INTEGER
        )
    """)
    conn.commit()
    conn.close()