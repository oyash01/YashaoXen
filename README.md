# YashaoXen - Advanced EarnApp Manager

YashaoXen is a powerful management system for EarnApp instances, designed to handle multiple instances with unique device identities and dedicated proxies. It provides advanced features for performance optimization, monitoring, and security.

## Features

- 🔒 **Unique Device Identity**: Each instance runs as a unique device with its own identity
- 🌐 **Dedicated Proxy Support**: One proxy per instance for maximum security
- 📊 **Performance Optimization**: Configurable resource limits and priorities
- 🔄 **Instance Management**: Easy creation, removal, and monitoring of instances
- 📈 **Monitoring & Stats**: Real-time performance and earnings tracking
- 🔐 **Security Features**: Proxy verification, device verification, and network isolation
- 💾 **Backup & Restore**: Configuration backup and restore functionality
- 🔄 **Auto Update**: Automatic updates for EarnApp and system components

## Prerequisites

- Python 3.8 or higher
- Docker installed and running
- Linux-based system (Ubuntu/Debian recommended)
- Root/sudo access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/oyash01/YashaoXen.git
cd YashaoXen
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

3. Run the installer:
```bash
sudo bash install.sh
```

4. Verify installation:
```bash
sudo yashaoxen --version
```

## Usage

### Basic Commands

```bash
# Launch interactive menu
sudo yashaoxen menu

# Start all instances
sudo yashaoxen start

# Stop all instances
sudo yashaoxen stop

# Show system status
sudo yashaoxen status

# View logs
sudo yashaoxen logs

# Update system
sudo yashaoxen update

# Backup configuration
sudo yashaoxen backup
```

### Instance Management

1. Add a new instance:
   - Select "Manage Instances" from the menu
   - Choose "Add New Instance"
   - Enter instance name
   - Select account
   - Choose a dedicated proxy
   - Instance will be created with unique device identity

2. List instances:
   - Shows all instances with their status, proxy, and earnings

3. Remove instance:
   - Select instance to remove
   - Confirm removal
   - Instance and its container will be removed

### Proxy Management

1. Add proxies:
   - Format: `ip:port:username:password`
   - Each proxy can be assigned to one instance
   - Proxies are validated before use

2. Test proxies:
   - Verify proxy connectivity
   - Check proxy anonymity
   - Test proxy speed

### Performance Settings

1. Resource Limits:
   - Memory per instance
   - CPU allocation
   - Network bandwidth
   - IO priority

2. Optimization:
   - CPU priority (high/normal/low)
   - Network priority
   - IO priority
   - Idle threshold

### Security Features

1. Network Isolation:
   - Each instance runs in isolated network
   - Prevents cross-instance communication
   - Configurable network mode

2. Verification:
   - Proxy verification
   - Device verification
   - Auto-update support

## Configuration Files

- `/etc/yashaoxen/config.json`: Main configuration
- `/etc/yashaoxen/proxies.txt`: Proxy list
- `/etc/yashaoxen/dns.txt`: DNS servers
- `/etc/yashaoxen/features.json`: Feature settings
- `/etc/yashaoxen/safeguards.json`: Security settings
- `/etc/yashaoxen/accounts.json`: Account management

## Logging

Logs are stored in `/var/log/yashaoxen/`:
- `yashaoxen.log`: Main application log
- `instance-*.log`: Individual instance logs

## Backup & Restore

1. Create backup:
   - All configuration files
   - Instance settings
   - Account information

2. Restore backup:
   - Select backup file
   - Verify configuration
   - Restore settings

## Troubleshooting

1. Instance won't start:
   - Check logs: `sudo yashaoxen logs`
   - Verify proxy: `sudo yashaoxen test-proxy`
   - Check resource limits

2. Performance issues:
   - Monitor system stats
   - Adjust resource limits
   - Check network settings

3. Proxy problems:
   - Test proxy connection
   - Verify proxy format
   - Check proxy availability

## Security Considerations

1. Proxy Security:
   - Use reliable proxy providers
   - Regular proxy testing
   - Monitor proxy health

2. Network Security:
   - Enable network isolation
   - Use secure DNS servers
   - Regular security updates

3. Instance Security:
   - Unique device identities
   - Regular verification
   - Monitor for suspicious activity

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.

## Credits

- EarnApp for the base application
- Docker for containerization
- Python community for libraries
- Contributors and maintainers
