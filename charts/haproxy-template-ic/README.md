# HAProxy Template Ingress Controller Helm Chart

This Helm chart deploys the HAProxy Template Ingress Controller, which manages HAProxy configurations dynamically based on Kubernetes resources.

## Overview

The HAProxy Template Ingress Controller:
- Watches Kubernetes Ingress and/or Gateway API resources
- Renders Jinja2 templates to generate HAProxy configurations
- Deploys configurations to HAProxy pods via Dataplane API
- Supports cross-namespace HAProxy pod management
- Template library system for modular feature support
- Conditional resource watching based on enabled features

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- HAProxy pods with Dataplane API sidecars (deployed separately)

## Installation

### Basic Installation

```bash
helm install my-controller ./charts/haproxy-template-ic
```

### With Custom Values

```bash
helm install my-controller ./charts/haproxy-template-ic \
  --set image.tag=v0.1.0 \
  --set replicaCount=2
```

### With Custom Values File

```bash
helm install my-controller ./charts/haproxy-template-ic \
  -f my-values.yaml
```

## Configuration

### Key Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of controller replicas (2+ recommended for HA) | `2` |
| `image.repository` | Controller image repository | `ghcr.io/phihos/haproxy-template-ic` |
| `image.tag` | Controller image tag | Chart appVersion |
| `controller.templateLibraries.ingress.enabled` | Enable Ingress resource support | `true` |
| `controller.templateLibraries.gateway.enabled` | Enable Gateway API support (HTTPRoute, GRPCRoute) | `false` |
| `ingressClass.enabled` | Create IngressClass resource | `true` |
| `ingressClass.name` | IngressClass name | `haproxy` |
| `gatewayClass.enabled` | Create GatewayClass resource | `true` |
| `gatewayClass.name` | GatewayClass name | `haproxy` |
| `controller.debugPort` | Debug HTTP server port (0=disabled) | `0` |
| `controller.config.pod_selector` | Labels to match HAProxy pods | `{app: haproxy, component: loadbalancer}` |
| `controller.config.logging.verbose` | Log level (0=WARN, 1=INFO, 2=DEBUG) | `1` |
| `credentials.dataplane.username` | Dataplane API username | `admin` |
| `credentials.dataplane.password` | Dataplane API password | `adminpass` |
| `networkPolicy.enabled` | Enable NetworkPolicy | `true` |

### Controller Configuration

The controller configuration is defined in `controller.config` and includes:

- **pod_selector**: Labels to identify HAProxy pods to manage
- **watched_resources**: Kubernetes resources to watch (Ingress, Service, EndpointSlice, Secret)
- **template_snippets**: Reusable Jinja2 template fragments
- **maps**: HAProxy map file templates
- **files**: Auxiliary files (error pages, etc.)
- **haproxy_config**: Main HAProxy configuration template

Example custom configuration:

```yaml
controller:
  config:
    pod_selector:
      match_labels:
        app: my-haproxy
        environment: production

    watched_resources:
      ingresses:
        api_version: networking.k8s.io/v1
        kind: Ingress
        index_by: ["metadata.namespace", "metadata.name"]
```

### Ingress Class Filtering

By default, the controller only watches Ingress resources with `spec.ingressClassName: haproxy`. This ensures the controller only processes ingresses intended for it.

**Default behavior:**
```yaml
controller:
  config:
    watched_resources:
      ingresses:
        fieldSelector: "spec.ingressClassName=haproxy"
```

**To change the ingress class name:**
```yaml
controller:
  config:
    watched_resources:
      ingresses:
        fieldSelector: "spec.ingressClassName=my-custom-class"
```

**To watch all ingresses regardless of class:**
```yaml
controller:
  config:
    watched_resources:
      ingresses:
        fieldSelector: ""
```

The field selector uses Kubernetes server-side filtering for efficient resource watching. Only ingresses matching the specified `spec.ingressClassName` will be processed by the controller.

## Template Libraries

The controller uses a template library system for modular feature support. Libraries are merged in order: base → ingress → gateway → haproxytech → user values.

### Available Libraries

**Base Library** (always enabled)
- Resource-agnostic HAProxy core configuration
- Error pages and plugin orchestration
- Uses `resource_*` patterns to discover implementations

