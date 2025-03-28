#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

echo -e "${GREEN}AetherNode Installation Script${NC}"
echo "================================"

# Function to check system requirements
check_requirements() {
    echo -e "\n${YELLOW}Checking system requirements...${NC}"
    
    # Check CPU cores
    CPU_CORES=$(nproc)
    if [ "$CPU_CORES" -lt 2 ]; then
        echo -e "${RED}Error: At least 2 CPU cores required. Found: $CPU_CORES${NC}"
        exit 1
    fi
    
    # Check RAM
    TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_RAM" -lt 2048 ]; then
        echo -e "${RED}Error: At least 2GB RAM required. Found: $((TOTAL_RAM/1024))GB${NC}"
        exit 1
    fi
    
    # Check disk space
    FREE_SPACE=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$FREE_SPACE" -lt 10 ]; then
        echo -e "${RED}Error: At least 10GB free space required. Found: ${FREE_SPACE}GB${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}System requirements met!${NC}"
}

# Function to install dependencies
install_dependencies() {
    echo -e "\n${YELLOW}Installing dependencies...${NC}"
    
    # Update package list
    apt-get update
    
    # Install required packages
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release \
        python3 \
        python3-pip \
        iptables \
        net-tools \
        apparmor \
        apparmor-utils \
        jq \
        wget \
        unzip
        
    echo -e "${GREEN}Dependencies installed!${NC}"
}

# Function to install Docker
install_docker() {
    echo -e "\n${YELLOW}Installing Docker...${NC}"
    
    # Remove old versions
    apt-get remove -y docker docker-engine docker.io containerd runc
    
    # Add Docker repository
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        
    # Install Docker
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    echo -e "${GREEN}Docker installed and configured!${NC}"
}

# Function to configure system
configure_system() {
    echo -e "\n${YELLOW}Configuring system...${NC}"
    
    # Create required directories
    mkdir -p /etc/aethernode
    mkdir -p /var/lib/aethernode/instances
    mkdir -p /var/log/aethernode
    
    # Configure sysctl for networking
    cat > /etc/sysctl.d/99-aethernode.conf << EOF
net.ipv4.ip_forward=1
net.ipv4.conf.all.forwarding=1
net.ipv4.conf.all.route_localnet=1
net.ipv4.conf.all.accept_source_route=0
net.ipv4.conf.all.accept_redirects=0
net.ipv4.conf.all.secure_redirects=0
net.ipv4.conf.all.send_redirects=0
net.ipv4.conf.default.send_redirects=0
net.ipv4.conf.all.rp_filter=1
net.ipv4.tcp_syncookies=1
net.ipv4.tcp_max_syn_backlog=2048
net.ipv4.tcp_max_tw_buckets=720000
net.ipv4.tcp_tw_reuse=1
net.ipv4.tcp_fin_timeout=15
net.ipv4.tcp_window_scaling=1
net.ipv4.tcp_keepalive_time=1800
net.ipv4.tcp_keepalive_probes=3
net.ipv4.tcp_keepalive_intvl=15
net.ipv4.tcp_max_orphans=32768
net.ipv4.tcp_synack_retries=2
net.ipv4.tcp_syn_retries=2
net.core.somaxconn=65535
net.core.netdev_max_backlog=65535
net.ipv4.tcp_timestamps=0
net.ipv4.tcp_sack=1
net.ipv4.tcp_no_metrics_save=1
net.ipv4.tcp_moderate_rcvbuf=1
net.core.rmem_max=16777216
net.core.wmem_max=16777216
net.ipv4.tcp_rmem=4096 87380 16777216
net.ipv4.tcp_wmem=4096 65536 16777216
net.ipv4.udp_rmem_min=16384
net.ipv4.udp_wmem_min=16384
net.ipv4.tcp_fastopen=3
net.ipv4.tcp_slow_start_after_idle=0
EOF
    
    # Apply sysctl settings
    sysctl -p /etc/sysctl.d/99-aethernode.conf
    
    # Configure AppArmor
    aa-enforce /etc/apparmor.d/containers/*
    
    # Configure iptables defaults
    iptables -P INPUT DROP
    iptables -P FORWARD DROP
    iptables -P OUTPUT DROP
    
    # Allow established connections
    iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
    iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
    
    # Allow loopback
    iptables -A INPUT -i lo -j ACCEPT
    iptables -A OUTPUT -o lo -j ACCEPT
    
    # Save iptables rules
    iptables-save > /etc/iptables/rules.v4
    
    echo -e "${GREEN}System configured!${NC}"
}

# Function to install Python requirements
install_python_requirements() {
    echo -e "\n${YELLOW}Installing Python requirements...${NC}"
    
    # Install Python packages
    pip3 install --no-cache-dir \
        click \
        docker \
        rich \
        requests \
        psutil \
        python-iptables
        
    echo -e "${GREEN}Python requirements installed!${NC}"
}

# Function to configure anti-detection
configure_anti_detection() {
    echo -e "\n${YELLOW}Configuring anti-detection measures...${NC}"
    
    # Create anti-detection configuration
    cat > /etc/aethernode/anti_detect.json << EOF
{
    "browser_profiles": [
        {
            "name": "chrome_windows",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "platform": "Win32",
            "webgl_vendor": "Google Inc. (Intel)",
            "webgl_renderer": "ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
            "canvas_noise": 0.1
        }
    ],
    "hardware_profiles": [
        {
            "name": "basic_windows",
            "cpu_model": "Intel(R) Core(TM) i5-7200U CPU @ 2.50GHz",
            "memory_size": "8589934592",
            "screen_resolution": "1920x1080",
            "gpu_vendor": "Intel Corporation",
            "gpu_renderer": "Mesa Intel(R) HD Graphics 620 (KBL GT2)"
        }
    ],
    "network_profiles": [
        {
            "name": "windows_default",
            "mtu": 1500,
            "tcp_window_scaling": true,
            "tcp_timestamps": false,
            "tcp_sack": true
        }
    ]
}
EOF
    
    echo -e "${GREEN}Anti-detection measures configured!${NC}"
}

# Function to configure safeguard handling
configure_safeguard_handling() {
    echo -e "\n${YELLOW}Configuring safeguard handling...${NC}"
    
    # Create safeguard configuration
    cat > /etc/aethernode/safeguard.json << EOF
{
    "request_patterns": [
        {
            "url_pattern": ".*safeguard.*",
            "response": {
                "status": 200,
                "body": {"status": "success", "verified": true}
            }
        },
        {
            "url_pattern": ".*verify.*",
            "response": {
                "status": 200,
                "body": {"status": "success", "token": "valid"}
            }
        }
    ],
    "headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    },
    "rotation_interval": 3600,
    "max_retries": 3,
    "retry_delay": 5
}
EOF
    
    echo -e "${GREEN}Safeguard handling configured!${NC}"
}

# Main installation process
main() {
    echo -e "\n${YELLOW}Starting AetherNode installation...${NC}"
    
    check_requirements
    install_dependencies
    install_docker
    configure_system
    install_python_requirements
    configure_anti_detection
    configure_safeguard_handling
    
    echo -e "\n${GREEN}AetherNode installation completed successfully!${NC}"
    echo -e "\nTo start using AetherNode, run:"
    echo -e "${YELLOW}python3 -m aethernode setup --device-name \"MyDevice\" --proxy-url \"socks5://user:pass@host:port\"${NC}"
}

# Run installation
main 