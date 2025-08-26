# Operations

## Monitoring

### Prometheus Metrics

Port 9090 exposes metrics:

```bash
# Port forward
kubectl port-forward deployment/haproxy-template-ic 9090:9090

# View metrics
curl http://localhost:9090/metrics
```

Key metrics:
- `haproxy_template_ic_reconciliations_total` - Reconciliation count
- `haproxy_template_ic_template_render_duration_seconds` - Render time
- `haproxy_template_ic_dataplane_sync_duration_seconds` - Sync time
- `haproxy_template_ic_errors_total` - Error count by type

### Health Check

Port 8080 health endpoint:

```bash
kubectl port-forward deployment/haproxy-template-ic 8080:8080
curl http://localhost:8080/healthz
```

### Management Socket

**Security Warning**: The management socket exposes sensitive configuration and resource data. Ensure proper RBAC and pod security policies are in place.

Runtime inspection via Unix socket:

```bash
# Dump all state
kubectl exec -it deployment/haproxy-template-ic -- \
  socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock <<< "dump all"

# Show resource indices
kubectl exec -it deployment/haproxy-template-ic -- \
  socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock <<< "dump indices"

# Show rendered config
kubectl exec -it deployment/haproxy-template-ic -- \
  socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock <<< "dump config"
```

### Structured Logging

Enable JSON logging for aggregation:

```yaml
env:
- name: STRUCTURED_LOGGING
  value: "true"
- name: VERBOSE
  value: "1"  # 0=WARNING, 1=INFO, 2=DEBUG
```

View logs:

```bash
kubectl logs deployment/haproxy-template-ic -f

# JSON output with jq
kubectl logs deployment/haproxy-template-ic | jq '.'
```

### OpenTelemetry Tracing

Enable distributed tracing:

```yaml
env:
- name: TRACING_ENABLED
  value: "true"
- name: JAEGER_ENDPOINT
  value: "http://jaeger:14268/api/traces"
- name: TRACING_SAMPLE_RATE
  value: "0.1"  # 10% sampling for production
```

## Troubleshooting

### Quick Diagnostics

For comprehensive troubleshooting, see [Troubleshooting Guide](TROUBLESHOOTING.md).

```bash
# Check controller health
kubectl logs deployment/haproxy-template-ic --tail=50 | grep -E "(ERROR|FATAL)"

# Test Dataplane API
kubectl exec deployment/haproxy-template-ic -- \
  wget -qO- --timeout=5 http://haproxy:5555/v3/services/haproxy/info

# Inspect current state
kubectl exec deployment/haproxy-template-ic -- \
  socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock <<< "dump config" | jq '.'
```

### Debug Mode

Enable debug logging:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: debug-config
data:
  DEBUG: "true"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: haproxy-template-ic
spec:
  template:
    spec:
      containers:
      - name: controller
        env:
        - name: VERBOSE
          value: "2"  # DEBUG level
        - name: STRUCTURED_LOGGING
          value: "false"  # Human readable
```

### Performance Issues

#### Slow Reconciliation

```bash
# Check metrics
curl http://localhost:9090/metrics | grep duration

# Common causes:
# - Large number of resources
# - Complex templates
# - Network latency to Dataplane API
```

Solutions:
- Use field filtering to reduce resource size
- Optimize template logic
- Increase reconciliation interval

#### High Memory Usage

```bash
# Check memory
kubectl top pod -l app=haproxy-template-ic

# Reduce memory:
watched_resources_ignore_fields:
  - metadata.managedFields
  - status
  - metadata.annotations
```

#### Dataplane API Slow Startup

**Critical**: Use HAProxy 3.1+

Version comparison:
- HAProxy 3.0: 30-60 second startup
- HAProxy 3.1+: 3-5 second startup

```yaml
# Correct image
image: haproxytech/haproxy-alpine:3.1

# Adjust probe for version
livenessProbe:
  failureThreshold: 3  # Works with 3.1
  # failureThreshold: 10  # Required for 3.0
```

## Production Deployment

### Resource Limits

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### High Availability

```yaml
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: haproxy-template-ic
spec:
  podSelector:
    matchLabels:
      app: haproxy-template-ic
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: prometheus
    ports:
    - port: 9090  # Metrics
  - from:
    - namespaceSelector: {}
    ports:
    - port: 9443  # Webhook
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: haproxy
    ports:
    - port: 5555  # Dataplane API
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - port: 443  # Kubernetes API
```

### Monitoring Setup

```yaml
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: haproxy-template-ic
spec:
  selector:
    matchLabels:
      app: haproxy-template-ic
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

### Backup and Recovery

```bash
# Backup ConfigMap
kubectl get cm haproxy-config -o yaml > backup-config.yaml

# Backup rendered config
kubectl exec deployment/haproxy-template-ic -- \
  socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock <<< "dump config" \
  > backup-rendered.json

# Restore
kubectl apply -f backup-config.yaml
kubectl rollout restart deployment/haproxy-template-ic
```