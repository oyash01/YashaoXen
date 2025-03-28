#!/usr/bin/env python3

import logging
import random
import string
import json
import hashlib
import uuid
import time
import subprocess
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime, timezone, timedelta

class AntiDetectionSystem:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.current_profile = {}
        
    def apply(self):
        """Apply all anti-detection measures"""
        try:
            if self.config['os_spoofing']['enabled']:
                self._apply_os_spoofing()
                
            if self.config['browser_masking']['enabled']:
                self._apply_browser_masking()
                
            if self.config['hardware_signature']['mode'] == 'random':
                self._randomize_hardware_signature()
                
            self._apply_advanced_masking()
            self._setup_traffic_patterns()
            
            # Save current profile
            self._save_profile()
            
        except Exception as e:
            self.logger.error(f"Error applying anti-detection measures: {e}")
            raise
            
    def _apply_os_spoofing(self):
        """Apply advanced OS spoofing measures"""
        profile = random.choice(self.config['os_spoofing']['profiles'])
        
        os_configs = {
            'ubuntu_20_04': {
                'kernel': '5.4.0-42-generic',
                'arch': 'x86_64',
                'distro': 'Ubuntu 20.04.6 LTS',
                'hostname_prefix': ['ubuntu', 'desktop', 'laptop'],
                'timezone': 'UTC',
                'locale': 'en_US.UTF-8'
            },
            'ubuntu_22_04': {
                'kernel': '5.15.0-56-generic',
                'arch': 'x86_64',
                'distro': 'Ubuntu 22.04.3 LTS',
                'hostname_prefix': ['ubuntu', 'workstation', 'pc'],
                'timezone': 'UTC',
                'locale': 'en_US.UTF-8'
            },
            'debian_11': {
                'kernel': '5.10.0-20-amd64',
                'arch': 'x86_64',
                'distro': 'Debian GNU/Linux 11',
                'hostname_prefix': ['debian', 'server', 'node'],
                'timezone': 'UTC',
                'locale': 'en_US.UTF-8'
            }
        }
        
        os_config = os_configs[profile]
        
        # Generate unique machine identifiers
        machine_id = self._generate_machine_id()
        hostname = self._generate_hostname(os_config['hostname_prefix'])
        
        # Apply OS configurations
        self._write_system_file('/etc/machine-id', machine_id)
        self._write_system_file('/etc/hostname', hostname)
        self._write_system_file('/etc/hosts', f"127.0.0.1 localhost\n127.0.1.1 {hostname}")
        
        # Set kernel parameters
        self._set_kernel_params({
            'kernel.osrelease': os_config['kernel'],
            'kernel.version': f"#{random.randint(1, 100)}-Ubuntu SMP {self._generate_date()}",
            'kernel.hostname': hostname
        })
        
        self.current_profile['os'] = {
            'profile': profile,
            'config': os_config,
            'machine_id': machine_id,
            'hostname': hostname
        }
        
    def _apply_browser_masking(self):
        """Apply advanced browser fingerprint masking"""
        profile = random.choice(self.config['browser_masking']['profiles'])
        
        browser_configs = {
            'chrome': {
                'versions': ['109.0.5414.119', '110.0.5481.177', '111.0.5563.64'],
                'build_ids': ['950560', '952506', '954547'],
                'webgl_vendor': 'Google Inc. (NVIDIA)',
                'webgl_renderer': 'ANGLE (NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0)'
            },
            'firefox': {
                'versions': ['109.0', '110.0', '111.0'],
                'build_ids': ['20230201000000', '20230301000000', '20230401000000'],
                'webgl_vendor': 'NVIDIA Corporation',
                'webgl_renderer': 'GeForce GTX 1660 SUPER/PCIe/SSE2'
            },
            'safari': {
                'versions': ['16.3', '16.4', '16.5'],
                'build_ids': ['17614.4.6.1.6', '17615.3.12.11', '17616.1.5.31.10'],
                'webgl_vendor': 'Apple Inc.',
                'webgl_renderer': 'Apple M1'
            }
        }
        
        browser_config = browser_configs[profile]
        version = random.choice(browser_config['versions'])
        build_id = random.choice(browser_config['build_ids'])
        
        # Generate browser fingerprint
        fingerprint = {
            'navigator': {
                'userAgent': self._generate_user_agent(profile, version),
                'platform': self._get_platform_string(),
                'language': self._get_random_language(),
                'languages': self._generate_language_list(),
                'hardwareConcurrency': random.choice([4, 6, 8, 12]),
                'deviceMemory': random.choice([4, 8, 16]),
                'maxTouchPoints': 0
            },
            'screen': {
                'width': random.choice([1366, 1440, 1920, 2560]),
                'height': random.choice([768, 900, 1080, 1440]),
                'colorDepth': 24,
                'pixelDepth': 24
            },
            'webgl': {
                'vendor': browser_config['webgl_vendor'],
                'renderer': browser_config['webgl_renderer'],
                'unmaskedVendor': browser_config['webgl_vendor'],
                'unmaskedRenderer': browser_config['webgl_renderer']
            },
            'media': {
                'audioInputs': random.randint(1, 2),
                'audioOutputs': random.randint(1, 3),
                'videoInputs': random.randint(0, 1)
            },
            'plugins': self._generate_plugins_list(profile),
            'timezone': self._get_random_timezone(),
            'webrtc': {
                'publicIP': '',
                'localIP': '',
                'ipMasking': True
            }
        }
        
        # Save browser profile
        profile_path = Path('.browser_profile.json')
        profile_path.write_text(json.dumps(fingerprint, indent=2))
        
        self.current_profile['browser'] = {
            'profile': profile,
            'version': version,
            'build_id': build_id,
            'fingerprint': fingerprint
        }
        
    def _randomize_hardware_signature(self):
        """Generate randomized hardware signature"""
        components = self.config['hardware_signature']['components']
        
        hardware_profile = {
            'cpu': self._generate_cpu_info() if 'cpu' in components else None,
            'memory': self._generate_memory_info() if 'memory' in components else None,
            'disk': self._generate_disk_info() if 'disk' in components else None,
            'network': self._generate_network_info() if 'network' in components else None
        }
        
        # Save hardware profile
        profile_path = Path('.hardware_profile.json')
        profile_path.write_text(json.dumps(hardware_profile, indent=2))
        
        self.current_profile['hardware'] = hardware_profile
        
    def _apply_advanced_masking(self):
        """Apply advanced anti-detection features"""
        if self.config['advanced']['canvas_noise']:
            self._setup_canvas_noise()
            
        if self.config['advanced']['webgl_noise']:
            self._setup_webgl_noise()
            
        if self.config['advanced']['audio_noise']:
            self._setup_audio_noise()
            
        if self.config['advanced']['timezone_masking']:
            self._setup_timezone_masking()
            
    def _setup_traffic_patterns(self):
        """Configure traffic pattern simulation"""
        pattern = self.config['traffic_pattern']
        
        if pattern['mode'] == 'natural':
            self._setup_natural_traffic_pattern(
                variance=pattern['variance'],
                peak_hours=pattern['peak_hours']
            )
            
    def _generate_machine_id(self) -> str:
        """Generate unique machine ID"""
        # Use UUID v4 for randomness and hash it
        raw_id = str(uuid.uuid4())
        return hashlib.sha256(raw_id.encode()).hexdigest()[:32]
        
    def _generate_hostname(self, prefixes: List[str]) -> str:
        """Generate random hostname"""
        prefix = random.choice(prefixes)
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return f"{prefix}-{suffix}"
        
    def _generate_date(self) -> str:
        """Generate random date within last 30 days"""
        days = random.randint(1, 30)
        date = datetime.now(timezone.utc) - timedelta(days=days)
        return date.strftime("%a %b %d %H:%M:%S UTC %Y")
        
    def _write_system_file(self, path: str, content: str):
        """Write content to system file"""
        Path(path).write_text(content)
        
    def _set_kernel_params(self, params: Dict[str, str]):
        """Set kernel parameters"""
        for key, value in params.items():
            subprocess.run(['sysctl', '-w', f"{key}={value}"], check=True)
            
    def _generate_user_agent(self, browser: str, version: str) -> str:
        """Generate user agent string"""
        os_version = self.current_profile['os']['config']['distro']
        return f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
        
    def _get_platform_string(self) -> str:
        """Get platform string"""
        return "Linux x86_64"
        
    def _get_random_language(self) -> str:
        """Get random browser language"""
        return random.choice(['en-US', 'en-GB', 'fr-FR', 'de-DE', 'es-ES'])
        
    def _generate_language_list(self) -> List[str]:
        """Generate list of browser languages"""
        primary = self._get_random_language()
        return [primary, 'en-US', 'en']
        
    def _generate_plugins_list(self, browser: str) -> List[Dict[str, str]]:
        """Generate browser plugins list"""
        plugins = {
            'chrome': [
                {'name': 'Chrome PDF Plugin', 'filename': 'internal-pdf-viewer'},
                {'name': 'Chrome PDF Viewer', 'filename': 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                {'name': 'Native Client', 'filename': 'internal-nacl-plugin'}
            ],
            'firefox': [],  # Firefox doesn't expose plugins
            'safari': []    # Safari has its own plugin system
        }
        return plugins.get(browser, [])
        
    def _get_random_timezone(self) -> str:
        """Get random timezone"""
        return random.choice([
            'America/New_York',
            'Europe/London',
            'Asia/Tokyo',
            'Australia/Sydney',
            'Europe/Paris'
        ])
        
    def _generate_cpu_info(self) -> Dict[str, Any]:
        """Generate CPU information"""
        cpu_models = [
            'Intel(R) Core(TM) i5-10400F',
            'Intel(R) Core(TM) i7-11700K',
            'AMD Ryzen 5 5600X',
            'AMD Ryzen 7 5800X'
        ]
        
        return {
            'model': random.choice(cpu_models),
            'cores': random.choice([4, 6, 8, 12]),
            'threads': random.choice([8, 12, 16, 24]),
            'frequency': f"{random.uniform(3.0, 4.5):.1f}GHz",
            'cache': f"{random.choice([8, 16, 32])}MB"
        }
        
    def _generate_memory_info(self) -> Dict[str, Any]:
        """Generate memory information"""
        total_gb = random.choice([8, 16, 32, 64])
        return {
            'total': total_gb * 1024 * 1024 * 1024,
            'type': 'DDR4',
            'speed': f"{random.choice([2400, 2666, 3200, 3600])}MHz",
            'channels': random.choice([1, 2]),
            'timings': f"{random.randint(14, 16)}-{random.randint(16, 18)}-{random.randint(16, 18)}-{random.randint(32, 36)}"
        }
        
    def _generate_disk_info(self) -> Dict[str, Any]:
        """Generate disk information"""
        return {
            'model': random.choice([
                'Samsung SSD 970 EVO Plus',
                'WD Blue SN550 NVMe',
                'Crucial P5 NVMe',
                'Seagate BarraCuda'
            ]),
            'size': random.choice([256, 512, 1024, 2048]),
            'type': random.choice(['SSD', 'NVMe']),
            'interface': 'PCIe 3.0 x4'
        }
        
    def _generate_network_info(self) -> Dict[str, Any]:
        """Generate network interface information"""
        return {
            'interface': 'eth0',
            'mac': ':'.join(['%02x' % random.randint(0, 255) for _ in range(6)]),
            'speed': random.choice(['100Mbps', '1Gbps']),
            'duplex': 'full',
            'mtu': random.choice([1400, 1460, 1480, 1500])
        }
        
    def _setup_canvas_noise(self):
        """Setup canvas fingerprint noise"""
        noise_config = {
            'enabled': True,
            'mode': 'subtle',
            'variance': 0.1,
            'seed': random.randint(1, 1000000)
        }
        
        Path('.canvas_noise.json').write_text(json.dumps(noise_config))
        
    def _setup_webgl_noise(self):
        """Setup WebGL fingerprint noise"""
        noise_config = {
            'enabled': True,
            'vendor_randomization': True,
            'renderer_randomization': True,
            'parameter_randomization': True
        }
        
        Path('.webgl_noise.json').write_text(json.dumps(noise_config))
        
    def _setup_audio_noise(self):
        """Setup audio fingerprint noise"""
        noise_config = {
            'enabled': True,
            'sample_rate': random.choice([44100, 48000]),
            'channel_count': random.choice([1, 2]),
            'buffer_size': random.choice([256, 512, 1024])
        }
        
        Path('.audio_noise.json').write_text(json.dumps(noise_config))
        
    def _setup_timezone_masking(self):
        """Setup timezone masking"""
        tz_config = {
            'timezone': self._get_random_timezone(),
            'offset': random.choice([-480, -420, -360, -300, -240, 0, 60, 120, 180, 240]),
            'dst': random.choice([True, False])
        }
        
        Path('.timezone_config.json').write_text(json.dumps(tz_config))
        
    def _setup_natural_traffic_pattern(self, variance: float, peak_hours: List[str]):
        """Setup natural traffic pattern simulation"""
        pattern_config = {
            'base_delay': random.uniform(0.1, 0.5),
            'variance': variance,
            'peak_hours': peak_hours,
            'peak_multiplier': random.uniform(1.5, 2.5),
            'random_bursts': {
                'enabled': True,
                'probability': 0.1,
                'duration': random.uniform(10, 30)
            }
        }
        
        Path('.traffic_pattern.json').write_text(json.dumps(pattern_config))
        
    def _save_profile(self):
        """Save current anti-detection profile"""
        profile_path = Path('.current_profile.json')
        profile_path.write_text(json.dumps(self.current_profile, indent=2)) 