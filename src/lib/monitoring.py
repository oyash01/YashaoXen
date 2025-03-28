#!/usr/bin/env python3

import logging
import psutil
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from prometheus_client import start_http_server, Gauge, Counter

class MonitoringSystem:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.metrics = {}
        self.telegram_config = config['monitoring']['telegram_webhook']
        
        # Initialize Prometheus metrics
        self.metrics['cpu_usage'] = Gauge('aethernode_cpu_usage_percent', 'CPU usage percentage')
        self.metrics['memory_usage'] = Gauge('aethernode_memory_usage_percent', 'Memory usage percentage')
        self.metrics['disk_usage'] = Gauge('aethernode_disk_usage_percent', 'Disk usage percentage')
        self.metrics['instance_count'] = Gauge('aethernode_instance_count', 'Number of running instances')
        self.metrics['failed_instances'] = Counter('aethernode_failed_instances_total', 'Total number of failed instance creations')
        self.metrics['bandwidth_usage'] = Gauge('aethernode_bandwidth_usage_bytes', 'Current bandwidth usage in bytes')
        
        # Start Prometheus HTTP server
        start_http_server(9100)
        
    def start_monitoring(self):
        """Start the monitoring loop"""
        self.logger.info("Starting monitoring system")
        
        while True:
            try:
                self._collect_metrics()
                self._check_alerts()
                time.sleep(self.config['monitoring']['metrics_interval'])
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait before retrying
                
    def _collect_metrics(self):
        """Collect system and instance metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            self.metrics['cpu_usage'].set(cpu_percent)
            self.metrics['memory_usage'].set(memory.percent)
            self.metrics['disk_usage'].set(disk.percent)
            
            # Instance metrics
            instance_count = self._get_instance_count()
            self.metrics['instance_count'].set(instance_count)
            
            # Network metrics
            net_io = psutil.net_io_counters()
            self.metrics['bandwidth_usage'].set(net_io.bytes_sent + net_io.bytes_recv)
            
            # Save metrics to file
            self._save_metrics({
                'timestamp': datetime.now().isoformat(),
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'disk_usage': disk.percent,
                'instance_count': instance_count,
                'bandwidth_usage': net_io.bytes_sent + net_io.bytes_recv
            })
            
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            
    def _check_alerts(self):
        """Check metrics against alert thresholds"""
        try:
            thresholds = self.telegram_config['alert_thresholds']
            alerts = []
            
            # Check CPU usage
            if self.metrics['cpu_usage']._value > thresholds['cpu_usage']:
                alerts.append(f"⚠️ High CPU usage: {self.metrics['cpu_usage']._value:.1f}%")
                
            # Check memory usage
            if self.metrics['memory_usage']._value > thresholds['memory_usage']:
                alerts.append(f"⚠️ High memory usage: {self.metrics['memory_usage']._value:.1f}%")
                
            # Check disk usage
            if self.metrics['disk_usage']._value > thresholds['disk_usage']:
                alerts.append(f"⚠️ High disk usage: {self.metrics['disk_usage']._value:.1f}%")
                
            # Send alerts if any
            if alerts and self.telegram_config['enabled']:
                self._send_telegram_alert('\n'.join(alerts))
                
        except Exception as e:
            self.logger.error(f"Error checking alerts: {e}")
            
    def _get_instance_count(self) -> int:
        """Get number of running instances"""
        try:
            instance_dir = Path('/var/run/aethernode/instances')
            return len(list(instance_dir.glob('*.pid')))
        except Exception:
            return 0
            
    def _save_metrics(self, metrics: Dict[str, Any]):
        """Save metrics to file"""
        try:
            metrics_file = Path('/var/log/aethernode/metrics.json')
            metrics_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing metrics
            if metrics_file.exists():
                with metrics_file.open('r') as f:
                    existing = json.load(f)
            else:
                existing = []
                
            # Add new metrics and maintain history
            existing.append(metrics)
            if len(existing) > 1000:  # Keep last 1000 entries
                existing = existing[-1000:]
                
            # Save updated metrics
            with metrics_file.open('w') as f:
                json.dump(existing, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving metrics: {e}")
            
    def _send_telegram_alert(self, message: str):
        """Send alert to Telegram webhook"""
        try:
            if not self.telegram_config['url']:
                return
                
            payload = {
                'text': f"🤖 AetherNode Alert\n\n{message}\n\nTimestamp: {datetime.now().isoformat()}"
            }
            
            response = requests.post(
                self.telegram_config['url'],
                json=payload,
                timeout=10
            )
            
            if response.status_code != 200:
                self.logger.error(f"Failed to send Telegram alert: {response.text}")
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram alert: {e}")
            
    def record_instance_failure(self, reason: str):
        """Record instance creation failure"""
        try:
            self.metrics['failed_instances'].inc()
            
            if self.telegram_config['enabled'] and self.telegram_config['alert_thresholds']['instance_creation_failed']:
                self._send_telegram_alert(f"❌ Instance creation failed\nReason: {reason}")
                
        except Exception as e:
            self.logger.error(f"Error recording instance failure: {e}")
            
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        try:
            return {
                'cpu_usage': self.metrics['cpu_usage']._value,
                'memory_usage': self.metrics['memory_usage']._value,
                'disk_usage': self.metrics['disk_usage']._value,
                'instance_count': self.metrics['instance_count']._value,
                'bandwidth_usage': self.metrics['bandwidth_usage']._value,
                'failed_instances': self.metrics['failed_instances']._value
            }
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {} 