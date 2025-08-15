# HAProxy Template Ingress Controller

[![build](https://img.shields.io/github/actions/workflow/status/phihos/haproxy-template-ingress-controller/test.yml?branch=main&logo=github)](https://github.com/phihos/haproxy-template-ingress-controller/actions/workflows/test.yml) [![codecov](https://codecov.io/gh/phihos/haproxy-template-ingress-controller/graph/badge.svg?token=YOUR_UPLOAD_TOKEN)](https://codecov.io/gh/phihos/haproxy-template-ingress-controller)

Proof-of-concept ingress controller for users who need direct control over [HAProxy](http://www.haproxy.org/) configuration beyond what existing ingress controllers provide.

## Overview

This controller enables full Jinja2 templating of HAProxy configurations, map files, certificates, and any resource pushable via [HAProxy's Dataplane API](https://www.haproxy.com/documentation/haproxy-data-plane-api/). Instead of being limited by predefined annotations, you can implement custom logic for any Kubernetes resource.

**Target users**: Those familiar with editing `haproxy.cfg` who feel constrained by existing ingress controllers.

**Key capability**: Template any HAProxy resource using watched Kubernetes resources, environment variables, and CLI arguments.

> [!WARNING]  
> This is a proof-of-concept. Most functionality is incomplete or potentially buggy. Use at your own risk.

## Features

### Current Implementation
- ✅ Watch arbitrary Kubernetes resources  
- ✅ Template HAProxy map files
- ✅ Template `haproxy.cfg` configuration files
- ✅ Template certificate files from Kubernetes Secrets
- ✅ Template snippet system with `{% include %}` support for reusable components
- ✅ Access watched resources, environment variables, and CLI arguments from templates
- ✅ Access target pod metadata (memory limits, labels, annotations, etc.) from templates
- ✅ Management socket for runtime state inspection
- ✅ Synchronize rendered templates with running HAProxy instances via Dataplane API
- ✅ Comprehensive observability with Prometheus metrics and OpenTelemetry tracing
- ✅ Resilient operations with retry logic, circuit breakers, and adaptive timeouts
- ✅ Validating admission webhooks for ConfigMaps and watched resources

## Architecture

### Components

**Production setup** requires two types of deployments:

#### 1. Controller Pod (Single Pod, 3 Containers)
- **Main Controller**: Watches resources, renders templates, orchestrates deployment
- **Validation HAProxy**: Tests configurations before production (port 8081)  
- **Validation Dataplane API**: Manages validation HAProxy (port 5556)

#### 2. Production HAProxy Pods (Multiple Pods, 2 Containers Each)
- **HAProxy Container**: Serves production traffic (port 80), health endpoint (port 8404)
- **Dataplane API Container**: Receives configs from controller (port 5555)
- **Labels**: Must match `pod_selector.match_labels` in ConfigMap
- **Initial State**: Pods start NOT ready due to missing health endpoint

#### 3. ConfigMap Configuration
Defines:
- Pod selector for target HAProxy pods
- Kubernetes resources to watch  
- Jinja2 templates for configs, maps, and certificates
- **Critical**: HAProxy template MUST include health endpoint on port 8404

### Reconciliation Process

1. **Trigger**: Watched Kubernetes resource changes
2. **Render**: Templates processed with inputs:
   - All watched resources
   - Environment variables  
   - CLI arguments
   - Referenced Kubernetes/HTTP resources
3. **Validate**: Push rendered configs to validation sidecar via Dataplane API
4. **Deploy**: On validation success, push structured state to production HAProxy pods
5. **Sync**: Full sync removes undeclared resources from target instances

Timer-based reconciliation prevents config drift during resource stability.

## Template Snippets

The controller supports reusable template snippets that can be included in any template (maps, configs, or certificates). This enables modular, maintainable configurations.

### Basic Usage

Define snippets in the `template_snippets` section of your ConfigMap:

```yaml
template_snippets:
  backend-name: |
    backend_{{ service_name }}_{{ port }}
  
  server-entry: |
    server {{ name }} {{ ip }}:{{ port }} check
```

Include snippets in templates using Jinja2's `{% include %}` syntax:

```yaml
maps:
  /etc/haproxy/maps/backends.map:
    template: |
      {% for service in services %}
      {% include "backend-name" %} {% include "server-entry" %}
      {% endfor %}
```

### Advanced Features

- **Nested includes**: Snippets can include other snippets
- **Template variables**: Use `{% set %}` to pass context between snippets
- **Error handling**: Missing snippets raise clear `TemplateNotFound` errors
- **Validation**: All snippets are validated at configuration load time

See [example-configmap.yaml](example-configmap.yaml) for a comprehensive example using template snippets to generate HAProxy configurations from Kubernetes Ingress resources.

## Validating Admission Webhooks

The controller includes validating admission webhooks that can prevent faulty resources from being applied to your cluster. This feature provides immediate feedback on configuration errors and helps maintain system stability.

### Webhook Types

**1. ConfigMap Validation (Always Enabled)**
- Automatically validates HAProxy Template IC ConfigMaps
- Checks YAML syntax, template structure, and resource references  
- Validates Jinja2 template syntax including snippet includes
- Provides warnings for potential issues

**2. Watched Resource Validation (Configurable)**  
- Optional validation for resources you're watching (Ingress, Service, etc.)
- Prevents broken resources from disrupting your HAProxy configuration
- Safe-by-default: disabled for critical resources like EndpointSlices
- Per-resource configuration via `enable_validation_webhook` flag

### Configuration

Enable webhook validation for specific watched resources:

```yaml
watch_resources:
  ingresses:
    group: networking.k8s.io
    version: v1
    kind: Ingress
    # Enable validation to prevent faulty Ingress configs
    enable_validation_webhook: true
    filter:
      field_selector:
        "spec.ingressClassName": "haproxy-template-ic"
  
  endpoints:
    group: discovery.k8s.io  
    version: v1
    kind: EndpointSlice
    # Keep disabled for critical resources
    enable_validation_webhook: false
    filter:
      label_selector:
        "kubernetes.io/service-name": "*"
```

### Benefits

- **Early Error Detection**: Catch configuration errors before they affect your load balancer
- **Template Validation**: Ensure Jinja2 templates are syntactically correct and all snippets exist
- **Resource Safety**: Prevent critical resources from being accidentally blocked
- **Immediate Feedback**: Get validation results instantly when applying resources with `kubectl`

## Quickstart

⚠️ **Kubernetes Required**: This application only runs in Kubernetes environments. Local development requires kind or minikube.

### Setup

```bash
# Clone repository
git clone https://github.com/phihos/haproxy-template-ingress-controller.git
cd haproxy-template-ingress-controller

# Install dependencies  
uv sync

# Create development cluster
kind create cluster --name haproxy-template-ic-dev

# Build and deploy
docker build --target production -t haproxy-template-ic:dev .
kind load docker-image haproxy-template-ic:dev --name haproxy-template-ic-dev

# Deploy with template snippet example
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: haproxy-template-ic-config
data:
  config: |
    pod_selector:
      match_labels:
        app: test
    template_snippets:
      backend-entry: |
        server {{ name }} {{ ip }}:{{ port }} check
    maps:
      /etc/haproxy/maps/backends.map:
        template: |
          # Generated backend entries
          {% for backend in resources.get('pods', {}).values() %}
          {% include "backend-entry" %}
          {% endfor %}
EOF

kubectl run haproxy-template-ic --image=haproxy-template-ic:dev \
  --env="CONFIGMAP_NAME=haproxy-template-ic-config" \
  --env="VERBOSE=1"

# Check status
kubectl logs -f haproxy-template-ic
```

### Development

```bash
# Pre-commit setup
pre-commit install

# Test suite
uv run pytest                    # Unit tests
uv run pytest -m "slow"         # Acceptance tests (creates test cluster)

# Code quality
uv run ruff format
uv run ruff check --fix  
uv run mypy haproxy_template_ic/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development information.

## Management Socket

Runtime state inspection via Unix socket at `/run/haproxy-template-ic/management.sock`.

### Commands

Access from within the pod or via `kubectl exec`:

```bash
# Complete state
kubectl exec -it haproxy-template-ic -- \
  echo "dump all" | socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock

# Resource indices only  
kubectl exec -it haproxy-template-ic -- \
  echo "dump indices" | socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock

# Specific index
kubectl exec -it haproxy-template-ic -- \
  echo "dump index pods" | socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock

# HAProxy config context
kubectl exec -it haproxy-template-ic -- \
  echo "dump config" | socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock
```

### Configuration

The controller supports configuration via CLI options or environment variables:

| Environment Variable | CLI Option | Default | Description |
|---------------------|------------|---------|-------------|
| `CONFIGMAP_NAME` | `--configmap-name` | *Required* | ConfigMap name containing controller configuration |
| `VERBOSE` | `--verbose` | `0` | Logging verbosity (0=WARNING, 1=INFO, 2=DEBUG) |
| `STRUCTURED_LOGGING` | `--structured-logging` | `false` | Enable JSON structured logging output |
| `HEALTHZ_PORT` | `--healthz-port` | `8080` | Controller health check endpoint port |
| `METRICS_PORT` | `--metrics-port` | `9090` | Prometheus metrics endpoint port |
| `SOCKET_PATH` | `--socket-path` | `/run/haproxy-template-ic/management.sock` | Management socket path |
| `WEBHOOK_ENABLED` | `--webhook-enabled` | `false` | Enable validating admission webhooks |
| `WEBHOOK_PORT` | `--webhook-port` | `9443` | Webhook server port |
| `TRACING_ENABLED` | `--tracing-enabled` | `false` | Enable OpenTelemetry distributed tracing |

#### Logging Configuration

**Plain Text Mode** (default): Context fields appended in logfmt format:
```bash
kubectl run haproxy-template-ic --image=haproxy-template-ic:dev \
  --env="CONFIGMAP_NAME=haproxy-config" \
  --env="VERBOSE=2"
```

**JSON Mode**: Structured JSON output for log aggregation:
```bash
kubectl run haproxy-template-ic --image=haproxy-template-ic:dev \
  --env="CONFIGMAP_NAME=haproxy-config" \
  --env="STRUCTURED_LOGGING=true" \
  --env="VERBOSE=1"
```

### Response Structure

**`dump all`** returns complete state with sections:
- **config**: Operator configuration (pod selector, watched resources, templates)
- **haproxy_config_context**: Rendered HAProxy config, map templates, and certificates
- **metadata**: Runtime information (ConfigMap name, flags)
- **indices**: Current Kubernetes resource state

**`dump indices`** returns only resource indices.

**`dump index <name>`** returns specific index (e.g., `pods_index`).

**`dump config`** returns HAProxy configuration context only, including rendered maps, HAProxy config, and certificates.

Example output:
```json
{
  "config": {
    "pod_selector": "app=haproxy",
    "watch_resources": {
      "pods": {"kind": "Pod", "group": "", "version": "v1"}
    },
    "maps": {
      "/etc/haproxy/maps/backend.map": {
        "template_source": "server {{ resources.name }} {{ resources.host }}:{{ resources.port }}"
      }
    }
  },
  "indices": {
    "pods_index": {
      "('default', 'web-pod')": {"name": "web-pod", "host": "10.0.1.5", "port": "80"}
    }
  }
}
```
