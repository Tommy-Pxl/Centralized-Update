from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
)
from database import (
    init_db,
    get_machines,
    add_machine,
    delete_machine,
    get_machine,
    get_machine_by_hostname,
    update_machine_ip,
    save_scan,
    get_scans_for_machine,
    get_latest_scan_for_machine,
    save_updates,
    get_updates_for_machine,
)
from ansible_interface import run_playbook, rebuild_inventory

import os
import json
import re

app = Flask(__name__)

# ---------------------------------------------------------
# Initialize DB
# ---------------------------------------------------------
with app.app_context():
    init_db()


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def parse_upgradable(upgradable_lines, version_list_results):
    """
    Parse `apt list --upgradable` lines and match them with
    apt-cache madison outputs from version_list_results.
    Returns a list of packages with current/from/version choices.
    """
    packages = []

    # Build map: package -> list of available versions (parsed)
    versions_map = {}
    for r in version_list_results or []:
        item = r.get("item")
        if not item:
            continue
        name = item
        lines = (r.get("stdout") or "").splitlines()

        version_choices = []
        for line in lines:
            parts = line.split("|")
            if len(parts) >= 2:
                version_choices.append(parts[1].strip())

        versions_map[name] = version_choices

    for line in upgradable_lines or []:
        if not line or line.startswith("Listing"):
            continue

        parts = line.split()
        if len(parts) < 2:
            continue

        name = parts[0].split("/")[0]
        current = parts[1]  # candidate version
        from_ver = None

        if "[upgradable from:" in line:
            idx = line.find("[upgradable from:")
            frag = line[idx:].strip("[]")
            try:
                from_ver = frag.split("upgradable from:")[1].strip()
            except Exception:
                from_ver = None

        packages.append(
            {
                "name": name,
                "current": current,
                "from": from_ver,
                "versions": versions_map.get(name, []),
            }
        )

    return packages


def parse_ansible_summary(result_text: str):
    """
    Parse Ansible play recap from raw output and classify status.

    Returns dict:
      {
        "status": "success" | "failed" | "timeout" | "unknown",
        "recap": <recap_line or None>
      }
    """
    if not result_text:
        return {"status": "unknown", "recap": None}

    # Timeout from run_playbook
    if result_text.startswith("Timed out after"):
        return {"status": "timeout", "recap": None}

    lines = result_text.splitlines()
    recap_line = None

    for line in lines:
        # Typical recap line: "ubuntu2 : ok=4 changed=3 unreachable=0 failed=1 skipped=0 ..."
        if "failed=" in line and "unreachable=" in line and ":" in line:
            recap_line = line.strip()

    if recap_line is None:
        return {"status": "unknown", "recap": None}

    failed = 0
    unreachable = 0

    m_fail = re.search(r"failed=(\d+)", recap_line)
    if m_fail:
        failed = int(m_fail.group(1))

    m_unreach = re.search(r"unreachable=(\d+)", recap_line)
    if m_unreach:
        unreachable = int(m_unreach.group(1))

    if failed == 0 and unreachable == 0:
        status = "success"
    else:
        status = "failed"

    return {"status": status, "recap": recap_line}


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------

@app.route("/")
def index():
    return redirect("/machines")


@app.route("/machines")
def machines_page():
    machines = get_machines()
    return render_template("machines.html", machines=machines)


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


@app.route("/machines/delete/<int:id>")
def machines_delete(id):
    delete_machine(id)
    rebuild_inventory()
    return redirect(url_for("machines_page"))


@app.route("/machine/<int:machine_id>")
def machine_detail(machine_id):
    machine = get_machine(machine_id)
    if not machine:
        return "Machine not found", 404

    scans = get_scans_for_machine(machine_id)
    latest_row = get_latest_scan_for_machine(machine_id)
    updates = get_updates_for_machine(machine_id)

    packages = []
    latest_timestamp = None

    if latest_row:
        _, latest_timestamp, data_json = latest_row
        try:
            data = json.loads(data_json)
        except json.JSONDecodeError:
            data = {}
        upgradable_lines = data.get("upgradable", [])
        version_list_results = data.get("version_list", [])
        packages = parse_upgradable(upgradable_lines, version_list_results)

    return render_template(
        "machine.html",
        machine=machine,
        scans=scans,
        latest_timestamp=latest_timestamp,
        packages=packages,
        updates=updates,
    )


