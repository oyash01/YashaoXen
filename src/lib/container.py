#!/usr/bin/env python3

import os
import logging
import docker
import uuid
import json
import subprocess
from typing import Dict, Any, List, Optional
from docker.types import Mount
from pathlib import Path
from docker.errors import DockerException

logger = logging.getLogger(__name__)

class ContainerManager:
    def __init__(self):
        try:
            self.client = docker.from_env()
        except DockerException as e:
            logger.error(f"Failed to initialize Docker client: {str(e)}")
            raise

    def create_container(self, name: str, image: str, environment: Dict[str, str]) -> bool:
        """Create a new container"""
        try:
            # Check if container already exists
            try:
                existing = self.client.containers.get(name)
                if existing:
                    logger.warning(f"Container {name} already exists")
                    return False
            except docker.errors.NotFound:
                pass

            # Create container
            container = self.client.containers.create(
                image=image,
                name=name,
                environment=environment,
                detach=True,
                restart_policy={"Name": "unless-stopped"},
                ports={'4040/tcp': None},  # Dynamic port mapping
                volumes={
                    '/etc/earnapp': {'bind': f'/etc/earnapp/{name}', 'mode': 'rw'},
                    '/var/log/earnapp': {'bind': f'/var/log/earnapp/{name}', 'mode': 'rw'}
                },
                security_opt=[
                    'no-new-privileges:true',
                    'apparmor:unconfined'
                ],
                ulimits={
                    'nofile': {'soft': 65536, 'hard': 65536}
                },
                sysctls={
                    'net.ipv4.tcp_keepalive_time': '60',
                    'net.ipv4.tcp_keepalive_intvl': '10',
                    'net.ipv4.tcp_keepalive_probes': '6'
                }
            )

            # Start container
            container.start()
            logger.info(f"Successfully created and started container: {name}")
            return True

        except Exception as e:
            logger.error(f"Error creating container {name}: {str(e)}")
            return False

    def stop_container(self, name: str) -> bool:
        """Stop a container"""
        try:
            container = self.client.containers.get(name)
            container.stop()
            logger.info(f"Successfully stopped container: {name}")
            return True
        except Exception as e:
            logger.error(f"Error stopping container {name}: {str(e)}")
            return False

    def remove_container(self, name: str) -> bool:
        """Remove a container"""
        try:
            container = self.client.containers.get(name)
            container.remove(force=True)
            logger.info(f"Successfully removed container: {name}")
            return True
        except Exception as e:
            logger.error(f"Error removing container {name}: {str(e)}")
            return False

    def get_container_status(self, name: str) -> Optional[str]:
        """Get container status"""
        try:
            container = self.client.containers.get(name)
            return container.status
        except Exception as e:
            logger.error(f"Error getting container status {name}: {str(e)}")
            return None

    def list_containers(self) -> list:
        """List all containers"""
        try:
            containers = self.client.containers.list(all=True)
            return [{
                'name': c.name,
                'status': c.status,
                'image': c.image.tags[0] if c.image.tags else 'none'
            } for c in containers]
        except Exception as e:
            logger.error(f"Error listing containers: {str(e)}")
            return []

    def get_container_logs(self, name: str, tail: int = 100) -> Optional[str]:
        """Get container logs"""
        try:
            container = self.client.containers.get(name)
            return container.logs(tail=tail).decode('utf-8')
        except Exception as e:
            logger.error(f"Error getting container logs {name}: {str(e)}")
            return None

    def _save_instance_config(self, container_id: str, config: Dict[str, Any]) -> None:
        """Save instance configuration to file"""
        try:
            config_dir = Path("/etc/yashaoxen/config")
            config_dir.mkdir(parents=True, exist_ok=True)
            
            config_file = config_dir / f"instance-{container_id}.json"
            with open(config_file, "w") as f:
                json.dump(config, f, indent=4)
            
            # Set appropriate permissions
            os.chmod(config_file, 0o600)
            
        except Exception as e:
            logger.error(f"Error saving instance config: {e}")
            raise
    
    def get_container(self, name: str) -> Dict[str, Any]:
        """Get container details"""
        try:
            cmd = ["docker", "inspect", name]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)[0]
        except Exception as e:
            logger.error(f"Error getting container: {e}")
            raise
    
    def update_container(self, name: str, proxy: str) -> None:
        """Update container configuration"""
        try:
            # Stop container
            self.stop_container(name)
            
            # Update environment variables
            container = self.get_container(name)
            env_vars = container["Config"]["Env"]
            
            # Update proxy settings
            new_env_vars = []
            for var in env_vars:
                if not var.startswith(("HTTP_PROXY=", "HTTPS_PROXY=")):
                    new_env_vars.append(var)
            
            new_env_vars.extend([
                f"HTTP_PROXY={proxy}",
                f"HTTPS_PROXY={proxy}",
                "NO_PROXY=localhost,127.0.0.1"
            ])
            
            # Update container
            cmd = ["docker", "update"]
            for var in new_env_vars:
                cmd.extend(["-e", var])
            cmd.append(name)
            
            subprocess.run(cmd, check=True)
            
        except Exception as e:
            logger.error(f"Error updating container: {e}")
            raise 