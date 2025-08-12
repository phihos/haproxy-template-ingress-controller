# HAProxy Template Ingress Controller

[![build](https://img.shields.io/github/actions/workflow/status/phihos/haproxy-template-ingress-controller/test.yml?branch=main&logo=github)](https://github.com/phihos/haproxy-template-ingress-controller/actions/workflows/test.yml) [![Coverage Status](https://coveralls.io/repos/github/phihos/haproxy-template-ingress-controller/badge.svg)](https://coveralls.io/github/phihos/haproxy-template-ingress-controller)

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
- ✅ Access watched resources, environment variables, and CLI arguments from templates
- ✅ Management socket for runtime state inspection

### Planned
- ⏳ Template `haproxy.cfg`
- ⏳ Template certificate files  
- ⏳ Synchronize rendered templates with running HAProxy instances via Dataplane API
- ⏳ Validating webhook for config changes
- ⏳ Access target pod metadata (memory limits, etc.) from templates

## Architecture

### Components

**Production setup** requires:
1. **HAProxy pods** with:
   - HAProxy instance with minimal default config
   - Dataplane API server with admin socket access
   - Shared config directories via `EmptyDir` volumes
2. **Validation sidecars** with identical HAProxy + Dataplane API setup
3. **ConfigMap** defining:
   - Pod selector for target HAProxy pods
   - Kubernetes resources to watch
   - Jinja2 templates for configs, maps, and certificates

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

# Deploy with minimal config
kubectl create configmap haproxy-template-ic-config --from-literal=config="pod_selector: app=test"
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

Customize socket path via environment variable:

```bash
kubectl run haproxy-template-ic --image=haproxy-template-ic:dev \
  --env="SOCKET_PATH=/tmp/custom.sock" \
  --env="CONFIGMAP_NAME=haproxy-template-ic-config"
```

### Response Structure

**`dump all`** returns complete state with sections:
- **config**: Operator configuration (pod selector, watched resources, templates)
- **haproxy_config_context**: Rendered templates and content  
- **metadata**: Runtime information (ConfigMap name, flags)
- **indices**: Current Kubernetes resource state

**`dump indices`** returns only resource indices.

**`dump index <name>`** returns specific index (e.g., `pods_index`).

**`dump config`** returns HAProxy configuration context only.

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
