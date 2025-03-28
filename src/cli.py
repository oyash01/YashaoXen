#!/usr/bin/env python3

import click
import json
import logging
import os
from typing import Dict, Any
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from rich.panel import Panel

from lib.instance_manager import InstanceManager
from lib.network import NetworkManager
from lib.anti_detect import AntiDetectionSystem
from lib.config_manager import ConfigManager
from lib.container import ContainerManager
from lib.proxy_handler import ProxyHandler
from .config import Config
from lib.updater import Updater

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
    """Load configuration file"""
    config_path = os.getenv('AETHER_CONFIG', 'config/config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        exit(1)

@click.group()
def cli():
    """AetherNode CLI for managing EarnApp instances"""
    pass

@cli.command()
@click.option('--device-name', required=True, help='Device name for EarnApp')
@click.option('--proxy-url', help='Proxy URL (format: type://[user:pass@]host:port)')
def setup(device_name: str, proxy_url: str = None):
    """Set up EarnApp configuration"""
    try:
        config.setup_earnapp(device_name, proxy_url)
        click.echo("EarnApp configuration completed successfully")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.option('--proxy-url', required=True, help='Proxy URL (format: type://[user:pass@]host:port)')
def update_proxy(proxy_url: str):
    """Update proxy configuration"""
    try:
        config.update_proxy(proxy_url)
        click.echo("Proxy configuration updated successfully")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.option('--memory', help='Memory limit (e.g., 1G, 512M)')
@click.option('--cpu-shares', type=int, help='CPU shares (default: 1024)')
@click.option('--aggressive/--normal', default=False, help='Enable aggressive performance mode')
def configure_performance(memory: str, cpu_shares: int, aggressive: bool):
    """Configure performance settings"""
    try:
        config.configure_performance(memory, cpu_shares, aggressive)
        click.echo("Performance settings updated successfully")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.option('--seccomp/--no-seccomp', help='Enable/disable seccomp')
@click.option('--apparmor/--no-apparmor', help='Enable/disable AppArmor')
@click.option('--network-isolation/--no-network-isolation', help='Enable/disable network isolation')
def configure_security(seccomp: bool, apparmor: bool, network_isolation: bool):
    """Configure security settings"""
    try:
        config.configure_security(seccomp, apparmor, network_isolation)
        click.echo("Security settings updated successfully")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
def show_config():
    """Display current configuration"""
    try:
        current_config = config.get_config()
        click.echo("\nAetherNode Configuration")
        click.echo("=====================")
        
        # EarnApp settings
        click.echo("\nEarnApp Settings:")
        click.echo(f"  Device Name: {current_config['earnapp']['device_name']}")
        click.echo(f"  UUID: {current_config['earnapp']['uuid']}")
        click.echo(f"  Max Instances: {current_config['earnapp']['max_instances']}")
        click.echo(f"  Auto Restart: {current_config['earnapp']['auto_restart']}")
        click.echo(f"  Block Safeguard: {current_config.get('block_safeguard', True)}")
        
        # Proxy settings
        click.echo("\nProxy Settings:")
        proxy = current_config['proxy']
        if proxy['host']:
            auth = f"{proxy['username']}:****@" if proxy['username'] else ""
            click.echo(f"  URL: {proxy['type']}://{auth}{proxy['host']}:{proxy['port']}")
        else:
            click.echo("  No proxy configured")
            
        # Container settings
        click.echo("\nContainer Settings:")
        resources = current_config['container']['resources']
        click.echo(f"  Memory Limit: {resources['memory_limit']}")
        click.echo(f"  CPU Shares: {resources['cpu_shares']}")
        
        # Security settings
        click.echo("\nSecurity Settings:")
        security = current_config['container']['security']
        click.echo(f"  Seccomp: {security['enable_seccomp']}")
        click.echo(f"  AppArmor: {security['enable_apparmor']}")
        click.echo(f"  Network Isolation: {security['enable_network_isolation']}")
        
        click.echo("\nPerformance Settings:")
        click.echo("  Memory Options: 1G or 2G")
        click.echo("  Current Memory: " + resources['memory_limit'])
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.option('--memory', type=click.Choice(['1G', '2G']), required=True, help='Memory limit (1G or 2G)')
@click.option('--proxy-file', default='proxies.txt', help='File containing proxies (one per line)')
@click.option('--block-safeguard/--allow-safeguard', default=True, help='Enable/disable safeguard blocking')
def create_instances(memory: str, proxy_file: str, block_safeguard: bool):
    """Create instances using proxies from file"""
    try:
        # Read proxies from file
        with open(proxy_file, 'r') as f:
            proxy_lines = f.readlines()
            
        # Clean and validate proxies
        proxies = [line.strip() for line in proxy_lines if line.strip()]
        
        if not proxies:
            click.echo("Error: No proxies found in file", err=True)
            return
            
        click.echo(f"Found {len(proxies)} proxies in {proxy_file}")
        click.echo(f"Safeguard blocking: {'Enabled' if block_safeguard else 'Disabled'}")
        
        # Create instances for each proxy
        for i, proxy_url in enumerate(proxies, 1):
            try:
                # Parse proxy URL
                proxy_parts = proxy_url.split('://')
                if len(proxy_parts) != 2:
                    click.echo(f"Skipping invalid proxy format: {proxy_url}")
                    continue
                    
                proxy_type = proxy_parts[0]
                proxy_auth = proxy_parts[1].split('@')
                
                if len(proxy_auth) == 2:
                    auth, address = proxy_auth
                    user, password = auth.split(':')
                    host, port = address.split(':')
                else:
                    host, port = proxy_auth[0].split(':')
                    user = password = None
                    
                proxy_config = {
                    'type': proxy_type,
                    'host': host,
                    'port': int(port),
                    'username': user,
                    'password': password,
                    'block_safeguard': block_safeguard
                }
                
                # Update container resources with selected memory
                config.configure_performance(memory_limit=memory)
                
                # Create instance
                instance_manager = InstanceManager(config.get_config())
                instance_id = instance_manager.create_instance(proxy_config)
                
                click.echo(f"Created instance {instance_id} ({i}/{len(proxies)}) with {memory} memory")
                
            except Exception as e:
                click.echo(f"Error creating instance with proxy {proxy_url}: {e}", err=True)
                continue
                
        click.echo("\nImportant: Please wait a few minutes for the instances to fully initialize.")
        click.echo("You can check instance status using the 'list_instances' command.")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.argument('instance_id')
def stop_instance(instance_id: str):
    """Stop an EarnApp instance"""
    try:
        instance_manager = InstanceManager(config.get_config())
        instance_manager.stop_instance(instance_id)
        click.echo(f"Stopped instance {instance_id}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.argument('instance_id')
def restart_instance(instance_id: str):
    """Restart an EarnApp instance"""
    try:
        instance_manager = InstanceManager(config.get_config())
        instance_manager.restart_instance(instance_id)
        click.echo(f"Restarted instance {instance_id}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
def list_instances():
    """List all EarnApp instances"""
    try:
        instance_manager = InstanceManager(config.get_config())
        instances = instance_manager.list_instances()
        
        if not instances:
            click.echo("No instances found")
            return
            
        click.echo("\nEarnApp Instances:")
        click.echo("=================")
        
        for instance in instances:
            click.echo(f"\nInstance ID: {instance['id']}")
            click.echo(f"Status: {instance['status']}")
            click.echo("Proxy:")
            proxy = instance['proxy']
            auth = f"{proxy['username']}:****@" if proxy['username'] else ""
            click.echo(f"  {proxy['type']}://{auth}{proxy['host']}:{proxy['port']}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.group()
def safeguard():
    """Manage safeguard detection and blocking"""
    pass

@safeguard.command()
def status():
    """Show current safeguard configuration"""
    try:
        safeguard_config = config.get_safeguard_config()
        
        click.echo("\nSafeguard Configuration")
        click.echo("=====================")
        
        click.echo(f"\nGlobal Status: {'Enabled' if safeguard_config['enabled'] else 'Disabled'}")
        
        click.echo("\nDetection Settings:")
        detection = safeguard_config['detection']
        click.echo(f"  Detection System: {'Enabled' if detection['enabled'] else 'Disabled'}")
        click.echo(f"  Request Logging: {'Enabled' if detection['log_requests'] else 'Disabled'}")
        click.echo(f"  Auto-Learning: {'Enabled' if detection['auto_learn'] else 'Disabled'}")
        
        click.echo("\nBlocking Methods:")
        blocking = safeguard_config['blocking']
        click.echo(f"  DNS Blocking: {'Enabled' if blocking['dns_blocking'] else 'Disabled'}")
        click.echo(f"  IP Blocking: {'Enabled' if blocking['ip_blocking'] else 'Disabled'}")
        click.echo(f"  Request Pattern Blocking: {'Enabled' if blocking['request_pattern_blocking'] else 'Disabled'}")
        click.echo(f"  Hosts File Blocking: {'Enabled' if blocking['hosts_file_blocking'] else 'Disabled'}")
        
        click.echo("\nKnown Patterns:")
        patterns = safeguard_config['patterns']
        click.echo("  Domains:")
        for domain in patterns['domains']:
            click.echo(f"    - {domain}")
        click.echo("  IPs:")
        for ip in patterns['ips']:
            click.echo(f"    - {ip}")
        click.echo("  Request Patterns:")
        for pattern in patterns['request_patterns']:
            click.echo(f"    - {pattern}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@safeguard.command()
@click.option('--enable/--disable', required=True, help='Enable or disable safeguard system')
def toggle(enable: bool):
    """Enable or disable entire safeguard system"""
    try:
        config.update_safeguard_config(enabled=enable)
        click.echo(f"Safeguard system {'enabled' if enable else 'disabled'}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@safeguard.command()
@click.option('--detection/--no-detection', help='Enable/disable detection system')
@click.option('--logging/--no-logging', help='Enable/disable request logging')
@click.option('--auto-learn/--no-auto-learn', help='Enable/disable auto-learning')
def configure_detection(detection: bool, logging: bool, auto_learn: bool):
    """Configure safeguard detection settings"""
    try:
        config.update_safeguard_config(
            detection_enabled=detection,
            log_requests=logging,
            auto_learn=auto_learn
        )
        click.echo("Detection settings updated successfully")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@safeguard.command()
@click.option('--dns/--no-dns', help='Enable/disable DNS blocking')
@click.option('--ip/--no-ip', help='Enable/disable IP blocking')
@click.option('--pattern/--no-pattern', help='Enable/disable request pattern blocking')
@click.option('--hosts/--no-hosts', help='Enable/disable hosts file blocking')
def configure_blocking(dns: bool, ip: bool, pattern: bool, hosts: bool):
    """Configure safeguard blocking methods"""
    try:
        config.update_safeguard_config(
            dns_blocking=dns,
            ip_blocking=ip,
            request_pattern_blocking=pattern,
            hosts_file_blocking=hosts
        )
        click.echo("Blocking settings updated successfully")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@safeguard.command()
@click.argument('pattern_type', type=click.Choice(['domains', 'ips', 'request_patterns']))
@click.argument('pattern')
def add_pattern(pattern_type: str, pattern: str):
    """Add a new safeguard pattern"""
    try:
        config.add_safeguard_pattern(pattern_type, pattern)
        click.echo(f"Added {pattern_type} pattern: {pattern}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@safeguard.command()
@click.argument('pattern_type', type=click.Choice(['domains', 'ips', 'request_patterns']))
@click.argument('pattern')
def remove_pattern(pattern_type: str, pattern: str):
    """Remove a safeguard pattern"""
    try:
        config.remove_safeguard_pattern(pattern_type, pattern)
        click.echo(f"Removed {pattern_type} pattern: {pattern}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.group()
def config():
    """Manage AetherNode configuration"""
    pass

@config.command()
def wizard():
    """Interactive configuration wizard"""
    try:
        click.echo("\nAetherNode Configuration Wizard")
        click.echo("===========================")
        
        # EarnApp Configuration
        click.echo("\n[1/4] EarnApp Configuration")
        device_name = click.prompt("Device Name", type=str)
        max_instances = click.prompt("Max Instances", type=int, default=1)
        auto_restart = click.confirm("Enable Auto Restart?", default=True)
        
        # Performance Configuration
        click.echo("\n[2/4] Performance Configuration")
        memory_limit = click.prompt("Memory Limit", type=click.Choice(['1G', '2G']), default='1G')
        cpu_shares = click.prompt("CPU Shares (1-1024)", type=int, default=512)
        aggressive_mode = click.confirm("Enable Aggressive Mode?", default=False)
        
        # Security Configuration
        click.echo("\n[3/4] Security Configuration")
        enable_seccomp = click.confirm("Enable Seccomp?", default=True)
        enable_apparmor = click.confirm("Enable AppArmor?", default=True)
        enable_network_isolation = click.confirm("Enable Network Isolation?", default=True)
        
        # Safeguard Configuration
        click.echo("\n[4/4] Safeguard Configuration")
        block_safeguard = click.confirm("Enable Safeguard Blocking?", default=True)
        if block_safeguard:
            enable_dns_blocking = click.confirm("Enable DNS Blocking?", default=True)
            enable_ip_blocking = click.confirm("Enable IP Blocking?", default=True)
            enable_pattern_blocking = click.confirm("Enable Pattern Blocking?", default=True)
            enable_hosts_blocking = click.confirm("Enable Hosts File Blocking?", default=True)
            enable_auto_learn = click.confirm("Enable Auto-Learning?", default=True)
        
        # Save Configuration
        new_config = {
            'earnapp': {
                'device_name': device_name,
                'max_instances': max_instances,
                'auto_restart': auto_restart
            },
            'container': {
                'resources': {
                    'memory_limit': memory_limit,
                    'cpu_shares': cpu_shares
                },
                'security': {
                    'enable_seccomp': enable_seccomp,
                    'enable_apparmor': enable_apparmor,
                    'enable_network_isolation': enable_network_isolation
                }
            },
            'performance': {
                'aggressive_mode': aggressive_mode
            }
        }
        
        if block_safeguard:
            new_config['safeguard'] = {
                'enabled': True,
                'detection': {
                    'enabled': True,
                    'auto_learn': enable_auto_learn
                },
                'blocking': {
                    'dns_blocking': enable_dns_blocking,
                    'ip_blocking': enable_ip_blocking,
                    'request_pattern_blocking': enable_pattern_blocking,
                    'hosts_file_blocking': enable_hosts_blocking
                }
            }
        
        config.save_config(new_config)
        click.echo("\nConfiguration saved successfully!")
        click.echo("\nYou can now:")
        click.echo("1. Edit configuration: aethernode config edit")
        click.echo("2. View configuration: aethernode config show")
        click.echo("3. Create instances: aethernode create-instances")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@config.command()
def edit():
    """Edit configuration in default text editor"""
    try:
        config_path = config.get_config_path()
        click.edit(filename=config_path)
        click.echo("Configuration updated. Run 'aethernode config validate' to check for errors.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@config.command()
def validate():
    """Validate current configuration"""
    try:
        current_config = config.get_config()
        errors = []
        
        # Validate EarnApp settings
        if 'earnapp' not in current_config:
            errors.append("Missing EarnApp configuration")
        elif not current_config['earnapp'].get('device_name'):
            errors.append("Missing device name")
            
        # Validate container resources
        if 'container' not in current_config:
            errors.append("Missing container configuration")
        elif 'resources' not in current_config['container']:
            errors.append("Missing container resources configuration")
        
        if errors:
            click.echo("\nConfiguration Errors:")
            for error in errors:
                click.echo(f"- {error}")
        else:
            click.echo("Configuration is valid!")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@config.command()
def backup():
    """Create backup of current configuration"""
    try:
        from datetime import datetime
        import shutil
        
        config_path = config.get_config_path()
        backup_path = f"{config_path}.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        shutil.copy2(config_path, backup_path)
        click.echo(f"Configuration backed up to: {backup_path}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@config.command()
def restore():
    """Restore configuration from backup"""
    try:
        import glob
        
        config_dir = os.path.dirname(config.get_config_path())
        backups = glob.glob(f"{config_dir}/*.backup-*")
        
        if not backups:
            click.echo("No backup files found")
            return
            
        backups.sort(reverse=True)
        
        click.echo("\nAvailable backups:")
        for i, backup in enumerate(backups):
            timestamp = backup.split('-')[-1]
            click.echo(f"{i+1}. {timestamp}")
            
        choice = click.prompt("Select backup to restore (number)", type=int, default=1)
        if 1 <= choice <= len(backups):
            import shutil
            shutil.copy2(backups[choice-1], config.get_config_path())
            click.echo("Configuration restored successfully!")
        else:
            click.echo("Invalid selection")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@config.command()
def reset():
    """Reset configuration to defaults"""
    if click.confirm("This will reset all settings to defaults. Continue?", default=False):
        try:
            config.reset_to_defaults()
            click.echo("Configuration reset to defaults")
        except Exception as e:
            click.echo(f"Error: {e}", err=True)

@cli.command()
def setup():
    """Quick setup wizard for new users"""
    click.echo("\nWelcome to AetherNode!")
    click.echo("This wizard will help you set up your EarnApp instances.")
    
    if click.confirm("Would you like to start the configuration wizard?", default=True):
        ctx = click.get_current_context()
        ctx.invoke(wizard)
    else:
        click.echo("\nYou can run the wizard later with: aethernode config wizard")

# Update show_config to use rich tables for better formatting
@config.command(name='show')
def show_config():
    """Display current configuration"""
    try:
        current_config = config.get_config()
        
        # Create main table
        table = Table(title="AetherNode Configuration", show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        # EarnApp settings
        table.add_row("Device Name", current_config['earnapp']['device_name'])
        table.add_row("Max Instances", str(current_config['earnapp']['max_instances']))
        table.add_row("Auto Restart", str(current_config['earnapp']['auto_restart']))
        
        # Container settings
        resources = current_config['container']['resources']
        table.add_row("Memory Limit", resources['memory_limit'])
        table.add_row("CPU Shares", str(resources['cpu_shares']))
        
        # Security settings
        security = current_config['container']['security']
        table.add_row("Seccomp", str(security['enable_seccomp']))
        table.add_row("AppArmor", str(security['enable_apparmor']))
        table.add_row("Network Isolation", str(security['enable_network_isolation']))
        
        # Performance settings
        table.add_row("Aggressive Mode", str(current_config['performance']['aggressive_mode']))
        
        # Safeguard settings
        if 'safeguard' in current_config:
            safeguard = current_config['safeguard']
            table.add_row("Safeguard Blocking", str(safeguard['enabled']))
            if safeguard['enabled']:
                table.add_row("DNS Blocking", str(safeguard['blocking']['dns_blocking']))
                table.add_row("IP Blocking", str(safeguard['blocking']['ip_blocking']))
                table.add_row("Pattern Blocking", str(safeguard['blocking']['request_pattern_blocking']))
        
        console.print(table)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.group()
def update():
    """Manage AetherNode updates"""
    pass

@update.command(name='check')
def check_updates():
    """Check for available updates"""
    try:
        updater = Updater()
        latest_version = updater.check_for_updates()
        
        if latest_version:
            click.echo(f"\nNew version available: {latest_version}")
            click.echo("Run 'aethernode update install' to update")
        else:
            click.echo("\nYou are running the latest version")
            
    except Exception as e:
        click.echo(f"Error checking for updates: {e}", err=True)

@update.command(name='install')
@click.option('--force', is_flag=True, help='Force update even if no new version is available')
def install_update(force: bool):
    """Install latest update"""
    try:
        updater = Updater()
        
        with Progress() as progress:
            task = progress.add_task("Updating AetherNode...", total=100)
            
            # Backup current installation
            progress.update(task, advance=20, description="Creating backup...")
            backup_path = updater.backup_current_installation()
            
            # Install update
            progress.update(task, advance=40, description="Installing update...")
            success = updater.update(force=force)
            
            if success:
                progress.update(task, advance=40, description="Update complete!")
                click.echo("\nUpdate completed successfully!")
                click.echo(f"Backup created at: {backup_path}")
            else:
                progress.update(task, advance=40, description="Update failed!")
                click.echo("\nUpdate failed. Rolling back to previous version...")
                updater.rollback()
                
    except Exception as e:
        click.echo(f"Error installing update: {e}", err=True)

@update.command(name='rollback')
@click.option('--timestamp', help='Specific backup timestamp to restore')
def rollback_update(timestamp: str = None):
    """Rollback to previous version"""
    try:
        updater = Updater()
        
        if timestamp:
            success = updater.rollback(timestamp)
        else:
            # Show available backups
            backups = updater.list_backups()
            
            if not backups:
                click.echo("No backups found")
                return
                
            click.echo("\nAvailable backups:")
            for i, backup in enumerate(backups, 1):
                size_mb = round(backup['size'], 2)
                click.echo(f"{i}. {backup['timestamp']} ({size_mb} MB)")
                
            choice = click.prompt("\nSelect backup to restore (number)", type=int, default=1)
            if 1 <= choice <= len(backups):
                success = updater.rollback(backups[choice-1]['timestamp'])
            else:
                click.echo("Invalid selection")
                return
                
        if success:
            click.echo("Rollback completed successfully!")
        else:
            click.echo("Rollback failed!")
            
    except Exception as e:
        click.echo(f"Error during rollback: {e}", err=True)

@update.command(name='list-backups')
def list_backups():
    """List available backups"""
    try:
        updater = Updater()
        backups = updater.list_backups()
        
        if not backups:
            click.echo("No backups found")
            return
            
        table = Table(title="Available Backups", show_header=True, header_style="bold magenta")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Size", style="green")
        table.add_column("Path", style="blue")
        
        for backup in backups:
            size_mb = round(backup['size'], 2)
            table.add_row(
                backup['timestamp'],
                f"{size_mb} MB",
                backup['path']
            )
            
        console.print(table)
        
    except Exception as e:
        click.echo(f"Error listing backups: {e}", err=True)

if __name__ == '__main__':
    cli() 