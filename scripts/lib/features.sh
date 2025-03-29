#!/bin/bash

source "$(dirname "$0")/colors.sh"

# Features configuration file
FEATURES_CONFIG="/etc/yashaoxen/features.json"

# Initialize features if not exists
init_features() {
    if [ ! -f "$FEATURES_CONFIG" ]; then
        cat > "$FEATURES_CONFIG" << EOF
{
    "proxy_manager": {
        "enabled": true,
        "auto_test": true,
        "rotation_enabled": true,
        "max_fails": 3
    },
    "dns_manager": {
        "enabled": true,
        "custom_resolvers": true,
        "blocking_enabled": true
    },
    "device_manager": {
        "enabled": true,
        "auto_name": true,
        "id_protection": true
    },
    "monitoring": {
        "enabled": true,
        "prometheus": false,
        "grafana": false,
        "alerts": true
    },
    "security": {
        "firewall": true,
        "network_isolation": true,
        "container_hardening": true
    },
    "optimization": {
        "auto_scaling": true,
        "resource_limits": true,
        "performance_mode": false
    },
    "automation": {
        "auto_update": false,
        "auto_restart": true,
        "auto_recovery": true
    }
}
EOF
        print_success "Initialized default features configuration"
    fi
}

# Get feature status
get_feature() {
    local category=$1
    local feature=$2
    if [ -f "$FEATURES_CONFIG" ]; then
        value=$(jq -r ".$category.$feature" "$FEATURES_CONFIG")
        echo "$value"
    else
        print_error "Features configuration not found"
        return 1
    fi
}

# Set feature status
set_feature() {
    local category=$1
    local feature=$2
    local value=$3
    if [ -f "$FEATURES_CONFIG" ]; then
        tmp=$(mktemp)
        jq ".$category.$feature = $value" "$FEATURES_CONFIG" > "$tmp" && mv "$tmp" "$FEATURES_CONFIG"
        print_success "Updated $category.$feature feature"
    else
        print_error "Features configuration not found"
        return 1
    fi
}

# Configure features menu
configure_features() {
    while true; do
        clear
        print_header "Features Configuration"
        echo
        echo "1) Proxy Manager Settings"
        echo "2) DNS Manager Settings"
        echo "3) Device Manager Settings"
        echo "4) Monitoring Settings"
        echo "5) Security Settings"
        echo "6) Optimization Settings"
        echo "7) Automation Settings"
        echo "8) Show Current Configuration"
        echo "9) Reset to Defaults"
        echo "10) Back to Main Menu"
        echo
        read -p "Select an option: " choice
        
        case $choice in
            1) configure_category "proxy_manager" ;;
            2) configure_category "dns_manager" ;;
            3) configure_category "device_manager" ;;
            4) configure_category "monitoring" ;;
            5) configure_category "security" ;;
            6) configure_category "optimization" ;;
            7) configure_category "automation" ;;
            8) show_features ;;
            9) reset_features ;;
            10) return ;;
            *) print_error "Invalid option" ;;
        esac
        
        read -p "Press Enter to continue..."
    done
}

# Configure category
configure_category() {
    local category=$1
    local features=$(jq -r ".$category | keys[]" "$FEATURES_CONFIG")
    
    while true; do
        clear
        print_header "${category^} Configuration"
        echo
        
        local i=1
        while IFS= read -r feature; do
            local status=$(get_feature "$category" "$feature")
            if [ "$status" = "true" ]; then
                echo -e "$i) ${feature^}: ${GREEN}Enabled${NC}"
            else
                echo -e "$i) ${feature^}: ${RED}Disabled${NC}"
            fi
            i=$((i + 1))
        done <<< "$features"
        
        echo "$i) Back"
        echo
        read -p "Select feature to toggle: " feature_choice
        
        if [ "$feature_choice" = "$i" ]; then
            return
        fi
        
        if [ "$feature_choice" -ge 1 ] && [ "$feature_choice" -lt "$i" ]; then
            local selected_feature=$(echo "$features" | sed -n "${feature_choice}p")
            local current_status=$(get_feature "$category" "$selected_feature")
            
            if [ "$current_status" = "true" ]; then
                set_feature "$category" "$selected_feature" "false"
            else
                set_feature "$category" "$selected_feature" "true"
            fi
        else
            print_error "Invalid option"
        fi
    done
}

# Show current features
show_features() {
    clear
    print_header "Current Features Configuration"
    echo
    if [ -f "$FEATURES_CONFIG" ]; then
        jq . "$FEATURES_CONFIG" | while IFS= read -r line; do
            echo -e "${CYAN}$line${NC}"
        done
    else
        print_error "Features configuration not found"
    fi
}

# Reset features to defaults
reset_features() {
    if [ -f "$FEATURES_CONFIG" ]; then
        rm "$FEATURES_CONFIG"
    fi
    init_features
    print_success "Reset features to defaults"
} 