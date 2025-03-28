import os
import json
import docker
import logging
from pathlib import Path
from typing import Dict, List
from .proxy import ProxyManager
from .container import ContainerManager
from .security import SecurityManager

class YashCore:
    def __init__(self, config_path: str = "/etc/yashaoxen/config.json"):
        self.logger = logging.getLogger("YashCore")
        self.config_path = Path(config_path)
        self.docker_client = docker.from_env()
        self.proxy_manager = ProxyManager()
        self.container_manager = ContainerManager()
        self.security_manager = SecurityManager()
        self.instances: Dict[str, dict] = {}
        
    def load_config(self) -> dict:
        """Load configuration from file"""
        if not self.config_path.exists():
            self.logger.info("Creating default configuration")
            return self._create_default_config()
        
        with open(self.config_path) as f:
            return json.load(f)
    
    def _create_default_config(self) -> dict:
        """Create default configuration"""
        config = {
            "earnapp": {
                "image": "earnapp/earnapp:latest",
                "memory_limit": "1G",
                "cpu_shares": 512,
                "network_mode": "container",
                "security": {
                    "enable_seccomp": True,
                    "enable_apparmor": True,
                    "network_isolation": True
                }
            },
            "proxy": {
                "rotation_interval": 3600,
                "check_interval": 300,
                "retry_attempts": 3
            },
            "system": {
                "max_instances": 10,
                "log_level": "INFO",
                "enable_monitoring": True
            }
        }
        
        os.makedirs(self.config_path.parent, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config

    def create_instance(self, proxy_url: str, memory: str = "1G") -> str:
        """Create new EarnApp instance with proxy"""
        # Validate proxy
        if not self.proxy_manager.validate_proxy(proxy_url):
            raise ValueError("Invalid proxy URL")
        
        # Create container with security measures
        container_id = self.container_manager.create_earnapp_container(
            proxy_url=proxy_url,
            memory_limit=memory,
            security_config=self.load_config()["earnapp"]["security"]
        )
        
        # Setup security
        self.security_manager.setup_container_security(container_id)
        
        # Store instance info
        self.instances[container_id] = {
            "proxy": proxy_url,
            "memory": memory,
            "status": "running"
        }
        
        return container_id

    def create_instances_from_file(self, proxy_file: str, memory: str = "1G") -> List[str]:
        """Create multiple instances from proxy file"""
        with open(proxy_file) as f:
            proxies = [line.strip() for line in f if line.strip()]
        
        instance_ids = []
        for proxy in proxies:
            try:
                instance_id = self.create_instance(proxy, memory)
                instance_ids.append(instance_id)
                self.logger.info(f"Created instance {instance_id} with proxy {proxy}")
            except Exception as e:
                self.logger.error(f"Failed to create instance with proxy {proxy}: {e}")
        
        return instance_ids

    def stop_instance(self, instance_id: str):
        """Stop an instance"""
        if instance_id not in self.instances:
            raise ValueError(f"Instance {instance_id} not found")
        
        self.container_manager.stop_container(instance_id)
        self.instances[instance_id]["status"] = "stopped"

    def start_instance(self, instance_id: str):
        """Start a stopped instance"""
        if instance_id not in self.instances:
            raise ValueError(f"Instance {instance_id} not found")
        
        self.container_manager.start_container(instance_id)
        self.instances[instance_id]["status"] = "running"

    def list_instances(self) -> List[Dict]:
        """List all instances and their status"""
        return [
            {"id": k, **v}
            for k, v in self.instances.items()
        ]

    def monitor_instances(self):
        """Monitor instances and their performance"""
        for instance_id, info in self.instances.items():
            if info["status"] != "running":
                continue
            
            try:
                stats = self.container_manager.get_container_stats(instance_id)
                # Update instance stats
                self.instances[instance_id].update({
                    "cpu_usage": stats["cpu_percent"],
                    "memory_usage": stats["memory_usage"],
                    "network_rx": stats["network_rx"],
                    "network_tx": stats["network_tx"]
                })
            except Exception as e:
                self.logger.error(f"Failed to monitor instance {instance_id}: {e}")

    def rotate_proxies(self):
        """Rotate proxies for all instances"""
        for instance_id, info in self.instances.items():
            try:
                new_proxy = self.proxy_manager.get_next_proxy()
                self.container_manager.update_container_proxy(instance_id, new_proxy)
                self.instances[instance_id]["proxy"] = new_proxy
                self.logger.info(f"Rotated proxy for instance {instance_id}")
            except Exception as e:
                self.logger.error(f"Failed to rotate proxy for instance {instance_id}: {e}") 