**Ingress Library** (enabled by default)
- Kubernetes Ingress resource support (networking.k8s.io/v1)
- Path matching, host-based routing, backend management
- Watched resources: `ingresses` (filtered by `spec.ingressClassName`)

**Gateway Library** (disabled by default)
- Kubernetes Gateway API support (gateway.networking.k8s.io/v1)
- HTTPRoute and GRPCRoute routing with advanced features
- Watched resources: `httproutes`, `grpcroutes`

**HAProxyTech Library** (enabled by default)
- Support for haproxy.org/* annotations
- Works with both Ingress and Gateway API resources

### Enabling Gateway API Support

To enable Gateway API support:

```yaml
controller:
  templateLibraries:
    gateway:
      enabled: true
```

This automatically:
- Adds HTTPRoute and GRPCRoute to watched resources
- Grants necessary RBAC permissions (via ClusterRole)
- Includes Gateway API routing templates

### Gateway API Features

When the gateway library is enabled, the controller supports:

**HTTPRoute:**
- Path matching (Exact, PathPrefix)
- Host-based routing via `hostnames`
- Traffic splitting with `backendRefs` weights
- Header matching (future)
- Query parameter matching (future)

**GRPCRoute:**
- gRPC method matching
- Host-based routing
- Traffic splitting with server weights
- HTTP/2 backend connections

**Example HTTPRoute:**

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: example-route
spec:
  hostnames:
    - "example.com"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /api
      backendRefs:
        - name: api-service-v1
          port: 8080
          weight: 90
        - name: api-service-v2
          port: 8080
          weight: 10
```

This creates an HAProxy backend with 90/10 traffic split using server weights.

### Conditional Resource Watching

Watched resources are determined by enabled libraries:

| Library | Enabled | Watched Resources |
|---------|---------|-------------------|
| ingress | `true` (default) | ingresses |
| gateway | `false` (default) | - |
| gateway | `true` | httproutes, grpcroutes |

Core resources (services, endpoints, secrets) are always watched.

## IngressClass

The chart automatically creates an IngressClass resource when the ingress library is enabled and Kubernetes 1.18+ is detected.

### Configuration

```yaml
ingressClass:
  enabled: true       # Create IngressClass (default: true)
  name: haproxy       # IngressClass name
  default: false      # Mark as cluster default
  controllerName: haproxy-template-ic.github.io/controller
```

### Capability Detection

The chart uses `Capabilities.APIVersions.Has` to check for `networking.k8s.io/v1/IngressClass`. If the API is not available (Kubernetes < 1.18), the resource is silently skipped without error.

### Creation Conditions

IngressClass is created only when ALL of the following are true:
1. `ingressClass.enabled: true` (default)
2. `controller.templateLibraries.ingress.enabled: true` (default)
3. `networking.k8s.io/v1/IngressClass` API exists in cluster

### Multi-Controller Environments

When running multiple ingress controllers:

**Ensure unique identification:**
```yaml
# Controller 1 (haproxy-template-ic)
ingressClass:
  name: haproxy
  controllerName: haproxy-template-ic.github.io/controller

# Controller 2 (nginx)
ingressClass:
  name: nginx
  controllerName: k8s.io/ingress-nginx
```

**Only one should be default:**
```yaml
# Set default on one controller only
ingressClass:
  default: true  # Only on ONE controller
```

### Disabling IngressClass Creation

If you manage IngressClass resources separately or use an external tool:

```yaml
ingressClass:
  enabled: false
```

### Using IngressClass

Ingress resources reference the IngressClass via `spec.ingressClassName`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: example
spec:
  ingressClassName: haproxy  # References IngressClass.metadata.name
  rules:
    - host: example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: example-service
                port:
                  number: 80
```

## GatewayClass

The chart automatically creates a GatewayClass resource when the gateway library is enabled and Gateway API CRDs are installed.

### Prerequisites

Install Gateway API CRDs (standard channel) before enabling the gateway library:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.0/standard-install.yaml
```

### Configuration

```yaml
controller:
  templateLibraries:
    gateway:
      enabled: true

gatewayClass:
  enabled: true
  name: haproxy
  default: false
  controllerName: haproxy-template-ic.github.io/controller
  parametersRef:
    group: haproxy-template-ic.github.io
    kind: HAProxyTemplateConfig
    name: ""        # Defaults to controller.crdName
    namespace: ""   # Defaults to Release.Namespace
```

### Capability Detection

The chart checks for `gateway.networking.k8s.io/v1/GatewayClass` before creating the resource. If Gateway API CRDs are not installed, the resource is silently skipped without error.

### Creation Conditions

GatewayClass is created only when ALL of the following are true:
1. `gatewayClass.enabled: true` (default)
2. `controller.templateLibraries.gateway.enabled: true` (must be explicitly enabled)
3. `gateway.networking.k8s.io/v1/GatewayClass` API exists in cluster

### parametersRef - Controller Configuration Link

The GatewayClass automatically references the HAProxyTemplateConfig created by this chart via `parametersRef`. This links Gateway API configuration to the controller's template-based configuration system.

**How it works:**
1. GatewayClass points to HAProxyTemplateConfig via `spec.parametersRef`
2. Controller reads HAProxyTemplateConfig for template snippets, maps, watched resources, and HAProxy configuration
3. Gateway API consumers get the same routing capabilities as Ingress consumers

**Default behavior:**
- `parametersRef.name` defaults to `controller.crdName` (typically `haproxy-template-ic-config`)
- `parametersRef.namespace` defaults to chart's release namespace

**Inspect the reference:**
```bash
kubectl get gatewayclass haproxy -o yaml
```

### Multi-Controller Environments

When running multiple Gateway API controllers:

**Ensure unique identification:**
```yaml
# Controller 1 (haproxy-template-ic)
gatewayClass:
  name: haproxy
  controllerName: haproxy-template-ic.github.io/controller

# Controller 2 (nginx-gateway-fabric)
gatewayClass:
  name: nginx
  controllerName: gateway.nginx.org/nginx-gateway-controller
```

**Only one should be default:**
```yaml
# Set default on one controller only
gatewayClass:
  default: true  # Only on ONE controller
```

### Advanced: Multiple GatewayClasses

You can create multiple GatewayClasses pointing to different HAProxyTemplateConfig resources for different routing scenarios (e.g., internet-facing vs internal):

```bash
# Install chart with default config
helm install haproxy-internet ./charts/haproxy-template-ic

# Create separate HAProxyTemplateConfig for internal traffic with different templates
kubectl apply -f - <<EOF
apiVersion: haproxy-template-ic.github.io/v1alpha1
kind: HAProxyTemplateConfig
metadata:
  name: haproxy-internal-config
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: haproxy-internal
  # ... different template configuration ...
EOF

# Create additional GatewayClass pointing to the internal config
kubectl apply -f - <<EOF
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: haproxy-internal
spec:
  controllerName: haproxy-template-ic.github.io/controller
  parametersRef:
    group: haproxy-template-ic.github.io
    kind: HAProxyTemplateConfig
    name: haproxy-internal-config
    namespace: default
EOF
```

### Using GatewayClass

Gateway resources reference the GatewayClass, and HTTPRoutes attach to Gateways:

**1. Create a Gateway:**
```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: example-gateway
spec:
  gatewayClassName: haproxy  # References GatewayClass.metadata.name
  listeners:
    - name: http
      protocol: HTTP
      port: 80
```

**2. Create HTTPRoutes that attach to the Gateway:**
```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: example-route
spec:
  parentRefs:
    - name: example-gateway  # References Gateway.metadata.name
  hostnames:
    - "example.com"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: example-service
          port: 80
```

### Disabling GatewayClass Creation

If you manage GatewayClass resources separately:

```yaml
gatewayClass:
  enabled: false
```

## Resource Limits and Cloud-Native Behavior

The controller automatically detects and respects container resource limits for optimal cloud-native operation:

### CPU Limits (GOMAXPROCS)

**Go 1.25+ Native Support**: The controller uses Go 1.25, which includes built-in container-aware GOMAXPROCS. The Go runtime automatically:
- Detects cgroup CPU limits (v1 and v2)
- Sets GOMAXPROCS to match the container's CPU limit (not the host's core count)
- Dynamically adjusts if CPU limits change at runtime

No configuration needed - this works automatically when you set CPU limits in the deployment.

### Memory Limits (GOMEMLIMIT)

**automemlimit Library**: The controller uses the `automemlimit` library to automatically set GOMEMLIMIT based on cgroup memory limits. By default:
- Sets GOMEMLIMIT to 90% of the container memory limit
- Leaves 10% headroom for non-heap memory sources
- Works with both cgroups v1 and v2

### Configuration

Set resource limits in your values file:

```yaml
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

The controller will automatically log the detected limits at startup:

```
INFO HAProxy Template Ingress Controller starting ... gomaxprocs=1 gomemlimit="461373644 bytes (440.00 MiB)"
```

### Fine-Tuning Memory Limits

The `AUTOMEMLIMIT` environment variable can adjust the memory limit ratio (default: 0.9):

```yaml
# In deployment.yaml or via Helm values
env:
  - name: AUTOMEMLIMIT
    value: "0.8"  # Set GOMEMLIMIT to 80% of container limit
```

Valid range: 0.0 < AUTOMEMLIMIT ≤ 1.0

### Why This Matters

- **Prevents OOM kills**: GOMEMLIMIT helps the Go GC keep heap memory under control
- **Reduces CPU throttling**: Proper GOMAXPROCS prevents over-scheduling goroutines
- **Improves performance**: Better GC tuning and reduced context switching
- **Cloud-native best practice**: Industry standard for containerized Go applications in 2025

## NetworkPolicy Configuration

The controller requires network access to:
1. Kubernetes API Server (watch resources)
2. HAProxy Dataplane API pods in ANY namespace
3. DNS (CoreDNS/kube-dns)

### Default Configuration

By default, the NetworkPolicy allows:
- DNS: kube-system namespace
- Kubernetes API: 0.0.0.0/0 (adjust for production)
- HAProxy pods: All namespaces with matching labels

### Production Hardening

For production, restrict Kubernetes API access:

```yaml
networkPolicy:
  egress:
    kubernetesApi:
      - cidr: 10.96.0.0/12  # Your cluster's service CIDR
        ports:
          - port: 443
            protocol: TCP
```

### kind Cluster Specifics

For kind clusters with network policy enforcement:

```yaml
networkPolicy:
  enabled: true
  egress:
    allowDNS: true
    kubernetesApi:
      - cidr: 0.0.0.0/0  # kind requires broader access
```

## HAProxy Pod Requirements

The controller manages HAProxy pods deployed separately. Each HAProxy pod must:

1. **Have matching labels** as defined in `pod_selector`
2. **Run HAProxy with Dataplane API sidecar**
3. **Share config volume** between HAProxy and Dataplane containers
4. **Expose Dataplane API** on port 5555

### Example HAProxy Pod Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: haproxy
spec:
  replicas: 2
  selector:
    matchLabels:
      app: haproxy
      component: loadbalancer
  template:
    metadata:
      labels:
        app: haproxy
        component: loadbalancer
    spec:
      containers:
      - name: haproxy
        image: haproxytech/haproxy-debian:3.2
        command: ["/bin/sh", "-c"]
        args:
          - |
            mkdir -p /etc/haproxy/maps /etc/haproxy/certs
            cat > /etc/haproxy/haproxy.cfg <<EOF
            global
                log stdout len 4096 local0 info
            defaults
                timeout connect 5s
            frontend status
                bind *:8404
                http-request return status 200 if { path /healthz }
                # Note: /ready endpoint intentionally omitted - added by controller
            EOF
            exec haproxy -W -db -S "/etc/haproxy/haproxy-master.sock,level,admin" -- /etc/haproxy/haproxy.cfg
        volumeMounts:
        - name: haproxy-config
          mountPath: /etc/haproxy
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8404
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8404
          initialDelaySeconds: 5
          periodSeconds: 5

      - name: dataplane
        image: haproxytech/haproxy-debian:3.2
        command: ["/bin/sh", "-c"]
        args:
          - |
            # Wait for HAProxy to create the socket
            while [ ! -S /etc/haproxy/haproxy-master.sock ]; do
              echo "Waiting for HAProxy master socket..."
              sleep 1
            done

            # Create Dataplane API config
            cat > /etc/haproxy/dataplaneapi.yaml <<'EOF'
            config_version: 2
            name: haproxy-dataplaneapi
            dataplaneapi:
              host: 0.0.0.0
              port: 5555
              user:
                - name: admin
                  password: adminpass
                  insecure: true
              transaction:
                transaction_dir: /var/lib/dataplaneapi/transactions
                backups_number: 10
                backups_dir: /var/lib/dataplaneapi/backups
              resources:
                maps_dir: /etc/haproxy/maps
                ssl_certs_dir: /etc/haproxy/certs
            haproxy:
              config_file: /etc/haproxy/haproxy.cfg
              haproxy_bin: /usr/local/sbin/haproxy
              master_worker_mode: true
              master_runtime: /etc/haproxy/haproxy-master.sock
              reload:
                reload_delay: 1
                reload_cmd: /bin/sh -c "echo 'reload' | socat stdio unix-connect:/etc/haproxy/haproxy-master.sock"
                restart_cmd: /bin/sh -c "echo 'reload' | socat stdio unix-connect:/etc/haproxy/haproxy-master.sock"
                reload_strategy: custom
            log_targets:
              - log_to: stdout
                log_level: info
            EOF

            # Start Dataplane API
            exec dataplaneapi -f /etc/haproxy/dataplaneapi.yaml
        volumeMounts:
        - name: haproxy-config
          mountPath: /etc/haproxy

      volumes:
      - name: haproxy-config
        emptyDir: {}
```

## Ingress Annotations

The controller supports annotations on Ingress resources for configuring HAProxy features.

### Basic Authentication

Enable HTTP basic authentication on Ingress resources using these annotations:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: protected-app
  annotations:
    haproxy.org/auth-type: "basic-auth"
    haproxy.org/auth-secret: "my-auth-secret"
    haproxy.org/auth-realm: "Protected Application"
spec:
  ingressClassName: haproxy-template-ic
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-service
                port:
                  number: 80
```

**Annotations:**

| Annotation | Description | Required | Default |
|------------|-------------|----------|---------|
| `haproxy.org/auth-type` | Authentication type | Yes | - |
| `haproxy.org/auth-secret` | Secret name containing credentials | Yes | - |
| `haproxy.org/auth-realm` | HTTP auth realm shown to users | No | `"Restricted Area"` |

**Supported authentication types:**
- `basic-auth`: HTTP basic authentication with username/password

**Secret reference formats:**
- `"secret-name"`: Secret in same namespace as Ingress
- `"namespace/secret-name"`: Secret in specific namespace

### Creating Authentication Secrets

Secrets must contain username-password pairs where values are **base64-encoded crypt(3) SHA-512 password hashes**:

```bash
# Generate SHA-512 hash and encode for Kubernetes
HASH=$(openssl passwd -6 mypassword)

# Create secret with encoded hash
kubectl create secret generic my-auth-secret \
  --from-literal=admin=$(echo -n "$HASH" | base64 -w0) \
  --from-literal=user=$(echo -n "$HASH" | base64 -w0)
```

**Secret structure:**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-auth-secret
type: Opaque
data:
  # Keys are usernames, values are base64-encoded password hashes
  admin: JDYkMVd3c2YxNmprcDBkMVBpTyRkS3FHUTF0SW0uOGF1VlJIcVA3dVcuMVV5dVNtZ3YveEc3dEFiOXdZNzc1REw3ZGE0N0hIeVB4ZllDS1BMTktZclJvMHRNQWQyQk1YUHBDd2Z5ZW03MA==
  user: JDYkbkdxOHJ1T2kyd3l4MUtyZyQ1a2d1azEzb2tKWmpzZ2Z2c3JqdmkvOVoxQjZIbDRUcGVvdkpzb2lQeHA2eGRKWUpha21wUmIwSUVHb1ZUSC8zRzZrLmRMRzBuVUNMWEZnMEhTRTJ5MA==
```

**Important:**
- Multiple Ingress resources can reference the same secret
- Secrets are fetched on-demand (requires `store: on-demand` in secrets configuration)
- Password hashes must use crypt(3) SHA-512 format for HAProxy compatibility

## Validation Sidecar

Enable the validation sidecar to test configurations before deployment:

```yaml
validation:
  enabled: true
```

This adds HAProxy + Dataplane sidecars to the controller pod for config validation.

## Debugging

### Enable Debug HTTP Server

The controller provides a debug HTTP server that exposes internal state via `/debug/vars` and Go profiling via `/debug/pprof`. This is disabled by default for security.

Enable debug server:

```yaml
controller:
  debugPort: 6060
```

Access debug endpoints via port-forward:

```bash
# Forward debug port from controller pod
kubectl port-forward deployment/my-controller 6060:6060

# List all available debug variables
curl http://localhost:6060/debug/vars

# Get current controller configuration
curl http://localhost:6060/debug/vars/config

# Get rendered HAProxy configuration
curl http://localhost:6060/debug/vars/rendered

# Get recent events (last 100)
curl http://localhost:6060/debug/vars/events

# Get resource counts
curl http://localhost:6060/debug/vars/resources

# Go profiling (CPU, heap, goroutines)
curl http://localhost:6060/debug/pprof/
go tool pprof http://localhost:6060/debug/pprof/heap
```

### Debug Variables

Available debug variables:

| Endpoint | Description |
|----------|-------------|
| `/debug/vars` | List all available variables |
| `/debug/vars/config` | Current controller configuration |
| `/debug/vars/credentials` | Credentials metadata (not actual values) |
| `/debug/vars/rendered` | Last rendered HAProxy config |
| `/debug/vars/auxfiles` | Auxiliary files (SSL certs, maps) |
| `/debug/vars/resources` | Resource counts by type |
| `/debug/vars/events` | Recent events (default: last 100) |
| `/debug/vars/state` | Full state dump (use carefully) |
| `/debug/vars/uptime` | Controller uptime |
| `/debug/pprof/` | Go profiling endpoints |

### JSONPath Field Selection

Extract specific fields using JSONPath:

```bash
# Get only the config version
curl 'http://localhost:6060/debug/vars/config?field={.version}'

# Get only template names
curl 'http://localhost:6060/debug/vars/config?field={.config.templates}'

# Get rendered config size
curl 'http://localhost:6060/debug/vars/rendered?field={.size}'
```

## Monitoring

The controller exposes 11 Prometheus metrics on port 9090 at `/metrics` endpoint covering:

- **Reconciliation**: Cycles, errors, and duration
- **Deployment**: Operations, errors, and duration
- **Validation**: Total validations and errors
- **Resources**: Tracked resource counts by type
- **Events**: Event bus activity and subscribers

### Quick Access

Access metrics directly via port-forward:

```bash
# Port-forward to controller pod
kubectl port-forward -n <namespace> pod/<controller-pod> 9090:9090

# Fetch metrics
curl http://localhost:9090/metrics
```

### Prometheus ServiceMonitor

Enable Prometheus Operator integration:

```yaml
monitoring:
  serviceMonitor:
    enabled: true
    interval: 30s
    scrapeTimeout: 10s
    labels:
      prometheus: kube-prometheus  # Match your Prometheus selector
```

### With NetworkPolicy

If using NetworkPolicy, allow Prometheus to scrape metrics:

```yaml
networkPolicy:
  enabled: true
  ingress:
    monitoring:
      enabled: true  # Enable metrics ingress
      podSelector:
        matchLabels:
          app: prometheus
      namespaceSelector:
        matchLabels:
          name: monitoring
```

### Advanced ServiceMonitor Configuration

Add custom labels and relabeling:

```yaml
monitoring:
  serviceMonitor:
    enabled: true
    interval: 15s
    labels:
      prometheus: kube-prometheus
      team: platform
    # Add cluster label to all metrics
    relabelings:
      - sourceLabels: [__address__]
        targetLabel: cluster
        replacement: production
    # Drop specific metrics
    metricRelabelings:
      - sourceLabels: [__name__]
        regex: 'haproxy_ic_event_subscribers'
        action: drop
```

### Example Prometheus Queries

```promql
# Reconciliation rate (per second)
rate(haproxy_ic_reconciliation_total[5m])

# Error rate
rate(haproxy_ic_reconciliation_errors_total[5m])

# 95th percentile reconciliation duration
histogram_quantile(0.95, rate(haproxy_ic_reconciliation_duration_seconds_bucket[5m]))

# Current HAProxy pod count
haproxy_ic_resource_count{type="haproxy-pods"}
```

### Grafana Dashboard

Create dashboards using these key metrics:

1. **Operations Overview**: reconciliation_total, deployment_total, validation_total
2. **Error Tracking**: *_errors_total counters
3. **Performance**: *_duration_seconds histograms
4. **Resource Utilization**: resource_count gauge

For complete metric definitions and more queries, see `pkg/controller/metrics/README.md` in the repository.

## High Availability

The controller supports running multiple replicas with **leader election** to ensure only one replica deploys configurations to HAProxy while all replicas remain ready for immediate failover.

### Leader Election (Default)

**Default configuration (2 replicas with leader election):**

```yaml
replicaCount: 2  # Runs 2 replicas by default

controller:
  config:
    controller:
      leader_election:
        enabled: true  # Enabled by default
        lease_name: haproxy-template-ic-leader
        lease_duration: 60s    # Failover within ~15-20 seconds typically
        renew_deadline: 15s
        retry_period: 5s
```

**How it works:**
- All replicas watch resources, render templates, and validate configs
- Only the elected leader deploys configurations to HAProxy instances
- Automatic failover if leader fails (~15-20 second downtime)
- Leadership transitions are logged and tracked via Prometheus metrics

**Check current leader:**
```bash
# View Lease resource
kubectl get lease haproxy-template-ic-leader -o yaml

# Check metrics
kubectl port-forward deployment/haproxy-template-ic 9090:9090
curl http://localhost:9090/metrics | grep leader_election_is_leader
```

See [High Availability Operations Guide](../../docs/operations/high-availability.md) for detailed documentation.

### Multiple Replicas

Run 3+ replicas for enhanced availability:

```yaml
replicaCount: 3

podDisruptionBudget:
  enabled: true
  minAvailable: 2

# Distribute across availability zones
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels:
              app.kubernetes.io/name: haproxy-template-ic
          topologyKey: topology.kubernetes.io/zone
```

### Single Replica (Development)

Disable leader election for development/testing:

```yaml
replicaCount: 1

controller:
  config:
    controller:
      leader_election:
        enabled: false
```

### Autoscaling

```yaml
autoscaling:
  enabled: true
  minReplicas: 2  # Keep at least 2 for HA
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
```

## Upgrading

### Upgrade the Chart

```bash
helm upgrade my-controller ./charts/haproxy-template-ic
```

### Upgrade with New Values

```bash
helm upgrade my-controller ./charts/haproxy-template-ic \
  -f my-values.yaml
```

## Uninstalling

```bash
helm uninstall my-controller
```

This removes all resources created by the chart.

## Troubleshooting

### Controller Not Starting

Check logs:
```bash
kubectl logs -f -l app.kubernetes.io/name=haproxy-template-ic
```

Common issues:
- HAProxyTemplateConfig CRD or Secret missing
- RBAC permissions incorrect
- NetworkPolicy blocking access

### Cannot Connect to HAProxy Pods

1. **Check HAProxy pod labels** match `pod_selector`
   ```bash
   kubectl get pods --show-labels
   ```

2. **Verify Dataplane API is accessible**
   ```bash
   kubectl port-forward <haproxy-pod> 5555:5555
   curl http://localhost:5555/v3/info
   ```

3. **Check NetworkPolicy**
   ```bash
   kubectl describe networkpolicy
   ```

### NetworkPolicy Issues in kind

For kind clusters, ensure:
- Calico or Cilium CNI is installed
- DNS access is allowed
- Kubernetes API CIDR is correct

Debug NetworkPolicy:
```bash
# Check controller can resolve DNS
kubectl exec <controller-pod> -- nslookup kubernetes.default

# Check controller can reach HAProxy pod
kubectl exec <controller-pod> -- curl http://<haproxy-pod-ip>:5555/v3/info
```

## Examples

See the `examples/` directory for:
- Basic Ingress setup
- Multi-namespace configuration
- Production-ready values
- NetworkPolicy configurations

## Contributing

Contributions are welcome! Please see the main repository for guidelines.

## License

See the main repository for license information.
