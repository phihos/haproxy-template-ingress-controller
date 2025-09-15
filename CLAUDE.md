# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Package Management
- Install dependencies: `uv sync`
- Install with dev dependencies: `uv sync --group dev`
- Add new dependency: `uv add <package>`
- Remove dependency: `uv remove <package>`

### Testing
- **Development workflow**: First run unit tests `uv run pytest -m "not integration and not acceptance"`, fix all failures, then run all tests
- **All tests (recommended)**: `timeout 480 uv run pytest -n auto` - parallel execution, up to 8 minutes (use 480s timeout)
- **Unit tests**: `uv run pytest -m "not integration and not acceptance"`
- **Integration tests**: `uv run pytest -m integration` - Docker-based HAProxy testing
- **E2E tests**: `uv run pytest -m acceptance` - Full Kubernetes cluster testing
- **Coverage**: `uv run pytest --cov=haproxy_template_ic --cov-report=html`
- **Performance requirement**: All tests must complete in under 8 minutes for CI/CD pipelines

#### Test Structure & Options
```
tests/unit/         # Fast unit tests (no external dependencies)
tests/integration/  # Docker-based tests with HAProxy instances  
tests/e2e/         # End-to-end Kubernetes tests (marked 'acceptance')
tests/fixtures/    # Test data and configurations
```

**Debugging Options:**
- Integration: `--keep-containers=on-failure --show-container-logs --verbose-docker`
- E2E: `--keep-namespaces --keep-namespace-on-failure`
- Use `-s` for real-time output, `-n 0` for serial execution with full progress
- Serial debugging: `uv run pytest -n 0 -s -v` for step-by-step execution

#### ⚡ Performance Optimization with --keep-cluster

**IMPORTANT**: Use `--keep-cluster` to reuse existing clusters for repeated E2E test runs:

```bash
# First run: Creates cluster
uv run pytest tests/e2e/test_core_operator.py::test_basic_init --keep-cluster

# Subsequent runs: Reuses existing cluster
uv run pytest tests/e2e/test_config_management.py --keep-cluster

# Manual cleanup when done
kind delete cluster --name pytest-kind
```

**Benefit**: Avoids cluster recreation overhead by reusing the existing Kind cluster.

**How it works**: The `--keep-cluster` flag (provided by pytest-kind) prevents cluster deletion in the teardown phase, allowing subsequent test runs to reuse the existing cluster.

#### Integration Test Features
- **Docker containers**: Automated HAProxy + Dataplane API setup with Alpine 3.1
- **Progress reporting**: Visual indicators, container monitoring, port tracking
- **Failure diagnostics**: Automatic log collection and troubleshooting
- **Progress context**: Use `progress_context("test_name", reporter)` for structured reporting
- **Authentication**: Tests use `admin`/`adminpass`, IP addresses instead of hostnames
- **Performance validation**: Verifies HAProxy 3.1 startup time under 10 seconds

#### E2E Test Features
- **Real Kubernetes**: Creates temporary clusters for full system testing
- **Telepresence integration**: LocalOperatorRunner runs operators locally via Telepresence for rapid iteration
- **Time-based log analysis**: Millisecond-precision log searching with `since_milliseconds` parameter
- **Resource lifecycle**: Tests ConfigMap updates, pod discovery, template rendering
- **Webhook validation**: Tests admission controllers and error handling
- **Socket communication**: Management socket integration for runtime state inspection
- **Cleanup automation**: Namespaces and resources automatically removed unless `--keep-namespaces`

### Code Quality
- Format code: `uv run ruff format`
- Lint code: `uv run ruff check --fix`
- Type checking: `uv run mypy haproxy_template_ic/`
- Security scan: `uv run bandit -c pyproject.toml -r haproxy_template_ic/`
- Dependency hygiene: `uv run deptry .`

### Generated Client
- Regenerate HAProxy Dataplane API client: `bash ./scripts/regenerate_client.sh [--jar path/to/jar]`
  - Downloads the latest HAProxy Dataplane API v3 specification
  - Removes existing generated code and regenerates the complete client
  - Optional `--jar` parameter allows using custom OpenAPI Generator JAR for latest features
  - Built-in lazy loading support when using OpenAPI Generator master branch
  - Includes compatibility workarounds for known OpenAPI Generator bugs

### Docker Build Optimization

The Dockerfile is optimized for iterative development and efficient CI/CD builds:

