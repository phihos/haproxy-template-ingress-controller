# Architecture

## Overview

Template-driven HAProxy configuration management for Kubernetes. The controller watches Kubernetes resources, renders Jinja2 templates, and deploys validated configurations to HAProxy instances via Dataplane API.

## Components

### Controller Pod (3 containers)

```
┌─────────────────────────────────────────────┐
│ Controller Pod                              │
│                                             │
│ ┌──────────────┐ ┌──────────┐ ┌──────────┐ │
│ │ Main         │ │ Valid.   │ │ Valid.   │ │
│ │ Controller   │ │ HAProxy  │ │ Dataplane│ │
│ │              │ │          │ │ API      │ │
│ │ :8080 health │ │ :8404    │ │ :5555    │ │
│ │ :9090 metrics│ │          │ │          │ │
│ │ :9443 webhook│ │          │ │          │ │
│ └──────────────┘ └──────────┘ └──────────┘ │
└─────────────────────────────────────────────┘
```

**Main Controller**
- Watches Kubernetes resources
- Renders Jinja2 templates
- Orchestrates deployment
- Serves health, metrics, webhooks

**Validation Sidecar**
- HAProxy + Dataplane API
- Tests configurations before production
- Auth: `admin`/`validationpass`

### Production HAProxy Pods (2 containers each)

```
┌────────────────────────────────┐
│ HAProxy Pod                    │
│                                │
│ ┌──────────┐ ┌──────────────┐ │
│ │ HAProxy  │ │ Dataplane    │ │
│ │          │ │ API          │ │
│ │ :80 main │ │ :5555        │ │
│ │ :8404    │ │              │ │
│ └──────────┘ └──────────────┘ │
└────────────────────────────────┘
```

**HAProxy**
- Serves production traffic
- Port 8404 health endpoint (mandatory)

**Dataplane API**  
- Receives configuration updates
- Auth: `admin`/`adminpass`

## Data Flow

```
Resource Change → Watch Event → Template Render → Validation → Production Deploy
       ↑                                                              ↓
       └──────────────── Timer-based reconciliation ─────────────────┘
```

1. **Watch** - Kubernetes resource changes trigger events
2. **Render** - Templates processed with current state
3. **Validate** - Config tested in validation sidecar
4. **Deploy** - Validated config pushed to production
5. **Reconcile** - Periodic full sync prevents drift

## Resource Indexing

O(1) lookups through configurable JSONPath indexing:

```yaml
watched_resources:
  services:
    api_version: v1
    kind: Service
    # Index by custom field
    index_by: ["metadata.labels['app']"]
```

```python
# Template usage
service = resources.get('services').get_indexed_single('my-app')
```

## Template System

### Variables
- `resources` - Indexed Kubernetes resources
- `namespace` - Current namespace
- `env` - Environment variables
- `cli_args` - CLI arguments

### Snippets
Reusable template components:

```yaml
template_snippets:
  backend-name: |
    backend_{{ service }}_{{ port }}

haproxy_config:
  template: |
    {% include "backend-name" %}
```

## Deployment Models

### Development
```bash
kind create cluster
kubectl apply -k deploy/overlays/dev
```

### Production
```bash
kubectl apply -k deploy/overlays/production
```

Key differences:
- Resource limits
- Replica count
- Monitoring integration
- Network policies

## Critical Design Decisions

### HAProxy Version Requirements
**Required**: HAProxy 3.1+ with Alpine base image

**Performance comparison**:
- HAProxy 3.0: dataplaneapi binary takes 30-60 seconds to start
- HAProxy 3.1+: dataplaneapi binary takes 3-5 seconds to start

This 10x improvement in dataplaneapi startup time is critical for pod restarts and failover. The issue is specific to the dataplaneapi Go binary version, not the HAProxy core or Alpine version.

### Unified Port Configuration
All Dataplane API instances use port 5555 with environment-specific auth:
- Production: `admin`/`adminpass`
- Validation: `admin`/`validationpass`

### Validation-First Deployment
Every configuration tested in isolation before production deployment.

### No Backward Compatibility
Clean breaks over compatibility layers. Technical debt prevention over migration ease.