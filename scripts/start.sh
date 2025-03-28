#!/bin/bash

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Function to check if a service is running
check_service() {
    if systemctl is-active --quiet $1; then
        echo -e "${GREEN}$1 is running${NC}"
        return 0
    else
        echo -e "${RED}$1 is not running${NC}"
        return 1
    fi
}

# Check required services
echo "Checking required services..."
check_service docker || {
    echo -e "${RED}Docker is not running. Starting Docker...${NC}"
    systemctl start docker
}

# Clean up any existing containers
echo -e "${GREEN}Cleaning up existing containers...${NC}"
docker ps -a | grep 'earnapp_' | awk '{print $1}' | xargs -r docker rm -f

# Apply network optimizations
echo -e "${GREEN}Applying network optimizations...${NC}"
sysctl -p /etc/sysctl.d/99-aethernode.conf

# Start AetherNode service
echo -e "${GREEN}Starting AetherNode service...${NC}"
systemctl restart aethernode

# Wait for service to start
echo -e "${GREEN}Waiting for service to initialize...${NC}"
sleep 3

# Check service status
if systemctl is-active --quiet aethernode; then
    echo -e "${GREEN}AetherNode started successfully!${NC}"
    echo -e "View logs using: journalctl -u aethernode -f"
else
    echo -e "${RED}Failed to start AetherNode${NC}"
    echo -e "Check logs using: journalctl -u aethernode -e"
    exit 1
fi

# Display running containers
echo -e "\n${GREEN}Running containers:${NC}"
docker ps | grep 'earnapp_'

# Display network status
echo -e "\n${GREEN}Network configuration:${NC}"
ip a | grep -A 2 'eth0:'
echo -e "\nTCP BBR status:"
sysctl net.ipv4.tcp_congestion_control

# Display memory status
echo -e "\n${GREEN}Memory configuration:${NC}"
free -h

echo -e "\n${GREEN}Setup complete! AetherNode is now running.${NC}"
echo -e "Use 'systemctl status aethernode' to check the service status"
echo -e "Use 'journalctl -u aethernode -f' to view logs" 