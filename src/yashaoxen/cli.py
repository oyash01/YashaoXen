import os
import sys
import time
import click
import logging
from pathlib import Path
from typing import List
from .core import YashCore
from .proxy import ProxyManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("YashaoXen")

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
    """YashaoXen - Multi-Proxy EarnApp Management System"""
    print_banner()

@cli.command()
@click.option('--proxy-file', '-p', 
              type=click.Path(exists=True),
              callback=validate_proxy_file,
              help='File containing list of proxies (one per line)')
@click.option('--memory', '-m',
              type=click.Choice(['1G', '2G']),
              default='1G',
              help='Memory limit per instance')
@click.option('--yes', '-y',
              is_flag=True,
              help='Skip confirmation prompts')
def create_instances(proxy_file: str, memory: str, yes: bool):
    """Create EarnApp instances from proxy list"""
    try:
        # Load proxies
        print_step("Loading proxies", 5, 1)
        proxy_manager = ProxyManager(proxy_file)
        if not proxy_manager.proxies:
            click.echo(click.style("Error: No valid proxies found in file", fg='red'))
            return

        # Confirm action
        if not yes:
            total_proxies = len(proxy_manager.proxies)
            message = f"This will create {total_proxies} EarnApp instances using {memory} memory each.\nTotal memory required: {total_proxies * int(memory[0])}G\nDo you want to continue?"
            if not confirm_action(message):
                click.echo("Operation cancelled")
                return

        # Initialize core
        print_step("Initializing system", 5, 2)
        core = YashCore()
        
        # Validate proxies
        print_step("Validating proxies", 5, 3)
        valid_proxies = []
        with click.progressbar(proxy_manager.proxies,
                             label='Validating proxies',
                             item_show_func=lambda p: p if p else '') as proxies:
            for proxy in proxies:
                if proxy_manager.validate_proxy(proxy):
                    valid_proxies.append(proxy)
                time.sleep(1)  # Prevent too fast requests

        if not valid_proxies:
            click.echo(click.style("Error: No valid proxies found", fg='red'))
            return

        # Create instances
        print_step("Creating instances", 5, 4)
        created = 0
        failed = 0
        with click.progressbar(valid_proxies,
                             label='Creating instances',
                             item_show_func=lambda p: p if p else '') as proxies:
            for proxy in proxies:
                try:
                    core.create_instance(proxy, memory)
                    created += 1
                    time.sleep(2)  # Prevent too fast container creation
                except Exception as e:
                    logger.error(f"Failed to create instance with proxy {proxy}: {e}")
                    failed += 1

        # Print summary
        print_step("Summary", 5, 5)
        click.echo("\nInstance Creation Summary:")
        click.echo(click.style(f"✓ Successfully created: {created}", fg='green'))
        if failed > 0:
            click.echo(click.style(f"✗ Failed to create: {failed}", fg='red'))
        
        click.echo("\nTo monitor your instances, use:")
        click.echo(click.style("  yashaoxen monitor", fg='cyan'))
        click.echo("\nTo view instance status, use:")
        click.echo(click.style("  yashaoxen status", fg='cyan'))

    except Exception as e:
        logger.error(f"Failed to create instances: {e}")
        click.echo(click.style(f"\nError: {str(e)}", fg='red'))
        sys.exit(1)

@cli.command()
def status():
    """Show status of all instances"""
    try:
        core = YashCore()
        instances = core.list_instances()
        
        if not instances:
            click.echo("No instances found")
            return
        
        click.echo("\nInstance Status:")
        for instance in instances:
            status_color = 'green' if instance['status'] == 'running' else 'red'
            click.echo(
                f"ID: {instance['id'][:12]} | "
                f"Status: {click.style(instance['status'], fg=status_color)} | "
                f"Memory: {instance['memory']} | "
                f"Proxy: {instance['proxy']}"
            )
            
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        click.echo(click.style(f"\nError: {str(e)}", fg='red'))
        sys.exit(1)

@cli.command()
def monitor():
    """Monitor instances in real-time"""
    try:
        core = YashCore()
        click.echo("Monitoring instances (Press Ctrl+C to stop)")
        
        while True:
            click.clear()
            print_banner()
            core.monitor_instances()
            instances = core.list_instances()
            
            if not instances:
                click.echo("No instances found")
                time.sleep(5)
                continue
            
            click.echo("\nInstance Monitoring:")
            for instance in instances:
                status_color = 'green' if instance['status'] == 'running' else 'red'
                click.echo(
                    f"\nID: {instance['id'][:12]}"
                    f"\nStatus: {click.style(instance['status'], fg=status_color)}"
                    f"\nMemory Usage: {instance.get('memory_usage', 'N/A')}"
                    f"\nCPU Usage: {instance.get('cpu_usage', 'N/A')}%"
                    f"\nNetwork RX: {instance.get('network_rx', 'N/A')} bytes"
                    f"\nNetwork TX: {instance.get('network_tx', 'N/A')} bytes"
                    f"\nProxy: {instance['proxy']}"
                )
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        click.echo("\nMonitoring stopped")
    except Exception as e:
        logger.error(f"Failed to monitor: {e}")
        click.echo(click.style(f"\nError: {str(e)}", fg='red'))
        sys.exit(1)

if __name__ == '__main__':
    cli() 