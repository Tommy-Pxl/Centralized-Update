import sqlite3
from datetime import datetime

DB_PATH = "centralized_update.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Machines table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hostname TEXT,
            ip TEXT,
            username TEXT
        )
    """)

    # Scan history table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id INTEGER,
            timestamp TEXT,
            data TEXT,
            FOREIGN KEY(machine_id) REFERENCES machines(id)
        )
    """)

    conn.commit()
    conn.close()


# ---------------- Machines ---------------- #

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
    cur.execute(
        "INSERT INTO machines (hostname, ip, username) VALUES (?, ?, ?)",
        (hostname, ip, username),
    )
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
    cur.execute(
        "SELECT id, hostname, ip, username FROM machines WHERE id = ?",
        (id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def get_machine_by_hostname(hostname):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, hostname, ip, username FROM machines WHERE hostname = ?",
        (hostname,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def update_machine_ip(hostname, new_ip):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE machines SET ip = ? WHERE hostname = ?",
        (new_ip, hostname),
    )
    conn.commit()
    conn.close()


# ---------------- Scans ---------------- #

def save_scan(machine_id, data_json):
    conn = get_db()
    cur = conn.cursor()
    ts = datetime.utcnow().isoformat()
    cur.execute(
        "INSERT INTO scans (machine_id, timestamp, data) VALUES (?, ?, ?)",
        (machine_id, ts, data_json),
    )
    conn.commit()
    conn.close()


def get_scans_for_machine(machine_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, timestamp, data FROM scans WHERE machine_id = ? "
        "ORDER BY id DESC",
        (machine_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_latest_scan_for_machine(machine_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, timestamp, data FROM scans WHERE machine_id = ? "
        "ORDER BY id DESC LIMIT 1",
        (machine_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row
