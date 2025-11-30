import subprocess
from database import get_machine, get_machines

INVENTORY_PATH = "ansible/inventory.ini"

def rebuild_inventory():
    machines = get_machines()
    with open(INVENTORY_PATH, "w") as f:
        for m in machines:
            f.write(f"{m[2]} ansible_user={m[3]}\n")
    print("[+] Inventory rebuilt.")

def run_playbook(playbook, machine_id):
    machine = get_machine(machine_id)
    target = machine[2]

    cmd = [
        "ansible-playbook",
        playbook,
        "-i", INVENTORY_PATH,
        "--extra-vars", f"target={target}"
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return "<pre>" + result.stdout + "</pre>"
