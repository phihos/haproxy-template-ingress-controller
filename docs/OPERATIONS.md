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
- `haproxy_template_ic_rendered_templates_total` - Template render count
- `haproxy_template_ic_template_render_duration_seconds` - Render time
- `haproxy_template_ic_dataplane_api_duration_seconds` - Dataplane API time
- `haproxy_template_ic_errors_total` - Error count by type

### Health Check

Port 8080 health endpoint:

```bash
kubectl port-forward deployment/haproxy-template-ic 8080:8080
curl http://localhost:8080/healthz
```

### Runtime Inspection

Check logs for detailed information:

```bash
# Check logs for detailed information
kubectl logs -f deployment/haproxy-template-ic
```

### Structured Logging

Enable JSON logging in the ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: haproxy-template-ic-config
data:
  config: |
    logging:
      structured: true  # Enable JSON structured logging
      verbose: 1        # Log level (0=WARNING, 1=INFO, 2=DEBUG)
```

View logs:

```bash
kubectl logs deployment/haproxy-template-ic -f

# JSON output with jq
kubectl logs deployment/haproxy-template-ic | jq '.'
```

### OpenTelemetry Tracing

Enable distributed tracing in the ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: haproxy-template-ic-config
data:
  config: |
    tracing:
      enabled: true                             # Enable OpenTelemetry tracing
      jaeger_endpoint: "jaeger:14268"          # Jaeger collector endpoint
      sample_rate: 0.1                         # 10% sampling for reduced overhead
      console_export: false                    # Console export for debugging
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

# Inspect current logs for state information
kubectl logs deployment/haproxy-template-ic | grep "rendered template"
```

### Debug Mode

Enable debug logging in the ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: haproxy-template-ic-config
data:
  config: |
    logging:
      verbose: 2        # DEBUG level (0=WARNING, 1=INFO, 2=DEBUG)
      structured: false # Human readable format for debugging

    # Optional: Enable debug console tracing
    tracing:
      enabled: true
      console_export: true  # Print traces to console for debugging
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

# Backup configuration (ConfigMap)
kubectl get configmap haproxy-template-ic-config -o yaml > backup-config.yaml

# Restore
kubectl apply -f backup-config.yaml
kubectl rollout restart deployment/haproxy-template-ic
```