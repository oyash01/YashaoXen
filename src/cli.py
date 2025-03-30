#!/usr/bin/env python3

import os
import json
import logging
import click
from typing import Dict, Any, Optional
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.progress import Progress

from .lib.instance_manager import InstanceManager
from .lib.network import NetworkManager
from .lib.anti_detect import AntiDetectionSystem
from lib.config_manager import ConfigManager
from .lib.container import ContainerManager
from lib.proxy_handler import ProxyHandler
from .config import Config
from lib.updater import Updater
from .lib.earnapp import EarnAppManager

console = Console()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize configuration
config = Config()

def load_config() -> Dict[str, Any]:
    """Load configuration from file"""
    config_file = Path("config.json")
    if not config_file.exists():
        raise click.ClickException("Configuration file not found. Please run setup first.")
    
    try:
        with open(config_file) as f:
            return json.load(f)
    except Exception as e:
        raise click.ClickException(f"Error loading configuration: {e}")

def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file"""
    config_file = Path("config.json")
    try:
        with open(config_file, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        raise click.ClickException(f"Error saving configuration: {e}")

@click.group()
def cli():
    """YashaoXen CLI - Manage your EarnApp containers"""
    pass

@cli.group()
def earnapp():
    """Manage EarnApp accounts"""
    pass

@earnapp.command()
@click.option('--uuid', prompt='Enter your EarnApp UUID', help='Your EarnApp device UUID')
@click.option('--name', prompt='Enter a name for this device', help='A friendly name for this device')
def connect(uuid: str, name: str):
    """Connect a new EarnApp account"""
    try:
        container_manager = ContainerManager()
        earnapp_manager = EarnAppManager(container_manager)
        
        if earnapp_manager.connect_account(uuid, name):
            click.echo(f"Successfully connected account: {name}")
        else:
            click.echo("Failed to connect account. Check the logs for details.")
    except Exception as e:
        logger.error(f"Error connecting account: {str(e)}")
        click.echo("An error occurred while connecting the account.")

@earnapp.command()
@click.option('--uuid', prompt='Enter the EarnApp UUID to disconnect', help='The UUID of the account to disconnect')
def disconnect(uuid: str):
    """Disconnect an EarnApp account"""
    try:
        container_manager = ContainerManager()
        earnapp_manager = EarnAppManager(container_manager)
        
        if earnapp_manager.disconnect_account(uuid):
            click.echo("Successfully disconnected account")
        else:
            click.echo("Failed to disconnect account. Check the logs for details.")
    except Exception as e:
        logger.error(f"Error disconnecting account: {str(e)}")
        click.echo("An error occurred while disconnecting the account.")

@earnapp.command()
def list():
    """List all connected EarnApp accounts"""
    try:
        container_manager = ContainerManager()
        earnapp_manager = EarnAppManager(container_manager)
        
        accounts = earnapp_manager.list_accounts()
        if not accounts:
            click.echo("No accounts found.")
            return
            
        click.echo("\nConnected EarnApp Accounts:")
        click.echo("-" * 80)
        for account in accounts:
            click.echo(f"Name: {account['name']}")
            click.echo(f"UUID: {account['uuid']}")
            click.echo(f"Status: {account['status']}")
            click.echo(f"Container Status: {account['container_status']}")
            click.echo(f"Created: {account['created_at']}")
            click.echo("-" * 80)
            
    except Exception as e:
        logger.error(f"Error listing accounts: {str(e)}")
        click.echo("An error occurred while listing accounts.")

@earnapp.command()
@click.option('--uuid', prompt='Enter the EarnApp UUID', help='The UUID of the account to check')
def status(uuid: str):
    """Check status of an EarnApp account"""
    try:
        container_manager = ContainerManager()
        earnapp_manager = EarnAppManager(container_manager)
        
        status = earnapp_manager.get_account_status(uuid)
        if status:
            click.echo("\nAccount Status:")
            click.echo("-" * 40)
            click.echo(f"Name: {status['name']}")
            click.echo(f"UUID: {status['uuid']}")
            click.echo(f"Status: {status['status']}")
            click.echo(f"Container Status: {status['container_status']}")
            click.echo(f"Created: {status['created_at']}")
        else:
            click.echo("Account not found.")
            
    except Exception as e:
        logger.error(f"Error checking account status: {str(e)}")
        click.echo("An error occurred while checking account status.")

@cli.command()
def setup():
    """Setup YashaoXen configuration"""
    try:
        # Get EarnApp token
        token = click.prompt("Enter your EarnApp device token", type=str)
        
        # Get number of instances
        num_instances = click.prompt("Enter number of instances to run", type=int, default=1)
        
        # Get proxy file path
        proxy_file = click.prompt("Enter path to proxy file (one proxy per line)", type=str)
        if not os.path.exists(proxy_file):
            raise click.ClickException("Proxy file not found")
        
        # Get DNS file path
        dns_file = click.prompt("Enter path to DNS file (one DNS per line)", type=str)
        if not os.path.exists(dns_file):
            raise click.ClickException("DNS file not found")
        
        # Configure safeguards
        safeguards = {
            "anti_detection": click.confirm("Enable anti-detection measures?", default=True),
            "resource_limits": click.confirm("Enable resource limits?", default=True),
            "auto_restart": click.confirm("Enable auto-restart on failure?", default=True)
        }
        
        # Configure features
        features = {
            "auto_update": click.confirm("Enable auto-update?", default=True),
            "performance_mode": click.confirm("Enable performance mode?", default=True),
            "proxy_rotation": click.confirm("Enable proxy rotation?", default=True)
        }
        
        # Save configuration
        config = {
            "earnapp_token": token,
            "num_instances": num_instances,
            "proxy_file": proxy_file,
            "dns_file": dns_file,
            "safeguards": safeguards,
            "features": features
        }
        save_config(config)
        
        click.echo("Configuration saved successfully!")
        
    except Exception as e:
        raise click.ClickException(f"Error during setup: {e}")

@cli.command()
def start():
    """Start EarnApp instances"""
    try:
        config = load_config()
        container_manager = ContainerManager(config)
        earnapp_manager = EarnAppManager(config)
        proxy_handler = ProxyHandler(config)
        
        # Start instances
        for i in range(config["num_instances"]):
            name = f"earnapp_{i+1}"
            click.echo(f"Starting instance {name}...")
            
            # Get next proxy
            proxy = proxy_handler.get_next_proxy()
            
            # Create container
            container_id = container_manager.create_container(name, proxy)
            
            # Start EarnApp service
            earnapp_manager.start_service(container_id)
            
            click.echo(f"Instance {name} started successfully!")
        
        click.echo("All instances started successfully!")
        
    except Exception as e:
        raise click.ClickException(f"Error starting instances: {e}")

@cli.command()
def stop():
    """Stop all EarnApp instances"""
    try:
        config = load_config()
        container_manager = ContainerManager(config)
        
        # Stop all containers
        containers = container_manager.list_containers()
        for container in containers:
            name = container["Names"][0].lstrip("/")
            if name.startswith("earnapp_"):
                click.echo(f"Stopping instance {name}...")
                container_manager.stop_container(name)
                click.echo(f"Instance {name} stopped successfully!")
        
        click.echo("All instances stopped successfully!")
        
    except Exception as e:
        raise click.ClickException(f"Error stopping instances: {e}")

@cli.command()
def status():
    """Check status of all instances"""
    try:
        config = load_config()
        container_manager = ContainerManager(config)
        
        # Get container status
        containers = container_manager.list_containers()
        
        # Format output
        click.echo("\nInstance Status:")
        click.echo("-" * 80)
        click.echo(f"{'Name':<20} {'Status':<10} {'IP':<15} {'Proxy':<30}")
        click.echo("-" * 80)
        
        for container in containers:
            name = container["Names"][0].lstrip("/")
            if name.startswith("earnapp_"):
                status = container["Status"]
                ip = container["NetworkSettings"]["Networks"]["bridge"]["IPAddress"]
                proxy = container["Config"]["Env"][0].split("=")[1]
                
                click.echo(f"{name:<20} {status:<10} {ip:<15} {proxy:<30}")
        
        click.echo("-" * 80)
        
    except Exception as e:
        raise click.ClickException(f"Error checking status: {e}")

@cli.command()
def rotate():
    """Rotate proxies for all instances"""
    try:
        config = load_config()
        container_manager = ContainerManager(config)
        proxy_handler = ProxyHandler(config)
        
        # Rotate proxies
        containers = container_manager.list_containers()
        for container in containers:
            name = container["Names"][0].lstrip("/")
            if name.startswith("earnapp_"):
                click.echo(f"Rotating proxy for instance {name}...")
                
                # Get next proxy
                proxy = proxy_handler.get_next_proxy()
                
                # Update container
                container_manager.update_container(name, proxy)
                
                click.echo(f"Proxy rotated successfully for instance {name}!")
        
        click.echo("All proxies rotated successfully!")
        
    except Exception as e:
        raise click.ClickException(f"Error rotating proxies: {e}")

@cli.command()
def check():
    """Check configuration and system status"""
    try:
        config = load_config()
        
        # Check EarnApp token
        if not config.get("earnapp_token"):
            raise click.ClickException("EarnApp token not configured")
        
        # Check proxy file
        if not os.path.exists(config["proxy_file"]):
            raise click.ClickException("Proxy file not found")
        
        # Check DNS file
        if not os.path.exists(config["dns_file"]):
            raise click.ClickException("DNS file not found")
        
        # Check Docker
        try:
            import docker
            client = docker.from_env()
            client.ping()
        except Exception as e:
            raise click.ClickException(f"Docker not available: {e}")
        
        # Check container image
        try:
            client = docker.from_env()
            client.images.get("fazalfarhan01/earnapp:lite")
        except Exception as e:
            raise click.ClickException("EarnApp container image not found. Please run setup first.")
        
        click.echo("All checks passed successfully!")
        
    except Exception as e:
        raise click.ClickException(f"Error during checks: {e}")

if __name__ == "__main__":
    cli() 