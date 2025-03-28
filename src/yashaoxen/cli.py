import os
import sys
import json
import time
import click
import logging
from pathlib import Path
from typing import Dict, List, Optional
from .core import YashCore
from .proxy import ProxyManager
from .install import Installer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("YashaoXen")

CONFIG_DIR = "/etc/yashaoxen"

def load_config() -> Dict:
    """Load main configuration file."""
    config_file = os.path.join(CONFIG_DIR, "config.json")
    try:
        with open(config_file) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {str(e)}")
        sys.exit(1)

def load_features() -> Dict:
    """Load feature toggles."""
    feature_file = os.path.join(CONFIG_DIR, "features.json")
    try:
        with open(feature_file) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load features: {str(e)}")
        sys.exit(1)

def load_proxies() -> List[str]:
    """Load proxy list."""
    proxy_file = os.path.join(CONFIG_DIR, "proxies.txt")
    try:
        with open(proxy_file) as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Failed to load proxies: {str(e)}")
        sys.exit(1)

def load_dns() -> Dict[str, str]:
    """Load DNS configuration."""
    dns_file = os.path.join(CONFIG_DIR, "dns.txt")
    try:
        dns_config = {}
        with open(dns_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    domain, ip = line.split()
                    dns_config[domain] = ip
        return dns_config
    except Exception as e:
        logger.error(f"Failed to load DNS config: {str(e)}")
        sys.exit(1)

def load_devices() -> List[Dict]:
    """Load device configurations."""
    device_file = os.path.join(CONFIG_DIR, "devices.txt")
    try:
        devices = []
        with open(device_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    name, hw_id, bandwidth, location = line.split(",")
                    devices.append({
                        "name": name,
                        "hardware_id": hw_id,
                        "bandwidth": bandwidth,
                        "location": location
                    })
        return devices
    except Exception as e:
        logger.error(f"Failed to load device config: {str(e)}")
        sys.exit(1)

def validate_proxy_file(ctx, param, value):
    """Validate proxy file exists and has valid content"""
    if not value:
        return None
    
    try:
        path = Path(value)
        if not path.exists():
            raise click.BadParameter(f"Proxy file {value} does not exist")
        
        with open(path) as f:
            proxies = [line.strip() for line in f if line.strip()]
            
        if not proxies:
            raise click.BadParameter(f"Proxy file {value} is empty")
            
        return value
    except Exception as e:
        raise click.BadParameter(str(e))

def print_banner():
    """Print welcome banner"""
    banner = """
╔═══════════════════════════════════════════╗
║             Welcome to YashaoXen           ║
║      Multi-Proxy EarnApp Management       ║
║                                           ║
║           Created by: @oyash01            ║
╚═══════════════════════════════════════════╝
    """
    click.echo(click.style(banner, fg='green'))

def print_step(step: str, total: int, current: int):
    """Print step progress"""
    click.echo(click.style(f"\n[{current}/{total}] {step}", fg='blue', bold=True))

def confirm_action(message: str) -> bool:
    """Confirm user action with timeout"""
    try:
        return click.confirm(
            click.style(message, fg='yellow'),
            default=False,
            prompt_suffix=' (waiting 5s) ',
            show_default=True
        )
    except click.exceptions.Abort:
        return False

@click.group()
def cli():
    """YashaoXen CLI - Advanced EarnApp Management Tool"""
    print_banner()

@cli.command()
def install():
    """Install YashaoXen and its dependencies"""
    if os.geteuid() != 0:
        logger.error("Installation requires root privileges. Please run with sudo.")
        sys.exit(1)
    
    installer = Installer()
    if installer.run_installation():
        logger.info("Installation completed successfully!")
    else:
        logger.error("Installation failed!")
        sys.exit(1)

@cli.command()
def start():
    """Start YashaoXen with configuration from files"""
    try:
        # Load all configurations
        config = load_config()
        features = load_features()
        proxies = load_proxies()
        dns_config = load_dns()
        devices = load_devices()
        
        # Initialize core
        core = YashCore()
        
        # Apply configurations
        core.apply_config(config)
        core.apply_features(features)
        core.configure_dns(dns_config)
        
        # Create instances for each proxy
        for proxy in proxies:
            try:
                instance_id = core.create_instance(
                    proxy_url=proxy,
                    memory=config["system"]["memory_per_instance"]
                )
                logger.info(f"Created instance {instance_id}")
            except Exception as e:
                logger.error(f"Failed to create instance with proxy {proxy}: {str(e)}")
        
        logger.info("YashaoXen started successfully!")
        
    except Exception as e:
        logger.error(f"Failed to start YashaoXen: {str(e)}")
        sys.exit(1)

@cli.command()
def stop():
    """Stop all YashaoXen instances"""
    try:
        core = YashCore()
        core.cleanup()
        logger.info("All instances stopped successfully")
    except Exception as e:
        logger.error(f"Failed to stop instances: {str(e)}")
        sys.exit(1)

@cli.command()
def status():
    """Show status of all instances"""
    try:
        core = YashCore()
        instances = core.list_instances()
        
        if not instances:
            logger.info("No instances running")
            return
        
        for instance in instances:
            logger.info(f"\nInstance {instance['id']}:")
            logger.info(f"  Status: {instance['status']}")
            logger.info(f"  Proxy: {instance['proxy']}")
            logger.info(f"  Memory: {instance['memory']}")
            if 'stats' in instance:
                logger.info(f"  CPU Usage: {instance['stats']['cpu_percent']}%")
                logger.info(f"  Memory Usage: {instance['stats']['memory_usage']}")
                logger.info(f"  Network RX: {instance['stats']['network_rx']}")
                logger.info(f"  Network TX: {instance['stats']['network_tx']}")
        
    except Exception as e:
        logger.error(f"Failed to get status: {str(e)}")
        sys.exit(1)

@cli.command()
def check():
    """Check configuration and system status"""
    try:
        # Check configuration files
        logger.info("Checking configuration files...")
        config = load_config()
        features = load_features()
        proxies = load_proxies()
        dns_config = load_dns()
        devices = load_devices()
        
        # Initialize core and check system
        core = YashCore()
        status = core.check_installation()
        
        # Report results
        logger.info("\nConfiguration Status:")
        logger.info(f"  Main Config: {'Valid' if config else 'Invalid'}")
        logger.info(f"  Features: {'Valid' if features else 'Invalid'}")
        logger.info(f"  Proxies: {len(proxies)} found")
        logger.info(f"  DNS Rules: {len(dns_config)} found")
        logger.info(f"  Devices: {len(devices)} configured")
        
        logger.info("\nSystem Status:")
        for component, status in status.items():
            logger.info(f"  {component}: {'OK' if status else 'Failed'}")
        
    except Exception as e:
        logger.error(f"Check failed: {str(e)}")
        sys.exit(1)

@cli.command()
def rotate():
    """Rotate proxies for all instances"""
    try:
        core = YashCore()
        proxies = load_proxies()
        
        instances = core.list_instances()
        if not instances:
            logger.info("No instances to rotate")
            return
        
        for instance in instances:
            try:
                # Get next proxy from list
                next_proxy = proxies[instances.index(instance) % len(proxies)]
                if core.rotate_proxy(instance['id'], next_proxy):
                    logger.info(f"Rotated proxy for instance {instance['id']}")
                else:
                    logger.error(f"Failed to rotate proxy for instance {instance['id']}")
            except Exception as e:
                logger.error(f"Error rotating proxy: {str(e)}")
        
    except Exception as e:
        logger.error(f"Failed to rotate proxies: {str(e)}")
        sys.exit(1)

def main():
    """Main entry point for CLI"""
    try:
        cli()
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 