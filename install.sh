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

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "This script must be run as root"
    fi
}

# Function to install system dependencies
install_system_deps() {
    log "Installing system dependencies..."
    apt-get update || error "Failed to update package list"
    
    # Install required system packages
    apt-get install -y \
        python3-full \
        python3-venv \
        python3-pip \
        git \
        curl \
        wget \
        docker.io \
        docker-compose \
        || error "Failed to install system dependencies"
    
    # Start and enable Docker
    systemctl start docker || error "Failed to start Docker"
    systemctl enable docker || error "Failed to enable Docker"
}

# Function to setup virtual environment
setup_venv() {
    log "Setting up Python virtual environment..."
    VENV_DIR="/opt/yashaoxen/venv"
    
    # Create virtual environment directory
    mkdir -p "$VENV_DIR" || error "Failed to create virtual environment directory"
    
    # Create virtual environment
    python3 -m venv "$VENV_DIR" || error "Failed to create virtual environment"
    
    # Activate virtual environment and install dependencies
    source "$VENV_DIR/bin/activate" || error "Failed to activate virtual environment"
    pip install --upgrade pip || error "Failed to upgrade pip"
    
    # Install Python dependencies
    pip install -r requirements.txt || error "Failed to install Python dependencies"
}

# Function to setup configuration
setup_config() {
    log "Setting up configuration..."
    CONFIG_DIR="/etc/yashaoxen"
    
    # Create configuration directory
    mkdir -p "$CONFIG_DIR" || error "Failed to create configuration directory"
    
    # Copy configuration files
    cp -r config/* "$CONFIG_DIR/" || error "Failed to copy configuration files"
    cp -r docker "$CONFIG_DIR/" || error "Failed to copy Docker files"
    
    # Create default configuration if not exists
    if [ ! -f "$CONFIG_DIR/config.json" ]; then
        cat > "$CONFIG_DIR/config.json" << 'EOF'
{
    "version": "1.0.0",
    "instances": [],
    "proxies": [],
    "dns_servers": [],
    "features": {
        "auto_update": true,
        "network_isolation": true,
        "proxy_verification": true,
        "device_verification": true
    },
    "safeguards": {
        "max_instances": 10,
        "memory_limit": "512m",
        "cpu_limit": "0.5",
        "network_isolation": true,
        "proxy_verification": true,
        "device_verification": true,
        "auto_update": true,
        "allowed_countries": ["US", "CA", "GB", "DE", "FR", "IT", "ES", "NL", "SE", "AU"],
        "blocked_ips": []
    }
}
EOF
    fi
    
    # Set permissions
    chown -R root:root "$CONFIG_DIR"
    chmod -R 755 "$CONFIG_DIR"
}

# Function to setup logging
setup_logging() {
    log "Setting up logging..."
    
    # Create log directory
    mkdir -p "$LOG_DIR" || error "Failed to create log directory"
    
    # Create log file
    touch "$LOG_DIR/yashaoxen.log" || error "Failed to create log file"
    
    # Set permissions
    chown -R root:root "$LOG_DIR"
    chmod -R 755 "$LOG_DIR"
    chmod 644 "$LOG_DIR/yashaoxen.log"
}

# Function to create wrapper script
create_wrapper() {
    log "Creating wrapper script..."
    
    # Create wrapper script
    cat > /usr/local/bin/yashaoxen << 'EOF'
#!/bin/bash
source /opt/yashaoxen/venv/bin/activate
/opt/yashaoxen/yashaoxen "$@"
EOF
    
    # Make wrapper executable
    chmod +x /usr/local/bin/yashaoxen || error "Failed to make wrapper executable"
}

# Function to copy application files
copy_app_files() {
    log "Copying application files..."
    APP_DIR="/opt/yashaoxen"
    
    # Create application directory
    mkdir -p "$APP_DIR" || error "Failed to create application directory"
    
    # Copy application files
    cp -r . "$APP_DIR/" || error "Failed to copy application files"
    
    # Set permissions
    chown -R root:root "$APP_DIR"
    chmod -R 755 "$APP_DIR"
}

# Main installation process
main() {
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

    # Check if running as root
    check_root
    
    # Create log directory
    mkdir -p "$LOG_DIR"
    chmod 755 "$LOG_DIR"
    
    log "Starting YashaoXen installation..."
    
    # Run installation steps
    install_system_deps
    setup_venv
    setup_config
    setup_logging
    copy_app_files
    create_wrapper
    
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

Configuration directory: /etc/yashaoxen
Logs directory: $LOG_DIR
Application directory: /opt/yashaoxen
"
}

# Run main installation process
main 