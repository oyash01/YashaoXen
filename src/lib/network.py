#!/usr/bin/env python3

import os
import json
import logging
import random
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

class NetworkManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.proxy_file = config.get("proxy_file")
        self.dns_file = config.get("dns_file")
        self.proxies = self._load_proxies()
        self.dns_servers = self._load_dns()
        self.current_proxy_index = 0
        self.current_dns_index = 0
    
    def get_next_proxy(self) -> Dict[str, str]:
        """Get next proxy from the list"""
        if not self.proxies:
            raise ValueError("No proxies available")
            
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        
        return {
            "http": f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}",
            "https": f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
        }
    
    def get_next_dns(self) -> List[str]:
        """Get next DNS server from the list"""
        if not self.dns_servers:
            raise ValueError("No DNS servers available")
            
        dns = self.dns_servers[self.current_dns_index]
        self.current_dns_index = (self.current_dns_index + 1) % len(self.dns_servers)
        
        return [dns]
    
    def _load_proxies(self) -> List[Dict[str, str]]:
        """Load proxies from file"""
        if not self.proxy_file or not os.path.exists(self.proxy_file):
            logger.warning("No proxy file specified or file does not exist")
            return []
            
        try:
            with open(self.proxy_file, 'r') as f:
                proxies = []
                for line in f:
                    # Expected format: host:port:username:password
                    host, port, username, password = line.strip().split(':')
                    proxies.append({
                        "host": host,
                        "port": port,
                        "username": username,
                        "password": password
                    })
                return proxies
        except Exception as e:
            logger.error(f"Error loading proxies: {e}")
            return []
    
    def _load_dns(self) -> List[str]:
        """Load DNS servers from file"""
        if not self.dns_file or not os.path.exists(self.dns_file):
            logger.warning("No DNS file specified or file does not exist")
            return []
            
        try:
            with open(self.dns_file, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"Error loading DNS servers: {e}")
            return []
    
    def validate_proxy(self, proxy: Dict[str, str]) -> bool:
        """Validate proxy connection"""
        try:
            import requests
            response = requests.get(
                "https://earnapp.com",
                proxies=proxy,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Proxy validation failed: {e}")
            return False
    
    def validate_dns(self, dns: str) -> bool:
        """Validate DNS server"""
        try:
            import socket
            socket.setdefaulttimeout(5)
            socket.gethostbyname("earnapp.com")
            return True
        except Exception as e:
            logger.warning(f"DNS validation failed: {e}")
            return False
    
    def setup_network_isolation(self, container_id: str) -> None:
        """Set up network isolation for container"""
        try:
            # Create network namespace
            os.system(f"ip netns add netns_{container_id}")
            
            # Create virtual interface
            os.system(f"ip link add veth_{container_id} type veth peer name veth_{container_id}_ns")
            
            # Move interface to namespace
            os.system(f"ip link set veth_{container_id}_ns netns netns_{container_id}")
            
            # Configure interfaces
            os.system(f"ip addr add 10.0.0.1/24 dev veth_{container_id}")
            os.system(f"ip link set veth_{container_id} up")
            
            os.system(f"ip netns exec netns_{container_id} ip addr add 10.0.0.2/24 dev veth_{container_id}_ns")
            os.system(f"ip netns exec netns_{container_id} ip link set veth_{container_id}_ns up")
            
            # Set default route
            os.system(f"ip netns exec netns_{container_id} ip route add default via 10.0.0.1")
            
            logger.info(f"Set up network isolation for container {container_id}")
            
        except Exception as e:
            logger.error(f"Error setting up network isolation: {e}")
            raise
    
    def cleanup_network_isolation(self, container_id: str) -> None:
        """Clean up network isolation for container"""
        try:
            # Remove virtual interface
            os.system(f"ip link delete veth_{container_id}")
            
            # Remove network namespace
            os.system(f"ip netns delete netns_{container_id}")
            
            logger.info(f"Cleaned up network isolation for container {container_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up network isolation: {e}")
            # Don't raise the exception as this is cleanup code
            
    def setup(self):
        """Setup network optimizations"""
        if self.config['tcp']['enabled']:
            self._setup_tcp()
        if self.config['udp']['enabled']:
            self._setup_udp()
            
    def _setup_tcp(self):
        """Configure TCP optimizations"""
        try:
            # Enable BBR congestion control
            if self.config['tcp']['bbr']:
                self._run_command("sysctl -w net.ipv4.tcp_congestion_control=bbr")
                self._run_command("sysctl -w net.core.default_qdisc=fq")
                
            # Configure TCP window size
            window_size = self.config['tcp']['window_size']
            self._run_command(f"sysctl -w net.core.rmem_max={window_size}")
            self._run_command(f"sysctl -w net.core.wmem_max={window_size}")
            self._run_command(f"sysctl -w net.ipv4.tcp_rmem='4096 87380 {window_size}'")
            self._run_command(f"sysctl -w net.ipv4.tcp_wmem='4096 87380 {window_size}'")
            
            # Enable TCP Fast Open if configured
            if self.config['tcp']['fastopen']:
                self._run_command("sysctl -w net.ipv4.tcp_fastopen=3")
                
            # Apply OS fingerprint
            self._apply_tcp_fingerprint()
            
            logger.info("TCP optimizations applied successfully")
            
        except Exception as e:
            logger.error(f"Error setting up TCP: {e}")
            raise
            
    def _setup_udp(self):
        """Configure UDP optimizations"""
        try:
            # Set UDP buffer size
            buffer_size = self.config['udp']['buffer_size']
            self._run_command(f"sysctl -w net.core.rmem_max={buffer_size}")
            self._run_command(f"sysctl -w net.core.wmem_max={buffer_size}")
            
            # Set MTU
            mtu = self.config['udp']['mtu']
            self._run_command(f"ip link set dev eth0 mtu {mtu}")
            
            logger.info("UDP optimizations applied successfully")
            
        except Exception as e:
            logger.error(f"Error setting up UDP: {e}")
            raise
            
    def _apply_tcp_fingerprint(self):
        """Apply TCP/IP fingerprint for the specified OS"""
        fingerprints = {
            'ubuntu_20_04': {
                'ttl': 64,
                'window_size': 29200,
                'mss': 1460,
                'timestamps': 1
            },
            'windows_10': {
                'ttl': 128,
                'window_size': 64240,
                'mss': 1460,
                'timestamps': 0
            }
        }
        
        fp = fingerprints.get(self.config['tcp']['fingerprint'])
        if not fp:
            logger.warning(f"Unknown fingerprint: {self.config['tcp']['fingerprint']}")
            return
            
        try:
            self._run_command(f"iptables -t mangle -A POSTROUTING -j TTL --ttl-set {fp['ttl']}")
            self._run_command(f"sysctl -w net.ipv4.tcp_timestamps={fp['timestamps']}")
            self._run_command(f"ip route add local default dev lo table 100")
            self._run_command(f"ip rule add fwmark 1 lookup 100")
            
            logger.info(f"Applied TCP fingerprint: {self.config['tcp']['fingerprint']}")
            
        except Exception as e:
            logger.error(f"Error applying TCP fingerprint: {e}")
            raise
            
    def cleanup(self):
        """Cleanup network configurations"""
        try:
            # Remove custom iptables rules
            self._run_command("iptables -t mangle -F")
            # Remove custom routing rules
            self._run_command("ip rule del fwmark 1 lookup 100")
            self._run_command("ip route del local default dev lo table 100")
            
            logger.info("Network cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during network cleanup: {e}")
            raise
            
    def _run_command(self, command: str) -> str:
        """Execute shell command and return output"""
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {command}")
            logger.error(f"Error output: {e.stderr}")
            raise 