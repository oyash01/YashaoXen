#!/usr/bin/env python3

import logging
import json
import time
import argparse
from pathlib import Path
from typing import Dict, Any
from lib.proxy_handler import ProxyHandler
from lib.instance_manager import InstanceManager

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def load_config() -> Dict[str, Any]:
    """Load configuration from file"""
    config_path = Path(__file__).parent.parent / 'config' / 'config.json'
    if not config_path.exists():
        raise Exception("Configuration file not found")
        
    return json.loads(config_path.read_text())

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='AetherNode - EarnApp Manager')
    parser.add_argument('--proxy-list', type=str, help='Path to proxy list file')
    parser.add_argument('--instances', type=int, help='Number of instances to create')
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        config = load_config()
        
        # Initialize handlers
        proxy_handler = ProxyHandler(config)
        instance_manager = InstanceManager(config, proxy_handler)
        
        # Load proxy list
        if not args.proxy_list or not Path(args.proxy_list).exists():
            raise Exception("Proxy list file not found")
            
        with open(args.proxy_list) as f:
            proxy_list = [line.strip().split(':') for line in f if line.strip()]
            
        # Create instances
        num_instances = min(
            args.instances or len(proxy_list),  # Default to one instance per proxy
            len(proxy_list)  # Cannot exceed number of proxies
        )
        
        logger.info(f"Creating {num_instances} instances (one per proxy)...")
        
        for i in range(num_instances):
            try:
                # Parse proxy details
                proxy = proxy_list[i]
                proxy_config = {
                    'host': proxy[0],
                    'port': proxy[1],
                    'username': proxy[2] if len(proxy) > 2 else None,
                    'password': proxy[3] if len(proxy) > 3 else None
                }
                
                # Create instance
                instance_id = instance_manager.create_instance(proxy_config)
                logger.info(f"Created instance {instance_id} with dedicated proxy {proxy_config['host']}:{proxy_config['port']}")
                
                # Wait between instances
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to create instance: {e}")
                continue
                
        # Monitor instances
        while True:
            for instance_id in list(instance_manager.instances.keys()):
                try:
                    status = instance_manager.get_instance_status(instance_id)
                    
                    if not status or status.get('status') != 'running':
                        logger.warning(f"Instance {instance_id} not running, restarting...")
                        
                        # Get the instance's original proxy config
                        original_proxy = instance_manager.instances[instance_id]['config']['proxy']
                        
                        # Stop the instance
                        instance_manager.stop_instance(instance_id)
                        
                        # Restart with same proxy
                        new_instance_id = instance_manager.create_instance(original_proxy)
                        logger.info(f"Restarted instance as {new_instance_id} with same proxy")
                        
                except Exception as e:
                    logger.error(f"Error monitoring instance {instance_id}: {e}")
                    
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        for instance_id in list(instance_manager.instances.keys()):
            instance_manager.stop_instance(instance_id)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == '__main__':
    main() 