import subprocess
import os
import json
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


def run_playbook(playbook, machine_id, extra_vars=None):
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

    if extra_vars is not None:
        cmd.extend(["-e", json.dumps(extra_vars)])

    env = os.environ.copy()
    env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
    env["ANSIBLE_PRIVATE_KEY_FILE"] = "/app/ssh/id_rsa"
    print(f"[ANSIBLE] Running on {hostname}: {' '.join(cmd)}")
    if extra_vars:
        print(f"[ANSIBLE] extra_vars = {json.dumps(extra_vars)}")

    try:
        output = subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            env=env,
        )
        print(f"[ANSIBLE] Completed playbook for {hostname}")
        return output.decode()
    except subprocess.CalledProcessError as e:
        print(f"[ANSIBLE] ERROR for {hostname}")
        return e.output.decode()