#### Build Optimization Features
- **Multi-stage caching**: Separates system dependencies, Python dependencies, and application code for maximum cache reuse
- **Optimized layer ordering**: Least frequently changed items first (system packages → Python deps → code)
- **BuildKit cache mounts**: Shared caches across builds with proper cache IDs
- **Minimized context**: Comprehensive `.dockerignore` excludes development files

**Build Improvements:**
- **Parallelized stages**: Multi-stage builds with concurrent execution
- **Layer caching**: Code changes benefit from cached dependency layers
- **Optimized structure**: Dependencies and application code in separate layers
- **CI/CD optimization**: Registry cache support for shared builds

#### Recommended Build Commands
```bash
# Enable BuildKit (required for optimizations)
export DOCKER_BUILDKIT=1

# Local development (persistent cache)
docker build \
  --cache-from type=local,src=/tmp/docker-cache \
  --cache-to type=local,dest=/tmp/docker-cache \
  --target production -t haproxy-template-ic:dev .

# CI/CD with registry cache
docker build \
  --cache-from type=registry,ref=ghcr.io/your-org/haproxy-template-ic:buildcache \
  --cache-to type=inline --target production -t haproxy-template-ic:latest .
```

**Optimization Details:**
- System dependencies cached separately in `system-deps` stage
- UV tool installation cached in `uv-base` stage  
- Python dependencies installed in `dependencies` stage (independent of code changes)
- Application code installed in `build` stage using bind mounts (no COPY needed)
- Runtime stages inherit from `system-deps` to avoid duplicate system setup

### Development Environment
**Main script**: `bash ./scripts/start-dev-env.sh [COMMAND] [OPTIONS]`
- `up`: Start development environment (default)
- `down`/`clean`: Delete the kind cluster
- `logs`: Follow controller logs
- `exec`: Execute shell in controller pod
- `restart`: Restart controller deployment
- `status`: Show deployment status
- Options: `--skip-build`, `--skip-echo`, `--force-rebuild`, `--verbose`, `--watch`, etc.

**Manual setup** (basic builds):
- Build production image: `docker build --target production -t haproxy-template-ic:dev .`
- Build coverage image: `docker build --target coverage -t haproxy-template-ic:coverage .`
- Create kind cluster: `kind create cluster --name haproxy-template-ic-dev`
- Load image to kind: `kind load docker-image haproxy-template-ic:dev --name haproxy-template-ic-dev`

### Application
- **Run operator**: `uv run haproxy-template-ic run --configmap-name=<name>` (or use `version` subcommand)
- **Monitoring endpoints** (require port-forward):
  - Metrics: `curl http://localhost:9090/metrics`
  - Health: `curl http://localhost:8080/healthz`

## Architecture Overview

This is a proof-of-concept Kubernetes ingress controller that enables full Jinja2 templating of HAProxy configurations. The controller watches arbitrary Kubernetes resources and renders templates for HAProxy maps, configs, and certificates.

### Core Components

- **`haproxy_template_ic/__main__.py`**: CLI interface using Click, application entry point
- **`haproxy_template_ic/operator/`**: Kubernetes operator logic using kopf framework
  - `initialization.py`: Startup and shutdown logic
  - `configmap.py`: ConfigMap change handling
  - `pod_management.py`: HAProxy pod discovery and management
  - `synchronization.py`: Resource synchronization orchestration
  - `k8s_resources.py`: Kubernetes resource operations
- **`haproxy_template_ic/models/`**: Pydantic configuration models with IndexedResourceCollection for O(1) resource lookups
  - `config.py`: Configuration validation and parsing
  - `resources.py`: Resource collections and indexing
  - `templates.py`: Template models and validation
  - `context.py`: Template rendering context
- **`haproxy_template_ic/dataplane/`**: HAProxy Dataplane API client and synchronization logic
  - `client.py`: Dataplane API client wrapper
  - `synchronizer.py`: Configuration deployment logic
  - `models.py`: Dataplane API models
  - `utils.py`: Dataplane utilities and helpers
- **`haproxy_template_ic/core/`**: Core functionality (`logging.py`: Structured logging with context injection)
- **`haproxy_template_ic/k8s/`**: Kubernetes integration utilities
  - `field_filter.py`: Resource field filtering
  - `kopf_utils.py`: Kopf framework utilities
  - `resource_utils.py`: Resource manipulation helpers
