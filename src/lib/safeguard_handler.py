#!/usr/bin/env python3

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class SafeguardHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()
        self.session = self._setup_session()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load safeguard configuration"""
        try:
            config_path = Path("/etc/aethernode/safeguard.json")
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load safeguard config: {e}")
            return {
                "request_patterns": [],
                "headers": {},
                "rotation_interval": 3600,
                "max_retries": 3,
                "retry_delay": 5
            }
            
    def _setup_session(self) -> requests.Session:
        """Set up requests session with retry strategy"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config['max_retries'],
            backoff_factor=self.config['retry_delay'],
            status_forcelist=[429, 500, 502, 503, 504]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update(self.config['headers'])
        
        return session
        
    def handle_request(self, url: str, method: str = 'GET', 
                      data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle incoming request and return appropriate response"""
        try:
            # Check if URL matches any safeguard patterns
            for pattern in self.config['request_patterns']:
                if re.match(pattern['url_pattern'], url):
                    self.logger.info(f"Blocked safeguard request to: {url}")
                    return pattern['response']
                    
            # If no pattern matches, proxy the request
            response = self._proxy_request(url, method, data)
            return response
            
        except Exception as e:
            self.logger.error(f"Error handling request: {e}")
            return {
                'status': 500,
                'body': {'error': 'Internal server error'}
            }
            
    def _proxy_request(self, url: str, method: str,
                      data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Proxy request to actual endpoint with modifications"""
        try:
            # Modify request headers
            headers = self.session.headers.copy()
            headers['X-Forwarded-For'] = self._generate_ip()
            
            # Make request
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=10
            )
            
            return {
                'status': response.status_code,
                'body': response.json() if response.content else {}
            }
            
        except Exception as e:
            self.logger.error(f"Error proxying request: {e}")
            return {
                'status': 502,
                'body': {'error': 'Bad gateway'}
            }
            
    def _generate_ip(self) -> str:
        """Generate a random IP address"""
        import random
        return f"{random.randint(1,255)}.{random.randint(0,255)}." \
               f"{random.randint(0,255)}.{random.randint(1,255)}"
               
    def intercept_dns(self, hostname: str) -> Optional[str]:
        """Intercept DNS requests for safeguard domains"""
        blocked_domains = [
            'safeguard.earnapp.com',
            'verify.earnapp.com',
            'check.earnapp.com'
        ]
        
        if any(domain in hostname.lower() for domain in blocked_domains):
            self.logger.info(f"Blocked DNS request for: {hostname}")
            return '127.0.0.1'
            
        return None
        
    def setup_iptables_rules(self):
        """Set up iptables rules to block safeguard requests"""
        try:
            import iptc
            
            # Create chain for safeguard rules
            chain = iptc.Chain(iptc.Table(iptc.Table.FILTER), "SAFEGUARD")
            if chain not in iptc.Table(iptc.Table.FILTER).chains:
                iptc.Table(iptc.Table.FILTER).create_chain("SAFEGUARD")
                
            # Clear existing rules
            chain.flush()
            
            # Add rules to block safeguard domains
            blocked_ips = [
                '34.102.136.180',  # Example safeguard IP
                '35.186.224.25',   # Example verification IP
            ]
            
            for ip in blocked_ips:
                rule = iptc.Rule()
                rule.target = iptc.Target(rule, "DROP")
                rule.src = ip
                chain.insert_rule(rule)
                
            self.logger.info("Iptables rules configured for safeguard blocking")
            
        except Exception as e:
            self.logger.error(f"Failed to configure iptables: {e}")
            
    def modify_hosts_file(self):
        """Modify hosts file to block safeguard domains"""
        try:
            hosts_entries = [
                "127.0.0.1 safeguard.earnapp.com",
                "127.0.0.1 verify.earnapp.com",
                "127.0.0.1 check.earnapp.com"
            ]
            
            with open('/etc/hosts', 'a') as f:
                f.write("\n# AetherNode safeguard blocking\n")
                f.write("\n".join(hosts_entries) + "\n")
                
            self.logger.info("Hosts file updated for safeguard blocking")
            
        except Exception as e:
            self.logger.error(f"Failed to modify hosts file: {e}")
            
    def setup_blocking(self):
        """Set up all safeguard blocking mechanisms"""
        self.setup_iptables_rules()
        self.modify_hosts_file()
        self.logger.info("Safeguard blocking mechanisms configured") 