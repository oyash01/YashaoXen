#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging
log() {
    echo -e "${GREEN}[+]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

error() {
    echo -e "${RED}[x]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root (sudo ./install.sh)"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    error "Cannot detect OS"
    exit 1
fi

log "Installing on $OS $VER"

# Create directories
create_directories() {
    log "Creating directories..."
    mkdir -p /etc/yashaoxen
    mkdir -p /var/log/yashaoxen
    mkdir -p /etc/iptables
}

# Install system packages
install_packages() {
    log "Installing required packages..."
    case $OS in
        "Ubuntu"|"Debian")
            apt-get update
            DEBIAN_FRONTEND=noninteractive apt-get install -y \
                python3.8 \
                python3-pip \
                python3-venv \
                docker.io \
                docker-compose \
                iptables \
                net-tools \
                curl \
                wget
            ;;
        "CentOS"|"Red Hat")
            yum -y update
            yum -y install \
                python38 \
                python38-pip \
                docker \
                docker-compose \
                iptables \
                net-tools \
                curl \
                wget
            ;;
        *)
            error "Unsupported OS: $OS"
            exit 1
            ;;
    esac
}

# Configure Docker
setup_docker() {
    log "Configuring Docker..."
    systemctl start docker
    systemctl enable docker
    
    # Add current user to docker group
    usermod -aG docker $SUDO_USER
    
    # Test Docker
    if ! docker run hello-world > /dev/null 2>&1; then
        error "Docker test failed"
        exit 1
    fi
}

# Configure system settings
configure_system() {
    log "Configuring system settings..."
    
    # Create sysctl config
    cat > /etc/sysctl.d/99-yashaoxen.conf << EOL
# Network settings
net.ipv4.ip_forward = 1
net.ipv4.conf.all.forwarding = 1
net.ipv4.conf.all.route_localnet = 1
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.rp_filter = 1

# TCP optimizations
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_max_tw_buckets = 720000
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_keepalive_time = 1800
net.ipv4.tcp_keepalive_probes = 3
net.ipv4.tcp_keepalive_intvl = 15
net.ipv4.tcp_max_orphans = 32768
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 2

# Core settings
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216

# TCP memory settings
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.udp_rmem_min = 16384
net.ipv4.udp_wmem_min = 16384

# TCP performance
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_slow_start_after_idle = 0
EOL

    # Apply sysctl settings
    sysctl -p /etc/sysctl.d/99-yashaoxen.conf

    # Setup iptables
    setup_iptables
}

# Configure iptables
setup_iptables() {
    log "Configuring iptables..."
    
    # Create iptables rules
    cat > /etc/iptables/rules.v4 << EOL
*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
:YASHAOXEN - [0:0]

# Allow established connections
-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH
-A INPUT -p tcp --dport 22 -j ACCEPT

# Allow Docker
-A INPUT -i docker0 -j ACCEPT

# Custom chain for YashaoXen
-A INPUT -j YASHAOXEN
-A FORWARD -j YASHAOXEN

COMMIT

*nat
:PREROUTING ACCEPT [0:0]
:INPUT ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]

# Enable NAT for Docker
-A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE

COMMIT
EOL

    # Apply iptables rules
    iptables-restore < /etc/iptables/rules.v4
    
    # Make iptables rules persistent
    case $OS in
        "Ubuntu"|"Debian")
            apt-get install -y iptables-persistent
            ;;
        "CentOS"|"Red Hat")
            service iptables save
            ;;
    esac
}

# Setup Python virtual environment
setup_python() {
    log "Setting up Python environment..."
    
    # Create virtual environment
    python3 -m venv /opt/yashaoxen/venv
    
    # Activate virtual environment and install requirements
    source /opt/yashaoxen/venv/bin/activate
    
    # Install pip requirements
    pip install --no-cache-dir -r requirements.txt
    
    # Create activation script
    cat > /etc/profile.d/yashaoxen.sh << EOL
#!/bin/bash
export YASHAOXEN_HOME=/opt/yashaoxen
export PATH=\$YASHAOXEN_HOME/venv/bin:\$PATH
EOL
    
    chmod +x /etc/profile.d/yashaoxen.sh
}

# Main installation
main() {
    log "Starting YashaoXen installation..."
    
    create_directories
    install_packages
    setup_docker
    configure_system
    setup_python
    
    log "Installation completed successfully!"
    log "Please log out and log back in for changes to take effect."
    log "Then run: source /opt/yashaoxen/venv/bin/activate"
    log "And: yashaoxen init"
}

# Run main installation
main 