- **Other components**: `webhook.py` (validating admission webhook handlers), `metrics.py` (Prometheus metrics), `tracing.py` (OpenTelemetry tracing), `templating.py` (Jinja2 engine), `activity.py` (activity tracking), `deployment_state.py` (deployment state management)

### Key Technologies

- **kopf**: Kubernetes operator framework for event handling
- **kr8s**: Modern Kubernetes client library
  - **IMPORTANT**: Use `from kr8s.asyncio.objects import Pod, ConfigMap, Secret` for async operations
  - Never use `from kr8s.objects import ...` in async contexts - those are synchronous only
- **jinja2**: Template engine for HAProxy configurations
- **httpx**: Async HTTP client for Dataplane API integration
- **click**: CLI interface framework
- **uvloop**: High-performance event loop
- **pytest**: Testing framework with custom markers
- **prometheus-client**: Metrics collection and exposure for monitoring
- **pydantic**: Data validation and settings management with type safety

### Deployment Architecture

**Controller Pod** (3 containers):
- Main controller: watches resources, renders templates (ports: 8080 health, 9090 metrics, 9443 webhook)
- Validation HAProxy: config validation (port 8404, minimal config)
- Validation Dataplane API: manages validation instance (port 5555, auth: `admin`/`validationpass`)

**Production HAProxy Pods** (2 containers each):
- HAProxy: production traffic (ports: 80 main, 8404 health - **mandatory**)
- Dataplane API: receives configs (port 5555, auth: `admin`/`adminpass`)

**Flow**: Initial → Validation → Deployment → Ready
**Critical**: Health endpoint required, pod selector matching, shared volumes, validation-first
**Configuration**: Universal ConfigMap (`deploy/base/configmap-universal.yaml`) manages both HAProxy and dataplane configs with runtime API support

#### Port Reference
| Component | Port | Purpose | Notes |
|-----------|------|---------|-------|
| Controller | 8080 | Health (`/healthz`) | |
| Controller | 9090 | Metrics (`/metrics`) | |
| Controller | 9443 | Webhook validation | Optional |
| Validation HAProxy | 8404 | Config validation | |
| Validation API | 5555 | Manages validation | `admin`/`validationpass` |
| Production HAProxy | 80 | Main traffic | HTTP/HTTPS |
| Production HAProxy | 8404 | Health (`/healthz`) | **Mandatory** |
| Production API | 5555 | Config deployment | `admin`/`adminpass` |
| Testing | 8001-8003 | Dummy backends | Dev/test only |

### Current Implementation Status

✅ Complete: Watch arbitrary K8s resources, template HAProxy map/config/certificate files, template snippet system with `{% include %}` support, validating admission webhooks, dataplane API synchronization with validation/deployment, Prometheus metrics, reliable operations with error handling/recovery, distributed tracing with OpenTelemetry, resource indexing with O(1) lookups using IndexedResourceCollection

## Webhook Validation System

Validating admission webhooks prevent faulty resources from being applied, providing immediate feedback on configuration errors.

**Features**: ConfigMap/YAML/template validation, per-resource control, automatic certificate management
**Configuration**: Webhook settings configured via ConfigMap (see Configuration section)
**Certificates**: Uses mounted TLS or generates self-signed for development
**Control**: Set `enable_validation_webhook: true/false` per watched resource type

## ConfigMap Structure

**Required sections**: `pod_selector`, `haproxy_config`
**Optional sections**: `watched_resources`, `maps`, `template_snippets`, `certificates`

### Unified Dataplane Configuration

All dataplane instances use port 5555 with environment-specific authentication:
- **Production**: `admin`/`adminpass` (default)  
- **Validation**: `admin`/`validationpass` (sidecar)

This simplifies configuration management and deployment templates across all environments.

### Resource Indexing

The `index_by` parameter in `watched_resources` configures custom indexing for O(1) resource lookups using JSONPath expressions. Default indexing is by `["metadata.namespace", "metadata.name"]`.

**JSONPath Implementation**: Uses `python-jsonpath` library supporting standard JSONPath syntax:
- Dot notation: `metadata.name`
- Bracket notation: `metadata.labels['kubernetes.io/service-name']`
- Array indexing: `spec.rules[0].host`, negative indexing: `spec.rules[-1].host`

**Library Choice**: `python-jsonpath` selected for JSONPath compliance, active maintenance, and comprehensive syntax support.

