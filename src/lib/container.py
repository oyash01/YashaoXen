#!/usr/bin/env python3

import os
import logging
import docker
import uuid
from typing import Dict, Any
from pathlib import Path
from .security_manager import SecurityManager

class ContainerManager:
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.client = docker.from_env()
        self.security_manager = SecurityManager()
        
    def start_container(self, instance_id: str, proxy_config: Dict[str, Any]) -> str:
        """Start a new EarnApp container with security measures"""
        try:
            container_name = f"earnapp_{instance_id}"
            
            # Set up security
            self.security_manager.setup_container_isolation(container_name, self.config)
            self.security_manager.setup_network_security(container_name, self.config)
            
            # Prepare container configuration
            container_config = self._prepare_container_config(instance_id, proxy_config)
            
            # Create and start container
            container = self.client.containers.run(**container_config)
            
            self.logger.info(f"Started container {container_name} with ID {container.id}")
            return container.id
            
        except Exception as e:
            self.logger.error(f"Failed to start container: {e}")
            raise
            
    def stop_container(self, container_id: str) -> None:
        """Stop and remove a container"""
        try:
            container = self.client.containers.get(container_id)
            container_name = container.name
            
            # Stop container
            container.stop()
            container.remove()
            
            # Clean up security configurations
            self._cleanup_security(container_name)
            
            self.logger.info(f"Stopped and removed container {container_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to stop container: {e}")
            raise
            
    def _prepare_container_config(self, instance_id: str, proxy_config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare Docker container configuration"""
        container_name = f"earnapp_{instance_id}"
        
        # Base configuration
        config = {
            'name': container_name,
            'image': 'earnapp/earnapp:latest',
            'detach': True,
            'restart_policy': {'Name': 'unless-stopped'},
            'network_mode': f"container:netns_{container_name}",
            'security_opt': [
                f"seccomp=/etc/docker/seccomp/{container_name}.json",
                f"apparmor={container_name}"
            ],
            'environment': {
                'EARNAPP_UUID': self.config['earnapp']['uuid'],
                'PROXY_URL': f"{proxy_config['type']}://{proxy_config['host']}:{proxy_config['port']}",
                'PROXY_USER': proxy_config.get('username'),
                'PROXY_PASS': proxy_config.get('password')
            }
        }
        
        # Add resource limits
        resources = self.config.get('container', {}).get('resources', {})
        if resources:
            config['mem_limit'] = resources.get('memory_limit', '1G')
            config['cpu_shares'] = resources.get('cpu_shares', 1024)
            
        return config
        
    def _cleanup_security(self, container_name: str) -> None:
        """Clean up security configurations for container"""
        try:
            # Remove seccomp profile
            seccomp_path = Path(f"/etc/docker/seccomp/{container_name}.json")
            if seccomp_path.exists():
                seccomp_path.unlink()
                
            # Remove AppArmor profile
            apparmor_path = Path(f"/etc/apparmor.d/containers/{container_name}")
            if apparmor_path.exists():
                apparmor_path.unlink()
                
            # Remove network namespace
            namespace = f"netns_{container_name}"
            os.system(f"ip netns del {namespace}")
            
            # Remove cgroup
            cgroup_path = Path(f"/sys/fs/cgroup/memory/{container_name}")
            if cgroup_path.exists():
                os.system(f"rmdir {cgroup_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to clean up security configurations: {e}")
            # Don't raise the exception as this is cleanup code
            
    def _load_config(self, filename: str) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            config_path = Path(filename)
            if config_path.exists():
                return eval(config_path.read_text())
            return {}
        except Exception as e:
            self.logger.error(f"Error loading config {filename}: {e}")
            return {}
            
    def _get_performance_env(self) -> Dict[str, str]:
        """Get environment variables for performance optimization"""
        return {
            # Bypass EarnApp's bandwidth limits
            "EARNAPP_BANDWIDTH_LIMIT": "0",
            "EARNAPP_TRAFFIC_LIMIT": "0",
            "EARNAPP_RATE_LIMIT": "0",
            
            # System resource settings
            "GOMAXPROCS": "0",  # Use all available CPUs
            "GOGC": "100",      # Aggressive garbage collection
            
            # Network optimizations
            "TCP_NODELAY": "1",
            "TCP_QUICKACK": "1",
            
            # Memory optimizations
            "MALLOC_ARENA_MAX": "2",
            "MALLOC_TRIM_THRESHOLD_": "131072",
            
            # Additional optimizations
            "EARNAPP_AGGRESSIVE_MODE": "1",
            "EARNAPP_OPTIMIZE_BANDWIDTH": "1"
        } 