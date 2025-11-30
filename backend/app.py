from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import init_db, get_machines, add_machine, delete_machine, get_machine, update_machine_ip
from ansible_interface import run_playbook, rebuild_inventory
import subprocess
import os

app = Flask(__name__)

# ---------------------------------------------------------
# Initialize DB (Flask 3 safe)
# ---------------------------------------------------------
with app.app_context():
    init_db()


# ---------------------------------------------------------
# Home redirect → /machines
# ---------------------------------------------------------
@app.route("/")
def index():
    return redirect("/machines")


# ---------------------------------------------------------
# List all machines
# ---------------------------------------------------------
@app.route("/machines")
def machines_page():
    machines = get_machines()   # returns list of tuples
    return render_template("machines.html", machines=machines)


# ---------------------------------------------------------
# Add a new machine
# ---------------------------------------------------------
@app.route("/machines/add", methods=["GET", "POST"])
def machines_add():
    if request.method == "POST":
        hostname = request.form["hostname"]
        ip = request.form["ip"]
        username = request.form["username"]

        add_machine(hostname, ip, username)
        rebuild_inventory()
        return redirect(url_for("machines_page"))

    return render_template("machine_add.html")


# ---------------------------------------------------------
# Delete machine
# ---------------------------------------------------------
@app.route("/machines/delete/<int:id>")
def machines_delete(id):
    delete_machine(id)
    rebuild_inventory()
    return redirect(url_for("machines_page"))


# ---------------------------------------------------------
# Scan machine
# ---------------------------------------------------------
@app.route("/scan/<int:machine_id>")
def scan(machine_id):
    machine = get_machine(machine_id)
    if machine is None:
        return "Machine not found", 404

    rebuild_inventory()
    result = run_playbook("ansible/playbook_scan.yml", machine_id)
    return result


# ---------------------------------------------------------
# Update machine
# ---------------------------------------------------------
@app.route("/update/<int:machine_id>")
def update(machine_id):
    machine = get_machine(machine_id)
    if machine is None:
        return "Machine not found", 404

    rebuild_inventory()
    result = run_playbook("ansible/playbook_update.yml", machine_id)
    return result


# ---------------------------------------------------------
# Generate client setup script for this VM
# ---------------------------------------------------------
@app.route("/generate_client_script/<int:machine_id>")
def generate_client_script(machine_id):
    machine = get_machine(machine_id)
    if machine is None:
        return "Machine not found", 404

    machine_id, hostname, ip, username = machine

    # Read master SSH pubkey
    ssh_key_path = f"/home/{os.getenv('USER')}/.ssh/id_rsa.pub"
    with open(ssh_key_path, "r") as f:
        pubkey = f.read().strip()

    # Detect master IP
    master_ip = subprocess.check_output("hostname -I", shell=True).decode().split()[0]

    script = render_template(
        "client_setup.sh.j2",
        master_ip=master_ip,
        ssh_public_key=pubkey,
        ansible_user=username,
        hostname=hostname
    )

    return script, 200, {
        "Content-Type": "text/plain",
        "Content-Disposition": "attachment; filename=client_setup.sh"
    }


# ---------------------------------------------------------
# AUTO ENROLL API (client calls master)
# ---------------------------------------------------------
@app.route("/api/enroll", methods=["POST"])
def api_enroll():
    data = request.json
    hostname = data.get("hostname")
    ip = data.get("ip")

    machine = get_machine_by_hostname(hostname)
    if machine:
        update_machine_ip(hostname, ip)
    else:
        add_machine(hostname, ip, "ansible")

    rebuild_inventory()

    return jsonify({"status": "ok"}), 200


# ---------------------------------------------------------
# Run app
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
