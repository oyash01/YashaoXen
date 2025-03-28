# YashaoXen Updater Guide

This guide explains how to update YashaoXen and manage your EarnApp instances during updates.

## Automatic Updates

YashaoXen includes an automatic update system that checks for new versions and applies updates seamlessly:

```bash
# Check for updates
yashaoxen update check

# Apply available updates
yashaoxen update apply
```

## Manual Update Process

If you prefer to update manually, follow these steps:

1. **Backup Your Configuration**
   ```bash
   # Backup your config
   sudo cp /etc/yashaoxen/config.json /etc/yashaoxen/config.json.backup
   
   # Backup your proxy list
   cp proxies.txt proxies.txt.backup
   ```

2. **Stop Running Instances**
   ```bash
   # List running instances
   yashaoxen list-instances
   
   # Stop all instances
   yashaoxen cleanup
   ```

3. **Update the Repository**
   ```bash
   # Pull latest changes
   cd /opt/yashaoxen
   git pull origin main
   
   # Update dependencies
   source venv/bin/activate
   pip install -r requirements.txt --upgrade
   ```

4. **Restart Services**
   ```bash
   # Reinitialize YashaoXen
   yashaoxen init
   
   # Start instances with updated configuration
   yashaoxen create-instances --proxy-file proxies.txt
   ```

## Version-Specific Updates

### Updating from v1.0.x to v1.1.x
1. Backup your configuration files
2. Update system packages:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
3. Update YashaoXen:
   ```bash
   pip install yashaoxen --upgrade
   ```
4. Run database migrations (if any):
   ```bash
   yashaoxen migrate
   ```

### Updating from v0.x to v1.x
For major version updates, we recommend a fresh installation:
1. Backup all configuration and data
2. Uninstall old version
3. Install new version following the installation guide
4. Restore your configuration and proxies

## Troubleshooting Updates

### Common Issues

1. **Configuration Conflicts**
   - Backup your config
   - Remove the old config: `sudo rm /etc/yashaoxen/config.json`
   - Reinitialize: `yashaoxen init`
   - Restore your settings manually

2. **Docker Issues**
   ```bash
   # Restart Docker service
   sudo systemctl restart docker
   
   # Rebuild containers
   yashaoxen cleanup
   yashaoxen create-instances --proxy-file proxies.txt
   ```

3. **Permission Issues**
   ```bash
   # Fix permissions
   sudo chown -R $USER:$USER /etc/yashaoxen
   sudo chmod -R 755 /etc/yashaoxen
   ```

### Recovery Steps

If an update fails:
1. Stop all instances: `yashaoxen cleanup`
2. Restore backup configuration
3. Reinstall if necessary: `sudo ./install.sh`
4. Contact support if issues persist

## Best Practices

1. **Always Backup First**
   - Configuration files
   - Proxy lists
   - Custom scripts

2. **Update During Low Activity**
   - Schedule updates during off-peak hours
   - Notify users if running in production

3. **Test Updates**
   - Test on a single instance first
   - Verify functionality before full deployment

4. **Monitor After Updates**
   ```bash
   # Check system status
   yashaoxen status
   
   # Monitor logs
   tail -f /var/log/yashaoxen/core.log
   ```

## Rollback Procedure

If you need to rollback to a previous version:

1. **Stop Services**
   ```bash
   yashaoxen cleanup
   ```

2. **Restore Backup**
   ```bash
   sudo cp /etc/yashaoxen/config.json.backup /etc/yashaoxen/config.json
   ```

3. **Switch Version**
   ```bash
   # List available versions
   pip list | grep yashaoxen
   
   # Install specific version
   pip install yashaoxen==1.0.0
   ```

4. **Restart Services**
   ```bash
   yashaoxen init
   yashaoxen create-instances --proxy-file proxies.txt.backup
   ```

## Support

For update-related issues or questions:
- GitHub Issues: [YashaoXen Issues](https://github.com/oyash01/YashaoXen/issues)
- Documentation: [YashaoXen Docs](https://github.com/oyash01/YashaoXen/docs)
- Email Support: charliehackerhack@gmail.com 