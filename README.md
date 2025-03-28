# YashaoXen - Multi-Proxy EarnApp Management System

YashaoXen is a robust and user-friendly system for managing multiple EarnApp instances with proxy support. It provides automated setup, monitoring, and management capabilities with built-in safeguards.

## Features

- 🚀 Easy setup and management of multiple EarnApp instances
- 🔄 Automatic proxy rotation and health monitoring
- 🛡️ Built-in safeguards and anti-detection measures
- 📊 Real-time monitoring and status reporting
- 🔒 Secure container isolation for each instance
- ⚡ Resource management and optimization

## Prerequisites

- Linux/Unix system
- Python 3.8 or higher
- Docker installed and running
- Root/sudo access
- Minimum 2GB RAM per instance
- Stable internet connection

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/oyash01/YashaoXen.git
   cd YashaoXen
   ```

2. Install the package:
   ```bash
   pip install -e .
   ```

3. Create a proxy file (e.g., `proxies.txt`) with one proxy per line:
   ```
   socks5://user:pass@host:port
   http://user:pass@host:port
   ```

## Usage

### Creating Instances

Create EarnApp instances using your proxy list:

```bash
yashaoxen create-instances --proxy-file proxies.txt --memory 1G
```

Options:
- `--proxy-file, -p`: Path to your proxy list file
- `--memory, -m`: Memory limit per instance (1G or 2G)
- `--yes, -y`: Skip confirmation prompts

The system will:
1. Validate your proxies
2. Check system resources
3. Create isolated containers
4. Configure proxy settings
5. Start EarnApp instances
6. Monitor health

### Monitoring Instances

View real-time status of your instances:

```bash
yashaoxen monitor
```

This will show:
- Instance status
- Memory usage
- CPU usage
- Network statistics
- Proxy status

### Checking Status

Get a quick overview of all instances:

```bash
yashaoxen status
```

## Safety Features

YashaoXen includes several safety measures:

1. **Proxy Validation**: Each proxy is tested before use
2. **Rate Limiting**: Prevents too rapid operations
3. **Resource Monitoring**: Ensures system stability
4. **Error Handling**: Graceful failure recovery
5. **Container Isolation**: Secure instance separation

## Troubleshooting

### Common Issues

1. **Docker Permission Error**
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

2. **Proxy Connection Failed**
   - Check proxy format
   - Verify proxy credentials
   - Ensure proxy is online

3. **Resource Limits**
   - Ensure enough RAM available
   - Check system CPU usage
   - Verify disk space

### Logs

- Application logs: `/var/log/yashaoxen/app.log`
- EarnApp logs: `/var/log/earnapp/`
- Container logs: Available via `docker logs`

## Best Practices

1. **Proxy Management**
   - Use high-quality proxies
   - Regularly update proxy list
   - Monitor proxy health

2. **Resource Planning**
   - Plan memory allocation
   - Monitor system resources
   - Scale gradually

3. **Maintenance**
   - Regular health checks
   - Update proxies as needed
   - Monitor earnings

## Support

For issues and support:
- Create an issue on GitHub
- Join our community discussions
- Check the documentation

## License

MIT License - see LICENSE file for details
