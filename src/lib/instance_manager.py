#!/usr/bin/env python3

import logging
import json
import uuid
import subprocess
import random
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from .container import ContainerManager

class InstanceManager:
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.container_manager = ContainerManager(config)
        self.instances: Dict[str, Dict[str, Any]] = {}
        self.instance_dir = Path("/var/lib/aethernode/instances")
        self.instance_dir.mkdir(parents=True, exist_ok=True)
        
    def create_instance(self, proxy_config: Dict[str, Any]) -> str:
        """Create a new EarnApp instance with dedicated proxy"""
        try:
            # Generate instance ID
            instance_id = str(uuid.uuid4())[:8]
            
            # Start container with security measures
            container_id = self.container_manager.start_container(instance_id, proxy_config)
            
            # Store instance information
            instance_info = {
                'id': instance_id,
                'container_id': container_id,
                'proxy': proxy_config,
                'status': 'running'
            }
            
            self.instances[instance_id] = instance_info
            self._save_instance(instance_id, instance_info)
            
            self.logger.info(f"Created instance {instance_id} with container {container_id}")
            return instance_id
            
        except Exception as e:
            self.logger.error(f"Failed to create instance: {e}")
            raise
            
    def stop_instance(self, instance_id: str) -> None:
        """Stop an instance and clean up resources"""
        try:
            if instance_id not in self.instances:
                raise ValueError(f"Instance {instance_id} not found")
                
            instance = self.instances[instance_id]
            
            # Stop container
            self.container_manager.stop_container(instance['container_id'])
            
            # Update instance status
            instance['status'] = 'stopped'
            self._save_instance(instance_id, instance)
            
            self.logger.info(f"Stopped instance {instance_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to stop instance: {e}")
            raise
            
    def restart_instance(self, instance_id: str) -> None:
        """Restart a stopped instance"""
        try:
            if instance_id not in self.instances:
                raise ValueError(f"Instance {instance_id} not found")
                
            instance = self.instances[instance_id]
            
            # Stop existing container if running
            if instance['status'] == 'running':
                self.container_manager.stop_container(instance['container_id'])
                
            # Start new container with same proxy
            container_id = self.container_manager.start_container(instance_id, instance['proxy'])
            
            # Update instance information
            instance['container_id'] = container_id
            instance['status'] = 'running'
            self._save_instance(instance_id, instance)
            
            self.logger.info(f"Restarted instance {instance_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to restart instance: {e}")
            raise
            
    def get_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get instance information"""
        return self.instances.get(instance_id)
        
    def list_instances(self) -> List[Dict[str, Any]]:
        """List all instances"""
        return list(self.instances.values())
        
    def load_instances(self) -> None:
        """Load instance information from disk"""
        try:
            for instance_file in self.instance_dir.glob('*.json'):
                with open(instance_file, 'r') as f:
                    instance = json.load(f)
                    self.instances[instance['id']] = instance
                    
            self.logger.info(f"Loaded {len(self.instances)} instances")
            
        except Exception as e:
            self.logger.error(f"Failed to load instances: {e}")
            raise
            
    def _save_instance(self, instance_id: str, instance: Dict[str, Any]) -> None:
        """Save instance information to disk"""
        try:
            instance_file = self.instance_dir / f"{instance_id}.json"
            with open(instance_file, 'w') as f:
                json.dump(instance, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save instance {instance_id}: {e}")
            raise 