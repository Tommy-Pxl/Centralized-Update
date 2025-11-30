import sqlite3

DB_PATH = "centralized_update.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hostname TEXT,
            ip TEXT,
            username TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_machines():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, hostname, ip, username FROM machines")
    rows = cur.fetchall()
    conn.close()
    return rows

def add_machine(hostname, ip, username):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO machines (hostname, ip, username) VALUES (?, ?, ?)", 
                (hostname, ip, username))
    conn.commit()
    conn.close()

def delete_machine(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM machines WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def get_machine(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, hostname, ip, username FROM machines WHERE id = ?", (id,))
    machine = cur.fetchone()
    conn.close()
    return machine

def get_machine_by_hostname(hostname):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, hostname, ip, username FROM machines WHERE hostname = ?", (hostname,))
    machine = cur.fetchone()
    conn.close()
    return machine

def update_machine_ip(hostname, new_ip):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE machines SET ip = ? WHERE hostname = ?", (new_ip, hostname))
    conn.commit()
    conn.close()