**Advanced indexing examples:**
- Service by name: `["metadata.labels['kubernetes.io/service-name']"]`
- Ingress by host: `["spec.rules[0].host"]` 
- Cross-resource matching: `["metadata.namespace", "metadata.labels['app']"]`

### Field Filtering

The `watched_resources_ignore_fields` configuration omits unnecessary fields from indexed resources to reduce memory usage.

**Configuration**: Add JSONPath expressions for fields to remove:
```yaml
watched_resources_ignore_fields:
  - metadata.managedFields  # Default: removes Kubernetes server-side apply metadata
  - metadata.resourceVersion  # Remove version tracking if not needed
  - status  # Remove entire status section if not used in templates
```

**Default**: `metadata.managedFields` ignored (rarely needed in templates, can consume significant memory).

**Common fields to ignore:**
- `metadata.managedFields`: Server-side apply metadata (can be very large)
- `metadata.resourceVersion`: Version tracking (changes frequently)
- `metadata.generation`: Generation counter (if not used)
- `metadata.annotations['kubectl.kubernetes.io/last-applied-configuration']`: Last applied config (can be large)
- `status`: Status information (if not used in templates)

**Implementation**: Field filtering during resource indexing. Deep copy preserves originals. JSONPath expressions compiled/cached (256 paths max). Same ignore_fields for all types. Invalid JSONPath validated at load.

```yaml
data:
  config: |
    pod_selector:
      match_labels: {app: haproxy, component: loadbalancer}
    
    watched_resources_ignore_fields:
      - metadata.managedFields
    
    watched_resources:
      ingresses: 
        api_version: networking.k8s.io/v1
        kind: Ingress
        enable_validation_webhook: true
        index_by: ["metadata.namespace", "metadata.name"]  # Default indexing
      services: 
        api_version: v1
        kind: Service
        enable_validation_webhook: false
        index_by: ["metadata.labels['kubernetes.io/service-name']"]  # Custom indexing
      secrets:
        api_version: v1
        kind: Secret
        enable_validation_webhook: false
        index_by: ["metadata.namespace", "metadata.labels['app']"]  # Multi-field indexing
    
    template_snippets:
      backend-name: "backend_{{ service_name }}_{{ port }}"
    
    maps:
      host.map:
        template: |
          {% for _, ingress in resources.get('ingresses', {}).items() %}
          {% if ingress.spec.rules %}
          {% for rule in ingress.spec.rules %}
          {{ rule.host }} {{ rule.host }}
          {% endfor %}{% endif %}{% endfor %}
    
    haproxy_config:
      template: |
        global
            daemon
        defaults
            mode http
            timeout connect 5000ms
        frontend health
            bind *:8404
            http-request return status 200 if { path /healthz }
        frontend main
            bind *:80
            {% include "backend-routing" %}
    
    certificates:
      tls.pem:
        template: |
          {% for _, secret in resources.get('secrets', {}).items() %}
          {% if secret.type == "kubernetes.io/tls" %}
          {{ secret.data.get('tls.crt') | b64decode }}
          {{ secret.data.get('tls.key') | b64decode }}
          {% endif %}{% endfor %}
```

## Important Architectural Decisions

### HAProxy Version Requirement: 3.1+ (Critical for Startup)
**Decision**: All HAProxy containers MUST use `haproxytech/haproxy-alpine:3.1` or newer.

**Rationale**: Version 3.0 dataplaneapi has slow startup (30-60s) vs. 3.1+ which starts in 3-5s. HAProxy core unaffected - dataplaneapi issue only. Slow startup causes routing failures. **Do NOT use 3.0** despite LTS.

**Measured dataplaneapi startup times:**
- Version 3.0: 30-60+ seconds (requires failureThreshold: 10)
- Version 3.1+: 3-5 seconds (works with failureThreshold: 3)

### Runtime API Configuration Requirements
**Critical**: Runtime API requires proper HAProxy stats socket and dataplane API master socket configuration to avoid "Runtime API not configured, not using it" warnings.

**Required HAProxy Master Socket:**
```bash
haproxy -W -S "/etc/haproxy/haproxy-master.sock,level,admin" -- /etc/haproxy/haproxy.cfg
```

**Required Dataplane API Configuration:**
```yaml
haproxy:
  master_runtime: /etc/haproxy/haproxy-master.sock
```

**Note**: The `-S` flag creates the master socket that dataplane API uses for runtime operations. No separate `stats socket` in global section needed.

