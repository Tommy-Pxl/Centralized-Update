import sqlite3

DB_PATH = "centralized_update.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # existing tables...
    c.execute("""
    CREATE TABLE IF NOT EXISTS machines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostname TEXT NOT NULL,
        ip TEXT NOT NULL UNIQUE,
        username TEXT DEFAULT 'ansible',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def add_machine(hostname, ip, username="ansible"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO machines (hostname, ip, username) VALUES (?, ?, ?)",
              (hostname, ip, username))
    conn.commit()
    conn.close()

def delete_machine(machine_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM machines WHERE id=?", (machine_id,))
    conn.commit()
    conn.close()

def get_machines():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, hostname, ip, username FROM machines")
    rows = c.fetchall()
    conn.close()
    return rows

def get_machine(machine_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, hostname, ip, username FROM machines WHERE id=?", (machine_id,))
    row = c.fetchone()
    conn.close()
    return row
