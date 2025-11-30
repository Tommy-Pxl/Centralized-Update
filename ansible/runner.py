import sys
import json
import subprocess

if len(sys.argv) < 3:
    print("Usage: runner.py <playbook> <json_vars>")
    sys.exit(1)

playbook = sys.argv[1]
extra_vars = json.loads(sys.argv[2])

cmd = [
    "ansible-playbook",
    playbook,
    "-i", "inventory.ini",
    "--extra-vars", json.dumps(extra_vars)
]

result = subprocess.run(cmd, capture_output=True, text=True)

# Print raw output so backend can parse
print(result.stdout)

# Print stderr for debugging (but does not break parsing)
if result.stderr.strip():
    print(result.stderr)