**Version Parameter Requirements**: Runtime API operations require `transaction_id` OR `version` parameter. Non-transactional operations need current config version. Implemented in `dataplane.py:505` via `_get_configuration_version()`. Prevents HTTP 400 errors.

### Runtime API Optimization for Zero-Reload Deployments
**Decision**: Controller optimizes deployments by separating runtime-eligible operations from configuration operations to avoid unnecessary HAProxy reloads.

**Implementation:**
- **Server Operations**: Applied without transactions when possible, enabling Go dataplane API to automatically use HAProxy's runtime API
- **Map Operations**: Use runtime API endpoints exclusively (no reload required)
- **ACL Operations**: Use runtime API endpoints (no reload required)
- **Mixed Operations**: Server changes applied first via runtime API, then other changes via transaction

**Runtime Requirements for Servers:**
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

## Important Development Notes

- **K8s Required**: Application only runs in K8s environments. Local development requires kind/minikube.
- **Python 3.13+**: Target version with type hints
- **uv Package Manager**: Use exclusively for Python packages (never pip/poetry)
- **Pre-commit Hooks**: Automatically enforces code quality
- **3-tier Testing Strategy**: Fast unit tests + integration tests with Docker + e2e tests with K8s clusters

## Template System

**Snippets**: Define in `template_snippets`, use with `{% include "snippet-name" %}`
**Variables**: `resources` (IndexedResourceCollections by type)
**Filters**: `b64decode` for base64 strings, plus standard Jinja2 filters

### Resource Access Patterns

**Standard iteration** (all resources of a type):
```jinja2
{% for _, resource in resources.get('ingresses', {}).items() %}
  {{ resource.metadata.name }} in {{ resource.metadata.namespace }}
{% endfor %}
```

**Indexed lookups** (O(1) performance using `index_by` configuration):
```jinja2
{# Get specific resource by index key #}
{% set service = resources.get('services', {}).get_indexed_single('my-service-name') %}
{% if service %}
  Service {{ service.metadata.name }} found
{% endif %}

{# Get all resources matching index key #}
{% for resource in resources.get('secrets', {}).get_indexed('default', 'my-app') %}
  Secret: {{ resource.metadata.name }}
{% endfor %}
```

**Cross-resource matching** using custom indexing:
```jinja2
{# Match services to ingresses using app labels #}
{% for _, ingress in resources.get('ingresses', {}).items() %}
  {% set app_label = ingress.metadata.labels.get('app', '') %}
  {% if app_label %}
    {% for service in resources.get('services', {}).get_indexed('default', app_label) %}
      Ingress {{ ingress.metadata.name }} → Service {{ service.metadata.name }}
    {% endfor %}
  {% endif %}
{% endfor %}
```

**IndexedResourceCollection methods:**
- `get_indexed(*args)`: Returns list of resources matching index key
- `get_indexed_iter(*args)`: Returns iterator of resources (memory efficient for large datasets)
- `get_indexed_single(*args)`: Returns single resource or None (raises error if multiple found)
- `items()`: Iterate over all indexed resources
- `values()`: Iterate over resource values only

**Performance**: Use `get_indexed_iter()` for large result sets. Index keys cached for O(1) lookup. Resource validation prevents invalid data indexing.

## Distributed Tracing

OpenTelemetry tracing for end-to-end observability across template rendering and deployment pipeline.

**Configuration**: Tracing settings configured via ConfigMap
**Operations traced**: Template rendering, dataplane API, Kubernetes operations, pod discovery
**Development**: Set `tracing.console_export: true` in ConfigMap for console output
**Production**: Use `tracing.sample_rate: 0.1` in ConfigMap for reduced overhead, deploy Jaeger collector

## Dataplane API Integration

Uses official OpenAPI-generated HAProxy Dataplane API v3 client (218 endpoints, asyncio-compatible, lazy loading).

**Components**: `HAProxyPodDiscovery`, `DataplaneClient`, `ConfigSynchronizer`
**Process**: Discovery → Validation → Deployment → Monitoring
**Requirements**: Dataplane API enabled (port 5555), matching pod labels, validation sidecars
**Error handling**: Validation failures stop deployment, retry logic, version tracking
**Resource Indexing**: IndexedResourceCollection provides O(1) resource lookups using `from_kopf_index()`


## Monitoring and Observability

**Structured Logging**: Uses structlog with operation correlation, component context, JSON output (set `logging.structured: true` in ConfigMap)
**Prometheus Metrics**: Port 9090, tracks application/resources/templates/dataplane/errors

