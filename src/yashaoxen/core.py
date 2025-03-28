import os
import sys
import json
import logging
import docker
import psutil
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from .container import ContainerManager
from .proxy import ProxyManager
from .security import SecurityManager

class YashCore:
    def __init__(self, config_path: str = "/etc/yashaoxen/config.json"):
        """Initialize YashCore with configuration."""
        self.logger = self._setup_logging()
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        try:
            self.docker_client = docker.from_env()
            self.container_manager = ContainerManager(self.docker_client, self.config)
            self.proxy_manager = ProxyManager(self.config.get("proxy_config", {}))
            self.security_manager = SecurityManager()
        except Exception as e:
            self.logger.error(f"Failed to initialize core components: {str(e)}")
            raise

    def _setup_logging(self) -> logging.Logger:
        """Configure logging for YashCore."""
        logger = logging.getLogger("yashaoxen")
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = Path("/var/log/yashaoxen")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler
        fh = logging.FileHandler("/var/log/yashaoxen/core.log")
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger

    def _load_config(self) -> Dict:
        """Load configuration from file or create default."""
        if not self.config_path.exists():
            self.logger.info("Config not found, creating default configuration")
            default_config = {
                "container_config": {
                    "image": "earnapp/earnapp:latest",
                    "cpu_count": 2,
                    "memory_limit": "2g",
                    "network_mode": "bridge",
                    "security_opt": ["apparmor=docker-default"],
                    "cap_drop": ["ALL"],
                    "cap_add": ["NET_ADMIN", "NET_RAW"]
                },
                "proxy_config": {
                    "rotation_interval": 3600,
                    "max_retries": 3,
                    "retry_delay": 5
                },
                "security_config": {
                    "enable_apparmor": True,
                    "enable_seccomp": True,
                    "enable_network_isolation": True,
                    "enable_resource_limits": True
                },
                "monitoring_config": {
                    "enable_prometheus": True,
                    "metrics_port": 9090,
                    "collect_interval": 60
                }
            }
            
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            
            return default_config
        
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {str(e)}")
            raise

    def create_instance(self, proxy_url: str, memory: str = "1g") -> str:
        """Create a new EarnApp instance with specified proxy and memory."""
        try:
            # Validate proxy URL
            if not self.proxy_manager.validate_proxy(proxy_url):
                raise ValueError("Invalid proxy URL format")
            
            # Check system resources
            if not self._check_system_resources(memory):
                raise RuntimeError("Insufficient system resources")
            
            # Create container
            container_id = self.container_manager.create_earnapp_container(
                proxy_url=proxy_url,
                memory_limit=memory
            )
            
            self.logger.info(f"Created instance with ID: {container_id}")
            return container_id
            
        except Exception as e:
            self.logger.error(f"Failed to create instance: {str(e)}")
            raise

    def _check_system_resources(self, requested_memory: str) -> bool:
        """Check if system has sufficient resources."""
        try:
            # Convert memory string to bytes
            mem_value = int(requested_memory[:-1])
            mem_unit = requested_memory[-1].lower()
            mem_multiplier = {
                'k': 1024,
                'm': 1024 * 1024,
                'g': 1024 * 1024 * 1024
            }
            requested_bytes = mem_value * mem_multiplier.get(mem_unit, 1)
            
            # Get available system memory
            available_memory = psutil.virtual_memory().available
            
            # Check CPU cores
            cpu_count = psutil.cpu_count()
            if cpu_count < 2:
                self.logger.warning("Insufficient CPU cores")
                return False
                
            # Check memory
            if available_memory < requested_bytes:
                self.logger.warning("Insufficient memory available")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking system resources: {str(e)}")
            return False

    def start_instance(self, instance_id: str) -> bool:
        """Start an EarnApp instance."""
        try:
            return self.container_manager.start_container(instance_id)
        except Exception as e:
            self.logger.error(f"Failed to start instance {instance_id}: {str(e)}")
            return False

    def stop_instance(self, instance_id: str) -> bool:
        """Stop an EarnApp instance."""
        try:
            return self.container_manager.stop_container(instance_id)
        except Exception as e:
            self.logger.error(f"Failed to stop instance {instance_id}: {str(e)}")
            return False

    def list_instances(self) -> List[Dict]:
        """List all EarnApp instances and their status."""
        try:
            return self.container_manager.list_containers()
        except Exception as e:
            self.logger.error(f"Failed to list instances: {str(e)}")
            return []

    def get_instance_stats(self, instance_id: str) -> Optional[Dict]:
        """Get statistics for a specific instance."""
        try:
            return self.container_manager.get_container_stats(instance_id)
        except Exception as e:
            self.logger.error(f"Failed to get stats for instance {instance_id}: {str(e)}")
            return None

    def rotate_proxy(self, instance_id: str, new_proxy_url: str) -> bool:
        """Rotate proxy for an instance."""
        try:
            if not self.proxy_manager.validate_proxy(new_proxy_url):
                raise ValueError("Invalid proxy URL format")
                
            return self.container_manager.update_container_proxy(
                instance_id, 
                new_proxy_url
            )
        except Exception as e:
            self.logger.error(f"Failed to rotate proxy for instance {instance_id}: {str(e)}")
            return False

    def cleanup(self) -> None:
        """Clean up stopped instances and temporary files."""
        try:
            self.container_manager.cleanup_containers()
            self.proxy_manager.cleanup()
        except Exception as e:
            self.logger.error(f"Failed to perform cleanup: {str(e)}")

    def check_installation(self) -> Dict[str, bool]:
        """Check if all components are properly installed and configured."""
        status = {
            "docker_available": False,
            "config_exists": False,
            "logs_writable": False,
            "network_configured": False,
            "security_configured": False
        }
        
        try:
            # Check Docker
            status["docker_available"] = self._check_docker()
            
            # Check configuration
            status["config_exists"] = self.config_path.exists()
            
            # Check logs
            log_path = Path("/var/log/yashaoxen")
            status["logs_writable"] = os.access(log_path, os.W_OK)
            
            # Check network configuration
            status["network_configured"] = self._check_network_config()
            
            # Check security configuration
            status["security_configured"] = self._check_security_config()
            
        except Exception as e:
            self.logger.error(f"Installation check failed: {str(e)}")
            
        return status

    def _check_docker(self) -> bool:
        """Check if Docker is properly installed and running."""
        try:
            self.docker_client.ping()
            return True
        except Exception:
            return False

    def _check_network_config(self) -> bool:
        """Check if network is properly configured."""
        try:
            # Check IP forwarding
            with open("/proc/sys/net/ipv4/ip_forward") as f:
                ip_forward = f.read().strip() == "1"
            
            # Check iptables
            iptables_check = subprocess.run(
                ["iptables", "-L", "YASHAOXEN"],
                capture_output=True
            ).returncode == 0
            
            return ip_forward and iptables_check
            
        except Exception:
            return False

    def _check_security_config(self) -> bool:
        """Check if security measures are properly configured."""
        try:
            # Check AppArmor
            apparmor_status = subprocess.run(
                ["apparmor_status"],
                capture_output=True
            ).returncode == 0
            
            # Check seccomp
            seccomp_status = os.path.exists("/etc/docker/seccomp-profiles")
            
            return apparmor_status and seccomp_status
            
        except Exception:
            return False 