#!/bin/bash
set -e

echo "======================================================"
echo "  Centralized-Update — Master VM Setup"
echo "======================================================"

if [ "$EUID" -ne 0 ]; then
    echo "[ERROR] Run as root:"
    echo "sudo ./setup.sh"
    exit 1
fi

echo "[+] Updating apt..."
apt update -y

echo "[+] Installing base packages..."
apt install -y python3 python3-pip curl git ansible sshpass

echo "[+] Installing Docker (universal method)..."
apt remove -y docker docker-engine docker.io containerd runc || true

apt install -y ca-certificates curl gnupg lsb-release

mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" \
  > /etc/apt/sources.list.d/docker.list

apt update -y
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

usermod -aG docker $SUDO_USER
systemctl enable docker
echo "[+] Docker installed successfully!"

if [ ! -f "/home/$SUDO_USER/.ssh/id_rsa" ]; then
    echo "[+] Generating SSH key..."
    sudo -u $SUDO_USER ssh-keygen -t rsa -b 4096 -f /home/$SUDO_USER/.ssh/id_rsa -N ""
else
    echo "[+] SSH key already exists."
fi

echo "[+] Creating empty dynamic inventory..."
touch ansible/inventory.ini

echo "[+] Building containers..."
sudo -u $SUDO_USER docker compose build

echo "[+] Starting services..."
sudo -u $SUDO_USER docker compose up -d

MASTER_IP=$(hostname -I | awk '{print $1}')
echo
echo "======================================================"
echo "  Setup Complete!"
echo "  Dashboard: http://$MASTER_IP:5000"
echo "======================================================"