## Reliability and Error Handling

**Error recovery**: Graceful degradation, validation isolation, state consistency, operational visibility
**Validation-first approach**: Configuration tested before production deployment
**Robust deployment**: Smart change detection, version tracking, deployment rollback
**Operational monitoring**: Comprehensive metrics for debugging and operational tracking

## Configuration

The application is configured via:
- ConfigMap specified by `CONFIGMAP_NAME` environment variable (contains all runtime settings)
- Secret specified by `SECRET_NAME` environment variable (contains credentials)
- Management socket path configurable via ConfigMap

Environment variables (bootstrap parameters only):
- `CONFIGMAP_NAME`: Required ConfigMap name
- `SECRET_NAME`: Required Secret name for credentials

### Runtime Configuration

All runtime settings configured via ConfigMap specified by `CONFIGMAP_NAME` using grouped structure:

```yaml
# Operator runtime settings
operator:
  healthz_port: 8080        # Health check port  
  metrics_port: 9090        # Prometheus metrics port

# Logging configuration
logging:
  verbose: 1                # Log level (0=WARNING, 1=INFO, 2=DEBUG)
  structured: false         # Enable JSON structured logging output

# Distributed tracing configuration
tracing:
  enabled: false            # Enable distributed tracing with OpenTelemetry
  service_name: haproxy-template-ic
  service_version: ""       # Empty uses application version
  jaeger_endpoint: ""       # e.g., "jaeger-collector:14268"
  sample_rate: 1.0         # Tracing sample rate (0.0 to 1.0)
  console_export: false    # Export traces to console for debugging

# Validation sidecar configuration
validation:
  dataplane_host: localhost  # Host for validation dataplane API
  dataplane_port: 5555      # Port for validation dataplane API
```

**Note**: Runtime settings can no longer be configured via environment variables or CLI options. This centralizes all configuration in the ConfigMap for better management and consistency.

## Code Style Guidelines

Follow the style guide in `STYLEGUIDE.md`:
- Use Ruff for formatting and linting
- Type-annotate all public functions
- Descriptive names over abbreviations
- Guard clauses to avoid deep nesting
- Use logging module (not print)
- Keep async code clean with asyncio
- Strict config validation
- Write deterministic tests

### Type Safety and Data Modeling

- **Prefer explicit types over primitives**: Use dataclasses, Pydantic models, or custom classes instead of raw tuples, dicts, or lists
- **Pydantic for external data**: Use Pydantic models for data that comes from external sources (APIs, configs, user input)
- **Dataclasses for internal state**: Use dataclasses for internal data structures that don't need validation
- **Type aliases for clarity**: Create type aliases for complex types to improve readability
- **No magic tuples**: Avoid returning multiple values as tuples; use named tuples or dataclasses instead

Examples:
```python
# ❌ Avoid primitive types
credentials = (("admin", "pass"), ("validator", "pass"))
auth = credentials[0]  # Unclear what this represents

# ✅ Use explicit types
@dataclass
class AuthCredentials:
    username: str
    password: SecretStr

class Credentials(BaseModel):
    dataplane: AuthCredentials
    validation: AuthCredentials

credentials = Credentials(...)
auth = credentials.dataplane  # Clear and type-safe
```

## Development Workflow

**Standard Process**: Feature branch → Plan/implement → Test (`uv run pytest -n auto`) → Quality checks → Self-review → Commit → PR → Review → Merge

**CRITICAL**: All tests (unit, integration, acceptance) must pass before PR merge. Full test suite (`timeout 480 uv run pytest -n auto`) must complete without failures or flaky tests.

**Self-Review**: After changes but before commit, Claude should proactively review changes using `code-reviewer` agent and act on suggestions to ensure quality and catch issues early.

