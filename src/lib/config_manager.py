#!/usr/bin/env python3

import os
import json
import logging
import uuid
from typing import Dict, Any, Optional, List
from pathlib import Path

class ConfigManager:
    def __init__(self, config_dir: str = "/etc/aethernode"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        self.safeguard_file = self.config_dir / "safeguard_patterns.json"
        self.logger = logging.getLogger(__name__)
        self.config: Dict[str, Any] = {}
        
        # Initialize default safeguard configuration
        self.default_safeguard_config = {
            "enabled": True,
            "detection": {
                "enabled": True,
                "log_requests": True,
                "auto_learn": True
            },
            "blocking": {
                "dns_blocking": True,
                "ip_blocking": True,
                "request_pattern_blocking": True,
                "hosts_file_blocking": True
            },
            "patterns": {
                "domains": [],
                "ips": [],
                "request_patterns": []
            }
        }
        
        self._init_config()
        
    def _init_config(self):
        """Initialize configuration files if they don't exist"""
        if not self.config_file.exists():
            self._save_config({})
        
        if not self.safeguard_file.exists():
            self._save_safeguard_config(self.default_safeguard_config)
        
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save main configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            os.chmod(self.config_file, 0o600)  # Secure file permissions
            self.logger.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
            raise
    
    def _save_safeguard_config(self, config: Dict[str, Any]) -> None:
        """Save safeguard configuration"""
        try:
            with open(self.safeguard_file, 'w') as f:
                json.dump(config, f, indent=4)
            os.chmod(self.safeguard_file, 0o600)  # Secure file permissions
            self.logger.info(f"Saved safeguard configuration to {self.safeguard_file}")
        except Exception as e:
            self.logger.error(f"Error saving safeguard config: {e}")
            raise
    
    def get_safeguard_config(self) -> Dict[str, Any]:
        """Get current safeguard configuration"""
        try:
            with open(self.safeguard_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Error loading safeguard config: {e}")
            return self.default_safeguard_config
    
    def update_safeguard_config(self,
                              enabled: bool = None,
                              detection_enabled: bool = None,
                              log_requests: bool = None,
                              auto_learn: bool = None,
                              dns_blocking: bool = None,
                              ip_blocking: bool = None,
                              request_pattern_blocking: bool = None,
                              hosts_file_blocking: bool = None):
        """Update safeguard configuration settings"""
        config = self.get_safeguard_config()
        
        if enabled is not None:
            config["enabled"] = enabled
        
        if detection_enabled is not None:
            config["detection"]["enabled"] = detection_enabled
        
        if log_requests is not None:
            config["detection"]["log_requests"] = log_requests
            
        if auto_learn is not None:
            config["detection"]["auto_learn"] = auto_learn
            
        if dns_blocking is not None:
            config["blocking"]["dns_blocking"] = dns_blocking
            
        if ip_blocking is not None:
            config["blocking"]["ip_blocking"] = ip_blocking
            
        if request_pattern_blocking is not None:
            config["blocking"]["request_pattern_blocking"] = request_pattern_blocking
            
        if hosts_file_blocking is not None:
            config["blocking"]["hosts_file_blocking"] = hosts_file_blocking
        
        self._save_safeguard_config(config)
        return config
    
    def add_safeguard_pattern(self, pattern_type: str, pattern: str):
        """Add a new safeguard pattern"""
        if pattern_type not in ["domains", "ips", "request_patterns"]:
            raise ValueError("Invalid pattern type")
            
        config = self.get_safeguard_config()
        if pattern not in config["patterns"][pattern_type]:
            config["patterns"][pattern_type].append(pattern)
            self._save_safeguard_config(config)
    
    def remove_safeguard_pattern(self, pattern_type: str, pattern: str):
        """Remove a safeguard pattern"""
        if pattern_type not in ["domains", "ips", "request_patterns"]:
            raise ValueError("Invalid pattern type")
            
        config = self.get_safeguard_config()
        if pattern in config["patterns"][pattern_type]:
            config["patterns"][pattern_type].remove(pattern)
            self._save_safeguard_config(config)
    
    def get_safeguard_patterns(self) -> Dict[str, List[str]]:
        """Get all safeguard patterns"""
        config = self.get_safeguard_config()
        return config["patterns"]
    
    def setup_earnapp(self, device_name: str, proxy_config: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Configure EarnApp settings with improved security"""
        earnapp_config = {
            "device": {
                "name": device_name,
                "uuid": f"sdk-node-{uuid.uuid4().hex}",
                "type": "residential"
            },
            "container": {
                "image": "earnapp/client:latest",
                "network_mode": "container:proxy" if proxy_config else "host",
                "capabilities": ["NET_ADMIN"],
                "security_opt": [
                    "no-new-privileges:true",
                    "seccomp=unconfined"
                ],
                "resources": {
                    "cpu_count": 1,
                    "cpu_shares": 512,
                    "memory_limit": "1G",
                    "memory_reservation": "512M"
                }
            },
            "network": {
                "proxy": proxy_config if proxy_config else None,
                "dns": ["1.1.1.1", "8.8.8.8"],
                "isolation": {
                    "enabled": True,
                    "namespace": f"earnapp_{device_name}"
                }
            },
            "security": {
                "user": "nobody:nogroup",
                "read_only": True,
                "drop_capabilities": [
                    "ALL"
                ],
                "add_capabilities": [
                    "NET_ADMIN",
                    "NET_RAW"
                ]
            },
            "performance": {
                "bandwidth_limit": "0",
                "traffic_limit": "0",
                "aggressive_mode": True,
                "tcp_optimization": {
                    "nodelay": True,
                    "quickack": True,
                    "keepalive": 60
                }
            }
        }
        
        # Save EarnApp config
        self._save_config("earnapp.json", earnapp_config)
        return earnapp_config
        
    def setup_proxy(self, proxy_url: str, proxy_type: str = "socks5") -> Dict[str, Any]:
        """Configure proxy settings with security measures"""
        proxy_config = {
            "url": proxy_url,
            "type": proxy_type,
            "security": {
                "isolation": True,
                "dns_leak_protection": True,
                "kill_switch": True
            },
            "network": {
                "mtu": 1500,
                "mark_id": self._generate_mark_id(),
                "routing_table": self._generate_routing_table()
            },
            "tunsocks": {
                "enabled": True,
                "device": "tun0",
                "mtu": 1500,
                "routes": ["0.0.0.0/0"]
            }
        }
        
        # Save proxy config
        self._save_config("proxy.json", proxy_config)
        return proxy_config
        
    def setup_network_security(self) -> Dict[str, Any]:
        """Configure network security rules"""
        security_config = {
            "iptables": {
                "input_policy": "DROP",
                "forward_policy": "DROP",
                "output_policy": "DROP",
                "allowed_ports": [80, 443],
                "allowed_protocols": ["tcp", "udp"],
                "nat": {
                    "enabled": True,
                    "masquerade": True
                }
            },
            "namespaces": {
                "enabled": True,
                "isolation": True
            },
            "seccomp": {
                "enabled": True,
                "default_policy": "SCMP_ACT_ERRNO",
                "allowed_syscalls": [
                    "accept",
                    "bind",
                    "connect",
                    "socket"
                ]
            }
        }
        
        # Save security config
        self._save_config("security.json", security_config)
        return security_config
        
    def _generate_mark_id(self) -> int:
        """Generate unique mark ID for packet marking"""
        return int.from_bytes(os.urandom(4), byteorder='big') % 50000
        
    def _generate_routing_table(self) -> int:
        """Generate unique routing table ID"""
        return int.from_bytes(os.urandom(4), byteorder='big') % 250 