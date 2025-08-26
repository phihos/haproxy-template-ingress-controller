# HAProxy Template Ingress Controller

[![build](https://img.shields.io/github/actions/workflow/status/phihos/haproxy-template-ingress-controller/test.yml?branch=main&logo=github)](https://github.com/phihos/haproxy-template-ingress-controller/actions/workflows/test.yml)

Template-driven HAProxy ingress controller for Kubernetes. Full control over HAProxy configuration through Jinja2 templates instead of limited annotations.

## Features

- **Full HAProxy control** - Direct `haproxy.cfg` templating with Jinja2
- **Watch any resource** - Ingress, Service, Secret, ConfigMap, custom CRDs
- **O(1) lookups** - Custom indexing for efficient cross-resource matching
- **Live reload** - HAProxy Dataplane API v3 integration
- **Validation** - Test configs before production deployment
- **Observable** - Prometheus metrics, OpenTelemetry tracing, structured logging

## Quick Start

```bash
# Create cluster
kind create cluster --name haproxy-ic

# Deploy controller
kubectl apply -k deploy/overlays/dev

# Apply example configuration
kubectl apply -f examples/config-schema-example.yaml

# Check status
kubectl logs -l app=haproxy-template-ic
```

## Example Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: haproxy-config
data:
  config: |
    pod_selector:
      match_labels: {app: haproxy}
    
    watched_resources:
      ingresses:
        api_version: networking.k8s.io/v1
        kind: Ingress
      services:
        api_version: v1
        kind: Service
        index_by: ["metadata.name"]  # Index by name for get_indexed_single()
    
    haproxy_config:
      template: |
        global
            daemon
        defaults
            mode http
            timeout connect 5s
        
        frontend health
            bind *:8404
            http-request return status 200 if { path /healthz }
        
        frontend main
            bind *:80
            {% for _, ingress in resources.get('ingresses', {}).items() %}
            {% for rule in ingress.spec.rules %}
            use_backend {{ rule.backend.service.name }} if { hdr(host) {{ rule.host }} }
            {% endfor %}
            {% endfor %}
        
        {% for _, ingress in resources.get('ingresses', {}).items() %}
        {% for rule in ingress.spec.rules %}
        backend {{ rule.backend.service.name }}
            # Services must be indexed by name in watched_resources config
            {% set svc = resources.get('services', {}).get_indexed_single(rule.backend.service.name) %}
            {% if svc %}
            server srv {{ svc.spec.clusterIP }}:{{ rule.backend.service.port.number }}
            {% endif %}
        {% endfor %}
        {% endfor %}
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [Quick Start](docs/QUICKSTART.md) - Installation and first deployment
- [Configuration](docs/CONFIGURATION.md) - ConfigMap structure and options
- [Templates](docs/TEMPLATES.md) - Jinja2 syntax and examples
- [Operations](docs/OPERATIONS.md) - Monitoring and production deployment
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Diagnostic commands and recovery
- [Security](docs/SECURITY.md) - RBAC, network policies, and hardening
- [Development](docs/DEVELOPMENT.md) - Build, test, and contribute
- [API Reference](docs/API.md) - CLI, environment variables, endpoints

## Requirements

- Kubernetes 1.28+
- HAProxy 3.1 or later (critical for performance)
- Python 3.13+ (development only)

## Status

⚠️ **Proof of concept** - Not production ready. Use at your own risk.

## License

Apache 2.0