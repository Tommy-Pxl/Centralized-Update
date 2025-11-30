# Centralized-Update
A centralized web-based update management system for Linux VMs using:

- Python Flask (web dashboard & API)
- SQLite3 (logging & inventory database)
- Ansible (remote execution)
- Docker (containerization)
- SSH (secure VM access)

All components run on a single master VM.

---

## Features

### VM Management
- Add unlimited client VMs
- Managed over SSH using Ansible
- Dashboard shows all connected systems

### Software Inventory
- Displays all installed packages per VM
- Shows available updates (apt)
- Highlights out-of-date software

### Update Actions
- Update to latest version
- Update to a specific version (dropdown)
- View changelog / version differences

### Logging
- Logs before/after versions
- Logs changelog entries
- Logs timestamp
- Logs who performed the update
- All data stored in SQLite database

---

## Architecture

