#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Print functions
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}× $1${NC}"; }
print_info() { echo -e "${YELLOW}➜ $1${NC}"; }
print_header() { echo -e "${PURPLE}=== $1 ===${NC}"; }

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Function to check if script is being piped
is_piped() {
    if [ -t 0 ]; then
        # Terminal has stdin (interactive)
        return 1
    else
        # No stdin (non-interactive/piped)
        return 0
    fi
}

# Function to check Python version
check_python_version() {
    print_header "Checking Python Version"
    required_version="3.8"
    
    # Try to get current Python version
    if command -v python3 >/dev/null 2>&1; then
        current_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' 2>/dev/null)
        
        # Check if version is sufficient
        if [ "$(printf '%s\n' "$required_version" "$current_version" | sort -V | head -n1)" != "$required_version" ]; then
            print_info "Current Python version ($current_version) is below $required_version"
            install_python38
        else
            print_success "Python $current_version is compatible"
            PYTHON_CMD="python3"
        fi
    else
        print_info "Python 3 not found"
        install_python38
    fi
}

# Function to install Python 3.8
install_python38() {
    print_info "Installing Python $required_version..."
    
    # Add deadsnakes PPA and install Python 3.8
    apt update
    apt install -y software-properties-common
    add-apt-repository -y ppa:deadsnakes/ppa
    apt update
    apt install -y python3.8 python3.8-venv python3.8-dev
    
    # Set Python 3.8 as default for the installation
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1
    PYTHON_CMD="python3.8"
    
    print_success "Python $required_version installed successfully"
}

# Function to install system dependencies
install_dependencies() {
    print_header "Installing System Dependencies"
    
    # Update package list
    apt update
    
    # Install essential packages
    apt install -y \
        software-properties-common \
        python3-pip \
        python3-venv \
        docker.io \
        jq \
        git \
        iptables \
        curl \
        wget || {
        print_error "Failed to install system dependencies"
        exit 1
    }
    
    # Check Python version and install if needed
    check_python_version
    
    print_success "System dependencies installed"
}

