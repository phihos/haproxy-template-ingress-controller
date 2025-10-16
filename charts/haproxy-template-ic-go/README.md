# HAProxy Template Ingress Controller (Go) Helm Chart

This Helm chart deploys the HAProxy Template Ingress Controller (Go version), which manages HAProxy configurations dynamically based on Kubernetes Ingress resources.

## Overview

The HAProxy Template Ingress Controller:
- Watches Kubernetes Ingress, Service, EndpointSlice, and Secret resources
- Renders Jinja2 templates to generate HAProxy configurations
- Deploys configurations to HAProxy pods via Dataplane API
- Supports cross-namespace HAProxy pod management
- Includes optional validation sidecar for config testing

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- HAProxy pods with Dataplane API sidecars (deployed separately)

## Installation

### Basic Installation

```bash
helm install my-controller ./charts/haproxy-template-ic-go
```

### With Custom Values

```bash
helm install my-controller ./charts/haproxy-template-ic-go \
  --set image.tag=v0.1.0 \
  --set replicaCount=2
```

### With Custom Values File

```bash
helm install my-controller ./charts/haproxy-template-ic-go \
  -f my-values.yaml
```

## Configuration

### Key Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of controller replicas | `1` |
| `image.repository` | Controller image repository | `ghcr.io/phihos/haproxy-template-ic-go` |
| `image.tag` | Controller image tag | Chart appVersion |
| `controller.config.pod_selector` | Labels to match HAProxy pods | `{app: haproxy, component: loadbalancer}` |
| `controller.config.logging.verbose` | Log level (0=WARN, 1=INFO, 2=DEBUG) | `1` |
| `credentials.dataplane.username` | Dataplane API username | `admin` |
| `credentials.dataplane.password` | Dataplane API password | `adminpass` |
| `validation.enabled` | Enable validation sidecar | `false` |
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
                stats socket /etc/haproxy/haproxy-master.sock mode 600 level admin
            defaults
                timeout connect 5s
            frontend status
                bind *:8404
                http-request return status 200 if { path /healthz }
            EOF
            exec haproxy -W -db -S "/etc/haproxy/haproxy-master.sock,level,admin" -- /etc/haproxy/haproxy.cfg
        volumeMounts:
        - name: haproxy-config
          mountPath: /etc/haproxy

      - name: dataplane
        image: haproxytech/haproxy-debian:3.2
        command: ["dataplaneapi"]
        args:
          - --config-file=/etc/haproxy/dataplaneapi.yaml
        env:
        - name: DATAPLANE_CONFIG
          value: |
            config_version: 2
            dataplaneapi:
              host: 0.0.0.0
              port: 5555
              user:
                - name: admin
                  password: adminpass
                  insecure: true
            haproxy:
              config_file: /etc/haproxy/haproxy.cfg
              haproxy_bin: /usr/local/sbin/haproxy
        volumeMounts:
        - name: haproxy-config
          mountPath: /etc/haproxy

      volumes:
      - name: haproxy-config
        emptyDir: {}
```

## Validation Sidecar

Enable the validation sidecar to test configurations before deployment:

```yaml
validation:
  enabled: true
```

This adds HAProxy + Dataplane sidecars to the controller pod for config validation.

## Monitoring

### Prometheus ServiceMonitor

Enable Prometheus Operator integration:

```yaml
monitoring:
  serviceMonitor:
    enabled: true
    interval: 30s
    labels:
      prometheus: kube-prometheus
```

## High Availability

### Multiple Replicas

```yaml
replicaCount: 3

podDisruptionBudget:
  enabled: true
  minAvailable: 2
```

### Autoscaling

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
```

## Upgrading

### Upgrade the Chart

```bash
helm upgrade my-controller ./charts/haproxy-template-ic-go
```

### Upgrade with New Values

```bash
helm upgrade my-controller ./charts/haproxy-template-ic-go \
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
kubectl logs -f -l app.kubernetes.io/name=haproxy-template-ic-go
```

Common issues:
- ConfigMap or Secret missing
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
