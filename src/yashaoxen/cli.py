"""
YashaoXen CLI - Advanced EarnApp Management Tool
"""

import os
import sys
import json
import time
import click
import logging
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from .core import YashCore
from .proxy import ProxyManager
from .install import Installer
from .security import SecurityManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("YashaoXen")

console = Console()

def load_config():
    """Load YashaoXen configuration."""
    config_file = "/etc/yashaoxen/config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    """Save YashaoXen configuration."""
    os.makedirs("/etc/yashaoxen", exist_ok=True)
    with open("/etc/yashaoxen/config.json", 'w') as f:
        json.dump(config, f, indent=4)

def load_features() -> Dict:
    """Load feature toggles."""
    feature_file = "/etc/yashaoxen/features.json"
    try:
        with open(feature_file) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load features: {str(e)}")
        sys.exit(1)

def load_proxies() -> List[str]:
    """Load proxy list."""
    proxy_file = "/etc/yashaoxen/proxies.txt"
    try:
        with open(proxy_file) as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Failed to load proxies: {str(e)}")
        sys.exit(1)

def load_dns() -> Dict[str, str]:
    """Load DNS configuration."""
    dns_file = "/etc/yashaoxen/dns.txt"
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
    device_file = "/etc/yashaoxen/devices.txt"
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
def setup():
    """Interactive setup wizard"""
    console.print(Panel.fit("Welcome to YashaoXen Setup Wizard!", style="bold green"))
    
    # Setup EarnApp
    config = setup_earnapp()
    
    # Setup proxies
    setup_proxies()
    
    # Initialize core
    core = YashCore()
    
    # Start instances
    if Confirm.ask("Would you like to start YashaoXen now?"):
        core.start_all()
        show_status(core)

@cli.command()
def start():
    """Start YashaoXen with current configuration"""
    try:
        core = YashCore()
        core.start_all()
        show_status(core)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

@cli.command()
def stop():
    """Stop all YashaoXen instances"""
    try:
        core = YashCore()
        core.stop_all()
        console.print("[green]All instances stopped successfully[/green]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

@cli.command()
def status():
    """Show status of all instances"""
    try:
        core = YashCore()
        show_status(core)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

@cli.command()
def rotate():
    """Rotate proxies for all instances"""
    try:
        core = YashCore()
        core.rotate_proxies()
        show_status(core)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

def setup_earnapp():
    """Interactive EarnApp setup."""
    console.print(Panel.fit("EarnApp Configuration", style="bold green"))
    
    config = load_config()
    if not config.get("earnapp"):
        config["earnapp"] = {}
    
    # Get EarnApp device token
    while True:
        token = Prompt.ask("Enter your EarnApp device token (from https://earnapp.com/devices)")
        if token and len(token) > 10:  # Basic validation
            config["earnapp"]["token"] = token
            break
        console.print("[red]Invalid token. Please enter a valid device token.[/red]")
    
    # Get number of instances
    instances = Prompt.ask("How many instances do you want to run?", default="1")
    config["earnapp"]["instances"] = int(instances)
    
    save_config(config)
    return config

def setup_proxies():
    """Interactive proxy setup."""
    console.print(Panel.fit("Proxy Configuration", style="bold green"))
    
    proxy_file = "/etc/yashaoxen/proxies.txt"
    
    # Create example proxy if file doesn't exist
    if not os.path.exists(proxy_file):
        os.makedirs(os.path.dirname(proxy_file), exist_ok=True)
        with open(proxy_file, 'w') as f:
            f.write("# Add your proxies here, one per line in format:\n")
            f.write("# http://username:password@host:port\n")
            f.write("# Example:\n")
            f.write("# http://user:pass@proxy.example.com:8080\n")
    
    console.print(f"\nProxy file location: {proxy_file}")
    console.print("Please add your proxies to this file, one per line.")
    
    if Confirm.ask("Would you like to add proxies now?"):
        proxies = []
        while True:
            proxy = Prompt.ask("Enter proxy (or press Enter to finish)")
            if not proxy:
                break
            proxies.append(proxy)
        
        if proxies:
            with open(proxy_file, 'w') as f:
                for proxy in proxies:
                    f.write(f"{proxy}\n")
    
    return True

def show_status(core):
    """Show status of all instances."""
    table = Table(title="YashaoXen Status")
    table.add_column("Instance", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Proxy", style="blue")
    table.add_column("Uptime", style="yellow")
    
    instances = core.list_instances()
    for instance in instances:
        table.add_row(
            instance["name"],
            instance["status"],
            instance["proxy"],
            instance["uptime"]
        )
    
    console.print(table)

def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main() 