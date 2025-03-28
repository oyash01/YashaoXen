import os
import json
import docker
import logging
from typing import Dict
from pathlib import Path
from docker.models.containers import Container

class ContainerManager:
    def __init__(self):
        self.logger = logging.getLogger("ContainerManager")
        self.client = docker.from_env()
        self.earnapp_config = self._load_earnapp_config()

    def _load_earnapp_config(self) -> dict:
        """Load EarnApp container configuration"""
        return {
            "image": "earnapp/earnapp:latest",
            "environment": {
                "EARNAPP_UUID": "",  # Will be generated per instance
                "EARNAPP_DEVICE_NAME": "",  # Will be set per instance
                "PROXY_ENABLED": "true",
                "PROXY_URL": "",  # Will be set per instance
                "TZ": "UTC"
            },
            "volumes": {
                "/etc/yashaoxen/data": {
                    "bind": "/etc/earnapp",
                    "mode": "rw"
                }
            },
            "network_mode": "bridge",
            "restart_policy": {
                "Name": "unless-stopped"
            },
            "cap_add": ["NET_ADMIN"],
            "security_opt": ["seccomp=unconfined"],
            "dns": ["1.1.1.1", "8.8.8.8"]
        }

    def create_earnapp_container(self, proxy_url: str, memory_limit: str = "1G", 
                               security_config: dict = None) -> str:
        """Create new EarnApp container with proxy configuration"""
        try:
            # Generate unique device name and UUID
            device_name = f"yashaoxen_{os.urandom(4).hex()}"
            uuid = os.urandom(16).hex()

            # Prepare container configuration
            config = self.earnapp_config.copy()
            config["environment"].update({
                "EARNAPP_UUID": uuid,
                "EARNAPP_DEVICE_NAME": device_name,
                "PROXY_URL": proxy_url
            })

            # Apply security configuration
            if security_config:
                if security_config.get("enable_seccomp"):
                    config["security_opt"].append("seccomp=/etc/yashaoxen/security/seccomp.json")
                if security_config.get("enable_apparmor"):
                    config["security_opt"].append("apparmor=earnapp")
                if security_config.get("network_isolation"):
                    config["network_mode"] = "none"  # Will be configured with proxy networking

            # Set resource limits
            config.update({
                "mem_limit": memory_limit,
                "memswap_limit": memory_limit,
                "cpu_shares": 512,
                "cpu_period": 100000,
                "cpu_quota": 50000
            })

            # Create and start container
            container = self.client.containers.run(
                self.earnapp_config["image"],
                detach=True,
                **config
            )

            self.logger.info(f"Created EarnApp container {container.id} with proxy {proxy_url}")
            return container.id

        except Exception as e:
            self.logger.error(f"Failed to create EarnApp container: {e}")
            raise

    def stop_container(self, container_id: str):
        """Stop a container"""
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            self.logger.info(f"Stopped container {container_id}")
        except Exception as e:
            self.logger.error(f"Failed to stop container {container_id}: {e}")
            raise

    def start_container(self, container_id: str):
        """Start a container"""
        try:
            container = self.client.containers.get(container_id)
            container.start()
            self.logger.info(f"Started container {container_id}")
        except Exception as e:
            self.logger.error(f"Failed to start container {container_id}: {e}")
            raise

    def update_container_proxy(self, container_id: str, proxy_url: str):
        """Update container's proxy configuration"""
        try:
            container = self.client.containers.get(container_id)
            
            # Update environment variables
            env = dict(e.split('=', 1) for e in container.attrs['Config']['Env'])
            env['PROXY_URL'] = proxy_url
            
            # Recreate container with new proxy
            new_container = self.client.containers.run(
                container.image,
                detach=True,
                environment=env,
                **{k: v for k, v in container.attrs['HostConfig'].items() 
                   if k not in ['NetworkMode', 'RestartPolicy']}
            )
            
            # Remove old container
            container.remove(force=True)
            
            self.logger.info(f"Updated proxy for container {container_id} to {proxy_url}")
            return new_container.id
            
        except Exception as e:
            self.logger.error(f"Failed to update proxy for container {container_id}: {e}")
            raise

    def get_container_stats(self, container_id: str) -> Dict:
        """Get container statistics"""
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                       stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                          stats["precpu_stats"]["system_cpu_usage"]
            cpu_percent = (cpu_delta / system_delta) * 100.0
            
            return {
                "cpu_percent": cpu_percent,
                "memory_usage": stats["memory_stats"]["usage"],
                "network_rx": stats["networks"]["eth0"]["rx_bytes"],
                "network_tx": stats["networks"]["eth0"]["tx_bytes"]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get stats for container {container_id}: {e}")
            raise

    def cleanup_containers(self):
        """Clean up stopped containers"""
        try:
            for container in self.client.containers.list(all=True):
                if container.status == "exited":
                    container.remove()
                    self.logger.info(f"Removed stopped container {container.id}")
        except Exception as e:
            self.logger.error(f"Failed to cleanup containers: {e}")
            raise 