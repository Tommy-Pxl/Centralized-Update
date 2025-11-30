import sqlite3
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "centralized_update.db")


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Machines table
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hostname TEXT,
            ip TEXT,
            username TEXT
        )
        """
    )

    # Scans table
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id INTEGER,
            timestamp TEXT,
            data TEXT
        )
        """
    )

    # Updates table (with status + result)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id INTEGER,
            timestamp TEXT,
            package TEXT,
            version TEXT,
            status TEXT,
            result TEXT
        )
        """
    )

    # Ensure new columns exist on older DBs
    c.execute("PRAGMA table_info(updates)")
    cols = [row[1] for row in c.fetchall()]

    if "status" not in cols:
        try:
            c.execute("ALTER TABLE updates ADD COLUMN status TEXT")
        except sqlite3.OperationalError:
            pass

    if "result" not in cols:
        try:
            c.execute("ALTER TABLE updates ADD COLUMN result TEXT")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()


# ----------------------------------------------------
# Machines
# ----------------------------------------------------

def get_machines():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, hostname, ip, username FROM machines ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows


def add_machine(hostname, ip, username):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO machines (hostname, ip, username) VALUES (?, ?, ?)",
        (hostname, ip, username),
    )
    conn.commit()
    conn.close()


def delete_machine(machine_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM machines WHERE id = ?", (machine_id,))
    conn.commit()
    conn.close()


def get_machine(machine_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT id, hostname, ip, username FROM machines WHERE id = ?",
        (machine_id,),
    )
    row = c.fetchone()
    conn.close()
    return row


def get_machine_by_hostname(hostname):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT id, hostname, ip, username FROM machines WHERE hostname = ?",
        (hostname,),
    )
    row = c.fetchone()
    conn.close()
    return row


def update_machine_ip(hostname, ip):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE machines SET ip = ? WHERE hostname = ?",
        (ip, hostname),
    )
    conn.commit()
    conn.close()


# ----------------------------------------------------
# Scans
# ----------------------------------------------------

def save_scan(machine_id, data_json):
    conn = get_conn()
    c = conn.cursor()
    ts = datetime.datetime.utcnow().isoformat()
    c.execute(
        "INSERT INTO scans (machine_id, timestamp, data) VALUES (?, ?, ?)",
        (machine_id, ts, data_json),
    )
    conn.commit()
    conn.close()


def get_scans_for_machine(machine_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT id, timestamp FROM scans WHERE machine_id = ? ORDER BY id DESC",
        (machine_id,),
    )
    rows = c.fetchall()
    conn.close()
    return rows


def get_latest_scan_for_machine(machine_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT id, timestamp, data FROM scans WHERE machine_id = ? ORDER BY id DESC LIMIT 1",
        (machine_id,),
    )
    row = c.fetchone()
    conn.close()
    return row


# ----------------------------------------------------
# Updates
# ----------------------------------------------------

def _classify_status(result_text, pkg_name):
    """
    Very simple per-package status classifier based on Ansible output.

    - Looks for lines like:
        changed: [ubuntu] => (item=pkg)
        ok: [ubuntu] => (item=pkg)
        skipping: [ubuntu] => (item=pkg)
        failed: [ubuntu] (item=pkg=version)

    - Returns: "Success", "Failed", "Skipped", or "Unknown".
    """
    if not result_text:
        return "Unknown"

    needle = f"(item={pkg_name}"
    lines = result_text.splitlines()

    for line in lines:
        if needle not in line:
            continue
        line = line.strip()
        if line.startswith("failed: ["):
            return "Failed"
        if line.startswith("changed: [") or line.startswith("ok: ["):
            return "Success"
        if line.startswith("skipping: ["):
            return "Skipped"

    return "Unknown"


def save_updates(machine_id, packages, result_text):
    """
    `packages` is a list of dicts:
      { "name": <pkg_name>, "version": <display_version> }

    We insert one row per package with a per-package status.
    """
    conn = get_conn()
    c = conn.cursor()
    ts = datetime.datetime.utcnow().isoformat()

    for pkg in packages:
        name = pkg.get("name")
        version = pkg.get("version")
        status = _classify_status(result_text, name)

        c.execute(
            """
            INSERT INTO updates (machine_id, timestamp, package, version, status, result)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (machine_id, ts, name, version, status, result_text),
        )

    conn.commit()
    conn.close()


def get_updates_for_machine(machine_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """
        SELECT id, timestamp, package, version, status
        FROM updates
        WHERE machine_id = ?
        ORDER BY id DESC
        """,
        (machine_id,),
    )
    rows = c.fetchall()
    conn.close()
    return rows
