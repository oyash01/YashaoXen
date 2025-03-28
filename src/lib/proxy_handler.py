#!/usr/bin/env python3

import logging
import random
import socket
import json
import subprocess
from typing import Dict, Any
from pathlib import Path

class ProxyHandler:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.active_tunnels = {}
        
    def setup_proxy(self, instance_id: str, proxy_config: Dict[str, str]) -> bool:
        """Setup TunSocks proxy tunnel for an instance"""
        try:
            # Generate unique TUN interface name
            tun_name = f"tun{instance_id[-4:]}"
            
            # Create TUN device
            self._create_tun_device(tun_name)
            
            # Configure routing
            self._setup_routing(tun_name)
            
            # Start TunSocks process
            process = self._start_tunsocks(tun_name, proxy_config)
            
            self.active_tunnels[instance_id] = {
                "tun_name": tun_name,
                "process": process,
                "proxy": proxy_config
            }
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up TunSocks: {e}")
            return False
            
    def _create_tun_device(self, tun_name: str):
        """Create and configure TUN device"""
        commands = [
            f"ip tuntap add dev {tun_name} mode tun user root",
            f"ip link set dev {tun_name} up",
            f"ip addr add 10.{random.randint(0,255)}.{random.randint(0,255)}.1/24 dev {tun_name}"
        ]
        
        for cmd in commands:
            subprocess.run(cmd.split(), check=True)
            
    def _setup_routing(self, tun_name: str):
        """Configure routing for TunSocks"""
        table_id = random.randint(100, 200)
        
        commands = [
            # Create routing table
            f"echo '{table_id} {tun_name}' >> /etc/iproute2/rt_tables",
            
            # Add routes
            f"ip route add default dev {tun_name} table {table_id}",
            
            # Add policy routing
            f"ip rule add fwmark {table_id} table {table_id}",
            
            # Configure iptables for marking packets
            f"iptables -t mangle -A OUTPUT -m owner --uid-owner tunsocks -j MARK --set-mark {table_id}"
        ]
        
        for cmd in commands:
            subprocess.run(cmd.split(), check=True)
            
    def _start_tunsocks(self, tun_name: str, proxy_config: Dict[str, str]) -> subprocess.Popen:
        """Start TunSocks process"""
        config = {
            "interface": {
                "name": tun_name,
                "mtu": self.config["network"]["mtu"],
                "ipv4": f"10.{random.randint(0,255)}.{random.randint(0,255)}.1",
                "netmask": "255.255.255.0"
            },
            "proxy": {
                "type": "socks5",
                "host": proxy_config["host"],
                "port": int(proxy_config["port"]),
                "username": proxy_config.get("username"),
                "password": proxy_config.get("password")
            },
            "dns": {
                "servers": self.config["proxy"]["dns_servers"],
                "timeout": 5
            },
            "routes": {
                "bypass": [
                    "127.0.0.0/8",
                    "169.254.0.0/16",
                    "172.16.0.0/12",
                    "192.168.0.0/16"
                ]
            },
            "advanced": {
                "tcp_keepalive": true,
                "tcp_keepalive_interval": 30,
                "udp_timeout": 60,
                "mss_fix": true
            }
        }
        
        config_path = Path(f"/tmp/tunsocks_{tun_name}.json")
        config_path.write_text(json.dumps(config))
        
        return subprocess.Popen([
            "tunsocks",
            "--config", str(config_path),
            "--daemon",
            "--user", "tunsocks",
            "--group", "tunsocks",
            "--pidfile", f"/var/run/tunsocks_{tun_name}.pid"
        ])
        
    def cleanup_tunnel(self, instance_id: str):
        """Clean up TunSocks tunnel"""
        if instance_id not in self.active_tunnels:
            return
            
        tunnel = self.active_tunnels[instance_id]
        
        try:
            # Stop TunSocks process
            tunnel["process"].terminate()
            tunnel["process"].wait(timeout=5)
            
            # Remove TUN device
            subprocess.run(["ip", "tuntap", "del", "dev", tunnel["tun_name"], "mode", "tun"])
            
            # Clean up routing
            table_id = int(tunnel["tun_name"][3:])
            subprocess.run(["ip", "rule", "del", "fwmark", str(table_id)])
            
            # Remove iptables rules
            subprocess.run([
                "iptables", "-t", "mangle", "-D", "OUTPUT",
                "-m", "owner", "--uid-owner", "tunsocks",
                "-j", "MARK", "--set-mark", str(table_id)
            ])
            
            # Clean up config
            config_path = Path(f"/tmp/tunsocks_{tunnel['tun_name']}.json")
            if config_path.exists():
                config_path.unlink()
                
            del self.active_tunnels[instance_id]
            
        except Exception as e:
            self.logger.error(f"Error cleaning up tunnel: {e}")
            
    def get_tunnel_info(self, instance_id: str) -> Dict[str, Any]:
        """Get tunnel information"""
        return self.active_tunnels.get(instance_id, {}) 