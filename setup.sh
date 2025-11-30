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
# Install Docker (universal method, works on all Ubuntu versions)
#--------------------------------------------------------
echo "[+] Installing Docker (universal method)..."

# Remove old Docker versions (if present)
apt remove -y docker docker-engine docker.io containerd runc || true

# Install prerequisites
apt install -y ca-certificates curl gnupg lsb-release

# Add Docker’s official GPG key
mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" \
  > /etc/apt/sources.list.d/docker.list

# Update again and install actual Docker packages
apt update -y
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Allow the primary user to run docker
usermod -aG docker $SUDO_USER
echo "[+] Docker installed successfully!"

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
