#!/bin/bash
set -e

# Setup proxy if provided
if [ ! -z "$PROXY_URL" ]; then
    echo "Setting up proxy: $PROXY_URL"
    export http_proxy=$PROXY_URL
    export https_proxy=$PROXY_URL
    export all_proxy=$PROXY_URL
fi

# Set memory limit
if [ ! -z "$MEMORY_LIMIT" ]; then
    echo "Setting memory limit: $MEMORY_LIMIT"
    # Convert memory limit to bytes for cgroups
    if [[ $MEMORY_LIMIT =~ ^([0-9]+)(G|M)$ ]]; then
        num=${BASH_REMATCH[1]}
        unit=${BASH_REMATCH[2]}
        if [ "$unit" = "G" ]; then
            mem_bytes=$((num * 1024 * 1024 * 1024))
        else
            mem_bytes=$((num * 1024 * 1024))
        fi
        echo $mem_bytes > /sys/fs/cgroup/memory/memory.limit_in_bytes
    fi
fi

# Create proxy monitor script
cat > /usr/local/bin/proxy-monitor.sh << 'EOF'
#!/bin/bash

while true; do
    if [ ! -z "$PROXY_URL" ]; then
        # Test proxy connectivity
        if ! curl -s --proxy $PROXY_URL https://api.ipify.org > /dev/null; then
            echo "Proxy connection failed, restarting EarnApp..."
            supervisorctl restart earnapp
        fi
    fi
    sleep 300  # Check every 5 minutes
done
EOF

chmod +x /usr/local/bin/proxy-monitor.sh

# Start supervisord
exec /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf 