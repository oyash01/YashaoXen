#!/usr/bin/env python3

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    def __init__(self):
        self.config_dir = Path(os.getenv('AETHER_CONFIG_DIR', '/etc/aethernode'))
        self.config_file = self.config_dir / 'config.json'
        self.logger = logging.getLogger(__name__)
        
        # Default configuration
        self.default_config = {
            'earnapp': {
                'device_name': '',
                'max_instances': 1,
                'auto_restart': True
            },
            'container': {
                'resources': {
                    'memory_limit': '1G',
                    'cpu_shares': 512
                },
                'security': {
                    'enable_seccomp': True,
                    'enable_apparmor': True,
                    'enable_network_isolation': True
                }
            },
            'performance': {
                'aggressive_mode': False,
                'tcp_optimization': {
                    'nodelay': True,
                    'quickack': True,
                    'keepalive': 60
                }
            },
            'safeguard': {
                'enabled': True,
                'detection': {
                    'enabled': True,
                    'log_requests': True,
                    'auto_learn': True
                },
                'blocking': {
                    'dns_blocking': True,
                    'ip_blocking': True,
                    'request_pattern_blocking': True,
                    'hosts_file_blocking': True
                },
                'patterns': {
                    'domains': [],
                    'ips': [],
                    'request_patterns': []
                }
            }
        }
        
        self._init_config()
    
    def _init_config(self):
        """Initialize configuration directory and file"""
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Create default config if it doesn't exist
            if not self.config_file.exists():
                self.reset_to_defaults()
                
        except Exception as e:
            self.logger.error(f"Error initializing config: {e}")
            raise
    
    def get_config_path(self) -> str:
        """Get path to configuration file"""
        return str(self.config_file)
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        try:
            # Merge with defaults to ensure all required fields exist
            merged_config = self.default_config.copy()
            merged_config.update(config)
            
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Save configuration
            with open(self.config_file, 'w') as f:
                json.dump(merged_config, f, indent=4)
            
            # Set secure permissions
            os.chmod(self.config_file, 0o600)
            
            self.logger.info("Configuration saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
            raise
    
    def reset_to_defaults(self):
        """Reset configuration to default values"""
        try:
            self.save_config(self.default_config)
            self.logger.info("Configuration reset to defaults")
        except Exception as e:
            self.logger.error(f"Error resetting config: {e}")
            raise
    
    def update_config(self, updates: Dict[str, Any]):
        """Update specific configuration values"""
        try:
            current_config = self.get_config()
            
            def deep_update(d: dict, u: dict) -> dict:
                for k, v in u.items():
                    if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                        d[k] = deep_update(d[k], v)
                    else:
                        d[k] = v
                return d
            
            updated_config = deep_update(current_config, updates)
            self.save_config(updated_config)
            
        except Exception as e:
            self.logger.error(f"Error updating config: {e}")
            raise
    
    def validate_config(self) -> list:
        """Validate configuration and return list of errors"""
        errors = []
        config = self.get_config()
        
        # Check required sections
        required_sections = ['earnapp', 'container', 'performance']
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: {section}")
        
        # Validate EarnApp settings
        if 'earnapp' in config:
            earnapp = config['earnapp']
            if not earnapp.get('device_name'):
                errors.append("Missing device name")
            if not isinstance(earnapp.get('max_instances'), int):
                errors.append("max_instances must be an integer")
        
        # Validate container resources
        if 'container' in config:
            container = config['container']
            if 'resources' not in container:
                errors.append("Missing container resources configuration")
            else:
                resources = container['resources']
                if 'memory_limit' not in resources:
                    errors.append("Missing memory limit")
                elif resources['memory_limit'] not in ['1G', '2G']:
                    errors.append("Invalid memory limit (must be '1G' or '2G')")
        
        return errors
    
    def get_instance_config(self, instance_id: str) -> Dict[str, Any]:
        """Get configuration for specific instance"""
        try:
            instance_file = self.config_dir / f"instance-{instance_id}.json"
            if instance_file.exists():
                with open(instance_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Error loading instance config: {e}")
            return {}
    
    def save_instance_config(self, instance_id: str, config: Dict[str, Any]):
        """Save configuration for specific instance"""
        try:
            instance_file = self.config_dir / f"instance-{instance_id}.json"
            with open(instance_file, 'w') as f:
                json.dump(config, f, indent=4)
            os.chmod(instance_file, 0o600)
        except Exception as e:
            self.logger.error(f"Error saving instance config: {e}")
            raise

    def setup_earnapp(self, device_name: str, proxy_url: Optional[str] = None) -> None:
        """Set up EarnApp configuration"""
        try:
            # Configure EarnApp settings
            self.config['earnapp'] = {
                'device_name': device_name,
                'uuid': os.environ.get('EARNAPP_UUID', ''),
                'max_instances': 10,
                'auto_restart': True
            }
            
            # Configure proxy settings if provided
            if proxy_url:
                proxy_parts = proxy_url.split('://')
                if len(proxy_parts) != 2:
                    raise ValueError("Invalid proxy URL format")
                    
                proxy_type = proxy_parts[0]
                proxy_auth = proxy_parts[1].split('@')
                
                if len(proxy_auth) == 2:
                    auth, address = proxy_auth
                    user, password = auth.split(':')
                    host, port = address.split(':')
                else:
                    host, port = proxy_auth[0].split(':')
                    user = password = None
                    
                self.config['proxy'] = {
                    'type': proxy_type,
                    'host': host,
                    'port': int(port),
                    'username': user,
                    'password': password
                }
                
            # Configure container settings
            self.config['container'] = {
                'resources': {
                    'memory_limit': '1G',
                    'cpu_shares': 1024
                },
                'security': {
                    'enable_seccomp': True,
                    'enable_apparmor': True,
                    'enable_network_isolation': True
                }
            }
            
            self._save_config()
            self.logger.info("EarnApp configuration updated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to set up EarnApp configuration: {e}")
            raise
            
    def update_proxy(self, proxy_url: str) -> None:
        """Update proxy configuration"""
        try:
            proxy_parts = proxy_url.split('://')
            if len(proxy_parts) != 2:
                raise ValueError("Invalid proxy URL format")
                
            proxy_type = proxy_parts[0]
            proxy_auth = proxy_parts[1].split('@')
            
            if len(proxy_auth) == 2:
                auth, address = proxy_auth
                user, password = auth.split(':')
                host, port = address.split(':')
            else:
                host, port = proxy_auth[0].split(':')
                user = password = None
                
            self.config['proxy'] = {
                'type': proxy_type,
                'host': host,
                'port': int(port),
                'username': user,
                'password': password
            }
            
            self._save_config()
            self.logger.info("Proxy configuration updated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to update proxy configuration: {e}")
            raise
            
    def configure_performance(self, memory_limit: str = None, cpu_shares: int = None,
                            aggressive_mode: bool = False) -> None:
        """Configure performance settings"""
        try:
            if memory_limit:
                self.config['container']['resources']['memory_limit'] = memory_limit
                
            if cpu_shares is not None:
                self.config['container']['resources']['cpu_shares'] = cpu_shares
                
            if aggressive_mode:
                self.config['container']['resources']['memory_swappiness'] = 0
                self.config['container']['resources']['cpu_rt_runtime_us'] = 950000
                
            self._save_config()
            self.logger.info("Performance settings updated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to update performance settings: {e}")
            raise
            
    def configure_security(self, enable_seccomp: bool = None,
                         enable_apparmor: bool = None,
                         enable_network_isolation: bool = None) -> None:
        """Configure security settings"""
        try:
            security = self.config['container']['security']
            
            if enable_seccomp is not None:
                security['enable_seccomp'] = enable_seccomp
                
            if enable_apparmor is not None:
                security['enable_apparmor'] = enable_apparmor
                
            if enable_network_isolation is not None:
                security['enable_network_isolation'] = enable_network_isolation
                
            self._save_config()
            self.logger.info("Security settings updated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to update security settings: {e}")
            raise
        
    def _save_config(self) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save config file: {e}")
            raise 