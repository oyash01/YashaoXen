#!/usr/bin/env python3

import logging
import subprocess
from typing import Dict, Any

class NetworkManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
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
            
            self.logger.info("TCP optimizations applied successfully")
            
        except Exception as e:
            self.logger.error(f"Error setting up TCP: {e}")
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
            
            self.logger.info("UDP optimizations applied successfully")
            
        except Exception as e:
            self.logger.error(f"Error setting up UDP: {e}")
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
            self.logger.warning(f"Unknown fingerprint: {self.config['tcp']['fingerprint']}")
            return
            
        try:
            self._run_command(f"iptables -t mangle -A POSTROUTING -j TTL --ttl-set {fp['ttl']}")
            self._run_command(f"sysctl -w net.ipv4.tcp_timestamps={fp['timestamps']}")
            self._run_command(f"ip route add local default dev lo table 100")
            self._run_command(f"ip rule add fwmark 1 lookup 100")
            
            self.logger.info(f"Applied TCP fingerprint: {self.config['tcp']['fingerprint']}")
            
        except Exception as e:
            self.logger.error(f"Error applying TCP fingerprint: {e}")
            raise
            
    def cleanup(self):
        """Cleanup network configurations"""
        try:
            # Remove custom iptables rules
            self._run_command("iptables -t mangle -F")
            # Remove custom routing rules
            self._run_command("ip rule del fwmark 1 lookup 100")
            self._run_command("ip route del local default dev lo table 100")
            
            self.logger.info("Network cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during network cleanup: {e}")
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
            self.logger.error(f"Command failed: {command}")
            self.logger.error(f"Error output: {e.stderr}")
            raise 