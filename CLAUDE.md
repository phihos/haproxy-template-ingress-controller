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
- **Integration tests**: `uv run pytest -m integration`
- **E2E tests**: `uv run pytest -m acceptance`
- **Coverage**: `uv run pytest --cov=haproxy_template_ic --cov-report=html`

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

#### Integration Test Features
- **Progress reporting**: Visual indicators, container monitoring, port tracking
- **Failure diagnostics**: Automatic log collection and troubleshooting
- **Progress context**: Use `progress_context("test_name", reporter)` for structured reporting
- **Authentication**: Tests use `admin`/`adminpass`, IP addresses instead of hostnames

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

### Development Environment
- Setup dev environment: `bash ./scripts/start-dev-env.sh`
  - Creates kind cluster and deploys controller with metrics, monitoring, and observability features
  - Sets up echo server for testing Ingress functionality
  - Provides comprehensive troubleshooting tips and monitoring access instructions
- Build production image: `docker build --target production -t haproxy-template-ic:dev .`
- Build coverage image: `docker build --target coverage -t haproxy-template-ic:coverage .`
- Create kind cluster: `kind create cluster --name haproxy-template-ic-dev`
- Load image to kind: `kind load docker-image haproxy-template-ic:dev --name haproxy-template-ic-dev`

### Application
- Run operator: `uv run haproxy-template-ic run --configmap-name=<name>`
- Management socket: `socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock`
- Metrics endpoint: `curl http://localhost:9090/metrics` (requires port-forward)
- Health endpoint: `curl http://localhost:8080/healthz` (requires port-forward)

## Architecture Overview

This is a proof-of-concept Kubernetes ingress controller that enables full Jinja2 templating of HAProxy configurations. The controller watches arbitrary Kubernetes resources and renders templates for HAProxy maps, configs, and certificates.

### Core Components

- **`haproxy_template_ic/__main__.py`**: CLI interface using Click, application entry point
- **`haproxy_template_ic/operator.py`**: Kubernetes operator logic using kopf framework  
- **`haproxy_template_ic/config_models.py`**: Pydantic configuration models with IndexedResourceCollection for O(1) resource lookups
- **`haproxy_template_ic/dataplane.py`**: HAProxy Dataplane API client and synchronization logic
- **`haproxy_template_ic/webhook.py`**: Validating admission webhook handlers using kopf framework
- **`haproxy_template_ic/management_socket.py`**: Unix socket server for runtime state inspection
- **`haproxy_template_ic/metrics.py`**: Prometheus metrics collection and exposure
- **`haproxy_template_ic/tracing.py`**: OpenTelemetry distributed tracing implementation
- **`haproxy_template_ic/resilience.py`**: Retry policies, circuit breakers, and adaptive timeouts
- **`haproxy_template_ic/structured_logging.py`**: Structured logging with context injection
- **`haproxy_template_ic/utils.py`**: Kubernetes utilities (namespace detection)

### Key Technologies

- **kopf**: Kubernetes operator framework for event handling
- **kr8s**: Modern Kubernetes client library  
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
- Validation HAProxy: config validation (port 8081, minimal config)
- Validation Dataplane API: manages validation instance (port 5556, auth: `admin`/`validationpass`)

**Production HAProxy Pods** (2 containers each):
- HAProxy: production traffic (ports: 80 main, 8404 health - **mandatory**)
- Dataplane API: receives configs (port 5555, auth: `admin`/`adminpass`)

**Flow**: Initial → Validation → Deployment → Ready
**Critical**: Health endpoint required, pod selector matching, shared volumes, validation-first

#### Port Reference
| Component | Port | Purpose | Notes |
|-----------|------|---------|-------|
| Controller | 8080 | Health (`/healthz`) | |
| Controller | 9090 | Metrics (`/metrics`) | |
| Controller | 9443 | Webhook validation | Optional |
| Validation HAProxy | 8081 | Config validation | |
| Validation API | 5556 | Manages validation | `admin`/`validationpass` |
| Production HAProxy | 80 | Main traffic | HTTP/HTTPS |
| Production HAProxy | 8404 | Health (`/healthz`) | **Mandatory** |
| Production API | 5555 | Config deployment | `admin`/`adminpass` |
| Testing | 8001-8003 | Dummy backends | Dev/test only |

### Current Implementation Status

- ✅ Watch arbitrary Kubernetes resources
- ✅ Template HAProxy map files  
- ✅ Template `haproxy.cfg` configuration files
- ✅ Template certificate files from Kubernetes Secrets
- ✅ Template snippet system with `{% include %}` support for reusable components
- ✅ Validating admission webhooks for ConfigMaps and watched resources
- ✅ Management socket for state inspection
- ✅ Dataplane API synchronization with validation and deployment
- ✅ Prometheus metrics collection for comprehensive monitoring
- ✅ Resilient operations with retry logic, circuit breakers, and adaptive timeouts
- ✅ Distributed tracing with OpenTelemetry for end-to-end observability
- ✅ High-performance resource indexing with O(1) lookups using IndexedResourceCollection

