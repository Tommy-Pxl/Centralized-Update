import subprocess
import json

ANSIBLE_CONTAINER = "centralized_update_ansible_runner"

def run_scan(hostname):
    cmd = [
        "docker", "exec", ANSIBLE_CONTAINER,
        "python3", "runner.py", "playbook_scan.yml",
        json.dumps({"target": hostname})
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout


def run_update(hostname, package, version):
    cmd = [
        "docker", "exec", ANSIBLE_CONTAINER,
        "python3", "runner.py", "playbook_update.yml",
        json.dumps({
            "target": hostname,
            "package": package,
            "version": version
        })
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout
