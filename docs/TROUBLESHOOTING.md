# Troubleshooting

## Diagnostic Commands

### Check Controller Status

```bash
# Controller logs with error filtering
kubectl logs deployment/haproxy-template-ic --tail=50 | grep -E "(ERROR|FATAL)"

# Full logs with timestamps
kubectl logs deployment/haproxy-template-ic --timestamps=true

# Follow logs in real-time
kubectl logs deployment/haproxy-template-ic -f
```

### Test Connectivity

```bash
# Test Dataplane API from controller
kubectl exec deployment/haproxy-template-ic -- \
  wget -qO- --timeout=5 http://haproxy:5555/v3/services/haproxy/info

# Test from local machine
kubectl port-forward deployment/haproxy 5555:5555
curl -u admin:adminpass http://localhost:5555/v3/services/haproxy/info
```

### Inspect State

```bash
# Check logs for configuration details
kubectl logs deployment/haproxy-template-ic | grep "template render"
```

## Common Issues

### Template Rendering Failures

**Symptoms**: Error logs showing "Template rendering failed"

**Diagnosis**:
```bash
# Check for template syntax errors
kubectl logs deployment/haproxy-template-ic | grep -A5 "TemplateSyntaxError"

# Verify resources are being watched in logs
kubectl logs deployment/haproxy-template-ic | grep "watching resource"
```

**Resolution**:
1. Fix Jinja2 syntax errors in ConfigMap
2. Ensure all referenced snippets exist
3. Verify resource access patterns match actual resource structure

### Validation HAProxy Won't Start

**Symptoms**: Validation sidecar crashes, "validation failed" errors

**Diagnosis**:
```bash
# Check validation HAProxy logs
kubectl logs deployment/haproxy-template-ic -c validation-haproxy --tail=50

# Check validation Dataplane API logs
kubectl logs deployment/haproxy-template-ic -c validation-dataplane --tail=50
```

**Resolution**:
1. Ensure HAProxy config has required health frontend on port 8404
2. Check for HAProxy syntax errors in rendered config
3. Verify validation containers have correct image version (3.1+)

### Dataplane API Unreachable

**Symptoms**: "connection refused" or timeout errors

**Diagnosis**:
```bash
# Check if Dataplane API is running
kubectl get pods -l app=haproxy -o json | jq '.items[].status.containerStatuses[] | select(.name=="dataplane")'

# Test direct connectivity
kubectl exec deployment/haproxy -c dataplane -- ps aux | grep dataplane

# Check credentials
kubectl exec deployment/haproxy-template-ic -- env | grep -E "(DATAPLANE_USER|DATAPLANE_PASS)"
```

**Resolution**:
1. Ensure Dataplane API container is running
2. Verify port 5555 is exposed
3. Check authentication credentials match (admin/adminpass for production)

### Test Timing Issues

**Symptoms**: E2E tests fail with "Expected log line not found" or timing-related assertion errors

**Diagnosis**:
```python
# Check if tests are looking for old logs instead of new ones
assert_log_line(operator, "Config loaded")  # May find old log

# Use millisecond timing for precision
assert_log_line(operator, "Config loaded", since_milliseconds=100)  # Correct
```

**Resolution**:
1. Use `since_milliseconds` parameter for time-sensitive assertions
2. Avoid checking old logs for events that should be recent
3. Use appropriate timeouts for operations (100-500ms for config changes)
4. Check operator health with `assert_operator_health()` before assertions

### ConfigMap Reload Loops

**Symptoms**: Continuous "Config has changed: reloading" messages in logs, operator never stabilizes

**Diagnosis**:
```bash
# Check for repeated reload messages
kubectl logs deployment/haproxy-template-ic | grep -c "Config has changed: reloading"

# Enable debug logging to see configuration comparison
kubectl patch configmap haproxy-template-ic-config --patch '
data:
  config: |
    logging:
      structured: true
    # ... rest of config
'
```

**Resolution**:
1. **Fixed automatically** - Modern operator uses DeepDiff for accurate change detection
2. Identical configurations no longer trigger unnecessary reloads  
3. Check structured logs for configuration diff details
4. Verify ConfigMap updates contain actual content changes, not just metadata updates

### Package Import Issues

**Symptoms**: ImportError or ModuleNotFoundError after code updates

**Diagnosis**:
```python
# Old import paths (still work via compatibility layer)
from haproxy_template_ic.config_models import Config

# New modular import paths
from haproxy_template_ic.models.config import Config
```

**Resolution**:
1. **Backward compatibility maintained** - Old imports continue working
2. New code should use modular import paths for better organization
3. Run `uv sync` to ensure all dependencies are updated
4. Check for any cached bytecode: `find . -name "*.pyc" -delete`
4. Confirm HAProxy 3.1+ for fast startup

### Resources Deleted While In Use

**Symptoms**: HAProxy backends disappear, 503 errors

**Diagnosis**:
```bash
# Check for deleted resources
kubectl get events --sort-by='.lastTimestamp' | grep -i delete

# Check current resource counts in logs
kubectl logs deployment/haproxy-template-ic | grep "indexed resources"
```

**Resolution**:
1. Controller will automatically reconcile on next timer (default 30s)
2. Force immediate reconciliation by updating ConfigMap
3. Implement graceful deletion handling in templates

## Recovery Procedures

### Complete Reset

```bash
# 1. Delete controller
kubectl delete deployment haproxy-template-ic

# 2. Delete HAProxy pods
kubectl delete deployment haproxy

# 3. Verify ConfigMap is correct
kubectl get cm haproxy-config -o yaml

# 4. Redeploy in order
kubectl apply -f haproxy-deployment.yaml
kubectl wait --for=condition=ready pod -l app=haproxy --timeout=60s
kubectl apply -f controller-deployment.yaml
```

### Force Configuration Sync

```bash
# Trigger reconciliation by annotation change
kubectl annotate cm haproxy-config force-sync="$(date +%s)" --overwrite

# Monitor sync progress
kubectl logs deployment/haproxy-template-ic -f | grep -E "(Reconciling|Synchronized)"
```

### Debug Mode

```bash
# Enable debug logging
kubectl set env deployment/haproxy-template-ic VERBOSE=2

# Enable structured logging for parsing
kubectl set env deployment/haproxy-template-ic STRUCTURED_LOGGING=true

# View structured logs
kubectl logs deployment/haproxy-template-ic | jq 'select(.level=="DEBUG")'
```

## Performance Issues

### Slow Template Rendering

**Diagnosis**:
```bash
# Check rendering metrics
kubectl port-forward deployment/haproxy-template-ic 9090:9090
curl -s http://localhost:9090/metrics | grep template_render_duration
```

**Resolution**:
1. Simplify template logic
2. Use indexed lookups instead of iteration
3. Enable field filtering to reduce resource size

### High Memory Usage

**Diagnosis**:
```bash
# Check memory consumption
kubectl top pod -l app=haproxy-template-ic

# Check resource counts in logs
kubectl logs deployment/haproxy-template-ic | grep "resource count"
```

**Resolution**:
1. Add field filtering in ConfigMap:
   ```yaml
   watched_resources_ignore_fields:
     - metadata.managedFields
     - status
   ```
2. Reduce watched resource types
3. Increase memory limits if necessary