## Webhook Validation System

Validating admission webhooks prevent faulty resources from being applied, providing immediate feedback on configuration errors.

**Features**: ConfigMap/YAML/template validation, per-resource control, automatic certificate management
**Configuration**: `WEBHOOK_ENABLED=true WEBHOOK_PORT=9443` environment variables or webhook configuration in ConfigMap
**Certificates**: Uses mounted TLS or generates self-signed for development
**Control**: Set `enable_validation_webhook: true/false` per watched resource type

## ConfigMap Structure

**Required sections**: `pod_selector`, `haproxy_config`
**Optional sections**: `watched_resources`, `maps`, `template_snippets`, `certificates`

### Resource Indexing

The `index_by` parameter in `watched_resources` configures custom indexing for O(1) resource lookups. Default indexing is by `["metadata.namespace", "metadata.name"]`.

**Advanced indexing examples**:
- Service by name: `["metadata.labels['kubernetes.io/service-name']"]`
- Ingress by host: `["spec.rules[0].host"]` 
- Cross-resource matching: `["metadata.namespace", "metadata.labels['app']"]`

```yaml
data:
  config: |
    pod_selector:
      match_labels: {app: haproxy, component: loadbalancer}
    
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
      /etc/haproxy/maps/host.map:
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
      /etc/haproxy/certs/tls.pem:
        template: |
          {% for _, secret in resources.get('secrets', {}).items() %}
          {% if secret.type == "kubernetes.io/tls" %}
          {{ secret.data.get('tls.crt') | b64decode }}
          {{ secret.data.get('tls.key') | b64decode }}
          {% endif %}{% endfor %}
```

## Important Development Notes

- **Kubernetes Required**: Application only runs in Kubernetes environments. Local development requires kind or minikube.
- **Python 3.13+**: Target version with type hints support
- **uv Package Manager**: Use exclusively for Python package management (never pip/poetry)
- **Pre-commit Hooks**: Automatically enforces code quality standards
- **Three-tier Testing Strategy**: Fast unit tests + integration tests with Docker + e2e tests with real Kubernetes clusters

## Template System

**Snippets**: Define in `template_snippets`, use with `{% include "snippet-name" %}`
**Variables**: `resources` (IndexedResourceCollections by type), `namespace` (current namespace)
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

**IndexedResourceCollection methods**:
- `get_indexed(*args)`: Returns list of resources matching index key
- `get_indexed_iter(*args)`: Returns iterator of resources (memory efficient for large datasets)
- `get_indexed_single(*args)`: Returns single resource or None (raises error if multiple found)
- `items()`: Iterate over all indexed resources
- `values()`: Iterate over resource values only

**Performance considerations**:
- Use `get_indexed_iter()` for memory efficiency with large result sets
- Index keys are cached for O(1) lookup performance
- Resource validation prevents invalid data from being indexed

## Distributed Tracing

OpenTelemetry tracing for end-to-end observability across template rendering and deployment pipeline.

**Configuration**: `TRACING_ENABLED=true`, `JAEGER_ENDPOINT=jaeger:14268`, `--tracing-enabled`
**Operations traced**: Template rendering, dataplane API, Kubernetes operations, pod discovery
**Development**: `TRACING_CONSOLE_EXPORT=true` for console output
**Production**: Use `TRACING_SAMPLE_RATE=0.1` for performance, deploy Jaeger collector

## Dataplane API Integration

Uses official OpenAPI-generated HAProxy Dataplane API v3 client (218 endpoints, asyncio-compatible, lazy loading).

**Components**: `HAProxyPodDiscovery`, `DataplaneClient`, `ConfigSynchronizer`
**Process**: Discovery → Validation → Deployment → Monitoring
**Requirements**: Dataplane API enabled (port 5555), matching pod labels, validation sidecars
**Error handling**: Validation failures stop deployment, retry logic, version tracking
**Resource Indexing**: IndexedResourceCollection provides O(1) resource lookups using `from_kopf_index()`

## Monitoring and Observability

**Structured Logging**: Uses structlog with operation correlation, component context, JSON output (`STRUCTURED_LOGGING=true`)
**Prometheus Metrics**: Port 9090, tracks application/resources/templates/dataplane/errors
**Management Socket**: `/run/haproxy-template-ic/management.sock` for runtime inspection
- Commands: `dump all|indices|config`, `get maps|template_snippets <name>`

## Resilience and Reliability

**Retry mechanisms**: Exponential backoff, jitter, error categorization, configurable policies
**Circuit breakers**: Automatic failure detection, fast failure, recovery timeouts, per-instance isolation
**Adaptive timeouts**: Dynamic adjustment, operation-specific, bounded limits, metrics tracking
**Error recovery**: Graceful degradation, validation isolation, state consistency, operational visibility

