import subprocess
import os
from database import get_machines

INVENTORY_PATH = "/app/ansible/inventory.ini"

def ensure_ansible_dir():
    ansible_dir = "/app/ansible"
    if not os.path.isdir(ansible_dir):
        os.makedirs(ansible_dir, exist_ok=True)


def rebuild_inventory():
    ensure_ansible_dir()

    machines = get_machines()

    with open(INVENTORY_PATH, "w") as f:
        for m in machines:
            id, hostname, ip, username = m
            f.write(f"{hostname} ansible_host={ip} ansible_user={username}\n")


def run_playbook(playbook, machine_id):
    machines = {m[0]: m for m in get_machines()}
    if machine_id not in machines:
        return "Machine not found"

    id, hostname, ip, username = machines[machine_id]

    ensure_ansible_dir()

    cmd = [
        "ansible-playbook",
        "-i", INVENTORY_PATH,
        playbook,
        "--limit", hostname,
    ]

    env = os.environ.copy()
    # Disable host key checking and specify private key file
    env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
    env["ANSIBLE_PRIVATE_KEY_FILE"] = "/app/ssh/id_rsa"

    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, env=env)
        return output.decode()
    except subprocess.CalledProcessError as e:
        return e.output.decode()
