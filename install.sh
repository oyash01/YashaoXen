#!/bin/bash

# Set log directory
LOG_DIR="/var/log/yashaoxen"
APP_DIR="/opt/yashaoxen"
CONFIG_DIR="/etc/yashaoxen"
VENV_DIR="/opt/yashaoxen/venv"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_DIR/install.log"
}

# Function to handle errors
error() {
    log "ERROR: $1"
    cleanup
    exit 1
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "This script must be run as root"
    fi
}

# Function to cleanup on failure
cleanup() {
    log "Cleaning up..."
    # Stop any running Docker containers
    docker stop $(docker ps -q --filter "name=yashaoxen") 2>/dev/null || true
    docker rm $(docker ps -aq --filter "name=yashaoxen") 2>/dev/null || true
    
    # Remove temporary files
    rm -rf /tmp/yashaoxen_* 2>/dev/null || true
    
    # Restore original files if backup exists
    if [ -d "${APP_DIR}_backup" ]; then
        log "Restoring from backup..."
        rm -rf "$APP_DIR" 2>/dev/null || true
        mv "${APP_DIR}_backup" "$APP_DIR" || true
    fi
}

# Function to backup existing installation
backup_existing() {
    if [ -d "$APP_DIR" ]; then
        log "Backing up existing installation..."
        rm -rf "${APP_DIR}_backup" 2>/dev/null || true
        cp -r "$APP_DIR" "${APP_DIR}_backup" || error "Failed to backup existing installation"
    fi
}

# Function to verify directory permissions
verify_permissions() {
    local dir="$1"
    local owner="$2"
    local perms="$3"
    
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir" || error "Failed to create directory: $dir"
    fi
    
    chown -R "$owner" "$dir" || error "Failed to set ownership for: $dir"
    chmod -R "$perms" "$dir" || error "Failed to set permissions for: $dir"
}

# Function to install system dependencies
install_system_deps() {
    log "Installing system dependencies..."
    
    # Update package lists
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
    
    # Verify Docker is running
    if ! docker info >/dev/null 2>&1; then
        error "Docker is not running properly"
    fi
}

# Function to setup virtual environment
setup_venv() {
    log "Setting up Python virtual environment..."
    
    # Remove existing venv if it exists
    if [ -d "$VENV_DIR" ]; then
        log "Removing existing virtual environment..."
        rm -rf "$VENV_DIR"
    fi
    
    # Create virtual environment directory with proper permissions
    mkdir -p "$VENV_DIR" || error "Failed to create virtual environment directory"
    chown -R root:root "$VENV_DIR"
    chmod -R 755 "$VENV_DIR"
    
    # Create virtual environment with system packages
    log "Creating virtual environment..."
    python3 -m venv --system-site-packages "$VENV_DIR" || error "Failed to create virtual environment"
    
    # Verify virtual environment structure
    if [ ! -d "$VENV_DIR/bin" ] || [ ! -d "$VENV_DIR/lib" ] || [ ! -d "$VENV_DIR/include" ]; then
        error "Virtual environment structure is incomplete"
    fi
    
    # Ensure activate script exists and is executable
    if [ ! -f "$VENV_DIR/bin/activate" ]; then
        error "Virtual environment activation script not found"
    fi
    chmod +x "$VENV_DIR/bin/activate"
    
    # Activate virtual environment
    log "Activating virtual environment..."
    source "$VENV_DIR/bin/activate" || error "Failed to activate virtual environment"
    
    # Verify we're in the virtual environment
    if [ -z "$VIRTUAL_ENV" ]; then
        error "Failed to activate virtual environment"
    fi
    
    # Upgrade pip and install wheel
    log "Upgrading pip and installing wheel..."
    pip install --upgrade pip wheel || error "Failed to upgrade pip"
    
    # Install Python dependencies with retry mechanism
    log "Installing Python dependencies..."
    for i in {1..3}; do
        if pip install -r requirements.txt; then
            break
        elif [ $i -eq 3 ]; then
            error "Failed to install Python dependencies after 3 attempts"
        else
            log "Retrying dependency installation (attempt $i)..."
            sleep 2
        fi
    done
    
    # Verify virtual environment packages
    if [ ! -d "$VENV_DIR/lib/python3.12/site-packages" ]; then
        error "Virtual environment packages directory not found"
    fi
    
    # Verify critical packages are installed
    for package in docker requests psutil PyYAML click rich python-dotenv; do
        if ! pip show "$package" >/dev/null 2>&1; then
            error "Critical package not installed: $package"
        fi
    done
    
    # Set proper permissions
    chown -R root:root "$VENV_DIR"
    chmod -R 755 "$VENV_DIR"
    chmod +x "$VENV_DIR/bin"/*
    
    # Verify permissions
    if [ ! -x "$VENV_DIR/bin/activate" ] || [ ! -x "$VENV_DIR/bin/pip" ] || [ ! -x "$VENV_DIR/bin/python" ]; then
        error "Virtual environment executables are not properly set"
    fi
    
    log "Virtual environment setup completed successfully"
}

# Function to setup configuration
setup_config() {
    log "Setting up configuration..."
    
    # Create configuration directory
    mkdir -p "$CONFIG_DIR" || error "Failed to create configuration directory"
    
    # Backup existing config if exists
    if [ -f "$CONFIG_DIR/config.json" ]; then
        cp "$CONFIG_DIR/config.json" "$CONFIG_DIR/config.json.bak" || true
    fi
    
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
    verify_permissions "$CONFIG_DIR" "root:root" "755"
}

# Function to setup logging
setup_logging() {
    log "Setting up logging..."
    
    # Create log directory
    mkdir -p "$LOG_DIR" || error "Failed to create log directory"
    
    # Create log file with proper permissions
    touch "$LOG_DIR/yashaoxen.log" || error "Failed to create log file"
    
    # Set permissions
    verify_permissions "$LOG_DIR" "root:root" "755"
    chmod 644 "$LOG_DIR/yashaoxen.log"
}

# Function to create wrapper script
create_wrapper() {
    log "Creating wrapper script..."
    
    # Create wrapper script with error handling
    cat > /usr/local/bin/yashaoxen << 'EOF'
#!/bin/bash
set -e
source /opt/yashaoxen/venv/bin/activate
/opt/yashaoxen/yashaoxen "$@"
EOF
    
    # Make wrapper executable
    chmod +x /usr/local/bin/yashaoxen || error "Failed to make wrapper executable"
}

# Function to copy application files
copy_app_files() {
    log "Copying application files..."
    
    # Create application directory
    mkdir -p "$APP_DIR" || error "Failed to create application directory"
    
    # Remove existing files if they exist
    rm -rf "$APP_DIR"/* || error "Failed to remove existing files"
    
    # Create config directory if it doesn't exist
    mkdir -p "$APP_DIR/config" || error "Failed to create config directory"
    
    # Copy application files with verification
    cp -r ./* "$APP_DIR/" || error "Failed to copy application files"
    
    # Ensure config.json exists
    if [ ! -f "$APP_DIR/config/config.json" ]; then
        log "Creating default config.json..."
        cat > "$APP_DIR/config/config.json" << 'EOF'
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
    
    # Verify critical files exist
    for file in "yashaoxen" "requirements.txt" "config/config.json"; do
        if [ ! -f "$APP_DIR/$file" ]; then
            error "Critical file missing: $file"
        fi
    done
    
    # Set permissions
    verify_permissions "$APP_DIR" "root:root" "755"
}

# Function to verify installation
verify_installation() {
    log "Verifying installation..."
    
    # Check critical directories
    for dir in "$APP_DIR" "$CONFIG_DIR" "$LOG_DIR" "$VENV_DIR"; do
        if [ ! -d "$dir" ]; then
            error "Critical directory missing: $dir"
        fi
    done
    
    # Verify virtual environment is properly set up
    if [ ! -f "$VENV_DIR/bin/activate" ] || [ ! -f "$VENV_DIR/bin/pip" ] || [ ! -f "$VENV_DIR/bin/python" ]; then
        error "Virtual environment is not properly set up"
    fi
    
    # Check wrapper script
    if [ ! -x /usr/local/bin/yashaoxen ]; then
        error "Wrapper script is not executable"
    fi
    
    # Test basic functionality
    if ! "$APP_DIR/yashaoxen" --version >/dev/null 2>&1; then
        error "Basic functionality test failed"
    fi
    
    log "Installation verification successful"
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
    
    # Backup existing installation
    backup_existing
    
    # Run installation steps with error handling
    {
        install_system_deps
        setup_venv
        setup_config
        setup_logging
        copy_app_files
        create_wrapper
        verify_installation
    } || {
        log "Installation failed. Cleaning up..."
        cleanup
        exit 1
    }
    
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

Configuration directory: $CONFIG_DIR
Logs directory: $LOG_DIR
Application directory: $APP_DIR
"
}

# Run main installation process
main 