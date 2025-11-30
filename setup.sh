#!/bin/bash
set -e

echo "======================================================"
echo "  Centralized-Update — Master VM Setup"
echo "======================================================"

#--------------------------------------------------------
# Check root
#--------------------------------------------------------
if [ "$EUID" -ne 0 ]; then
    echo "[ERROR] Run as root:"
    echo "sudo ./setup.sh"
    exit 1
fi

#--------------------------------------------------------
# Update system
#--------------------------------------------------------
echo "[+] Updating apt..."
apt update -y

#--------------------------------------------------------
# Install dependencies
#--------------------------------------------------------
echo "[+] Installing required packages..."
apt install -y python3 python3-pip curl git ansible sshpass

#--------------------------------------------------------
# Install Docker
#--------------------------------------------------------
echo "[+] Installing Docker..."
apt install -y docker.io docker-compose-plugin
usermod -aG docker $SUDO_USER

#--------------------------------------------------------
# Generate SSH keys for Ansible
#--------------------------------------------------------
if [ ! -f "/home/$SUDO_USER/.ssh/id_rsa" ]; then
    echo "[+] Generating SSH key..."
    sudo -u $SUDO_USER ssh-keygen -t rsa -b 4096 -f /home/$SUDO_USER/.ssh/id_rsa -N ""
else
    echo "[+] SSH key already exists."
fi

#--------------------------------------------------------
# Prepare inventory file
#--------------------------------------------------------
echo "[+] Preparing Ansible inventory file..."
cp ansible/inventory.ini.example ansible/inventory.ini

echo
echo "Enter the hostnames or IPs for managed VMs."
echo "Press ENTER on empty input to finish."
echo

while true; do
    read -p "Add VM: " host
    if [ -z "$host" ]; then break; fi
    echo "$host ansible_user=ansible" >> ansible/inventory.ini
done

#--------------------------------------------------------
# Build Docker images
#--------------------------------------------------------
echo "[+] Building containers..."
sudo -u $SUDO_USER docker-compose build

#--------------------------------------------------------
# Start containers
#--------------------------------------------------------
echo "[+] Starting services..."
sudo -u $SUDO_USER docker-compose up -d

#--------------------------------------------------------
# Test connectivity
#--------------------------------------------------------
echo "[+] Testing Ansible connectivity..."
ansible all -i ansible/inventory.ini -m ping || echo "Some hosts not reachable yet."

echo
echo "======================================================"
echo "  Setup Complete!"
echo "Dashboard:  http://<master-ip>:5000"
echo "======================================================"