# Function to fix requirements and setup Python environment
setup_python_env() {
    print_header "Setting up Python Environment"
    
    # Create virtual environment
    $PYTHON_CMD -m venv /opt/yashaoxen/venv
    source /opt/yashaoxen/venv/bin/activate
    
    # Update pip and install basic tools
    pip install --upgrade pip wheel setuptools

    # Create requirements.txt if it doesn't exist
    if [ ! -f "requirements.txt" ]; then
        print_info "Creating requirements.txt..."
        cat > requirements.txt << EOF
python-iptables==1.0.1
docker==6.1.3
requests==2.31.0
psutil==5.9.8
PyYAML==6.0.1
click==8.1.7
rich==13.7.0
python-dotenv==1.0.1
schedule==1.2.1
prometheus-client==0.19.0
EOF
    fi

    # Install requirements with error handling
    if ! pip install -r requirements.txt; then
        print_error "Failed to install requirements"
        print_info "Trying with more flexible versions..."
        sed -i 's/==/>=/g' requirements.txt
        if ! pip install -r requirements.txt; then
            print_error "Failed to install Python requirements"
            exit 1
        fi
    fi
    
    # Install the package
    if [ -f "setup.py" ]; then
        print_info "Installing YashaoXen package..."
        
        # Create package directory structure
        mkdir -p /opt/yashaoxen/src
        mkdir -p /opt/yashaoxen/yashaoxen
        
        # Copy package files
        cp -r src/* /opt/yashaoxen/src/
        cp setup.py /opt/yashaoxen/
        cp README.md /opt/yashaoxen/
        
        # Install the package in development mode
        cd /opt/yashaoxen
        if ! pip install -e .; then
            print_error "Failed to install YashaoXen package"
            exit 1
        fi
        cd - > /dev/null  # Return to previous directory
        
        print_success "YashaoXen package installed successfully"
    else
        print_error "setup.py not found. Cannot install YashaoXen package."
        exit 1
    fi
    
    print_success "Python environment setup complete"
}

# Function to setup directories and files
setup_directories() {
    print_header "Setting up Directories"
    
    # Create necessary directories
    mkdir -p /etc/yashaoxen
    mkdir -p /usr/local/lib/yashaoxen
    mkdir -p /opt/yashaoxen/{src,logs,config}
    mkdir -p /var/log/yashaoxen
    
    # Copy source files
    if [ -d "src" ]; then
        cp -r src/* /opt/yashaoxen/src/
    else
        print_error "Source directory not found"
        exit 1
    fi
    
    # Copy configuration files
    if [ -d "scripts/lib" ]; then
        cp -r scripts/lib/* /usr/local/lib/yashaoxen/
    fi
    
    # Create activation script
    cat > /usr/local/bin/yashaoxen << EOF
#!/bin/bash
if [ "\$EUID" -ne 0 ]; then 
    echo -e "${RED}Error: Please run as root (use sudo)${NC}"
    exit 1
fi

# Activate virtual environment
source /opt/yashaoxen/venv/bin/activate || {
    echo -e "${RED}Error: Failed to activate virtual environment${NC}"
    exit 1
}

# Set Python path
export PYTHONPATH=/opt/yashaoxen/src:\$PYTHONPATH

# Run manager
yashaoxen-manager "\$@"
EOF
    chmod +x /usr/local/bin/yashaoxen
    
    print_success "Directories and files setup complete"
}

# Function to setup library files
setup_library_files() {
    print_header "Setting up Library Files"
    
    # Create lib directory if it doesn't exist
    mkdir -p /usr/local/lib/yashaoxen
    
    # Copy colors.sh first as it's a dependency
    if [ -f "scripts/lib/colors.sh" ]; then
        cp scripts/lib/colors.sh /usr/local/lib/yashaoxen/
        chmod +x /usr/local/lib/yashaoxen/colors.sh
    else
        # Create colors.sh if it doesn't exist
        cat > /usr/local/lib/yashaoxen/colors.sh << 'EOF'
#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Print functions
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}× $1${NC}"; }
print_info() { echo -e "${YELLOW}➜ $1${NC}"; }
print_header() { echo -e "${PURPLE}=== $1 ===${NC}"; }
EOF
        chmod +x /usr/local/lib/yashaoxen/colors.sh
    fi
    
    # Create safeguards.sh
    cat > /usr/local/lib/yashaoxen/safeguards.sh << 'EOF'
#!/bin/bash

source /usr/local/lib/yashaoxen/colors.sh

init_safeguards() {
    if [ ! -f "/etc/yashaoxen/safeguards.json" ]; then
        print_info "Creating default safeguards configuration..."
        mkdir -p /etc/yashaoxen
        cat > /etc/yashaoxen/safeguards.json << 'INNEREOF'
{
    "max_instances": 10,
    "memory_limit": "512m",
    "cpu_limit": "0.5",
    "network_isolation": true,
    "proxy_verification": true,
    "device_verification": true,
    "auto_update": true,
    "allowed_countries": ["US", "CA", "GB", "DE", "FR", "IT", "ES", "NL", "SE", "AU"],
    "blocked_ips": [],
    "security_checks": {
        "verify_proxy_ssl": true,
        "verify_proxy_anonymity": true,
        "check_proxy_location": true,
        "monitor_traffic": true
    }
}
INNEREOF
    fi
}
EOF
    chmod +x /usr/local/lib/yashaoxen/safeguards.sh
    
    # Create features.sh
    cat > /usr/local/lib/yashaoxen/features.sh << 'EOF'
#!/bin/bash

source /usr/local/lib/yashaoxen/colors.sh

init_features() {
    if [ ! -f "/etc/yashaoxen/features.json" ]; then
        print_info "Creating default features configuration..."
        mkdir -p /etc/yashaoxen
        cat > /etc/yashaoxen/features.json << 'INNEREOF'
{
    "proxy_rotation": {
        "enabled": true,
        "interval": 3600
    },
    "monitoring": {
        "enabled": true,
        "interval": 300
    },
    "auto_update": {
        "enabled": true,
        "check_interval": 86400
    },
    "logging": {
        "level": "INFO",
        "max_size": "10M",
        "backup_count": 5
    }
}
INNEREOF
    fi
}
EOF
    chmod +x /usr/local/lib/yashaoxen/features.sh
    
    print_success "Library files setup complete"
}

# Function to initialize configurations
init_configurations() {
    print_header "Initializing Configurations"
    
    # Source library files with error handling
    if ! source /usr/local/lib/yashaoxen/safeguards.sh; then
        print_error "Failed to load safeguards configuration"
        exit 1
    fi
    
    if ! source /usr/local/lib/yashaoxen/features.sh; then
        print_error "Failed to load features configuration"
        exit 1
    fi
    
    # Initialize configurations
    init_safeguards
    init_features
    
    # Set correct permissions
    chown -R root:root /etc/yashaoxen
    chmod -R 755 /etc/yashaoxen
    
    print_success "Configurations initialized"
}

# Function to verify installation
verify_installation() {
    print_header "Verifying Installation"
    
    # Check Python installation
    if ! $PYTHON_CMD --version; then
        print_error "Python installation verification failed"
        return 1
    fi
    
    # Check virtual environment
    if ! [ -f "/opt/yashaoxen/venv/bin/activate" ]; then
        print_error "Virtual environment verification failed"
        return 1
    fi
    
    # Check package installation
    if ! [ -f "/opt/yashaoxen/setup.py" ]; then
        print_error "Package installation verification failed"
        return 1
    fi
    
    # Check yashaoxen command
    if ! [ -x "/usr/local/bin/yashaoxen" ]; then
        print_error "YashaoXen command verification failed"
        return 1
    fi
    
    # Verify package is importable
    source /opt/yashaoxen/venv/bin/activate
    if ! python3 -c "import yashaoxen" 2>/dev/null; then
        print_error "Package import verification failed"
        return 1
    fi
    
    print_success "Installation verified successfully"
    return 0
}

# Function to run YashaoXen
run_yashaoxen() {
    if [ ! -f "/usr/local/bin/yashaoxen" ]; then
        print_error "YashaoXen is not installed"
        return 1
    fi
    
    print_info "Starting YashaoXen..."
    /usr/local/bin/yashaoxen
}

# Main installation function
main_install() {
    clear
    echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         YashaoXen Installation           ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
    echo
    
    # Installation steps with error handling
    install_dependencies || exit 1
    setup_python_env || exit 1
    setup_directories || exit 1
    setup_library_files || exit 1
    init_configurations || exit 1
    
    # Verify installation
    if ! verify_installation; then
        print_error "Installation verification failed"
        print_info "Please check the error messages above and try again"
        exit 1
    fi
    
    echo
    print_success "YashaoXen installation completed successfully!"
    echo
    print_info "To start YashaoXen, simply run: sudo yashaoxen"
    echo
}

# Main menu function
show_menu() {
    while true; do
        clear
        echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║         YashaoXen One-Click Setup         ║${NC}"
        echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
        echo
        echo "1) Install YashaoXen"
        echo "2) Run YashaoXen"
        echo "3) Exit"
        echo
        read -p "Select an option (1-3): " choice
        
        case "$choice" in
            1)
                main_install
                break
                ;;
            2)
                run_yashaoxen
                break
                ;;
            3)
                exit 0
                ;;
            *)
                print_error "Invalid option. Please enter 1, 2, or 3"
                sleep 2
                ;;
        esac
    done
}

# Check if being run through pipe (curl) or directly
if is_piped; then
    # When piped (e.g., through curl), run installation directly
    main_install
else
    # When run directly, show interactive menu
    show_menu
fi 