#!/bin/bash
set -e

echo "Starting HAProxy entrypoint script..."

# Copy default configuration to runtime location
cp /usr/local/etc/haproxy-default/haproxy.cfg /etc/haproxy/haproxy.cfg
echo "Configuration copied to /etc/haproxy/haproxy.cfg"

# Ensure the socket directory exists and has correct permissions
mkdir -p /etc/haproxy
chown haproxy:haproxy /etc/haproxy

# Check if we should start HAProxy or pass through other commands
if [ "$1" = "haproxy" ] || [ $# -eq 0 ]; then
    echo "Starting HAProxy in master-worker mode..."
    # Start HAProxy in master-worker mode with management socket
    exec haproxy -W -db -S "/etc/haproxy/haproxy-master.sock" -- /etc/haproxy/haproxy.cfg
else
    echo "Executing: $@"
    exec "$@"
fi