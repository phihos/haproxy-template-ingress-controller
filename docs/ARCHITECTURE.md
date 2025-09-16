# Architecture

This document provides a detailed architectural overview of the HAProxy Ingress Controller. It explains the
template-driven configuration management system, runtime components, and deployment workflows that enable
dynamic HAProxy orchestration in Kubernetes.

The guide covers the modular code structure, production pod architecture, data flow, and critical design
decisions that ensure reliability, performance, and maintainability in production environments.

## Contents

- [Overview](#overview)
- [Code Structure](#code-structure)
- [Runtime components](#runtime-components)
- [Data flow](#data-flow)
- [Resource Indexing](#resource-indexing)
- [Template System](#template-system)
- [Deployment Models](#deployment-models)
- [Critical Design Decisions](#critical-design-decisions)

## Overview

Template-driven HAProxy configuration management for Kubernetes. The controller watches Kubernetes resources, renders
Jinja2 templates, and deploys validated configurations to HAProxy instances via Dataplane API.

Built with modular architecture for maintainability, comprehensive test infrastructure for reliability, and optimized
performance for production environments.

## Code Structure

The controller is organized into focused packages for maintainability and testability:

```
haproxy_template_ic/
├── core/              # Core functionality
│   └── logging.py     # Structured logging setup
├── dataplane/         # HAProxy Dataplane API integration
│   ├── client.py      # API client wrapper
│   ├── synchronizer.py # Config deployment logic
│   └── utils.py       # Dataplane utilities
├── k8s/               # Kubernetes integration
│   ├── field_filter.py # Resource field filtering
│   ├── kopf_utils.py  # Kopf framework utilities
│   └── resource_utils.py # Resource manipulation
├── models/            # Data models and validation
│   ├── config.py      # Configuration models
│   ├── context.py     # Template context
│   ├── resources.py   # Resource collections
│   └── templates.py   # Template models
├── operator/          # Operator lifecycle management
│   ├── configmap.py   # ConfigMap change handling
│   ├── index_sync.py  # Index synchronization tracking
│   ├── initialization.py # Startup and cleanup
│   ├── pod_management.py # HAProxy pod discovery
└   └── utils.py       # Operator utilities
```

### Package Responsibilities

- **core/**: Foundation services like logging configuration
- **dataplane/**: All HAProxy Dataplane API interactions and deployment logic
- **k8s/**: Kubernetes-specific operations and resource handling
- **models/**: Type-safe data models with Pydantic validation
- **operator/**: Operator lifecycle, event handling, and configuration management

## Runtime Components

### Controller Pod (3 containers)

```
┌─────────────────────────────────────────────┐
│ Controller Pod                              │
│                                             │
│ ┌──────────────┐ ┌──────────┐ ┌──────────┐  │
│ │ Main         │ │ Valid.   │ │ Valid.   │  │
│ │ Controller   │ │ HAProxy  │ │ Dataplane│  │
│ │              │ │          │ │ API      │  │
│ │ :8080 health │ │ :8404    │ │ :5555    │  │
│ │ :9090 metrics│ │          │ │          │  │
│ │ :9443 webhook│ │          │ │          │  │
│ └──────────────┘ └──────────┘ └──────────┘  │
└─────────────────────────────────────────────┘
```

**Main Controller**

- Watches Kubernetes resources
- Renders Jinja2 templates
- Orchestrates deployment
- Serves health, metrics, webhooks

**Validation Sidecars**

- HAProxy + Dataplane API
- Tests configurations before production
- Auth: `admin`/`validationpass`

### Production HAProxy Pods (2 containers each)

```
┌────────────────────────────────┐
│ HAProxy Pod                    │
│                                │
│ ┌──────────┐ ┌──────────────┐  │
│ │ HAProxy  │ │ Dataplane    │  │
│ │          │ │ API          │  │
│ │ :80 main │ │ :5555        │  │
│ │ :8404    │ │              │  │
│ └──────────┘ └──────────────┘  │
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
Resource Change → Watch Event → Index Sync → Template Render → Validation → Production Deploy
       ↑                                                                              ↓
       └────────────────────── Timer-based reconciliation ───────────────────────────┘
```

1. **Watch** - Kubernetes resource changes trigger events
2. **Index Sync** - Wait for all indices to be initialized (startup only)
3. **Render** - Templates processed with current state
4. **Validate** - Config tested in validation sidecar
5. **Deploy** - Validated config pushed to production
6. **Reconcile** - Periodic full sync prevents drift

### Index Initialization Flow

During controller startup, the IndexSynchronizationTracker ensures template rendering doesn't begin until all Kopf indices are ready:

```
Controller Start → Setup Indices → Wait for Initialization → Template Rendering
                       ↓                        ↑
              Event Handlers Created → Report to Tracker
```

**Synchronization Process**:

1. **Index Setup**: Resource handlers and HAProxy pod handlers registered with tracking wrappers
2. **Event Tracking**: Each handler reports to IndexSynchronizationTracker when first called
3. **Timeout Protection**: 5-second timeout handles zero-resource cases (no resources exist)
4. **Initialization Complete**: All resource types ready or timed out
5. **Template Rendering**: Debouncer unblocked, normal operation begins

**Key Benefits**:
- **Startup Reliability**: Prevents incomplete configurations during controller initialization
- **Zero-Resource Handling**: Doesn't hang when no resources match selectors
- **Performance**: Tracking disabled after initialization for zero runtime overhead

### ConfigMap Change Detection

The operator uses intelligent change detection to prevent unnecessary reloads:

```python
# DeepDiff-based comparison
diff = DeepDiff(old_config.raw, new_config.raw, verbose_level=2)
if not diff:
    # No actual changes - skip reload
    return
```

Key features:

- **Accurate comparison**: DeepDiff detects actual content changes vs. Kubernetes metadata updates
- **Loop prevention**: Identical configurations don't trigger redundant reloads
- **Debug visibility**: Configuration diffs logged for troubleshooting
- **Event loop reuse**: Optimized asyncio handling across operator restarts

## Resource Indexing

O(1) lookups through configurable JSONPath indexing:

```yaml
watched_resources:
  services:
    api_version: v1
    kind: Service
    # Index by custom field
    index_by: [ "metadata.labels['app']" ]
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

### Index Synchronization System

**Decision**: IndexSynchronizationTracker prevents template rendering until all Kopf indices are initialized to avoid incomplete configurations during startup.

**Problem**: Template rendering could be triggered by timer events or partial index updates before all Kopf indices are fully populated, leading to incomplete HAProxy configurations during controller startup.

**Solution**: Event-based tracking system with timeout protection for zero-resource edge cases.

**Implementation**:
- **Event Handlers**: All resource handlers (watched resources + HAProxy pods) report to IndexSynchronizationTracker when called
- **Timeout Protection**: 5-second timeout handles cases where no resources exist for a given type (prevents infinite waiting)
- **Performance Optimization**: Tracking automatically disabled after initialization to eliminate runtime overhead
- **Clean Code**: Uses factory pattern with dependency injection, no global state

**Key Components**:
- `IndexSynchronizationTracker`: Core synchronization logic in `operator/index_sync.py`
- `TemplateRenderDebouncer`: Waits for index initialization before first render
- `create_tracking_decorator`: Factory function that creates tracking decorators with injected dependencies

**Always Tracked**: HAProxy pods are always included in synchronization regardless of configuration to ensure complete system startup coordination.

### HAProxy Version Requirement: 3.1+ (Critical for Startup)

**Decision**: All HAProxy containers MUST use `haproxytech/haproxy-alpine:3.1` or newer.

**Rationale**: Version 3.0 dataplaneapi has slow startup (30-60s) vs. 3.1+ which starts in 3-5s. HAProxy core unaffected - dataplaneapi issue only. Slow startup causes routing failures. **Do NOT use 3.0** despite LTS.

**Measured dataplaneapi startup times**:
- Version 3.0: 30-60+ seconds (requires failureThreshold: 10)
- Version 3.1+: 3-5 seconds (works with failureThreshold: 3)

### Runtime API Configuration Requirements

**Critical**: Runtime API requires proper HAProxy stats socket and dataplane API master socket configuration to avoid "Runtime API not configured, not using it" warnings.

**Required HAProxy Master Socket**:
```bash
haproxy -W -S "/etc/haproxy/haproxy-master.sock,level,admin" -- /etc/haproxy/haproxy.cfg
```

**Required Dataplane API Configuration**:
```yaml
haproxy:
  master_runtime: /etc/haproxy/haproxy-master.sock
```

**Note**: The `-S` flag creates the master socket that dataplane API uses for runtime operations. No separate `stats socket` in global section needed.

**Version Parameter Requirements**: Runtime API operations require `transaction_id` OR `version` parameter. Non-transactional operations need current config version. Implemented in `dataplane.py:505` via `_get_configuration_version()`. Prevents HTTP 400 errors.

### Runtime API Optimization for Zero-Reload Deployments

**Decision**: Controller optimizes deployments by separating runtime-eligible operations from configuration operations to avoid unnecessary HAProxy reloads.

**Implementation**:
- **Server Operations**: Applied without transactions when possible, enabling Go dataplane API to automatically use HAProxy's runtime API
- **Map Operations**: Use runtime API endpoints exclusively (no reload required)
- **ACL Operations**: Use runtime API endpoints (no reload required)
- **Mixed Operations**: Server changes applied first via runtime API, then other changes via transaction

**Runtime Requirements for Servers**:
- No `default_server` defined in backend or defaults section
- Backend uses compatible load balancing algorithm (roundrobin, leastconn, first, random)
- Operation not within a transaction
- Proper stats socket and master runtime configuration

**Benefits**: Zero reloads for most server operations, instant updates for map/ACL entries, improved availability, smart fallback to transaction/reload for complex configurations.

**Monitoring**: Look for "server added through runtime" log messages from dataplane API.

### HAProxy Dataplane API v3 Defaults Section Limitation

**Issue**: HAProxy Dataplane API v3 returns HTTP 501 Not Implemented for nested element endpoints on defaults sections.

**Impact**: Cannot fetch individual nested elements (ACLs, HTTP rules, etc.) from defaults sections. Affects configuration comparison and deployment for defaults sections only.

**Workaround**: Defaults sections handled as atomic units using `full_section=true` parameter. All nested elements included in main defaults configuration during fetch/deployment. Configuration changes trigger complete section replacement. Performance impact minimal as defaults sections typically small.

**Implementation**: `dataplane.py` skips nested element fetching for defaults. Comparison ignores nested differences for defaults. Deployment uses `full_section=true` for defaults updates.

This 10x improvement in dataplaneapi startup time is critical for pod restarts and failover. The issue is specific to
the dataplaneapi Go binary version, not the HAProxy core or Alpine version.

### Unified Port Configuration

All Dataplane API instances use port 5555 with environment-specific auth:

- Production: `admin`/`adminpass`
- Validation: `admin`/`validationpass`

### Validation-First Deployment

Every configuration tested in isolation before production deployment.

### No Backward Compatibility

Clean breaks over compatibility layers. Technical debt prevention over migration ease.