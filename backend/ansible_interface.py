import subprocess
from database import get_machines

def rebuild_inventory():
    machines = get_machines()
    with open("ansible/inventory.ini", "w") as f:
        for m in machines:
            id, hostname, ip, username = m
            f.write(f"{hostname} ansible_host={ip} ansible_user={username}\n")

def run_playbook(playbook, machine_id):
    machines = dict((m[0], m) for m in get_machines())
    if machine_id not in machines:
        return "Machine not found"

    id, hostname, ip, username = machines[machine_id]
    cmd = [
        "ansible-playbook",
        "-i", "ansible/inventory.ini",
        playbook,
        "--limit", hostname
    ]

    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return output.decode()
    except subprocess.CalledProcessError as e:
        return e.output.decode()
