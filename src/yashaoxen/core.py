"""
YashaoXen Core - Main implementation
"""

import os
import json
import time
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
from datetime import datetime, timedelta

class YashCore:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.docker_client = docker.from_env()
        self.security = SecurityManager()
        self.config = self._load_config()
        self._load_proxies()

    def _load_config(self) -> Dict:
        """Load configuration from file."""
        config_file = "/etc/yashaoxen/config.json"
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        return {}

    def _load_proxies(self) -> List[str]:
        """Load proxies from file."""
        self.proxies = []
        proxy_file = "/etc/yashaoxen/proxies.txt"
        if os.path.exists(proxy_file):
            with open(proxy_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.proxies.append(line)
        return self.proxies

    def _create_earnapp_container(self, instance_id: str, proxy: Optional[str] = None) -> str:
        """Create a new EarnApp container instance."""
        try:
            # Get EarnApp token from config
            token = self.config.get("earnapp", {}).get("token")
            if not token:
                raise ValueError("EarnApp token not configured")

            # Prepare container configuration
            container_name = f"yashaoxen_earnapp_{instance_id}"
            environment = {
                "EARNAPP_UUID": token,
                "PROXY_URL": proxy if proxy else ""
            }

            # Get resource limits from security manager
            resources = self.security.get_resource_limits()

            # Create and start container
            container = self.docker_client.containers.run(
                "earnapp/earnapp:latest",
                name=container_name,
                environment=environment,
                detach=True,
                restart_policy={"Name": "unless-stopped"},
                mem_limit=resources["memory"],
                cpu_period=100000,
                cpu_quota=int(float(resources["cpu"]) * 100000),
                security_opt=self.security.get_container_security_opts()
            )

            return container.id
        except Exception as e:
            self.logger.error(f"Failed to create container: {str(e)}")
            raise

    def start_all(self) -> None:
        """Start all EarnApp instances."""
        try:
            # Get number of instances from config
            num_instances = self.config.get("earnapp", {}).get("instances", 1)
            
            # Load available proxies
            if not self.proxies:
                self.logger.warning("No proxies configured. Running without proxies.")
            
            # Create instances
            for i in range(num_instances):
                proxy = self.proxies[i % len(self.proxies)] if self.proxies else None
                instance_id = f"instance_{i+1}"
                
                # Verify proxy if configured
                if proxy and not self.security.verify_proxy(proxy):
                    self.logger.warning(f"Proxy verification failed for {proxy}")
                    continue
                
                # Create container
                self._create_earnapp_container(instance_id, proxy)
                self.logger.info(f"Started instance {instance_id}")
            
            self.logger.info("All instances started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start instances: {str(e)}")
            raise

    def stop_all(self) -> None:
        """Stop all EarnApp instances."""
        try:
            containers = self.docker_client.containers.list(
                filters={"name": "yashaoxen_earnapp_"}
            )
            
            for container in containers:
                container.stop()
                container.remove()
            
            self.logger.info("All instances stopped successfully")
        except Exception as e:
            self.logger.error(f"Failed to stop instances: {str(e)}")
            raise

    def list_instances(self) -> List[Dict]:
        """List all running instances and their status."""
        try:
            instances = []
            containers = self.docker_client.containers.list(
                all=True,
                filters={"name": "yashaoxen_earnapp_"}
            )
            
            for container in containers:
                # Get container info
                info = container.attrs
                status = container.status
                name = container.name.replace("yashaoxen_earnapp_", "")
                
                # Calculate uptime
                started_at = datetime.fromisoformat(info["State"]["StartedAt"].replace("Z", "+00:00"))
                uptime = datetime.now(started_at.tzinfo) - started_at
                
                # Get proxy from environment
                env = dict(e.split("=") for e in info["Config"]["Env"] if "=" in e)
                proxy = env.get("PROXY_URL", "None")
                
                instances.append({
                    "name": name,
                    "status": status,
                    "proxy": proxy,
                    "uptime": str(uptime).split(".")[0]  # Remove microseconds
                })
            
            return instances
        except Exception as e:
            self.logger.error(f"Failed to list instances: {str(e)}")
            raise

    def rotate_proxies(self) -> None:
        """Rotate proxies for all instances."""
        try:
            if not self.proxies:
                self.logger.warning("No proxies available for rotation")
                return
            
            instances = self.list_instances()
            for i, instance in enumerate(instances):
                # Get next proxy
                proxy = self.proxies[i % len(self.proxies)]
                
                # Verify proxy
                if not self.security.verify_proxy(proxy):
                    self.logger.warning(f"Proxy verification failed for {proxy}")
                    continue
                
                # Stop old container
                container = self.docker_client.containers.get(f"yashaoxen_earnapp_{instance['name']}")
                container.stop()
                container.remove()
                
                # Create new container with rotated proxy
                self._create_earnapp_container(instance['name'], proxy)
                self.logger.info(f"Rotated proxy for {instance['name']}")
            
            self.logger.info("Proxy rotation completed")
        except Exception as e:
            self.logger.error(f"Failed to rotate proxies: {str(e)}")
            raise

    def create_instance(self, proxy_url: str, memory: str = "1g") -> str:
        """Create a new EarnApp instance with specified proxy and memory."""
        try:
            # Validate proxy URL
            if not self.proxies:
                raise ValueError("No proxies available")
            
            # Check system resources
            if not self._check_system_resources(memory):
                raise RuntimeError("Insufficient system resources")
            
            # Create container
            container_id = self._create_earnapp_container(
                instance_id=proxy_url.replace(".", "_"),
                proxy=proxy_url
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
            return self._create_earnapp_container(instance_id)
        except Exception as e:
            self.logger.error(f"Failed to start instance {instance_id}: {str(e)}")
            return False

    def stop_instance(self, instance_id: str) -> bool:
        """Stop an EarnApp instance."""
        try:
            container = self.docker_client.containers.get(f"yashaoxen_earnapp_{instance_id}")
            container.stop()
            container.remove()
            self.logger.info(f"Stopped instance {instance_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop instance {instance_id}: {str(e)}")
            return False

    def get_instance_stats(self, instance_id: str) -> Optional[Dict]:
        """Get statistics for a specific instance."""
        try:
            container = self.docker_client.containers.get(f"yashaoxen_earnapp_{instance_id}")
            stats = container.stats(stream=False)
            return {
                "cpu_usage": stats["cpu_stats"]["cpu_usage"]["total_usage"],
                "memory_usage": stats["memory_stats"]["usage"],
                "memory_limit": stats["memory_stats"]["limit"],
                "network_rx": stats["networks"]["eth0"]["rx_bytes"],
                "network_tx": stats["networks"]["eth0"]["tx_bytes"]
            }
        except Exception as e:
            self.logger.error(f"Failed to get stats for instance {instance_id}: {str(e)}")
            return None

    def rotate_proxy(self, instance_id: str, new_proxy_url: str) -> bool:
        """Rotate proxy for an instance."""
        try:
            if not self.proxies:
                raise ValueError("No proxies available for rotation")
            
            if not self.security.verify_proxy(new_proxy_url):
                raise ValueError("Invalid proxy")
            
            self.stop_instance(instance_id)
            self.start_instance(instance_id)
            self.logger.info(f"Rotated proxy for {instance_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to rotate proxy for instance {instance_id}: {str(e)}")
            return False

    def cleanup(self) -> None:
        """Clean up stopped instances and temporary files."""
        try:
            self.stop_all()
            self.logger.info("All instances cleaned up")
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
            status["config_exists"] = self._check_config()
            
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

    def _check_config(self) -> bool:
        """Check if configuration is valid."""
        try:
            # Check if proxies are loaded
            if not self.proxies:
                self.logger.warning("No proxies configured")
                return False
            
            # Check if all instances can be started
            for proxy in self.proxies:
                if not self._check_system_resources(proxy):
                    self.logger.warning(f"Insufficient resources for proxy: {proxy}")
                    return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error checking configuration: {str(e)}")
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