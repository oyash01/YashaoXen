import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Tuple
import logging

class Installer:
    def __init__(self):
        self.logger = self._setup_logging()
        self.os_type = platform.system().lower()
        self.is_root = os.geteuid() == 0

    def _setup_logging(self) -> logging.Logger:
        """Configure logging for installer."""
        logger = logging.getLogger("yashaoxen-installer")
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        
        logger.addHandler(ch)
        return logger

    def check_prerequisites(self) -> Tuple[bool, List[str]]:
        """Check if all prerequisites are met."""
        errors = []
        
        # Check root privileges
        if not self.is_root:
            errors.append("Root privileges required. Please run with sudo.")
        
        # Check Python version
        if sys.version_info < (3, 8):
            errors.append("Python 3.8 or higher required.")
        
        # Check system resources
        cpu_count = os.cpu_count() or 0
        if cpu_count < 2:
            errors.append(f"At least 2 CPU cores required. Found: {cpu_count}")
        
        try:
            import psutil
            mem_gb = psutil.virtual_memory().total / (1024 * 1024 * 1024)
            if mem_gb < 2:
                errors.append(f"At least 2GB RAM required. Found: {mem_gb:.1f}GB")
        except ImportError:
            errors.append("Could not check memory. Please install psutil.")
        
        return len(errors) == 0, errors

    def create_directories(self) -> bool:
        """Create necessary directories."""
        try:
            directories = [
                "/etc/yashaoxen",
                "/var/log/yashaoxen",
                "/opt/yashaoxen",
                "/etc/yashaoxen/security",
                "/etc/docker/seccomp-profiles"
            ]
            
            for directory in directories:
                Path(directory).mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created directory: {directory}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create directories: {str(e)}")
            return False

    def install_dependencies(self) -> bool:
        """Install system dependencies based on OS."""
        try:
            if self.os_type == "linux":
                if os.path.exists("/etc/debian_version"):
                    return self._install_debian_dependencies()
                elif os.path.exists("/etc/redhat-release"):
                    return self._install_redhat_dependencies()
                else:
                    self.logger.error("Unsupported Linux distribution")
                    return False
            else:
                self.logger.error(f"Unsupported operating system: {self.os_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to install dependencies: {str(e)}")
            return False

    def _install_debian_dependencies(self) -> bool:
        """Install dependencies for Debian-based systems."""
        try:
            commands = [
                "apt-get update",
                "DEBIAN_FRONTEND=noninteractive apt-get install -y python3.8 python3-pip python3-venv docker.io docker-compose iptables net-tools curl wget"
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd.split(), check=True)
                if result.returncode != 0:
                    return False
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install Debian dependencies: {str(e)}")
            return False

    def _install_redhat_dependencies(self) -> bool:
        """Install dependencies for RedHat-based systems."""
        try:
            commands = [
                "yum -y update",
                "yum -y install python38 python38-pip docker docker-compose iptables net-tools curl wget"
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd.split(), check=True)
                if result.returncode != 0:
                    return False
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install RedHat dependencies: {str(e)}")
            return False

    def setup_python_environment(self) -> bool:
        """Set up Python virtual environment and install requirements."""
        try:
            venv_path = Path("/opt/yashaoxen/venv")
            
            # Create virtual environment
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
            
            # Activate virtual environment and install requirements
            pip_path = venv_path / "bin" / "pip"
            subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
            subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
            
            # Create activation script
            with open("/etc/profile.d/yashaoxen.sh", "w") as f:
                f.write("""#!/bin/bash
export YASHAOXEN_HOME=/opt/yashaoxen
export PATH=$YASHAOXEN_HOME/venv/bin:$PATH
""")
            
            os.chmod("/etc/profile.d/yashaoxen.sh", 0o755)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup Python environment: {str(e)}")
            return False

    def configure_docker(self) -> bool:
        """Configure Docker service and permissions."""
        try:
            commands = [
                "systemctl start docker",
                "systemctl enable docker",
                f"usermod -aG docker {os.environ.get('SUDO_USER', 'root')}"
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd.split(), check=True)
                if result.returncode != 0:
                    return False
            
            # Test Docker
            test_result = subprocess.run(
                ["docker", "run", "--rm", "hello-world"],
                capture_output=True
            )
            
            return test_result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Failed to configure Docker: {str(e)}")
            return False

    def configure_network(self) -> bool:
        """Configure network settings and iptables."""
        try:
            # Configure sysctl
            sysctl_config = """
# Network settings
net.ipv4.ip_forward = 1
net.ipv4.conf.all.forwarding = 1
net.ipv4.conf.all.route_localnet = 1
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.rp_filter = 1

# TCP optimizations
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_max_tw_buckets = 720000
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_keepalive_time = 1800
net.ipv4.tcp_keepalive_probes = 3
net.ipv4.tcp_keepalive_intvl = 15
net.ipv4.tcp_max_orphans = 32768
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 2

# Core settings
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216

# TCP memory settings
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.udp_rmem_min = 16384
net.ipv4.udp_wmem_min = 16384

# TCP performance
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_slow_start_after_idle = 0
"""
            with open("/etc/sysctl.d/99-yashaoxen.conf", "w") as f:
                f.write(sysctl_config)
            
            # Apply sysctl settings
            subprocess.run(["sysctl", "-p", "/etc/sysctl.d/99-yashaoxen.conf"], check=True)
            
            # Configure iptables
            iptables_rules = """*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
:YASHAOXEN - [0:0]

# Allow established connections
-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH
-A INPUT -p tcp --dport 22 -j ACCEPT

# Allow Docker
-A INPUT -i docker0 -j ACCEPT

# Custom chain for YashaoXen
-A INPUT -j YASHAOXEN
-A FORWARD -j YASHAOXEN

COMMIT

*nat
:PREROUTING ACCEPT [0:0]
:INPUT ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]

# Enable NAT for Docker
-A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE

COMMIT
"""
            with open("/etc/iptables/rules.v4", "w") as f:
                f.write(iptables_rules)
            
            # Apply iptables rules
            subprocess.run(["iptables-restore", "/etc/iptables/rules.v4"], check=True)
            
            # Make iptables rules persistent
            if os.path.exists("/etc/debian_version"):
                subprocess.run(["apt-get", "install", "-y", "iptables-persistent"], check=True)
            else:
                subprocess.run(["service", "iptables", "save"], check=True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure network: {str(e)}")
            return False

    def run_installation(self) -> bool:
        """Run the complete installation process."""
        self.logger.info("Starting YashaoXen installation...")
        
        # Check prerequisites
        success, errors = self.check_prerequisites()
        if not success:
            for error in errors:
                self.logger.error(error)
            return False
        
        steps = [
            (self.create_directories, "Creating directories"),
            (self.install_dependencies, "Installing dependencies"),
            (self.configure_docker, "Configuring Docker"),
            (self.configure_network, "Configuring network"),
            (self.setup_python_environment, "Setting up Python environment")
        ]
        
        for step_func, step_name in steps:
            self.logger.info(f"Step: {step_name}")
            if not step_func():
                self.logger.error(f"Failed at step: {step_name}")
                return False
        
        self.logger.info("Installation completed successfully!")
        self.logger.info("Please log out and log back in for changes to take effect.")
        self.logger.info("Then run: source /opt/yashaoxen/venv/bin/activate")
        self.logger.info("And: yashaoxen init")
        
        return True

def main():
    """Main entry point for installation."""
    installer = Installer()
    success = installer.run_installation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 