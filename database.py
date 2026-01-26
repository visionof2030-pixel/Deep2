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