**PR Management:**
- Use [Conventional Commits](https://conventionalcommits.org/) format for PR titles as they become the first line of squashed merge commits: `<type>: <description>`
- **CRITICAL**: After pushing new commits to existing PR branch, ALWAYS update PR description using `gh pr edit <PR_NUMBER> --body "updated description"`
- PR descriptions should describe current state of all changes, not just original changes
- When addressing code review feedback, add summary of fixes/changes made

**Kind Development:**
1. Setup: `bash ./scripts/start-dev-env.sh up`, optionally with `--skip-build` or `--verbose`
2. Monitor: `bash ./scripts/start-dev-env.sh logs` or `status`
3. Debug: Check logs for debugging
4. **CRITICAL: Code Changes**: `bash ./scripts/start-dev-env.sh restart` - MANDATORY after ANY code changes to rebuild Docker image and reload to kind cluster
5. Clean: `bash ./scripts/start-dev-env.sh down` to remove cluster

**⚠️ CRITICAL**: When making code changes in dev environment, MUST rebuild and reload Docker image using `./scripts/start-dev-env.sh restart`. Code changes will NOT take effect without rebuild/reload into kind cluster. Controller runs in containers, not from source.

### Debugging

The project uses [Telepresence](https://www.telepresence.io/) for debugging in Kubernetes:

1. **Setup**: Install Telepresence via package manager or direct download
2. **Start environment**: `./scripts/start-dev-env.sh up`
3. **Enable debug mode**: `./scripts/start-dev-env.sh debug` (sleeps in-cluster controller)
4. **Connect via Telepresence**: `./scripts/start-dev-env.sh telepresence-connect`
5. **Debug locally**: `CONFIGMAP_NAME=haproxy-template-ic-config-dev SECRET_NAME=haproxy-template-ic-credentials uv run haproxy-template-ic run`
7. **Clean up**: `./scripts/start-dev-env.sh telepresence-disconnect && ./scripts/start-dev-env.sh no-debug`

No Docker rebuilds needed for code changes. Application runs locally with full cluster access.

**E2E Test Utilities:**
- **LocalOperatorRunner**: Context manager for running operators locally during tests
- **Log assertions**: `assert_log_line(operator, pattern, since_milliseconds=100)` for timing-sensitive checks
- **Socket commands**: `send_socket_command(operator, "dump all")` for runtime state inspection
- **Time-based search**: `get_log_position_at_time(milliseconds_ago)` for precise log analysis

**Other debugging tools:**
- Metrics: Port-forward 9090, `curl /metrics`
- Tracing: Set `tracing.enabled: true` and `tracing.console_export: true` in ConfigMap
- Logging: Set `logging.structured: true` in ConfigMap
- Webhooks: Enable via ConfigMap webhook configuration, test with `kubectl apply`
- Templates: Watch logs, use `dump config`, test incrementally
- Dataplane: Access via Telepresence networking (e.g., `haproxy-template-ic:5555`)

## Troubleshooting

### Common Issues

**Test Failures:**
- Kind conflicts: Use `--keep-namespaces` for debugging, clean with `kind delete cluster`
- Import errors: Run `uv sync --group dev` to install test dependencies
- Docker permissions: Ensure Docker daemon accessible without sudo
- Timing issues: Use `since_milliseconds` parameter for log assertions that need recent context

**Template Issues:**
- Use correct resource access patterns: `resources.get('type', {}).items()`
- Match snippet names exactly: `{% include "snippet-name" %}`
- Define all referenced maps and certificates in ConfigMap
- Use IP addresses not hostnames in tests (avoid DNS resolution)

**Dataplane API Issues:**
- Check pod selectors/labels match `pod_selector.match_labels` exactly
- Ensure pods are Running with assigned IPs before controller starts
- Verify dataplaneapi port 5555 accessible with correct authentication
- Check HAProxy config syntax before deployment
- **Version 3.0**: Increase `failureThreshold: 10` for slow dataplaneapi startup
- **Version 3.1+**: Use `failureThreshold: 3` for fast startup

**Runtime API Issues:**
- **"Runtime API not configured, not using it"**: Ensure HAProxy runs with `-S` master socket flag and `master_runtime` in dataplane config
- **HTTP 400 "version or transaction not specified"**: Verify current version is fetched before runtime operations
- **Missing master socket**: Ensure HAProxy starts with `-S "/etc/haproxy/haproxy-master.sock,level,admin"`
- **Missing master runtime**: Add `master_runtime: /etc/haproxy/haproxy-master.sock` to dataplane config
- Check `/home/phil/Quellcode/haproxy-template-ic/deploy/base/configmap-universal.yaml` for proper dataplane configuration

**Performance Issues:**
- HAProxy 3.0: dataplaneapi startup takes 30-60+ seconds
- HAProxy 3.1+: dataplaneapi startup takes 3-5 seconds
- Monitor pod startup time with `kubectl get events --sort-by='.firstTimestamp'`

**Configuration Validation:**
- Use `kubectl apply --dry-run=server` to test webhook validation
- Check controller logs for template rendering errors
- Validate Jinja2 syntax with `--webhook-enabled=true`
- Check logs to inspect rendered templates

**ConfigMap Reload Issues:**
- Configuration changes now properly trigger operator reload without infinite loops
- Debug with structured logging: `logging.structured: true` in ConfigMap
- ConfigMap change detection uses DeepDiff for accurate comparison
- Operator lifecycle properly manages event loop reuse across restarts

## Commit Message Guidelines

Use [Conventional Commits](https://conventionalcommits.org/): `<type>: <description>`
**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`, `perf`

## Development Rules

### CRITICAL: No Production Code Changes for Tests
**⚠️ ABSOLUTE RULE**: Production code must NEVER be modified solely to make tests pass. This is the most important development principle in this project.

**What this means:**
- NO environment variable overrides added just for testing
- NO test-only configuration options in production code
- NO conditional logic that checks if code is running in tests
- NO test-specific parameters or methods in production classes
- Test infrastructure MUST adapt to production code, not vice versa

**Examples of violations (DO NOT DO):**
```python
# ❌ WRONG: Adding test-only environment variable override
if os.environ.get("TEST_PORT"):  # Never do this!
    port = int(os.environ["TEST_PORT"])

# ❌ WRONG: Adding test-only configuration
class Config:
    def __init__(self, test_mode=False):  # Never add test_mode!
        self.port = 8080 if not test_mode else 0

# ❌ WRONG: Checking if running in tests
if "pytest" in sys.modules:  # Never check for test runners!
    behavior = "test_behavior"
```

**Correct approach:**
- Tests must work with production code AS IS
- Use fixtures to configure test environments properly
- Mock external dependencies when needed
- Configure test data to work with production requirements

### Other Development Rules
- Always fix failing tests without confirmation
- Run `uv run pytest -n auto` after code changes to verify full test suite passes
- Update tests as mandatory part of API changes in same session - test updates are NOT afterthoughts
- Never edit generated code - regenerate from source specifications
- Prefer module-level imports over local imports in Python
- Use `progress_context` (not `test_progress`) to avoid pytest discovery issues
- **Zero tolerance for flaky tests**: All tests must be deterministic and reliable. Flaky tests must be fixed or removed entirely. No `pytest.mark.skip` for flaky tests. Timing-sensitive tests should use mocking, controlled async primitives, or be redesigned.
- **No defensive programming**: Avoid getattr()/hasattr() patterns. Leverage required field knowledge to access attributes directly. Project uses strongly-typed models (ApplicationState, Config, etc.) that guarantee field presence - use type safety instead of defensive patterns.

## No Backward Compatibility Policy

**CRITICAL**: This project prioritizes clean code over backward compatibility. Always disregard backward compatibility when making improvements.

### Core Principles & Implementation Guidelines

- **Clean breaks over compatibility layers**: Remove deprecated APIs immediately, don't add fallback logic
- **No technical debt accumulation**: Delete old code patterns when introducing new ones
- **Explicit dependencies only**: Use dependency injection, avoid hidden state and implicit coupling
- **Forward-looking design**: Design for the future, not the past
- **Remove deprecated code immediately**: Don't add "backward compatibility" comments or deprecation warnings
- **Avoid fallback logic**: No `if old_way: ... else: new_way` patterns
- **No helper methods for old APIs**: Don't create bridge functions to maintain old interfaces  
- **Clean test updates**: Update test data formats and API calls to match new patterns
- **Explicit over implicit**: Prefer `config.create_template_compiler()` over hidden `_parent_config` injection
- **Package exports**: Packages must export public API through `__init__.py`. External modules import from package, not submodules (e.g., `from haproxy_template_ic.dataplane import DataplaneClient`, not `from haproxy_template_ic.dataplane.client import DataplaneClient`)

### Examples of What NOT to Do vs Clean Approach

```python
# ❌ Don't add backward compatibility
def new_method(self, arg):
    # For backward compatibility with old API...
    if hasattr(self, "_old_attribute"):
        return self._old_method(arg)
    return self._new_implementation(arg)

# ❌ Don't keep deprecated methods
@deprecated("Use new_method instead")
def old_method(self, arg):
    return self.new_method(arg)

# ✅ Clean replacement - remove old method entirely
def compile_template(self, compiler: TemplateCompiler) -> Template:
    """Compile template with explicit dependency injection."""
    return compiler.compile_template(self.template)
```

This ensures the codebase remains lean, maintainable, and technical debt-free.