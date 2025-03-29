# YashaoXen - Advanced EarnApp Manager

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Docker-lightgrey)

🌙 Professional EarnApp Management System with Advanced Proxy Support 🔄

</div>

## 📑 Table of Contents
- [Installation](#-one-command-installation)
- [Usage Guide](#-usage)
- [Quick Setup](#-quick-setup-guide)
- [Features](#-features)
- [Configuration](#-configuration)
- [Security](#-security-features)
- [Management](#️-management-commands)
- [Monitoring](#-monitoring)
- [Troubleshooting](#-troubleshooting)
- [Documentation](#-documentation)

## 🚀 One-Command Installation

```bash
curl -sSL https://raw.githubusercontent.com/oyash01/YashaoXen/main/install.sh | sudo bash
```

Or install manually:

```bash
# Clone repository
git clone https://github.com/oyash01/YashaoXen.git

# Enter directory
cd YashaoXen

# Run installer
sudo bash install.sh
```

## 🎮 Usage

After installation, simply run:

```bash
sudo yashaoxen
```

This will open the YashaoXen Manager menu:

```
=== System Management ===
1) Manage Instances
2) Configure Proxies
3) Configure DNS

=== Security & Features ===
4) Configure Safeguards
5) Manage Features

=== Maintenance ===
6) Update YashaoXen
7) Backup Configuration
8) View Logs

=== Monitoring ===
9) Show Status
10) Performance Stats
```

## 📋 Quick Setup Guide

1. Start YashaoXen Manager:
```bash
sudo yashaoxen
```

2. First-time setup:
   - Select option 4 to [configure safeguards](#safeguards)
   - Select option 2 to [add your proxies](#proxy-configuration)
   - Select option 3 to configure DNS settings

3. Start instances:
   - Select option 1
   - Choose "Start all instances"
   - Monitor status with option 9

## 🌟 Features

### 🛡️ Core Security
- **Device ID Protection**: Secure device identity management
- **Network Isolation**: Containerized instances with network separation
- **Firewall Integration**: Built-in firewall rules for enhanced security
- **Proxy Validation**: Automatic proxy testing and validation

### 🔄 Proxy Management
- **Auto Rotation**: Smart proxy rotation with configurable intervals
- **Health Checks**: Continuous proxy monitoring and health verification
- **Fail Protection**: Automatic failover for unreliable proxies
- **Custom Rules**: Flexible proxy configuration and routing

### ⚡ Performance
- **Resource Optimization**: Smart resource allocation per instance
- **Auto-scaling**: Dynamic instance management based on performance
- **Load Balancing**: Distribute load across multiple instances
- **Performance Monitoring**: Real-time stats and metrics

### 🛠️ Management Features
- **Interactive CLI**: User-friendly command-line interface
- **Configuration System**: JSON-based configuration management
- **Logging System**: Comprehensive logging with different levels
- **Backup System**: Automated configuration backups

## 🚀 Quick Start

### Prerequisites
- Linux system (Ubuntu 20.04+ recommended)
- Docker installed
- jq package installed
- Root access
- Python 3.8 or higher (automatically installed)

### Installation
```bash
# One-command installation (recommended)
curl -sSL https://raw.githubusercontent.com/oyash01/YashaoXen/main/install.sh | sudo bash

# Or manual installation
git clone https://github.com/oyash01/YashaoXen.git
cd YashaoXen
sudo ./install.sh
```

## 📋 Configuration

### Directory Structure
```
/etc/yashaoxen/
├── config.json       # Main configuration
├── proxies.txt      # Proxy list
├── dns.txt          # DNS settings
├── features.json    # Feature toggles
└── safeguards.json  # Security settings
```

### Basic Configuration
1. Open management interface:
```bash
sudo yashaoxen
```

2. Navigate through menus:
- [System Management](#-usage)
- [Security & Features](#️-core-security)
- [Maintenance](#️-management-features)
- [Monitoring](#-monitoring)

### Proxy Configuration
```bash
# Format: ip:port:username:password
1.2.3.4:8080:user:pass
5.6.7.8:8080:user2:pass2
```

### Resource Limits
```json
{
    "max_instances": 10,
    "max_memory_per_instance": "512M",
    "max_cpu_per_instance": "50%"
}
```

## 🔒 Security Features

### Safeguards
- Instance limits
- Resource constraints
- Network isolation
- Device ID protection
- Proxy validation
- DNS validation

### Monitoring
- Real-time status
- Performance metrics
- Error tracking
- Resource usage
- Proxy health

## 🛠️ Management Commands

### Basic Operations
```bash
# Start instances
yashaoxen start

# Stop instances
yashaoxen stop

# Check status
yashaoxen status

# View logs
yashaoxen logs
```

### Advanced Operations
```bash
# Test proxies
yashaoxen test-proxies

# Rotate proxies
yashaoxen rotate-proxies

# Backup configuration
yashaoxen backup

# Update system
yashaoxen update
```

## 📊 Monitoring

### Available Metrics
- Instance status
- Resource usage
- Proxy performance
- Error rates
- Network stats

### Integration
- Prometheus support
- Grafana dashboards
- Alert system
- Custom metrics

## 🔧 Troubleshooting

### Common Issues
1. **Instance won't start**
   - Check [resource limits](#resource-limits)
   - Verify [proxy configuration](#proxy-configuration)
   - Check network connectivity

2. **Proxy issues**
   - Validate proxy format in [proxy configuration](#proxy-configuration)
   - Test proxy connectivity using `yashaoxen test-proxies`
   - Check rotation settings in features.json

3. **Performance problems**
   - Review [resource limits](#resource-limits)
   - Check system load with `yashaoxen status`
   - Verify network settings

## 📚 Documentation

For detailed documentation, please refer to:

- [Technical Documentation](docs/technical.md) - System architecture and implementation details
- [User Guide](docs/user_guide.md) - Comprehensive usage instructions
- [API Documentation](docs/api.md) - API endpoints and integration
- [Security Guide](docs/security.md) - Security features and best practices
- [Updater Guide](docs/updater.md) - System update procedures
- [Use Cases](docs/use_cases.md) - Common usage scenarios and examples
- [Configuration Guide](docs/configuration.md) - Detailed configuration options

## 📝 License
MIT License

## 🤝 Support
For support, please open an issue on GitHub or contact the maintainers.

## 🔄 Updates
Check for updates regularly using the built-in update system:
```bash
sudo yashaoxen-manager
# Select "Update YashaoXen" from the menu
```
