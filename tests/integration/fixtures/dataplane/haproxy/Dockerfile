FROM haproxytech/haproxy-ubuntu

# Install socat for socket-based communication and curl for healthchecks
RUN apt-get update && apt-get install -y socat curl && rm -rf /var/lib/apt/lists/*

# Copy default HAProxy configuration
COPY haproxy-default.cfg /usr/local/etc/haproxy-default/haproxy.cfg

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["haproxy"]