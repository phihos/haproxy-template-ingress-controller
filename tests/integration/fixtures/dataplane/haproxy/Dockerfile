FROM haproxytech/haproxy-alpine:3.1

# Install curl for healthchecks (nc is already available in busybox)
RUN apk add --no-cache curl

# Copy default HAProxy configuration
COPY haproxy-default.cfg /usr/local/etc/haproxy-default/haproxy.cfg

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["haproxy"]