## Configuration

The application is configured via:
- ConfigMap specified by `CONFIGMAP_NAME` environment variable
- CLI options (use `haproxy-template-ic run --help` for details) or environment variables
- Management socket at `/run/haproxy-template-ic/management.sock` (configurable)

Environment variables:
- `CONFIGMAP_NAME`: Required ConfigMap name
- `VERBOSE`: Log level (0=WARNING, 1=INFO, 2=DEBUG)  
- `HEALTHZ_PORT`: Health check port (default: 8080)
- `SOCKET_PATH`: Management socket path (default: `/run/haproxy-template-ic/management.sock`)
- `METRICS_PORT`: Prometheus metrics port (default: 9090)
- `WEBHOOK_ENABLED`: Enable validating admission webhooks (default: false)
- `WEBHOOK_PORT`: Webhook server port (default: 9443)
- `STRUCTURED_LOGGING`: Enable JSON structured logging output (default: false)
- `TRACING_ENABLED`: Enable distributed tracing with OpenTelemetry (default: false)

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

## Development Workflow

**Standard Process**: Feature branch → Plan/implement → Test (`uv run pytest -n auto`) → Quality checks → Self-review → Commit → PR → Review → Merge

**CRITICAL**: Having all tests including unit, integration, and acceptance tests pass reliably is mandatory before merging a PR. The full test suite (`timeout 480 uv run pytest -n auto`) must complete successfully without any failures or flaky tests.

**Self-Review Step**: After all changes have been made but before committing, Claude should proactively review its own changes using the `code-reviewer` agent and act on any resulting suggestions to ensure code quality and catch potential issues early.

**PR Management**:
- Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) format for PR titles as they become the first line of squashed merge commits: `<type>: <description>`
- **CRITICAL**: After pushing new commits to an existing PR branch, ALWAYS update the PR description to reflect the changes using `gh pr edit <PR_NUMBER> --body "updated description"`
- PR descriptions should comprehensively describe the current state of all changes, not just the original changes
- When addressing code review feedback, add a summary of what was fixed/changed in response to the review

**Kind Development**:
1. Setup: `bash ./scripts/start-dev-env.sh`, build/load image
2. Test: Run unit/integration/e2e tests with debugging options
3. Debug: Port-forward management socket, inspect with `dump all`

**Debugging**:
- Metrics: Port-forward 9090, `curl /metrics`
- Tracing: `TRACING_ENABLED=true TRACING_CONSOLE_EXPORT=true`
- Logging: `STRUCTURED_LOGGING=true`
- Webhooks: `WEBHOOK_ENABLED=true`, test with `kubectl apply`
- Templates: Watch logs, use `dump config`, test incrementally
- Dataplane: Port-forward 5555, test with curl

## Troubleshooting

**Common**: Test failures (kind conflicts, use `--keep-namespaces`), import errors (`uv sync --group dev`), Docker permissions
**Templates**: Use correct resource access patterns, match snippet names, define all referenced maps, use IP addresses not hostnames
**Dataplane**: Check pod selectors/labels, ensure Running pods with IPs, verify port 5555, check HAProxy config syntax

## Commit Message Guidelines

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/): `<type>: <description>`
**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`, `perf`

## Development Rules

- Always fix failing tests without asking confirmation
- Run `uv run pytest -n auto` after code changes to verify full test suite passes
- Update tests as mandatory part of API changes in same session - test updates are NOT an afterthought
- Never edit generated code - regenerate from source specifications
- Prefer module-level imports over local imports in Python
- Use `progress_context` (not `test_progress`) to avoid pytest discovery issues

## No Backward Compatibility Policy

**CRITICAL**: This project prioritizes clean code over backward compatibility. Always disregard backward compatibility when making improvements.

### Core Principles

- **Clean breaks over compatibility layers**: Remove deprecated APIs immediately, don't add fallback logic
- **No technical debt accumulation**: Delete old code patterns when introducing new ones
- **Explicit dependencies only**: Use dependency injection, avoid hidden state and implicit coupling
- **Forward-looking design**: Design for the future, not the past

### Implementation Guidelines

- **Remove deprecated code immediately**: Don't add "backward compatibility" comments or deprecation warnings
- **Avoid fallback logic**: No `if old_way: ... else: new_way` patterns
- **No helper methods for old APIs**: Don't create bridge functions to maintain old interfaces  
- **Clean test updates**: Update test data formats and API calls to match new patterns
- **Explicit over implicit**: Prefer `config.create_template_compiler()` over hidden `_parent_config` injection

### Examples of What NOT to Do

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
```

### Examples of Clean Approach

```python
# ✅ Clean replacement - remove old method entirely
def compile_template(self, compiler: TemplateCompiler) -> Template:
    """Compile template with explicit dependency injection."""
    return compiler.compile_template(self.template)
```

This policy ensures the codebase remains lean, maintainable, and free of technical debt.
