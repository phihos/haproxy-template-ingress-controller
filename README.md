# HAProxy Template Ingress Controller

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Build Status](https://github.com/phihos/haproxy-template-ic/actions/workflows/lint.yml/badge.svg)](https://github.com/phihos/haproxy-template-ic/actions/workflows/lint.yml)

A Kubernetes ingress controller that manages HAProxy load balancer configurations through powerful template-driven approaches. Continuously monitors user-defined Kubernetes resources and translates them into optimized HAProxy configurations with zero-reload deployments.

## Highlights

**Complete HAProxy Control**
Unlike annotation-based ingress controllers, templates give you full access to HAProxy's configuration language. Configure advanced features like custom ACLs, stick tables, rate limiting, or multi-tier routing without being limited by a predefined set of annotations.

**Minimal Service Disruption**
Configuration updates apply through HAProxy's runtime API when possible, avoiding process reloads and maintaining existing connections. Only changes that require a reload will trigger one.

**Safe Deployments**
Multi-phase validation catches configuration errors before they reach production HAProxy instances. Invalid configurations are rejected early, preventing service outages from bad configs.

**Flexible Resource Mapping**
Watch any Kubernetes resource type as input, not just Ingress objects. Use Services, ConfigMaps, custom CRDs, or any combination to drive your HAProxy configuration. Define your own data model.

**Battle-Tested Load Balancer**
Built on HAProxy, trusted by high-traffic sites for decades. Get enterprise-grade load balancing with the flexibility of Kubernetes-native configuration management.

## Quick Example

Here's a minimal configuration that watches Kubernetes Ingress resources and generates HAProxy backends:

```yaml
# ConfigMap: haproxy-config
watched_resources:
  ingresses:
    api_version: networking.k8s.io/v1
    kind: Ingress
    index_by:
      - metadata.namespace
      - metadata.name

haproxy_config:
  template: |
    global
        daemon

    defaults
        mode http
        timeout client 30s
        timeout server 30s
        timeout connect 5s

    frontend http
        bind :80
        {% for ingress in resources.ingresses %}
        {% for rule in ingress.spec.rules %}
        acl host_{{ ingress.metadata.name }} hdr(host) -i {{ rule.host }}
        use_backend {{ ingress.metadata.name }} if host_{{ ingress.metadata.name }}
        {% endfor %}
        {% endfor %}

    {% for ingress in resources.ingresses %}
    backend {{ ingress.metadata.name }}
        balance roundrobin
        {% for rule in ingress.spec.rules %}
        {% for path in rule.http.paths %}
        server {{ path.backend.service.name }} {{ path.backend.service.name }}.{{ ingress.metadata.namespace }}.svc.cluster.local:{{ path.backend.service.port.number }} check
        {% endfor %}
        {% endfor %}
    {% endfor %}
```

Any Ingress created in your cluster automatically appears in the `resources.ingresses` collection, and the template generates the corresponding HAProxy configuration.

## Quick Start

Get the controller running in your cluster in a few minutes.

### 1. Deploy HAProxy with Dataplane API

Deploy HAProxy pods that the controller will manage. Here's a simplified example for testing:

> **Note**: This is a minimal example for quick testing. For production deployments with proper volume sharing, health checks, and configuration management, see the [Helm chart HAProxy examples](charts/haproxy-template-ic/README.md#haproxy-pod-requirements).

```bash
kubectl apply -f - <<EOF
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
        ports:
        - containerPort: 80
        - containerPort: 443
      - name: dataplane
        image: haproxytech/dataplane-api:3.0
        args:
          - --host=0.0.0.0
          - --port=5555
          - --haproxy-bin=/usr/local/sbin/haproxy
          - --config-file=/etc/haproxy/haproxy.cfg
        env:
        - name: DATAPLANE_USER
          value: admin
        - name: DATAPLANE_PASS
          value: adminpass
EOF
```

See [charts/haproxy-template-ic/README.md](charts/haproxy-template-ic/README.md#haproxy-pod-requirements) for production-ready HAProxy deployment examples.

### 2. Install the Controller

Install using Helm:

```bash
helm install haproxy-ic ./charts/haproxy-template-ic \
  --set credentials.dataplane.username=admin \
  --set credentials.dataplane.password=adminpass
```

The default configuration watches Ingress resources and generates HAProxy backends. Customize via values file for advanced scenarios.

### 3. Create an Ingress

Create a sample Ingress resource:

```bash
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: example
spec:
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-service
            port:
              number: 80
EOF
```

### 4. Verify

Check that the controller generated HAProxy configuration:

```bash
# Check controller logs
kubectl logs -l app.kubernetes.io/name=haproxy-template-ic

# View generated HAProxy config in HAProxy pod
kubectl exec -it deployment/haproxy -c haproxy -- cat /etc/haproxy/haproxy.cfg
```

You should see your Ingress translated into HAProxy frontend rules and backend servers.

### Next Steps

- Customize templates in the [ConfigMap configuration](charts/haproxy-template-ic/README.md#controller-configuration)
- Add more watched resources (Services, EndpointSlices, custom CRDs)
- Enable [validation sidecar](charts/haproxy-template-ic/README.md#validation-sidecar) for safer deployments
- Review [HAProxy pod requirements](charts/haproxy-template-ic/README.md#haproxy-pod-requirements) for production

## Architecture

The controller follows an event-driven architecture with pure components:

```
Kubernetes API → Resource Watchers → EventBus → Components
                                         ↓
                   ConfigLoader, Validators, Reconciler
                                         ↓
                   Template Engine → Validator → Deployer
                                         ↓
                              HAProxy Dataplane API
```

**Key Design Principles:**
- Multi-phase validation catches configuration errors early
- Optimized deployments minimize HAProxy reloads
- Template-driven for maximum flexibility

For detailed architecture documentation, see [docs/development/design.md](docs/development/design.md).

## Documentation

### Package Documentation

- [pkg/controller/](pkg/controller/README.md) - Event-driven controller orchestration
- [pkg/core/](pkg/core/README.md) - Configuration API reference
- [pkg/dataplane/](pkg/dataplane/README.md) - HAProxy integration guide
- [pkg/templating/](pkg/templating/README.md) - Template engine comprehensive guide
- [pkg/k8s/](pkg/k8s/README.md) - Kubernetes resource watching and indexing
- [pkg/events/](pkg/events/README.md) - Event bus infrastructure

### Development Documentation

- [docs/development/design.md](docs/development/design.md) - Complete architecture overview
- [docs/development/linting.md](docs/development/linting.md) - Code quality and linting guidelines
- [docs/supported-configuration.md](docs/supported-configuration.md) - Configuration options reference

## Development

### Build Commands

```bash
# Build binary
make build

# Run tests
make test

# Run integration tests (requires kind cluster)
make test-integration

# Run linting
make lint

# Run all checks
make check-all

# Build Docker image
make docker-build

# Coverage report
make test-coverage
```

## Contributing

Contributions are welcome!

Before submitting pull requests:
1. Run `make check-all` to verify code quality
2. Add tests for new functionality
3. Update documentation as needed
4. Follow the existing code style and patterns

## License

Licensed under the Apache License 2.0 - see [LICENSE](LICENSE) file for details.

Copyright 2025 Philipp Hossner

## Acknowledgments

This project builds on excellent open source software:
- [Kubernetes client-go](https://github.com/kubernetes/client-go) - Kubernetes API client
- [HAProxy client-native](https://github.com/haproxytech/client-native) - HAProxy Dataplane API client
- [Gonja](https://github.com/nikolalohinski/gonja) - Jinja2-like templating for Go
