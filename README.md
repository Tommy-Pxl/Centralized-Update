# Centralized-Update
A centralized web-based update management system for Ubuntu VMs using:

- Python Flask (web dashboard & API)
- SQLite3 (logging & inventory database)
- Ansible (remote execution)
- Docker (containerization)
- SSH (secure VM access)

I dont know anymore, 
it goes like

clone this, run setup
it will run a set up docker and all prereqs, 
then it will grab docker, install ansible and run flask (pythonAPIthingy)

the VM that runs setup.sh will be the controller vm

clients on the same network can access the ip of the controller VM and "enroll"
run the enrollment script on the client vm
updates can be scanned on the VM, and results saved to a database, 

when updates are applied, prior version info and current version info is also saved alongside timestamps

