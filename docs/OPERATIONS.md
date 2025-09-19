# Operations

This document provides information for deploying, monitoring, and maintaining the controller in production environments.
It covers observability, troubleshooting, and recovery procedures to ensure the reliability and efficiency of your
ingress infrastructure.

## Contents

- [Monitoring and Observability](#monitoring-and-observability)
- [Production Deployment](#production-deployment)
- [Error Recovery](#error-recovery)
- [Performance Optimization](#performance-optimization)

## Monitoring and Observability

### Prometheus Metrics

**Structured Logging**: Uses structlog with operation correlation, component context, JSON output (set `logging.structured: true` in ConfigMap)

**Prometheus Metrics**: Port 9090, tracks application/resources/templates/dataplane/errors

```bash
# Port forward metrics
kubectl port-forward deployment/haproxy-template-ic 9090:9090

# View all metrics
curl http://localhost:9090/metrics

# Key metrics to monitor
curl http://localhost:9090/metrics | grep -E "(haproxy_template_ic_|up|process_)"
```

**Important metrics**:
- `haproxy_template_ic_resources_total`: Resource counts by type
- `haproxy_template_ic_template_renders_total`: Template rendering frequency
- `haproxy_template_ic_dataplane_requests_total`: API request patterns
- `haproxy_template_ic_errors_total`: Error tracking by component
- `haproxy_template_ic_dataplane_pool_*`: Connection pool health and statistics

### Health Endpoints

```bash
# Health check
kubectl port-forward deployment/haproxy-template-ic 8080:8080
curl http://localhost:8080/healthz

# Metrics endpoint
curl http://localhost:9090/metrics
```

### Connection Pool Monitoring

Monitor dataplane API connection pool health for debugging connectivity issues:

```bash
# View pool metrics
curl http://localhost:9090/metrics | grep dataplane_pool

# Key pool metrics
curl http://localhost:9090/metrics | grep -E "(active_connections|total_references|clients_created|clients_cleaned)"
```

**Pool metrics**:
- `haproxy_template_ic_dataplane_pool_active_connections`: Current active connections
- `haproxy_template_ic_dataplane_pool_total_references`: Total connection references in use
- `haproxy_template_ic_dataplane_pool_clients_created_total`: Cumulative clients created
- `haproxy_template_ic_dataplane_pool_clients_reused_total`: Cumulative clients reused
- `haproxy_template_ic_dataplane_pool_clients_cleaned_total`: Cumulative clients cleaned up
- `haproxy_template_ic_dataplane_pool_cleanup_runs_total`: Pool cleanup operations

**Monitoring queries**:
```promql
# Connection pool utilization rate
rate(haproxy_template_ic_dataplane_pool_clients_reused_total[5m]) / 
rate(haproxy_template_ic_dataplane_pool_clients_created_total[5m])

# Pool cleanup efficiency
rate(haproxy_template_ic_dataplane_pool_clients_cleaned_total[5m])

# Active connections per instance
haproxy_template_ic_dataplane_pool_active_connections
```

### Distributed Tracing

OpenTelemetry tracing for end-to-end observability across template rendering and deployment pipeline.

**Development setup**:
```yaml
tracing:
  enabled: true
  console_export: true  # Console output for development
  sample_rate: 1.0     # Trace all operations
```

**Production setup**:
```yaml
tracing:
  enabled: true
  jaeger_endpoint: "jaeger-collector:14268"
  sample_rate: 0.1     # Sample 10% for reduced overhead
  console_export: false
```

**Operations traced**: Template rendering, dataplane API, Kubernetes operations, pod discovery

### Structured Logging

Enable JSON output for production log aggregation:

```yaml
logging:
  structured: true    # Enable JSON structured logging output
  verbose: 1         # Log level (0=WARNING, 1=INFO, 2=DEBUG)
```

**Log analysis**:
```bash
# Real-time logs with JSON parsing
kubectl logs -f deployment/haproxy-template-ic | jq .

# Filter for errors
kubectl logs deployment/haproxy-template-ic | jq 'select(.level=="ERROR")'

# Track template rendering
kubectl logs deployment/haproxy-template-ic | jq 'select(.event=="template_rendered")'
```

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

# Check index initialization status
kubectl logs deployment/haproxy-template-ic | grep -E "(Index.*complete|initialization.*timeout)"
```

### Startup Issues

#### Index Initialization Delays

During startup, the controller waits for all Kopf indices to be initialized before template rendering begins.

**Normal startup logs**:
```
Index synchronization tracker initialized for 4 resource types with 5s timeout
Event handler called for services
Event handler called for ingresses  
Index initialization complete - tracking disabled
```

**Common issues**:

1. **Slow startup (> 30 seconds)**:
   ```bash
   # Check which indices are pending
   kubectl logs deployment/haproxy-template-ic | grep "ready via timeout"
   
   # Possible causes:
   # - No matching resources exist (expected, will timeout after 5s)
   # - Network issues preventing API calls
   # - RBAC permissions missing for resource types
   ```

2. **Startup hangs indefinitely**:
   ```bash
   # Check resource permissions
   kubectl auth can-i list ingresses --as system:serviceaccount:default:haproxy-template-ic
   
   # Verify resource selectors
   kubectl get pods -l app=haproxy  # Should match pod_selector in config
   ```

3. **Faster startup needed**:
   ```yaml
   # Reduce timeout in ConfigMap
   operator:
     index_initialization_timeout: 2  # Faster for development
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
# Check memory usage
kubectl top pod -l app=haproxy-template-ic

# Reduce memory by ignoring unnecessary fields:
watched_resources_ignore_fields:
  - metadata.managedFields         # Large server-side apply metadata
  - status                        # If not used in templates
  - metadata.annotations['kubectl.kubernetes.io/last-applied-configuration']  # Can be very large
```

## Error Recovery

**Error recovery**: Graceful degradation, validation isolation, state consistency, operational visibility

**Validation-first approach**: Configuration tested before production deployment

**Robust deployment**: Smart change detection, version tracking, deployment rollback

### Recovery Procedures

```bash
# Restart controller
kubectl rollout restart deployment/haproxy-template-ic

# Reset ConfigMap if corrupted
kubectl patch configmap haproxy-template-ic-config --patch '{"data":null}'
kubectl apply -f your-good-config.yaml

# Check HAProxy pod health
kubectl get pods -l app=haproxy -o wide
kubectl describe pod -l app=haproxy
```

## Performance Optimization

### Runtime API Optimization for Zero-Reload Deployments

The controller optimizes deployments by separating runtime-eligible operations from configuration operations to avoid unnecessary HAProxy reloads.

**Benefits**: Zero reloads for most server operations, instant updates for map/ACL entries, improved availability, smart fallback to transaction/reload for complex configurations.

**Monitoring**: Look for "server added through runtime" log messages from dataplane API.

### Template Rendering Performance

```yaml
# Optimize template rendering intervals
template_rendering:
  min_render_interval: 5   # Minimum seconds between renders (rate limiting)
  max_render_interval: 60  # Maximum seconds without render (guaranteed refresh)
```

**Environment-specific settings**:

**Production (High Change Rate)**:
```yaml
template_rendering:
  min_render_interval: 5   # Protect against rapid changes
  max_render_interval: 60  # Balance freshness with stability
```

**Production (Low Change Rate)**:
```yaml
template_rendering:
  min_render_interval: 10  # Conservative rate limiting
  max_render_interval: 300 # 5 minutes for stable environments
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
        - namespaceSelector: { }
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