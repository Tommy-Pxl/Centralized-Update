from flask import Flask, render_template, redirect, request
import re, json
from datetime import datetime
from database import SessionLocal, Base, engine
from models import Machine, Software, UpdateHistory
import ansible_interface

# Create tables if not exist
Base.metadata.create_all(bind=engine)

app = Flask(__name__)


# -----------------------------------------------------------
# HOME PAGE
# -----------------------------------------------------------
@app.route("/")
def index():
    session = SessionLocal()
    machines = session.query(Machine).all()
    session.close()
    return render_template("index.html", machines=machines)


# -----------------------------------------------------------
# ADD MACHINE
# -----------------------------------------------------------
@app.route("/add_machine", methods=["POST"])
def add_machine():
    hostname = request.form.get("hostname")

    session = SessionLocal()
    m = Machine(hostname=hostname)
    session.add(m)
    session.commit()
    session.close()

    return redirect("/")


# -----------------------------------------------------------
# SCAN MACHINE
# -----------------------------------------------------------
@app.route("/scan/<hostname>")
def scan_machine(hostname):

    # Run ansible scan
    raw_output = ansible_interface.run_scan(hostname)

    # Convert Ansible’s debug msg block to Python dict safely
    match = re.search(r"\"msg\": ({.*?})\s*\}", raw_output, re.S)
    if not match:
        return f"Scan failed. Raw output:<br><pre>{raw_output}</pre>"

    data = json.loads(match.group(1))

    installed_raw = data["installed"]
    upgradable_raw = data["upgradable"]
    changelog_raw = data["changelogs"]

    # ----------------------------------------
    # Parse installed packages
    # ----------------------------------------
    installed_packages = []
    for line in installed_raw.splitlines():
        # Format: pkg/version status
        if "/" in line and "[" not in line:
            try:
                pkg = line.split("/")[0]
                version = line.split()[-1]
                installed_packages.append((pkg, version))
            except:
                pass

    # ----------------------------------------
    # Parse upgradable packages
    # ----------------------------------------
    upgradable_packages = {}
    for line in upgradable_raw.splitlines():
        # Format:
        # pkg/version <new-version> [upgradable from: old]
        if "upgradable" in line.lower():
            try:
                pkg = line.split("/")[0]
                new_ver = line.split()[1]  # second token is usually version
                upgradable_packages[pkg] = new_ver
            except:
                pass

    # ----------------------------------------
    # Update DB
    # ----------------------------------------
    session = SessionLocal()
    machine = session.query(Machine).filter_by(hostname=hostname).first()

    if machine is None:
        session.close()
        return f"Machine {hostname} not found!"

    # Clear old software entries
    session.query(Software).filter_by(machine_id=machine.id).delete()

    # Insert fresh scan results
    for pkg, ver in installed_packages:
        new_ver = upgradable_packages.get(pkg)
        s = Software(
            machine_id=machine.id,
            package=pkg,
            installed_version=ver,
            new_version=new_ver,
            last_checked=datetime.utcnow()
        )
        session.add(s)

    machine.last_scanned = datetime.utcnow()
    session.commit()
    session.close()

    return redirect(f"/machine/{hostname}")


# -----------------------------------------------------------
# MACHINE SOFTWARE PAGE
# -----------------------------------------------------------
@app.route("/machine/<hostname>")
def machine_page(hostname):
    session = SessionLocal()
    machine = session.query(Machine).filter_by(hostname=hostname).first()
    software = session.query(Software).filter_by(machine_id=machine.id).all()
    session.close()
    return render_template("machine.html", machine=machine, software=software)


# -----------------------------------------------------------
# UPDATE PACKAGE
# -----------------------------------------------------------
@app.route("/update/<hostname>/<package>/<version>")
def update_package(hostname, package, version):

    raw = ansible_interface.run_update(hostname, package, version)

    session = SessionLocal()
    machine = session.query(Machine).filter_by(hostname=hostname).first()

    # Get previous version
    sw = session.query(Software).filter_by(
        machine_id=machine.id,
        package=package
    ).first()

    before_version = sw.installed_version if sw else "unknown"

    # Log update
    entry = UpdateHistory(
        machine_id=machine.id,
        package=package,
        old_version=before_version,
        new_version=version,
        timestamp=datetime.utcnow(),
        performed_by="admin",
        notes=raw
    )
    session.add(entry)
    session.commit()
    session.close()

    return redirect(f"/machine/{hostname}")


# -----------------------------------------------------------
# VIEW UPDATE HISTORY
# -----------------------------------------------------------
@app.route("/history/<hostname>")
def history_page(hostname):
    session = SessionLocal()
    machine = session.query(Machine).filter_by(hostname=hostname).first()
    history = session.query(UpdateHistory).filter_by(machine_id=machine.id).all()
    session.close()
    return render_template("history.html", machine=machine, history=history)


# -----------------------------------------------------------
# VIEW CHANGELOG (raw)
# -----------------------------------------------------------
@app.route("/changelog/<hostname>/<package>")
def view_changelog(hostname, package):

    raw = ansible_interface.run_scan(hostname)

    match = re.search(r"\"changelogs\": \[(.*?\])", raw, re.S)
    changelog_text = match.group(1) if match else "No changelog found."

    return render_template("changelog.html",
                           hostname=hostname,
                           package=package,
                           changelog=changelog_text)


# -----------------------------------------------------------
# SELECT SPECIFIC VERSION
# -----------------------------------------------------------
@app.route("/versions/<hostname>/<package>")
def select_version(hostname, package):
    raw = ansible_interface.run_scan(hostname)

    # Extract version list
    match = re.search(r"\"version_list\": \[(.*?)\]", raw, re.S)
    if not match:
        return "No version list found."

    block = match.group(1)

    versions = []
    for line in block.splitlines():
        if package in line and "|" in line:
            parts = line.split("|")
            if len(parts) > 1:
                versions.append(parts[1].strip())

    return render_template("version_select.html",
                           hostname=hostname,
                           package=package,
                           versions=versions)


# -----------------------------------------------------------
# APP START
# -----------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
