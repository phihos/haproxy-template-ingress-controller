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
# Dump complete controller state
kubectl exec deployment/haproxy-template-ic -- \
  socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock <<< "dump all" | jq '.'

# Check rendered configuration
kubectl exec deployment/haproxy-template-ic -- \
  socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock <<< "dump config" | jq '.haproxy_config'
```

## Common Issues

### Template Rendering Failures

**Symptoms**: Error logs showing "Template rendering failed"

**Diagnosis**:
```bash
# Check for template syntax errors
kubectl logs deployment/haproxy-template-ic | grep -A5 "TemplateSyntaxError"

# Verify resources are being watched
kubectl exec deployment/haproxy-template-ic -- \
  socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock <<< "dump indices" | jq 'keys'
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
4. Confirm HAProxy 3.1+ for fast startup

### Resources Deleted While In Use

**Symptoms**: HAProxy backends disappear, 503 errors

**Diagnosis**:
```bash
# Check for deleted resources
kubectl get events --sort-by='.lastTimestamp' | grep -i delete

# Compare current state with rendered config
kubectl exec deployment/haproxy-template-ic -- \
  socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock <<< "dump indices" | \
  jq '.services_index | length'
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

# View resource count
kubectl exec deployment/haproxy-template-ic -- \
  socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock <<< "dump indices" | \
  jq 'to_entries | map({key: .key, count: (.value | length)})'
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