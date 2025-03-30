#!/usr/bin/env python3

import os
import json
import logging
import docker
from typing import Dict, Any, List
from pathlib import Path
from .container import ContainerManager
from .network import NetworkManager
from .proxy_handler import ProxyHandler
from .anti_detect import AntiDetectionSystem
from .earnapp import EarnAppManager

logger = logging.getLogger(__name__)

class InstanceManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.container_manager = ContainerManager()
        self.network_manager = NetworkManager(config)
        self.proxy_handler = ProxyHandler(config)
        self.earnapp_manager = EarnAppManager(config)
        self.anti_detect = AntiDetectionSystem(config)
        
    def create_instance(self) -> str:
        """Create a new EarnApp instance"""
        try:
            # Generate unique instance ID
            instance_id = f"yashaoxen_earnapp_{len(self.get_running_instances())}"
            
            # Get proxy and DNS for this instance
            proxy = self.proxy_handler.get_next_proxy()
            dns = self.network_manager.get_next_dns()
            
            # Create container with network isolation
            container = self.container_manager.create_container(
                name=instance_id,
                proxy=proxy,
                dns=dns,
                network_isolation=self.config.get("safeguards", {}).get("network_isolation", True)
            )
            
            # Configure anti-detection measures
            if self.config.get("safeguards", {}).get("enabled", True):
                self.anti_detect.apply_measures(container.id)
            
            # Start EarnApp service
            self.earnapp_manager.start_service(container.id)
            
            logger.info(f"Created instance {instance_id}")
            return instance_id
            
        except Exception as e:
            logger.error(f"Error creating instance: {e}")
            raise
    
    def stop_instance(self, instance_id: str) -> None:
        """Stop an EarnApp instance"""
        try:
            self.container_manager.stop_container(instance_id)
            logger.info(f"Stopped instance {instance_id}")
        except Exception as e:
            logger.error(f"Error stopping instance {instance_id}: {e}")
            raise
    
    def get_instance_status(self, instance_id: str) -> Dict[str, Any]:
        """Get status of an instance"""
        try:
            container = self.container_manager.get_container(instance_id)
            stats = container.stats(stream=False)
            
            # Get instance configuration
            instance_config = self.container_manager._get_instance_config(instance_id)
            
            return {
                "status": container.status,
                "uuid": instance_config["uuid"],
                "proxy": instance_config["proxy"],
                "dns": instance_config["dns"],
                "cpu_usage": self._calculate_cpu_usage(stats),
                "memory_usage": self._calculate_memory_usage(stats),
                "network_usage": self._calculate_network_usage(stats)
            }
        except Exception as e:
            logger.error(f"Error getting status for {instance_id}: {e}")
            return {
                "status": "error",
                "uuid": None,
                "proxy": None,
                "dns": None,
                "cpu_usage": 0,
                "memory_usage": 0,
                "network_usage": 0
            }
    
    def rotate_proxy(self, instance_id: str) -> None:
        """Rotate proxy for an instance"""
        try:
            new_proxy = self.proxy_handler.get_next_proxy()
            self.container_manager.update_proxy(instance_id, new_proxy)
            logger.info(f"Rotated proxy for instance {instance_id}")
        except Exception as e:
            logger.error(f"Error rotating proxy for {instance_id}: {e}")
            raise
    
    def get_running_instances(self) -> List[str]:
        """Get list of running instance IDs"""
        return self.container_manager.list_containers()
    
    def _calculate_cpu_usage(self, stats: Dict[str, Any]) -> float:
        """Calculate CPU usage percentage"""
        try:
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                       stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                         stats["precpu_stats"]["system_cpu_usage"]
            
            if system_delta > 0.0 and cpu_delta > 0.0:
                return (cpu_delta / system_delta) * 100.0
            return 0.0
        except Exception:
            return 0.0
    
    def _calculate_memory_usage(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate memory usage"""
        try:
            return {
                "used": stats["memory_stats"]["usage"],
                "limit": stats["memory_stats"]["limit"],
                "percentage": (stats["memory_stats"]["usage"] / stats["memory_stats"]["limit"]) * 100
            }
        except Exception:
            return {"used": 0, "limit": 0, "percentage": 0}
    
    def _calculate_network_usage(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate network usage"""
        try:
            return {
                "rx_bytes": stats["networks"]["eth0"]["rx_bytes"],
                "tx_bytes": stats["networks"]["eth0"]["tx_bytes"]
            }
        except Exception:
            return {"rx_bytes": 0, "tx_bytes": 0} 