# YashaoXen Configuration Guide

This guide explains how to configure YashaoXen using simple configuration files. No command-line arguments needed!

## Configuration Files Location

All configuration files are stored in the `/etc/yashaoxen/` directory:

```
/etc/yashaoxen/
├── config.json         # Main configuration
├── proxies.txt        # Proxy list
├── dns.txt           # Custom DNS settings
├── devices.txt       # Device configurations
└── features.json     # Feature toggles
```

## Main Configuration (config.json)

Edit `/etc/yashaoxen/config.json` to configure global settings:

```json
{
    "system": {
        "max_instances": 10,
        "memory_per_instance": "1g",
        "cpu_cores_per_instance": 1,
        "auto_update": true,
        "update_check_interval": 3600
    },
    "network": {
        "proxy_rotation_interval": 3600,
        "retry_attempts": 3,
        "retry_delay": 5,
        "dns_servers": [
            "1.1.1.1",
            "8.8.8.8"
        ]
    },
    "security": {
        "enable_apparmor": true,
        "enable_seccomp": true,
        "network_isolation": true,
        "resource_limits": true
    },
    "monitoring": {
        "enable_prometheus": true,
        "metrics_port": 9090,
        "log_level": "INFO"
    }
}
```

## Proxy Configuration (proxies.txt)

Add your proxies to `/etc/yashaoxen/proxies.txt`, one per line:

```text
socks5://user:pass@host1:port
socks5://user:pass@host2:port
http://user:pass@host3:port
```

## DNS Configuration (dns.txt)

Configure custom DNS settings in `/etc/yashaoxen/dns.txt`:

```text
# Format: domain ip_address
earnapp.com 127.0.0.1
*.earnapp.com 127.0.0.1
verify.earnapp.com 127.0.0.1
```

## Device Configuration (devices.txt)

Configure device settings in `/etc/yashaoxen/devices.txt`:

```text
# Format: name,hardware_id,bandwidth,location
device1,auto,10mbps,US
device2,custom-id-123,5mbps,UK
device3,auto,15mbps,CA
```

## Feature Toggles (features.json)

Enable/disable features in `/etc/yashaoxen/features.json`:

```json
{
    "safeguard_blocking": {
        "enabled": true,
        "methods": ["dns", "iptables", "hosts"]
    },
    "proxy_rotation": {
        "enabled": true,
        "random_rotation": false,
        "sequential_rotation": true
    },
    "anti_detection": {
        "enabled": true,
        "features": {
            "browser_spoofing": true,
            "hardware_spoofing": true,
            "network_spoofing": true
        }
    },
    "monitoring": {
        "enabled": true,
        "features": {
            "resource_monitoring": true,
            "earnings_tracking": true,
            "alert_system": true
        }
    }
}
```

## Quick Start

1. **Install YashaoXen**:
   ```bash
   sudo ./install.sh
   ```

2. **Configure Your Settings**:
   ```bash
   # Copy your proxy list
   sudo cp your_proxies.txt /etc/yashaoxen/proxies.txt

   # Edit main configuration
   sudo nano /etc/yashaoxen/config.json

   # Enable/disable features
   sudo nano /etc/yashaoxen/features.json
   ```

3. **Start YashaoXen**:
   ```bash
   yashaoxen start
   ```

## Configuration Examples

### 1. High-Performance Setup

`config.json`:
```json
{
    "system": {
        "max_instances": 20,
        "memory_per_instance": "2g",
        "cpu_cores_per_instance": 2
    },
    "network": {
        "proxy_rotation_interval": 1800,
        "retry_attempts": 5
    }
}
```

### 2. Low-Resource Setup

`config.json`:
```json
{
    "system": {
        "max_instances": 5,
        "memory_per_instance": "512m",
        "cpu_cores_per_instance": 1
    },
    "network": {
        "proxy_rotation_interval": 7200,
        "retry_attempts": 2
    }
}
```

### 3. Maximum Security Setup

`features.json`:
```json
{
    "safeguard_blocking": {
        "enabled": true,
        "methods": ["dns", "iptables", "hosts", "pattern_matching"]
    },
    "anti_detection": {
        "enabled": true,
        "features": {
            "browser_spoofing": true,
            "hardware_spoofing": true,
            "network_spoofing": true,
            "timezone_spoofing": true,
            "canvas_spoofing": true
        }
    }
}
```

## Advanced Configuration

### Custom Scripts

Place custom scripts in `/etc/yashaoxen/scripts/`:
```bash
/etc/yashaoxen/scripts/
├── pre-start.sh      # Runs before instance start
├── post-start.sh     # Runs after instance start
├── pre-rotate.sh     # Runs before proxy rotation
└── post-rotate.sh    # Runs after proxy rotation
```

### Environment Variables

Create `/etc/yashaoxen/env.conf` for environment variables:
```bash
# Performance tuning
YASHAOXEN_MEMORY_BUFFER=512m
YASHAOXEN_CPU_PRIORITY=high

# Network settings
YASHAOXEN_NETWORK_BUFFER=64k
YASHAOXEN_MAX_CONNECTIONS=1000

# Security settings
YASHAOXEN_SECURITY_LEVEL=high
YASHAOXEN_ENCRYPTION=aes256
```

## Monitoring Configuration

### Prometheus Configuration

Edit `/etc/yashaoxen/prometheus.yml`:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'yashaoxen'
    static_configs:
      - targets: ['localhost:9090']
```

### Alert Configuration

Edit `/etc/yashaoxen/alerts.yml`:
```yaml
alerts:
  - name: high_cpu_usage
    condition: cpu > 90%
    duration: 5m
    action: notify

  - name: proxy_failure
    condition: proxy_errors > 3
    duration: 1m
    action: rotate_proxy
```

## Troubleshooting

1. **Check Configuration**:
   ```bash
   yashaoxen check config
   ```

2. **Validate Proxies**:
   ```bash
   yashaoxen check proxies
   ```

3. **Test Features**:
   ```bash
   yashaoxen check features
   ```

## Support

Need help with configuration?
- Documentation: [YashaoXen Docs](https://github.com/oyash01/YashaoXen/docs)
- Issues: [GitHub Issues](https://github.com/oyash01/YashaoXen/issues)
- Email: charliehackerhack@gmail.com 