@app.route("/scan/<int:machine_id>")
def scan(machine_id):
    machine = get_machine(machine_id)
    if not machine:
        return "Machine not found", 404

    machine_id_val, hostname, ip, username = machine

    rebuild_inventory()

    result_text = run_playbook("ansible/playbook_scan.yml", machine_id)

    json_path = f"/app/ansible/scans/{hostname}.json"

    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            data_json = f.read()
        save_scan(machine_id_val, data_json)
        return redirect(url_for("machine_detail", machine_id=machine_id_val))
    else:
        return f"<pre>{result_text}</pre>"


@app.route("/update/<int:machine_id>", methods=["GET", "POST"])
def update(machine_id):
    machine = get_machine(machine_id)
    if not machine:
        return "Machine not found", 404

    machine_id_val, hostname, ip, username = machine

    # Load latest scan to know upgradable packages
    latest_row = get_latest_scan_for_machine(machine_id_val)
    packages = []
    if latest_row:
        _, _, data_json = latest_row
        try:
            data = json.loads(data_json)
        except json.JSONDecodeError:
            data = {}
        upgradable_lines = data.get("upgradable", [])
        version_list_results = data.get("version_list", [])
        packages = parse_upgradable(upgradable_lines, version_list_results)

    if request.method == "GET":
        # Show UI with checkboxes + version dropdowns
        return render_template(
            "update.html",
            machine=machine,
            packages=packages,
        )

    # POST: we maintain two lists:
    #  - selected_ansible: what we send to Ansible (may contain "latest")
    #  - selected_db:      what we store/display, with numeric version where known
    selected_ansible = []
    selected_db = []

    # "Update ALL" path
    if "update_all" in request.form:
        for pkg in packages:
            # What Ansible sees
            selected_ansible.append({
                "name": pkg["name"],
                "version": "latest",   # still use Ansible's "latest"
            })

            # What we store/display: candidate version from scan
            target_display = pkg.get("current") or "latest"
            selected_db.append({
                "name": pkg["name"],
                "version": target_display,
            })
    else:
        # Specific selection path
        for pkg in packages:
            checkbox_name = f"select_{pkg['name']}"
            if checkbox_name in request.form:
                version_field = f"version_{pkg['name']}"
                v_raw = request.form.get(version_field, "latest") or "latest"

                # For Ansible:
                selected_ansible.append({
                    "name": pkg["name"],
                    "version": v_raw,
                })

                # For DB display:
                if v_raw == "latest":
                    target_display = pkg.get("current") or "latest"
                else:
                    target_display = v_raw

                selected_db.append({
                    "name": pkg["name"],
                    "version": target_display,
                })

    if not selected_ansible:
        return "No packages selected for update.", 400

    rebuild_inventory()

    extra_vars = {"packages": selected_ansible}
    print(f"[UPDATE] Machine {machine_id_val} ({hostname}) selected packages: {selected_ansible}")
    result = run_playbook(
        "ansible/playbook_update.yml",
        machine_id_val,
        extra_vars=extra_vars,
    )

    summary = parse_ansible_summary(result)

    # Log the update run (one row per package) using the "display" versions
    save_updates(machine_id_val, selected_db, result)

    # Show a result page with summary + full Ansible output,
    # and show the display versions there too.
    return render_template(
        "update_result.html",
        machine=machine,
        selected=selected_db,
        result=result,
        summary=summary,
    )


@app.route("/generate_enrollment_script")
def generate_enrollment_script():
    ssh_key_path = "/app/ssh/id_rsa.pub"

    if not os.path.exists(ssh_key_path):
        return f"SSH public key not found at {ssh_key_path}", 500

    with open(ssh_key_path, "r") as f:
        pubkey = f.read().strip()

    master_ip = request.host.split(":")[0]

    script = render_template(
        "client_setup.sh.j2",
        master_ip=master_ip,
        ssh_public_key=pubkey,
    )

    return script, 200, {
        "Content-Type": "text/plain",
        "Content-Disposition": "attachment; filename=client_setup.sh",
    }


@app.route("/api/enroll", methods=["POST"])
def api_enroll():
    data = request.json
    hostname = data.get("hostname")
    ip = data.get("ip")

    existing = get_machine_by_hostname(hostname)

    if existing:
        update_machine_ip(hostname, ip)
    else:
        add_machine(hostname, ip, "ansible")

    rebuild_inventory()

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
