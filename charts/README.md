# Helm Charts

This directory contains Helm charts for deploying the HAProxy Template Ingress Controller.

## Charts

- **haproxy-template-ic**: Main Helm chart for the controller and HAProxy instances

## Installation

### Quick Start

```bash
# Add repository (when available)
helm repo add haproxy-template-ic https://example.com/helm-charts
helm repo update

# Install with default values
helm install my-haproxy-ic haproxy-template-ic/haproxy-template-ic

# Install from local chart
helm install my-haproxy-ic ./charts/haproxy-template-ic
```

### Custom Values

```bash
# Create custom values file
cat > my-values.yaml <<EOF
haproxy:
  replicas: 3

controller:
  verbose: 2
  tracing:
    enabled: true
    jaegerEndpoint: "jaeger-collector:14268"

webhook:
  enabled: true
EOF

# Install with custom values
helm install my-haproxy-ic ./charts/haproxy-template-ic -f my-values.yaml
```

## Configuration

### Required Values

- **haproxyImage.tag**: Must be "3.1" or newer for performance
- **controller.configmapName**: ConfigMap with controller configuration

### Key Configuration Options

```yaml
# HAProxy image (version 3.1+ required)
haproxyImage:
  repository: haproxytech/haproxy-alpine
  tag: "3.1"

# Production HAProxy instances
haproxy:
  enabled: true
  replicas: 2

# Validation sidecars
validation:
  enabled: true

# Webhooks (optional)
webhook:
  enabled: true

# Monitoring
monitoring:
  serviceMonitor:
    enabled: true
```

See [values.yaml](haproxy-template-ic/values.yaml) for complete configuration options.

## Upgrade Notes

### From Development to Production

When upgrading from development configuration to production:

1. Set appropriate resource limits
2. Configure monitoring and alerting
3. Enable webhooks for validation
4. Use secrets instead of literal passwords
5. Configure network policies

### Version Compatibility

- **HAProxy 3.1+**: Required for fast startup performance
- **Kubernetes 1.20+**: Required for EndpointSlice support
- **Helm 3.x**: Required for chart installation