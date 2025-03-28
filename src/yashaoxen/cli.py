import os
import sys
import time
import click
import logging
from pathlib import Path
from typing import List, Optional
from .core import YashCore
from .proxy import ProxyManager
from .install import Installer

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
def init():
    """Initialize YashaoXen configuration"""
    try:
        core = YashCore()
        status = core.check_installation()
        
        if not all(status.values()):
            logger.error("System not properly configured. Please run: sudo yashaoxen install")
            for component, configured in status.items():
                if not configured:
                    logger.error(f"{component} not properly configured")
            sys.exit(1)
        
        logger.info("YashaoXen initialized successfully!")
        
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        sys.exit(1)

@cli.command()
@click.option('--proxy-file', '-p', 
              type=click.Path(exists=True),
              callback=validate_proxy_file,
              help='File containing list of proxies (one per line)')
@click.option('--memory', '-m',
              type=click.Choice(['1G', '2G']),
              default='1G',
              help='Memory limit per instance')
@click.option('--optimize', is_flag=True, help='Enable performance optimization')
def create_instances(proxy_file: str, memory: str, optimize: bool):
    """Create EarnApp instances from a proxy list"""
    try:
        # Load proxies
        print_step("Loading proxies", 5, 1)
        proxy_manager = ProxyManager(proxy_file)
        if not proxy_manager.proxies:
            click.echo(click.style("Error: No valid proxies found in file", fg='red'))
            return

        # Confirm action
        if not optimize:
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
                    instance_id = core.create_instance(
                        proxy_url=proxy,
                        memory=memory
                    )
                    valid_proxies.append(proxy)
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
@click.argument('instance_id', required=False)
def list_instances(instance_id: Optional[str]):
    """List running instances and their status"""
    try:
        core = YashCore()
        instances = core.list_instances()
        
        if not instances:
            logger.info("No instances found")
            return
        
        if instance_id:
            instances = [i for i in instances if i['id'] == instance_id]
            if not instances:
                logger.error(f"Instance {instance_id} not found")
                sys.exit(1)
        
        for instance in instances:
            logger.info(f"Instance {instance['id']}:")
            logger.info(f"  Status: {instance['status']}")
            logger.info(f"  Proxy: {instance['proxy']}")
            logger.info(f"  Memory: {instance['memory']}")
            if 'stats' in instance:
                logger.info(f"  CPU Usage: {instance['stats']['cpu_percent']}%")
                logger.info(f"  Memory Usage: {instance['stats']['memory_usage']}")
                logger.info(f"  Network RX: {instance['stats']['network_rx']}")
                logger.info(f"  Network TX: {instance['stats']['network_tx']}")
            logger.info("---")
        
    except Exception as e:
        logger.error(f"Failed to list instances: {str(e)}")
        sys.exit(1)

@cli.command()
@click.argument('instance_id')
def start(instance_id: str):
    """Start a stopped instance"""
    try:
        core = YashCore()
        if core.start_instance(instance_id):
            logger.info(f"Instance {instance_id} started successfully")
        else:
            logger.error(f"Failed to start instance {instance_id}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start instance: {str(e)}")
        sys.exit(1)

@cli.command()
@click.argument('instance_id')
def stop(instance_id: str):
    """Stop a running instance"""
    try:
        core = YashCore()
        if core.stop_instance(instance_id):
            logger.info(f"Instance {instance_id} stopped successfully")
        else:
            logger.error(f"Failed to stop instance {instance_id}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to stop instance: {str(e)}")
        sys.exit(1)

@cli.command()
@click.argument('instance_id')
@click.argument('new_proxy')
def rotate_proxy(instance_id: str, new_proxy: str):
    """Rotate proxy for an instance"""
    try:
        core = YashCore()
        if core.rotate_proxy(instance_id, new_proxy):
            logger.info(f"Proxy rotated successfully for instance {instance_id}")
        else:
            logger.error(f"Failed to rotate proxy for instance {instance_id}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to rotate proxy: {str(e)}")
        sys.exit(1)

@cli.command()
def cleanup():
    """Clean up stopped instances and temporary files"""
    try:
        core = YashCore()
        core.cleanup()
        logger.info("Cleanup completed successfully")
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
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