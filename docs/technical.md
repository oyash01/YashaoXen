# YashaoXen Technical Documentation

## System Architecture

### Overview

YashaoXen is built on a modular architecture that separates concerns into distinct components while maintaining high cohesion and loose coupling. The system is designed to be scalable, maintainable, and secure.

```
YashaoXen/
├── src/
│   └── yashaoxen/
│       ├── core.py         # Core system management
│       ├── proxy.py        # Proxy handling
│       ├── container.py    # Container management
│       ├── cli.py         # Command-line interface
│       └── utils/
│           ├── security.py # Security utilities
│           └── network.py  # Network utilities
├── docker/
│   ├── Dockerfile         # Container definition
│   ├── supervisord.conf   # Process management
│   └── entrypoint.sh     # Container initialization
└── config/
    └── default.json      # Default configuration
```

### Core Components

#### 1. Core Engine (`core.py`)

The core engine is responsible for orchestrating all system components and managing the lifecycle of EarnApp instances.

```python
class YashCore:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.proxy_manager = ProxyManager()
        self.container_manager = ContainerManager()
        self.config = self._load_config()

    def create_instance(self, proxy: str, memory: str):
        # Validate resources
        self._check_resources(memory)
        
        # Create container
        container = self.container_manager.create_earnapp_container(
            proxy=proxy,
            memory_limit=memory
        )
        
        # Monitor health
        self._monitor_container_health(container)
```

#### 2. Proxy Management (`proxy.py`)

Handles all proxy-related operations including validation, health checking, and rotation.

```python
class ProxyManager:
    def validate_proxy(self, proxy_url: str) -> bool:
        # URL format validation
        parsed = urlparse(proxy_url)
        if not all([parsed.scheme, parsed.hostname, parsed.port]):
            return False
            
        # Connection testing
        try:
            response = self._test_connection(proxy_url)
            return response.status_code == 200
        except Exception:
            return False
```

#### 3. Container Management (`container.py`)

Manages Docker containers and their resources.

```python
class ContainerManager:
    def create_earnapp_container(self, proxy: str, memory_limit: str):
        container_config = {
            'image': 'yashaoxen/earnapp:latest',
            'environment': {
                'PROXY_URL': proxy,
                'MEMORY_LIMIT': memory_limit
            },
            'mem_limit': self._parse_memory(memory_limit),
            'security_opt': ['no-new-privileges'],
            'cap_drop': ['ALL'],
            'restart_policy': {'Name': 'unless-stopped'}
        }
        
        return self.docker_client.containers.run(**container_config)
```

### Security Implementation

#### 1. Container Isolation

Each EarnApp instance runs in its own container with:
- Dedicated network namespace
- Limited capabilities
- Resource constraints
- Volume isolation

```dockerfile
FROM ubuntu:20.04

# Security hardening
RUN apt-get update && apt-get install -y \
    ca-certificates \
    iptables \
    && rm -rf /var/lib/apt/lists/*

# Drop capabilities
RUN setcap cap_net_bind_service=+ep /usr/local/bin/earnapp

# Non-root user
RUN useradd -r -s /bin/false earnapp
USER earnapp

# Limited filesystem access
VOLUME ["/opt/earnapp/data"]
```

#### 2. Proxy Security

- Connection encryption
- Authentication validation
- Traffic monitoring
- Pattern detection

```python
def secure_proxy_connection(proxy_url: str) -> bool:
    # Validate proxy format
    if not is_valid_proxy_format(proxy_url):
        return False
        
    # Test connection security
    try:
        response = requests.get(
            'https://api.ipify.org',
            proxies={'https': proxy_url},
            verify=True,
            timeout=10
        )
        return response.status_code == 200
    except Exception:
        return False
```

### Resource Management

#### 1. Memory Management

```python
def allocate_memory(container: Container, limit: str):
    # Parse memory limit
    bytes_limit = parse_memory_string(limit)
    
    # Set container memory limit
    container.update(mem_limit=bytes_limit)
    
    # Monitor usage
    while container.status == 'running':
        stats = container.stats(stream=False)
        usage = stats['memory_stats']['usage']
        if usage > bytes_limit * 0.9:  # 90% threshold
            logger.warning(f"High memory usage: {usage/1024/1024}MB")
```

#### 2. CPU Management

```python
def manage_cpu(container: Container):
    # Set CPU quota
    container.update(cpu_quota=100000)  # 100ms
    container.update(cpu_period=100000)  # 100ms
    
    # Monitor CPU usage
    while container.status == 'running':
        stats = container.stats(stream=False)
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage']
        cpu_percent = (cpu_delta / system_delta) * 100
        if cpu_percent > 80:  # 80% threshold
            logger.warning(f"High CPU usage: {cpu_percent}%")
```

### Network Management

#### 1. Traffic Control

