#!/usr/bin/env python3

import os
import sys
import json
import shutil
import logging
import requests
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class Updater:
    def __init__(self, config_dir: Path = Path("/etc/yashaoxen")):
        self.config_dir = config_dir
        self.version_file = self.config_dir / "version.json"
        self.backup_dir = self.config_dir / "backups"
        self.repo_url = "https://api.github.com/repos/jonfedric/YashaoXen"  # Updated repository URL
        self.current_version = self._get_current_version()

    def _get_current_version(self) -> str:
        """Get current version from version file"""
        try:
            if self.version_file.exists():
                with open(self.version_file, 'r') as f:
                    data = json.load(f)
                    return data.get('version', '0.0.0')
            return '0.0.0'
        except Exception as e:
            logger.error(f"Error reading version file: {e}")
            return '0.0.0'

    def _save_version(self, version: str):
        """Save version information"""
        try:
            with open(self.version_file, 'w') as f:
                json.dump({'version': version}, f)
        except Exception as e:
            logger.error(f"Error saving version: {e}")

    def check_for_updates(self) -> Optional[str]:
        """Check for available updates"""
        try:
            response = requests.get(f"{self.repo_url}/releases/latest")
            if response.status_code == 200:
                latest_version = response.json()['tag_name'].lstrip('v')
                if latest_version > self.current_version:
                    return latest_version
            return None
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return None

    def backup_current_installation(self):
        """Backup current installation"""
        try:
            timestamp = subprocess.check_output(['date', '+%Y%m%d_%H%M%S']).decode().strip()
            backup_path = self.backup_dir / f"backup_{timestamp}"
            
            # Create backup directory
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup configuration
            shutil.copytree(self.config_dir, backup_path / "config", dirs_exist_ok=True)
            
            # Backup source code
            src_dir = Path(__file__).parent.parent
            shutil.copytree(src_dir, backup_path / "src", dirs_exist_ok=True)
            
            logger.info(f"Backup created at: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise

    def update(self, force: bool = False) -> bool:
        """Update AetherNode to latest version"""
        try:
            latest_version = self.check_for_updates()
            
            if not latest_version and not force:
                logger.info("Already running latest version")
                return False
                
            logger.info(f"Updating to version {latest_version}")
            
            # Create backup
            self.backup_current_installation()
            
            # Download latest release
            response = requests.get(f"{self.repo_url}/releases/latest/zipball")
            if response.status_code != 200:
                raise Exception("Failed to download update")
                
            # Extract update
            update_dir = self.config_dir / "update"
            update_dir.mkdir(parents=True, exist_ok=True)
            
            update_zip = update_dir / "update.zip"
            with open(update_zip, 'wb') as f:
                f.write(response.content)
                
            shutil.unpack_archive(update_zip, update_dir)
            
            # Apply update
            src_dir = Path(__file__).parent.parent
            extracted_dir = next(update_dir.glob('*-*'))  # Get extracted directory
            
            # Update source code
            shutil.rmtree(src_dir)
            shutil.copytree(extracted_dir / "src", src_dir)
            
            # Clean up
            shutil.rmtree(update_dir)
            
            # Update version
            self._save_version(latest_version)
            
            logger.info(f"Successfully updated to version {latest_version}")
            return True
            
        except Exception as e:
            logger.error(f"Error during update: {e}")
            return False

    def rollback(self, backup_timestamp: Optional[str] = None) -> bool:
        """Rollback to previous version"""
        try:
            if not backup_timestamp:
                # Get latest backup
                backups = sorted(self.backup_dir.glob("backup_*"))
                if not backups:
                    logger.error("No backups found")
                    return False
                backup_path = backups[-1]
            else:
                backup_path = self.backup_dir / f"backup_{backup_timestamp}"
                if not backup_path.exists():
                    logger.error(f"Backup not found: {backup_timestamp}")
                    return False
            
            # Restore configuration
            shutil.rmtree(self.config_dir)
            shutil.copytree(backup_path / "config", self.config_dir)
            
            # Restore source code
            src_dir = Path(__file__).parent.parent
            shutil.rmtree(src_dir)
            shutil.copytree(backup_path / "src", src_dir)
            
            logger.info(f"Successfully rolled back to backup: {backup_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            return False

    def list_backups(self) -> list:
        """List available backups"""
        try:
            backups = []
            for backup in sorted(self.backup_dir.glob("backup_*")):
                backups.append({
                    'timestamp': backup.name.replace('backup_', ''),
                    'path': str(backup),
                    'size': sum(f.stat().st_size for f in backup.rglob('*') if f.is_file()) / 1024 / 1024  # Size in MB
                })
            return backups
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return [] 