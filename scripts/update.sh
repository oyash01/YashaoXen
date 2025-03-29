#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Banner
show_banner() {
    clear
    echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         YashaoXen Management Tool         ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
    echo -e "${BLUE}Version: 1.0.0${NC}\n"
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then 
        echo -e "${RED}Error: Please run as root (use sudo)${NC}"
        exit 1
    fi
}

# Backup function
backup_configs() {
    echo -e "\n${YELLOW}Creating backup of configuration files...${NC}"
    BACKUP_DIR="/etc/yashaoxen/backup/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    cp -r /etc/yashaoxen/*.{json,txt} "$BACKUP_DIR/" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Backup created at $BACKUP_DIR${NC}"
    else
        echo -e "${YELLOW}! No configuration files found to backup${NC}"
    fi
}

# Stop running instances
stop_instances() {
    echo -e "\n${YELLOW}Stopping YashaoXen instances...${NC}"
    yashaoxen stop
    sleep 2
}

# Update from git
update_from_git() {
    echo -e "\n${YELLOW}Updating YashaoXen from repository...${NC}"
    cd /opt/yashaoxen || exit 1
    git fetch origin
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse @{u})

    if [ "$LOCAL" = "$REMOTE" ]; then
        echo -e "${GREEN}✓ YashaoXen is already up to date${NC}"
        return 0
    fi

    git pull
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Code updated successfully${NC}"
        return 0
    else
        echo -e "${RED}× Failed to update code${NC}"
        return 1
    fi
}

# Reinstall dependencies
update_dependencies() {
    echo -e "\n${YELLOW}Updating dependencies...${NC}"
    pip3 install -r /opt/yashaoxen/requirements.txt --upgrade
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Dependencies updated successfully${NC}"
    else
        echo -e "${RED}× Failed to update dependencies${NC}"
        return 1
    fi
}

# Configure proxies
configure_proxies() {
    show_banner
    echo -e "${YELLOW}Proxy Configuration${NC}\n"
    echo -e "1) Add new proxy"
    echo -e "2) Remove proxy"
    echo -e "3) List all proxies"
    echo -e "4) Test proxies"
    echo -e "5) Back to main menu"
    
    read -p "Select an option: " proxy_choice
    
    case $proxy_choice in
        1)
            read -p "Enter proxy (format - ip:port:user:pass): " proxy
            echo "$proxy" >> /etc/yashaoxen/proxies.txt
            echo -e "${GREEN}✓ Proxy added successfully${NC}"
            ;;
        2)
            if [ -f /etc/yashaoxen/proxies.txt ]; then
                nl -s ') ' /etc/yashaoxen/proxies.txt
                read -p "Enter line number to remove: " line_num
                sed -i "${line_num}d" /etc/yashaoxen/proxies.txt
                echo -e "${GREEN}✓ Proxy removed successfully${NC}"
            else
                echo -e "${RED}No proxies file found${NC}"
            fi
            ;;
        3)
            if [ -f /etc/yashaoxen/proxies.txt ]; then
                echo -e "\n${YELLOW}Current Proxies:${NC}"
                nl -s ') ' /etc/yashaoxen/proxies.txt
            else
                echo -e "${RED}No proxies file found${NC}"
            fi
            ;;
        4)
            echo -e "${YELLOW}Testing proxies...${NC}"
            yashaoxen test-proxies
            ;;
        *)
            return
            ;;
    esac
    
    read -p "Press Enter to continue..."
    configure_proxies
}

# Configure DNS
configure_dns() {
    show_banner
    echo -e "${YELLOW}DNS Configuration${NC}\n"
    echo -e "1) Add DNS server"
    echo -e "2) Remove DNS server"
    echo -e "3) List DNS servers"
    echo -e "4) Back to main menu"
    
    read -p "Select an option: " dns_choice
    
    case $dns_choice in
        1)
            read -p "Enter DNS server IP: " dns
            echo "$dns" >> /etc/yashaoxen/dns.txt
            echo -e "${GREEN}✓ DNS server added successfully${NC}"
            ;;
        2)
            if [ -f /etc/yashaoxen/dns.txt ]; then
                nl -s ') ' /etc/yashaoxen/dns.txt
                read -p "Enter line number to remove: " line_num
                sed -i "${line_num}d" /etc/yashaoxen/dns.txt
                echo -e "${GREEN}✓ DNS server removed successfully${NC}"
            else
                echo -e "${RED}No DNS configuration file found${NC}"
            fi
            ;;
        3)
            if [ -f /etc/yashaoxen/dns.txt ]; then
                echo -e "\n${YELLOW}Current DNS Servers:${NC}"
                nl -s ') ' /etc/yashaoxen/dns.txt
            else
                echo -e "${RED}No DNS configuration file found${NC}"
            fi
            ;;
        *)
            return
            ;;
    esac
    
    read -p "Press Enter to continue..."
    configure_dns
}

# Instance management
manage_instances() {
    show_banner
    echo -e "${YELLOW}Instance Management${NC}\n"
    echo -e "1) Start all instances"
    echo -e "2) Stop all instances"
    echo -e "3) Restart all instances"
    echo -e "4) Show status"
    echo -e "5) Show logs"
    echo -e "6) Back to main menu"
    
    read -p "Select an option: " instance_choice
    
    case $instance_choice in
        1)
            echo -e "${YELLOW}Starting all instances...${NC}"
            yashaoxen start
            ;;
        2)
            echo -e "${YELLOW}Stopping all instances...${NC}"
            yashaoxen stop
            ;;
        3)
            echo -e "${YELLOW}Restarting all instances...${NC}"
            yashaoxen restart
            ;;
        4)
            echo -e "${YELLOW}Current status:${NC}"
            yashaoxen status
            ;;
        5)
            echo -e "${YELLOW}Recent logs:${NC}"
            yashaoxen logs | tail -n 50
            ;;
        *)
            return
            ;;
    esac
    
    read -p "Press Enter to continue..."
    manage_instances
}

# Update YashaoXen
update_yashaoxen() {
    show_banner
    echo -e "${YELLOW}Starting YashaoXen update process...${NC}"
    
    backup_configs
    stop_instances
    
    if ! update_from_git; then
        echo -e "${RED}Update failed! Rolling back...${NC}"
        git reset --hard HEAD@{1}
        read -p "Press Enter to continue..."
        return
    fi
    
    if ! update_dependencies; then
        echo -e "${RED}Dependency update failed!${NC}"
        read -p "Press Enter to continue..."
        return
    fi
    
    if systemctl is-active --quiet yashaoxen; then
        echo -e "\n${YELLOW}Restarting YashaoXen service...${NC}"
        systemctl restart yashaoxen
        echo -e "${GREEN}✓ Service restarted${NC}"
    fi
    
    echo -e "\n${GREEN}Update completed successfully!${NC}"
    read -p "Press Enter to continue..."
}

# Show main menu
show_menu() {
    while true; do
        show_banner
        echo -e "1) ${PURPLE}Manage Instances${NC}"
        echo -e "2) ${PURPLE}Configure Proxies${NC}"
        echo -e "3) ${PURPLE}Configure DNS${NC}"
        echo -e "4) ${PURPLE}Update YashaoXen${NC}"
        echo -e "5) ${PURPLE}Backup Configuration${NC}"
        echo -e "6) ${RED}Exit${NC}"
        echo
        read -p "Select an option: " choice
        
        case $choice in
            1) manage_instances ;;
            2) configure_proxies ;;
            3) configure_dns ;;
            4) update_yashaoxen ;;
            5) backup_configs; read -p "Press Enter to continue..." ;;
            6) exit 0 ;;
            *) echo -e "${RED}Invalid option${NC}" ;;
        esac
    done
}

# Main
check_root
show_menu 