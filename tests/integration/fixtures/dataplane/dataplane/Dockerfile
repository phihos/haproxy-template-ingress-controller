FROM haproxytech/haproxy-alpine:3.1

# Install curl for healthchecks (nc is already available in busybox)
RUN apk add --no-cache curl

# Copy dataplane API configuration
COPY dataplaneapi.yaml /usr/local/etc/haproxy-default/dataplaneapi.yaml

# Copy entrypoint script
COPY haproxy-socket-reload.sh /usr/local/bin/haproxy-socket-reload.sh
RUN chmod +x /usr/local/bin/haproxy-socket-reload.sh

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["dataplaneapi"]