#!/bin/bash

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}Starting AetherNode setup...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Update system
echo -e "${GREEN}Updating system packages...${NC}"
apt-get update
apt-get upgrade -y

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
apt-get install -y \
    python3 \
    python3-pip \
    docker.io \
    docker-compose \
    iptables \
    net-tools \
    iproute2

# Install Python packages
echo -e "${GREEN}Installing Python packages...${NC}"
pip3 install -r requirements.txt

# Enable and start Docker
echo -e "${GREEN}Configuring Docker...${NC}"
systemctl enable docker
systemctl start docker

# Configure sysctl for network optimization
echo -e "${GREEN}Configuring network optimizations...${NC}"
cat > /etc/sysctl.d/99-aethernode.conf << EOL
# TCP optimizations
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_timestamps = 0

# UDP optimizations
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.udp_rmem_min = 8192
net.ipv4.udp_wmem_min = 8192

# General network optimizations
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65536
net.ipv4.tcp_max_syn_backlog = 65536
net.ipv4.tcp_max_tw_buckets = 1440000
EOL

# Apply sysctl settings
sysctl -p /etc/sysctl.d/99-aethernode.conf

# Create data directories
echo -e "${GREEN}Creating data directories...${NC}"
mkdir -p /etc/aethernode/data
mkdir -p /etc/aethernode/config

# Set up logging
echo -e "${GREEN}Setting up logging...${NC}"
mkdir -p /var/log/aethernode
touch /var/log/aethernode/aethernode.log
chown -R $SUDO_USER:$SUDO_USER /var/log/aethernode

# Create systemd service
echo -e "${GREEN}Creating systemd service...${NC}"
cat > /etc/systemd/system/aethernode.service << EOL
[Unit]
Description=AetherNode Service
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/aethernode
ExecStart=/usr/bin/python3 src/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd
systemctl daemon-reload

# Copy files to installation directory
echo -e "${GREEN}Installing AetherNode...${NC}"
mkdir -p /opt/aethernode
cp -r . /opt/aethernode/
chown -R $SUDO_USER:$SUDO_USER /opt/aethernode

# Create requirements.txt
echo -e "${GREEN}Creating requirements.txt...${NC}"
cat > /opt/aethernode/requirements.txt << EOL
docker==6.1.3
requests==2.31.0
python-dotenv==1.0.0
EOL

# Final setup steps
echo -e "${GREEN}Performing final setup steps...${NC}"
cd /opt/aethernode
pip3 install -r requirements.txt

# Enable and start service
echo -e "${GREEN}Enabling and starting AetherNode service...${NC}"
systemctl enable aethernode
systemctl start aethernode

echo -e "${GREEN}AetherNode setup completed successfully!${NC}"
echo -e "You can check the status using: systemctl status aethernode"
echo -e "View logs using: journalctl -u aethernode -f" 