```python
def setup_traffic_control(container: Container):
    # Set bandwidth limits
    container.update(
        host_config=docker.types.HostConfig(
            blkio_weight=500,  # IO priority
            device_read_bps=[{"Path": "/dev/sda", "Rate": 20971520}],  # 20MB/s
            device_write_bps=[{"Path": "/dev/sda", "Rate": 20971520}]
        )
    )
```

#### 2. Network Monitoring

```python
def monitor_network(container: Container):
    while container.status == 'running':
        stats = container.stats(stream=False)
        rx_bytes = stats['networks']['eth0']['rx_bytes']
        tx_bytes = stats['networks']['eth0']['tx_bytes']
        
        # Check for unusual patterns
        if is_suspicious_traffic(rx_bytes, tx_bytes):
            logger.warning("Suspicious network activity detected")
```

### Error Handling

```python
class ErrorHandler:
    def handle_container_error(self, container: Container, error: Exception):
        try:
            # Log error
            logger.error(f"Container {container.id}: {error}")
            
            # Attempt recovery
            if isinstance(error, docker.errors.ContainerError):
                container.restart()
            elif isinstance(error, docker.errors.APIError):
                self._handle_api_error(error)
                
        except Exception as e:
            logger.critical(f"Recovery failed: {e}")
            self._notify_admin(container, error)
```

### Monitoring System

```python
class MonitoringSystem:
    def __init__(self):
        self.metrics = {}
        self.alerts = []
        
    def collect_metrics(self, container: Container):
        stats = container.stats(stream=False)
        self.metrics[container.id] = {
            'cpu_usage': self._calculate_cpu_percent(stats),
            'memory_usage': stats['memory_stats']['usage'],
            'network_rx': stats['networks']['eth0']['rx_bytes'],
            'network_tx': stats['networks']['eth0']['tx_bytes']
        }
        
    def check_thresholds(self):
        for container_id, metrics in self.metrics.items():
            if metrics['cpu_usage'] > 80:
                self._create_alert('HIGH_CPU', container_id)
            if metrics['memory_usage'] > self.memory_threshold:
                self._create_alert('HIGH_MEMORY', container_id)
```

## Performance Optimization

### 1. Container Optimization

```dockerfile
# Optimize container size
FROM ubuntu:20.04 AS builder
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Multi-stage build
FROM ubuntu:20.04
COPY --from=builder /usr/local/bin/earnapp /usr/local/bin/
```

### 2. Resource Efficiency

```python
def optimize_resources(container: Container):
    # Set CPU affinity
    container.update(cpu_set='0-1')  # Use first two CPU cores
    
    # Configure memory swappiness
    container.update(memory_swappiness=60)
    
    # Set IO priority
    container.update(blkio_weight=500)
```

## Logging and Monitoring

### 1. Logging System

```python
class LogManager:
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/var/log/yashaoxen/app.log'),
                logging.StreamHandler()
            ]
        )
```

### 2. Metrics Collection

```python
class MetricsCollector:
    def collect_container_metrics(self, container: Container):
        return {
            'cpu_usage': self._get_cpu_usage(container),
            'memory_usage': self._get_memory_usage(container),
            'network_stats': self._get_network_stats(container),
            'disk_io': self._get_disk_io(container)
        }
```

## API Documentation

### 1. Core API

```python
class YashCore:
    def create_instance(self, proxy: str, memory: str) -> Container:
        """Create a new EarnApp instance.
        
        Args:
            proxy (str): Proxy URL in format scheme://user:pass@host:port
            memory (str): Memory limit (e.g., "1G", "2G")
            
        Returns:
            Container: Docker container instance
            
        Raises:
            ResourceError: If system resources are insufficient
            ProxyError: If proxy validation fails
        """
```

### 2. CLI API

```python
@click.command()
@click.option('--proxy-file', '-p', type=click.Path(exists=True))
@click.option('--memory', '-m', type=click.Choice(['1G', '2G']))
def create_instances(proxy_file: str, memory: str):
    """Create EarnApp instances from proxy list.
    
    Args:
        proxy_file (str): Path to file containing proxy list
        memory (str): Memory limit per instance
    """
```

## Configuration Reference

### 1. System Configuration

```json
{
    "system": {
        "max_instances": 10,
        "memory_buffer": "512M",
        "cpu_allocation": "0.5"
    },
    "security": {
        "enable_isolation": true,
        "drop_capabilities": ["ALL"],
        "allow_networking": true
    },
    "monitoring": {
        "interval": 60,
        "metrics_retention": "7d",
        "alert_threshold": {
            "cpu": 80,
            "memory": 90
        }
    }
}
```

### 2. Docker Configuration

```yaml
version: '3.8'
services:
  earnapp:
    build: .
    restart: unless-stopped
    environment:
      - PROXY_URL=${PROXY_URL}
      - MEMORY_LIMIT=${MEMORY_LIMIT}
    security_opt:
      - no-new-privileges
    cap_drop:
      - ALL
    volumes:
      - earnapp_data:/opt/earnapp/data
``` 