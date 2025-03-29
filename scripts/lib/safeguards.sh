#!/bin/bash

source "$(dirname "$0")/colors.sh"

# Safeguard configuration file
SAFEGUARD_CONFIG="/etc/yashaoxen/safeguards.json"

# Initialize safeguards if not exists
init_safeguards() {
    if [ ! -f "$SAFEGUARD_CONFIG" ]; then
        cat > "$SAFEGUARD_CONFIG" << EOF
{
    "max_instances": 10,
    "max_memory_per_instance": "512M",
    "max_cpu_per_instance": "50%",
    "auto_restart": true,
    "proxy_validation": true,
    "dns_validation": true,
    "ip_rotation": true,
    "ip_rotation_interval": 3600,
    "device_id_protection": true,
    "network_isolation": true,
    "logging_enabled": true,
    "monitoring_enabled": true,
    "auto_update": false,
    "backup_enabled": true,
    "backup_interval": 86400,
    "error_threshold": 5,
    "bandwidth_limit": "1GB",
    "firewall_enabled": true
}
EOF
        print_success "Initialized default safeguards configuration"
    fi
}

# Get safeguard value
get_safeguard() {
    local key=$1
    if [ -f "$SAFEGUARD_CONFIG" ]; then
        value=$(jq -r ".$key" "$SAFEGUARD_CONFIG")
        echo "$value"
    else
        print_error "Safeguards configuration not found"
        return 1
    fi
}

# Set safeguard value
set_safeguard() {
    local key=$1
    local value=$2
    if [ -f "$SAFEGUARD_CONFIG" ]; then
        tmp=$(mktemp)
        jq ".$key = $value" "$SAFEGUARD_CONFIG" > "$tmp" && mv "$tmp" "$SAFEGUARD_CONFIG"
        print_success "Updated $key safeguard"
    else
        print_error "Safeguards configuration not found"
        return 1
    fi
}

# Check if safeguard is enabled
is_safeguard_enabled() {
    local key=$1
    value=$(get_safeguard "$key")
    if [ "$value" = "true" ]; then
        return 0
    else
        return 1
    fi
}

# Validate configuration
validate_safeguards() {
    local errors=0
    
    # Check required fields
    required_fields=("max_instances" "max_memory_per_instance" "max_cpu_per_instance")
    for field in "${required_fields[@]}"; do
        if ! get_safeguard "$field" > /dev/null; then
            print_error "Missing required safeguard: $field"
            errors=$((errors + 1))
        fi
    done
    
    # Validate numeric values
    max_instances=$(get_safeguard "max_instances")
    if ! [[ "$max_instances" =~ ^[0-9]+$ ]]; then
        print_error "Invalid max_instances value: $max_instances"
        errors=$((errors + 1))
    fi
    
    # Validate intervals
    ip_rotation_interval=$(get_safeguard "ip_rotation_interval")
    if ! [[ "$ip_rotation_interval" =~ ^[0-9]+$ ]]; then
        print_error "Invalid ip_rotation_interval value: $ip_rotation_interval"
        errors=$((errors + 1))
    fi
    
    if [ $errors -gt 0 ]; then
        print_error "Found $errors validation errors"
        return 1
    fi
    
    print_success "Safeguards validation passed"
    return 0
}

# Configure safeguards menu
configure_safeguards() {
    while true; do
        clear
        print_header "Safeguards Configuration"
        echo
        echo "1) Toggle Auto-Restart"
        echo "2) Toggle Proxy Validation"
        echo "3) Toggle DNS Validation"
        echo "4) Toggle IP Rotation"
        echo "5) Toggle Device ID Protection"
        echo "6) Toggle Network Isolation"
        echo "7) Toggle Monitoring"
        echo "8) Toggle Auto-Update"
        echo "9) Configure Resource Limits"
        echo "10) Configure Intervals"
        echo "11) Show Current Configuration"
        echo "12) Reset to Defaults"
        echo "13) Back to Main Menu"
        echo
        read -p "Select an option: " choice
        
        case $choice in
            1) toggle_safeguard "auto_restart" ;;
            2) toggle_safeguard "proxy_validation" ;;
            3) toggle_safeguard "dns_validation" ;;
            4) toggle_safeguard "ip_rotation" ;;
            5) toggle_safeguard "device_id_protection" ;;
            6) toggle_safeguard "network_isolation" ;;
            7) toggle_safeguard "monitoring_enabled" ;;
            8) toggle_safeguard "auto_update" ;;
            9) configure_resource_limits ;;
            10) configure_intervals ;;
            11) show_safeguards ;;
            12) reset_safeguards ;;
            13) return ;;
            *) print_error "Invalid option" ;;
        esac
        
        read -p "Press Enter to continue..."
    done
}

# Toggle safeguard
toggle_safeguard() {
    local key=$1
    local current=$(get_safeguard "$key")
    
    if [ "$current" = "true" ]; then
        set_safeguard "$key" "false"
        print_info "$key disabled"
    else
        set_safeguard "$key" "true"
        print_info "$key enabled"
    fi
}

# Configure resource limits
configure_resource_limits() {
    clear
    print_header "Resource Limits Configuration"
    echo
    
    read -p "Max instances (current: $(get_safeguard "max_instances")): " max_instances
    if [[ "$max_instances" =~ ^[0-9]+$ ]]; then
        set_safeguard "max_instances" "$max_instances"
    fi
    
    read -p "Max memory per instance (current: $(get_safeguard "max_memory_per_instance")): " max_memory
    if [[ "$max_memory" =~ ^[0-9]+[MG]$ ]]; then
        set_safeguard "max_memory_per_instance" "\"$max_memory\""
    fi
    
    read -p "Max CPU per instance (current: $(get_safeguard "max_cpu_per_instance")): " max_cpu
    if [[ "$max_cpu" =~ ^[0-9]+%$ ]]; then
        set_safeguard "max_cpu_per_instance" "\"$max_cpu\""
    fi
}

# Configure intervals
configure_intervals() {
    clear
    print_header "Intervals Configuration"
    echo
    
    read -p "IP rotation interval in seconds (current: $(get_safeguard "ip_rotation_interval")): " rotation_interval
    if [[ "$rotation_interval" =~ ^[0-9]+$ ]]; then
        set_safeguard "ip_rotation_interval" "$rotation_interval"
    fi
    
    read -p "Backup interval in seconds (current: $(get_safeguard "backup_interval")): " backup_interval
    if [[ "$backup_interval" =~ ^[0-9]+$ ]]; then
        set_safeguard "backup_interval" "$backup_interval"
    fi
}

# Show current safeguards
show_safeguards() {
    clear
    print_header "Current Safeguards Configuration"
    echo
    if [ -f "$SAFEGUARD_CONFIG" ]; then
        jq . "$SAFEGUARD_CONFIG" | while IFS= read -r line; do
            echo -e "${CYAN}$line${NC}"
        done
    else
        print_error "Safeguards configuration not found"
    fi
}

# Reset safeguards to defaults
reset_safeguards() {
    if [ -f "$SAFEGUARD_CONFIG" ]; then
        rm "$SAFEGUARD_CONFIG"
    fi
    init_safeguards
    print_success "Reset safeguards to defaults"
} 