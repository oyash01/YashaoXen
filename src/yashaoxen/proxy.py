import re
import json
import logging
import requests
from typing import List, Optional
from urllib.parse import urlparse
from pathlib import Path

class ProxyManager:
    def __init__(self, proxy_file: str = "/etc/yashaoxen/proxies.txt"):
        self.logger = logging.getLogger("ProxyManager")
        self.proxy_file = Path(proxy_file)
        self.proxies: List[str] = []
        self.current_index = 0
        self._load_proxies()

    def _load_proxies(self):
        """Load proxies from file"""
        if not self.proxy_file.exists():
            self.logger.warning(f"Proxy file {self.proxy_file} not found")
            return

        with open(self.proxy_file) as f:
            self.proxies = [line.strip() for line in f if line.strip()]
        
        self.logger.info(f"Loaded {len(self.proxies)} proxies")

    def validate_proxy(self, proxy_url: str) -> bool:
        """Validate proxy URL format and connectivity"""
        try:
            # Validate URL format
            parsed = urlparse(proxy_url)
            if not all([parsed.scheme, parsed.hostname, parsed.port]):
                return False
            
            if parsed.scheme not in ['socks5', 'http', 'https']:
                return False

            # Test proxy connectivity
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            response = requests.get(
                'http://ip-api.com/json',
                proxies=proxies,
                timeout=10
            )
            
            if response.status_code != 200:
                return False

            # Verify we're getting response through proxy
            data = response.json()
            if not data.get('query'):  # Should return IP address
                return False

            return True

        except Exception as e:
            self.logger.error(f"Proxy validation failed for {proxy_url}: {e}")
            return False

    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy in rotation"""
        if not self.proxies:
            return None

        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy

    def add_proxy(self, proxy_url: str):
        """Add new proxy to the list"""
        if self.validate_proxy(proxy_url):
            if proxy_url not in self.proxies:
                self.proxies.append(proxy_url)
                self._save_proxies()
                self.logger.info(f"Added new proxy: {proxy_url}")
        else:
            raise ValueError(f"Invalid proxy: {proxy_url}")

    def remove_proxy(self, proxy_url: str):
        """Remove proxy from the list"""
        if proxy_url in self.proxies:
            self.proxies.remove(proxy_url)
            self._save_proxies()
            self.logger.info(f"Removed proxy: {proxy_url}")

    def _save_proxies(self):
        """Save proxies to file"""
        self.proxy_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.proxy_file, 'w') as f:
            f.write('\n'.join(self.proxies))

    def check_proxy_health(self, proxy_url: str) -> bool:
        """Check if proxy is healthy"""
        try:
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            response = requests.get(
                'http://ip-api.com/json',
                proxies=proxies,
                timeout=5
            )
            
            return response.status_code == 200

        except Exception as e:
            self.logger.error(f"Health check failed for proxy {proxy_url}: {e}")
            return False

    def get_proxy_info(self, proxy_url: str) -> dict:
        """Get information about proxy location and status"""
        try:
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            response = requests.get(
                'http://ip-api.com/json',
                proxies=proxies,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            
            return {}

        except Exception as e:
            self.logger.error(f"Failed to get proxy info for {proxy_url}: {e}")
            return {}

    def cleanup_dead_proxies(self):
        """Remove non-working proxies from the list"""
        working_proxies = []
        for proxy in self.proxies:
            if self.check_proxy_health(proxy):
                working_proxies.append(proxy)
            else:
                self.logger.warning(f"Removing dead proxy: {proxy}")
        
        self.proxies = working_proxies
        self._save_proxies()

    def get_proxy_stats(self) -> dict:
        """Get statistics about proxies"""
        total = len(self.proxies)
        working = sum(1 for p in self.proxies if self.check_proxy_health(p))
        
        return {
            "total": total,
            "working": working,
            "dead": total - working,
            "health_percentage": (working / total * 100) if total > 0 else 0
        } 