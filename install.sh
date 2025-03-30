#!/bin/bash

# Set log directory
LOG_DIR="/var/log/yashaoxen"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_DIR/install.log"
}

# Function to handle errors
error() {
    log "ERROR: $1"
    exit 1
}

# Create log directory
mkdir -p "$LOG_DIR"
chmod 755 "$LOG_DIR"

# Display banner
echo "
██╗   ██╗ █████╗ ███████╗██╗  ██╗ █████╗ ██╗  ██╗███████╗███╗   ██╗
╚██╗ ██╔╝██╔══██╗██╔════╝██║  ██║██╔══██╗██║ ██╔╝██╔════╝████╗  ██║
 ╚████╔╝ ███████║███████╗███████║███████║█████╔╝ █████╗  ██╔██╗ ██║
  ╚██╔╝  ██╔══██║╚════██║██╔══██║██╔══██║██╔═██╗ ██╔══╝  ██║╚██╗██║
   ██║   ██║  ██║███████║██║  ██║██║  ██║██║  ██╗███████╗██║ ╚████║
   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝
Advanced EarnApp Manager
"

log "Starting YashaoXen installation..."

# Check if Python 3.8+ is installed
if ! command -v python3 &> /dev/null; then
    log "Python 3 is not installed. Installing Python..."
    if [ -f /etc/debian_version ]; then
        apt-get update && apt-get install -y python3 python3-pip
    elif [ -f /etc/redhat-release ]; then
        yum install -y python3 python3-pip
    else
        error "Unsupported operating system"
    fi
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    log "Docker is not installed. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Create installation directory
INSTALL_DIR="/etc/yashaoxen"
log "Creating installation directory..."
mkdir -p "$INSTALL_DIR" || error "Failed to create installation directory"
cd "$INSTALL_DIR" || error "Failed to change to installation directory"

# Download repository
log "Downloading repository..."
git clone https://github.com/oyash01/YashaoXen.git . || error "Failed to download repository"

# Install Python dependencies
log "Installing Python dependencies..."
pip3 install -r requirements.txt || error "Failed to install Python dependencies"

# Create configuration files
log "Creating configuration files..."
mkdir -p config
touch config/proxies.txt config/dns.txt config/features.json config/safeguards.json

# Set permissions
chmod +x *.sh

# Create symlinks
log "Creating command symlinks..."
ln -sf "$INSTALL_DIR/yashaoxen" /usr/local/bin/yashaoxen

log "Installation completed successfully!"
echo "
YashaoXen has been installed successfully!

Available commands:
- yashaoxen: Start YashaoXen Manager
- yashaoxen start: Start all instances
- yashaoxen stop: Stop all instances
- yashaoxen status: Check instance status
- yashaoxen logs: View logs
- yashaoxen update: Update YashaoXen
- yashaoxen remove: Remove YashaoXen

Configuration directory: $INSTALL_DIR/config
Logs directory: $LOG_DIR
" 