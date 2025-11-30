from flask import Flask, render_template, request, redirect, url_for
from database import init_db, get_machines, add_machine, delete_machine
from ansible_interface import run_playbook, rebuild_inventory

app = Flask(__name__)

# ---------------------------------------------------------
# Initialize database immediately (Flask 3 removed before_first_request)
# ---------------------------------------------------------
with app.app_context():
    init_db()


# ---------------------------------------------------------
# Home page (optional, if you have an index.html)
# ---------------------------------------------------------
@app.route("/")
def index():
    return redirect("/machines")


# ---------------------------------------------------------
# Machines page
# ---------------------------------------------------------
@app.route("/machines")
def machines_page():
    machines = get_machines()
    return render_template("machines.html", machines=machines)


# ---------------------------------------------------------
# Add machine
# ---------------------------------------------------------
@app.route("/machines/add", methods=["GET", "POST"])
def machines_add():
    if request.method == "POST":
        hostname = request.form["hostname"]
        ip = request.form["ip"]
        username = request.form.get("username", "ansible")

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
    rebuild_inventory()
    result = run_playbook("ansible/playbook_scan.yml", machine_id)
    return result


# ---------------------------------------------------------
# Update machine
# ---------------------------------------------------------
@app.route("/update/<int:machine_id>")
def update(machine_id):
    rebuild_inventory()
    result = run_playbook("ansible/playbook_update.yml", machine_id)
    return result


# ---------------------------------------------------------
# Run app
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
