#!/bin/bash
set -e

echo "Starting HAProxy entrypoint script..."

# Copy default configuration to runtime location
cp /usr/local/etc/haproxy-default/dataplaneapi.yaml /etc/haproxy/dataplaneapi.yaml
cp /usr/local/etc/haproxy-default/dataplaneapi.yaml /etc/haproxy/dataplaneapi.yaml
echo "Configuration copied to /etc/haproxy/dataplaneapi.yaml"

# Ensure the socket directory exists and has correct permissions
mkdir -p /etc/haproxy
chown -R haproxy:haproxy /etc/haproxy

# Check if we should start HAProxy or pass through other commands
if [ "$1" = "dataplaneapi" ] || [ $# -eq 0 ]; then
    echo "Starting HAProxy Dataplane API..."
    # Start HAProxy Dataplane API
    exec /usr/local/bin/dataplaneapi
else
    echo "Executing: $@"
    exec "$@"
fi