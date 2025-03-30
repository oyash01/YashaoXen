# YashaoXen - Advanced EarnApp Manager

A powerful and user-friendly EarnApp management system with advanced features and security safeguards.

## Features

- Multi-instance management
- Advanced proxy support with rotation
- DNS configuration
- Security safeguards
- Performance monitoring
- Automatic updates
- Configuration backup
- Detailed logging
- Interactive CLI interface

## Quick Start

### One-Line Installation

```bash
curl -sSL https://raw.githubusercontent.com/oyash01/YashaoXen/main/install.sh | sudo bash
```

### Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/oyash01/YashaoXen.git
cd YashaoXen
```

2. Run the installer:
```bash
sudo ./install.sh
```

## Usage

### Interactive Menu

```bash
sudo yashaoxen menu
```

This will show the main menu with the following options:

1. Manage Instances
2. Configure Proxies
3. Configure DNS
4. Configure Safeguards
5. Manage Features
6. Update YashaoXen
7. Backup Configuration
8. View Logs
9. Show Status
10. Performance Stats

### Command Line Interface

```bash
# Start all instances
sudo yashaoxen start

# Stop all instances
sudo yashaoxen stop

# Check status
sudo yashaoxen status

# View logs
sudo yashaoxen logs

# Update YashaoXen
sudo yashaoxen update

# Remove YashaoXen
sudo yashaoxen remove
```

## Configuration

### Directory Structure

```
/etc/yashaoxen/
├── config/
│   ├── proxies.txt      # Proxy list
│   ├── dns.txt         # DNS settings
│   ├── features.json   # Feature toggles
│   └── safeguards.json # Security settings
└── backup/            # Configuration backups
```

### Proxy Configuration

Format: `ip:port:username:password`
```
1.2.3.4:8080:user:pass
5.6.7.8:8080:user2:pass2
```

### DNS Configuration

One DNS server per line:
```
8.8.8.8
1.1.1.1
```

### Security Safeguards

Default configuration:
```json
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
```

### Features

Default configuration:
```json
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
```

## Monitoring

### System Status

The status command shows:
- Docker version and container count
- CPU usage
- Memory usage
- Disk usage

### Performance Stats

The performance command shows:
- Instance name
- CPU usage
- Memory usage
- Network I/O

## Logging

Logs are stored in `/var/log/yashaoxen/`:
- `yashaoxen.log`: Main application log
- `install.log`: Installation log
- `update.log`: Update log

## Security

### Safeguards

- Instance limits
- Resource constraints
- Network isolation
- Proxy verification
- Device verification
- SSL verification
- Anonymity checks
- Location verification
- Traffic monitoring

### Proxy Security

- SSL verification
- Anonymity checks
- Location verification
- Automatic rotation
- Health checks

## Updates

### Automatic Updates

The system can automatically update:
- YashaoXen itself
- EarnApp containers
- Dependencies

### Manual Updates

```bash
# Update everything
sudo yashaoxen update

# Update specific component
sudo yashaoxen update --component [yashaoxen|earnapp]
```

## Backup

### Configuration Backup

```bash
# Create backup
sudo yashaoxen backup

# Restore backup
sudo yashaoxen restore [backup_file]
```

Backups are stored in `/etc/yashaoxen/backup/` with timestamps.

## Troubleshooting

### Common Issues

1. **Instance won't start**
   - Check resource limits
   - Verify proxy configuration
   - Check network connectivity

2. **Proxy issues**
   - Validate proxy format
   - Test proxy connectivity
   - Check rotation settings

3. **Performance problems**
   - Review resource limits
   - Check system load
   - Verify network settings

## Credits

- Based on money4band's EarnApp implementation
- Maintained by MRColorR
