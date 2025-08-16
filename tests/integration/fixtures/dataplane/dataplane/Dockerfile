FROM haproxytech/haproxy-ubuntu

# Install socat for socket-based communication and curl for healthchecks
RUN apt-get update && apt-get install -y socat curl strace && rm -rf /var/lib/apt/lists/*

# Copy dataplane API configuration
COPY dataplaneapi.yml /usr/local/etc/haproxy-default/dataplaneapi.yml

# Copy entrypoint script
COPY haproxy-socket-reload.sh /usr/local/bin/haproxy-socket-reload.sh
RUN chmod +x /usr/local/bin/haproxy-socket-reload.sh

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["dataplaneapi"]