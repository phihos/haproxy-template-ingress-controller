# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Package Management
- Install dependencies: `uv sync`
- Install with dev dependencies: `uv sync --group dev`
- Add new dependency: `uv add <package>`
- Remove dependency: `uv remove <package>`

### Testing
- Run unit tests (fast): `uv run pytest` or `uv run pytest -m "not slow"`
- Run acceptance tests (slow): `uv run pytest -m "slow"`
- Run all tests: `uv run pytest tests` and then `uv run pytest -m "slow"`
- Single test file: `uv run pytest tests/unit/test_config.py`
- With coverage: `uv run pytest --cov=haproxy_template_ic --cov-report=html`

### Code Quality
- Format code: `uv run ruff format`
- Lint code: `uv run ruff check --fix`
- Type checking: `uv run mypy haproxy_template_ic/`
- Security scan: `uv run bandit -c pyproject.toml -r haproxy_template_ic/`
- Dependency hygiene: `uv run deptry .`

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
- Run CLI: `uv run haproxy-template-ic --configmap-name=<name>`
- Management socket: `socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock`
- Metrics endpoint: `curl http://localhost:9090/metrics` (requires port-forward)
- Health endpoint: `curl http://localhost:8080/healthz` (requires port-forward)

## Architecture Overview

This is a proof-of-concept Kubernetes ingress controller that enables full Jinja2 templating of HAProxy configurations. The controller watches arbitrary Kubernetes resources and renders templates for HAProxy maps, configs, and certificates.

### Core Components

- **`haproxy_template_ic/__main__.py`**: CLI interface using Click, application entry point
- **`haproxy_template_ic/operator.py`**: Kubernetes operator logic using kopf framework
- **`haproxy_template_ic/config.py`**: Configuration data structures with Jinja2 template compilation
- **`haproxy_template_ic/dataplane.py`**: HAProxy Dataplane API client and synchronization logic
- **`haproxy_template_ic/management_socket.py`**: Unix socket server for runtime state inspection
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

### Deployment Architecture

Production deployments require:
1. HAProxy pods with Dataplane API servers
2. Validation sidecars with identical HAProxy setup
3. ConfigMap defining pod selectors, watched resources, and Jinja2 templates
4. The controller watches resources and pushes validated configs via Dataplane API

### Current Implementation Status

- ✅ Watch arbitrary Kubernetes resources
- ✅ Template HAProxy map files  
- ✅ Template `haproxy.cfg` configuration files
- ✅ Template certificate files from Kubernetes Secrets
- ✅ Template snippet system with `{% include %}` support for reusable components
- ✅ Management socket for state inspection
- ✅ Dataplane API synchronization with validation and deployment
- ✅ Prometheus metrics collection for comprehensive monitoring
- ✅ Resilient operations with retry logic, circuit breakers, and adaptive timeouts
- ✅ Distributed tracing with OpenTelemetry for end-to-end observability

## Important Development Notes

- **Kubernetes Required**: Application only runs in Kubernetes environments. Local development requires kind or minikube.
- **Python 3.13+**: Target version with type hints support
- **uv Package Manager**: Use exclusively for Python package management (never pip/poetry)
- **Pre-commit Hooks**: Automatically enforces code quality standards
- **Dual Testing Strategy**: Fast unit tests + slow acceptance tests with real Kubernetes clusters

## Template Snippet System

The controller supports reusable template snippets using Jinja2's `{% include %}` functionality:

- **Definition**: Define snippets in the `template_snippets` section of the ConfigMap
- **Usage**: Include snippets in any template (maps, configs, certificates) with `{% include "snippet-name" %}`
- **Features**: Supports nested includes, template variables, and comprehensive error handling
- **Implementation**: Custom `SnippetLoader` class extends Jinja2's `BaseLoader` to resolve snippet names

Example:
```yaml
template_snippets:
  backend-name: "backend_{{ service_name }}_{{ port }}"
  
maps:
  /etc/haproxy/maps/backends.map:
    template: |
      {% for service in services %}
      {% include "backend-name" %} server entry here
      {% endfor %}
```

Key implementation details:
- Snippets are parsed before other templates to ensure availability
- Each template environment includes access to all defined snippets
- Missing snippet references raise `TemplateNotFound` exceptions with clear error messages
- Configuration reload recreates snippet environments to prevent caching issues

### Built-in Template Filters

The controller provides custom Jinja2 filters for common operations:

- **`b64decode`**: Decodes base64-encoded strings (e.g., `{{ secret.data.cert | b64decode }}`)
- **Standard Jinja2 filters**: All standard filters are available (length, upper, lower, etc.)

Example usage:
```yaml
certificates:
  /etc/haproxy/certs/tls.pem:
    template: |
      {% for _, secret in resources.get('secrets', {}).items() %}
      {% if secret.type == "kubernetes.io/tls" %}
      {{ secret.data.get('tls.crt') | b64decode }}
      {{ secret.data.get('tls.key') | b64decode }}
      {% endif %}
      {% endfor %}
```

## Distributed Tracing

The controller supports distributed tracing with OpenTelemetry for end-to-end observability across the entire template rendering and deployment pipeline. This provides detailed insights into request flows, performance bottlenecks, and error attribution.

### Features

- **End-to-end correlation**: Track individual configuration changes from Kubernetes events through template rendering to HAProxy deployment
- **Performance analysis**: Identify bottlenecks in template rendering, API calls, and deployment operations
- **Error attribution**: Quickly identify where failures occur in complex workflows with detailed span context
- **Automatic instrumentation**: Built-in instrumentation for HTTP requests (via HTTPX) and async operations
- **Multiple exporters**: Support for Jaeger, console output, and other OpenTelemetry-compatible backends

### Configuration

Enable distributed tracing using CLI flags or environment variables:

```bash
# Enable tracing with CLI flag
uv run haproxy-template-ic --configmap-name=my-config --tracing-enabled

# Enable tracing with environment variables
export TRACING_ENABLED=true
export JAEGER_ENDPOINT=jaeger-collector:14268
export TRACING_SERVICE_NAME=haproxy-template-ic
export TRACING_SERVICE_VERSION=1.0.0
```

Environment variables:
- `TRACING_ENABLED`: Enable distributed tracing (default: false)
- `JAEGER_ENDPOINT`: Jaeger collector endpoint (e.g., "jaeger:14268")
- `TRACING_SERVICE_NAME`: Service name for traces (default: "haproxy-template-ic")
- `TRACING_SERVICE_VERSION`: Service version for traces (default: "1.0.0")
- `TRACING_SAMPLE_RATE`: Sampling rate from 0.0 to 1.0 (default: 1.0)
- `TRACING_CONSOLE_EXPORT`: Enable console trace export for development (default: false)

### Traced Operations

The controller automatically creates spans for key operations:

#### Template Operations
- **Template rendering**: Individual spans for HAProxy config, maps, and certificates
- **Template snippet resolution**: Track include operations and nested templates
- **Configuration validation**: Trace template compilation and variable resolution

#### Dataplane API Operations
- **Pod discovery**: Track HAProxy instance discovery and filtering
- **Configuration validation**: Trace validation API calls with retry and circuit breaker context
- **Configuration deployment**: Track deployment operations with version information
- **Synchronization workflows**: End-to-end spans for complete sync processes

#### Kubernetes Operations
- **ConfigMap operations**: Track configuration loading and change detection
- **Resource watching**: Trace resource index updates and event processing
- **Namespace operations**: Track namespace detection and resource queries

### Span Attributes and Events

Each span includes rich metadata for debugging and analysis:

```
Span: render_haproxy_config_template
├── template.type: "haproxy_config"
├── template.path: "/etc/haproxy/haproxy.cfg"
├── template_size: 2048
├── template_vars_count: 12
├── operation.category: "template_rendering"
└── Events:
    ├── haproxy_config_rendered
    └── sync_started
```

```
Span: dataplane_validate
├── dataplane.operation: "validate"
├── dataplane.instance_url: "http://10.244.0.5:5555"
├── config_size: 2048
├── operation.category: "dataplane_api"
└── Events:
    ├── validation_successful
    └── circuit_breaker_closed
```

### Development and Debugging

For local development, enable console tracing to see traces in logs:

```bash
export TRACING_ENABLED=true
export TRACING_CONSOLE_EXPORT=true
uv run haproxy-template-ic --configmap-name=my-config
```

This outputs structured trace information to the console alongside regular logs.

### Production Deployment

For production deployments with Jaeger:

1. **Deploy Jaeger**: Set up Jaeger collector in your cluster
2. **Configure endpoint**: Set `JAEGER_ENDPOINT` to your Jaeger collector
3. **Adjust sampling**: Set `TRACING_SAMPLE_RATE` for appropriate overhead (e.g., 0.1 for 10% sampling)
4. **Monitor performance**: Use Jaeger UI to analyze traces and identify bottlenecks

Example Kubernetes deployment with tracing:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: haproxy-template-ic
spec:
  template:
    spec:
      containers:
      - name: haproxy-template-ic
        image: haproxy-template-ic:latest
        env:
        - name: CONFIGMAP_NAME
          value: haproxy-template-ic-config
        - name: TRACING_ENABLED
          value: "true"
        - name: JAEGER_ENDPOINT
          value: jaeger-collector:14268
        - name: TRACING_SAMPLE_RATE
          value: "0.1"
```

### Performance Impact

- **Overhead**: Minimal performance impact when properly configured
- **Sampling**: Use sampling rates < 1.0 in high-throughput environments
- **Async export**: Spans are exported asynchronously without blocking operations
- **Graceful degradation**: Tracing failures don't affect application functionality

## Dataplane API Integration

The controller implements full Dataplane API synchronization to deploy rendered configurations to HAProxy instances:

### Architecture

- **Pod Discovery**: Automatically discovers HAProxy pods using configured label selectors
- **Validation Sidecars**: Validates configurations on dedicated sidecar instances before production deployment
- **Production Deployment**: Pushes validated configurations to production HAProxy instances via Dataplane API
- **Error Handling**: Comprehensive error handling with detailed logging for failed operations

### Key Components

- **`HAProxyPodDiscovery`**: Discovers HAProxy pods matching label selectors, distinguishes validation vs production pods
- **`DataplaneClient`**: HTTP client for Dataplane API operations (validation, deployment, version retrieval)
- **`ConfigSynchronizer`**: Orchestrates the complete sync process with validation and deployment phases

### Configuration Requirements

HAProxy pods must be configured with:
- **Dataplane API enabled**: Default port 5555 (configurable via `haproxy-template-ic/dataplane-port` annotation)
- **Pod labels**: Must match the `pod_selector.match_labels` in the ConfigMap
- **Validation sidecars**: Pods labeled with `haproxy-template-ic/role: validation` are used for config validation

### Synchronization Process

1. **Discovery**: Find all HAProxy pods matching the selector
2. **Separation**: Separate validation sidecars from production instances
3. **Validation**: Test configuration on validation sidecars first
4. **Deployment**: Deploy to production instances only after successful validation
5. **Monitoring**: Log results and track configuration versions

Example pod selector configuration:
```yaml
pod_selector:
  match_labels:
    app: haproxy
    component: loadbalancer
```

### Required Map Templates

The HAProxy configuration references several map files that must be defined in your configuration:

- **`/etc/haproxy/maps/host.map`**: Maps host headers to normalized identifiers for routing
- **`/etc/haproxy/maps/path-exact.map`**: Maps host+path combinations to backends using exact matching
- **`/etc/haproxy/maps/path-prefix-exact.map`**: Maps host+path combinations using prefix matching
- **`/etc/haproxy/maps/path-prefix.map`**: Maps host+path combinations using prefix matching with trailing slash

Example host map template:
```yaml
maps:
  /etc/haproxy/maps/host.map:
    template: |
      # Maps host headers to normalized identifiers
      {% for _, ingress in resources.get('ingresses', {}).items() %}
      {% if ingress.spec and ingress.spec.rules %}
      {% for rule in ingress.spec.rules %}
      {% if rule.host %}
      {{ rule.host }} {{ rule.host }}
      {% endif %}
      {% endfor %}
      {% endif %}
      {% endfor %}
```

### Error Handling

- **Validation failures**: Stop deployment if any validation sidecar rejects the configuration
- **Network errors**: Retry logic with detailed error reporting
- **Version tracking**: Each successful deployment tracks the HAProxy configuration version
- **Partial failures**: Continue deploying to other instances if individual pods fail

## Monitoring and Observability

The controller provides comprehensive monitoring capabilities through Prometheus metrics, management socket inspection, and structured logging:

### Structured Logging

The controller supports both traditional and structured JSON logging with automatic context injection:

- **Operation correlation**: Each operation gets a unique ID for tracing across log entries
- **Component context**: Automatic tagging of log entries by component (operator, dataplane, management)
- **Resource context**: Automatic inclusion of Kubernetes resource metadata (type, namespace, name)
- **JSON output**: Optional structured JSON format for log aggregation systems
- **Context managers**: Programmatic context management for nested operations

Enable structured logging with `--structured-logging` or `STRUCTURED_LOGGING=true` for JSON output suitable for log aggregation systems like ELK or Fluentd.

### Prometheus Metrics

The controller exposes metrics on port 9090 (configurable via `--metrics-port` or `METRICS_PORT`):

- **Application metrics**: Version info, uptime, and runtime information
- **Resource tracking**: Counts of watched Kubernetes resources by type and namespace
- **Template rendering**: Success/failure counts and timing histograms for all template types
- **HAProxy instances**: Counts of production and validation pod instances
- **Dataplane API**: Request counts, timing, and error rates for all API operations
- **Configuration**: Reload success/failure counts and timing
- **Management socket**: Connection counts and command execution metrics
- **Error tracking**: Categorized error counts by component and type

Example metrics:
```
# Application info
haproxy_template_ic_info{version="1.0.0"} 1

# Watched resources
haproxy_template_ic_watched_resources_total{resource_type="ingresses",namespace="default"} 5

# Template rendering
haproxy_template_ic_template_renders_total{template_type="haproxy_config",status="success"} 42
haproxy_template_ic_template_render_duration_seconds{template_type="map"} 0.003

# Dataplane API operations  
haproxy_template_ic_dataplane_requests_total{operation="validate",status="success"} 15
haproxy_template_ic_dataplane_duration_seconds{operation="deploy"} 0.125
```

### Management Socket

The Unix socket at `/run/haproxy-template-ic/management.sock` provides runtime state inspection:

```bash
# Dump complete operator state
echo "dump all" | socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock

# Dump specific components
echo "dump indices" | socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock
echo "dump config" | socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock

# Get specific configuration elements
echo "get maps /etc/haproxy/maps/host.map" | socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock
echo "get template_snippets backend-name" | socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock
```

### Deployment Monitoring

For production deployments, consider:
- ServiceMonitor CRD for Prometheus scraping
- Grafana dashboards for metrics visualization  
- Alerting rules for error rates and performance thresholds
- Log aggregation for detailed troubleshooting

## Resilience and Reliability

The controller implements comprehensive resilience patterns to handle failures gracefully in production environments:

### Retry Mechanisms

- **Exponential backoff**: Automatic retry with increasing delays to avoid overwhelming failing services
- **Jitter**: Random delay variations to prevent thundering herd effects
- **Error categorization**: Different retry strategies based on error types (network, rate limiting, server errors)
- **Configurable policies**: Customizable retry attempts, delays, and error categories

### Circuit Breaker Pattern

- **Failure detection**: Automatically opens circuits when failure thresholds are exceeded
- **Fast failure**: Prevents cascading failures by failing fast when services are unavailable
- **Automatic recovery**: Attempts to close circuits after recovery timeouts
- **Per-instance isolation**: Individual circuit breakers for each HAProxy instance

### Adaptive Timeouts

- **Dynamic adjustment**: Timeouts increase after failures and decrease after successes  
- **Per-operation customization**: Different timeout strategies for validation vs deployment
- **Bounded adaptation**: Minimum and maximum timeout limits prevent extreme values
- **Integrated monitoring**: Timeout adjustments are tracked via metrics

### Error Recovery Strategies

- **Graceful degradation**: Continue operating with partial functionality when some instances fail
- **Validation isolation**: Failed validation sidecars don't block deployments to healthy instances  
- **State consistency**: Configuration versions track successful deployments across instances
- **Operational visibility**: All resilience events are logged with structured context

Example configuration:
```python
retry_policy = RetryPolicy(
    max_attempts=5,
    base_delay=2.0,
    max_delay=30.0,
    timeout_config=TimeoutConfig(
        initial_timeout=15.0,
        max_timeout=60.0
    )
)
```

## Configuration

The application is configured via:
- ConfigMap specified by `CONFIGMAP_NAME` environment variable
- CLI options or environment variables (see `__main__.py`)
- Management socket at `/run/haproxy-template-ic/management.sock` (configurable)

Environment variables:
- `CONFIGMAP_NAME`: Required ConfigMap name
- `VERBOSE`: Log level (0=WARNING, 1=INFO, 2=DEBUG)  
- `HEALTHZ_PORT`: Health check port (default: 8080)
- `SOCKET_PATH`: Management socket path (default: `/run/haproxy-template-ic/management.sock`)
- `METRICS_PORT`: Prometheus metrics port (default: 9090)
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

## Troubleshooting

### Common Issues

- **Test failures**: Check if kind clusters conflict, use `--keep-cluster` for debugging
- **Import errors**: Run `uv sync --group dev` to ensure all dependencies installed
- **Docker issues**: Ensure user can run Docker commands (add to docker group on Linux)
- **Kind clusters**: Delete with `kind delete cluster --name <name>` if stuck

### Template Rendering Issues

- **"'Store object' has no attribute 'spec'"**: This error was fixed in the operator by properly converting kopf index stores to resource objects. Templates now correctly access Kubernetes resource attributes.
- **TemplateNotFound errors**: Ensure snippet names in `{% include %}` directives match those defined in `template_snippets`
- **Resource access patterns**: Use `{% for key, resource in resources.get('resource_type', {}).items() %}` to access watched resources
- **"Failed to decode base64 value"**: Ensure base64 data is properly encoded before using the `b64decode` filter
- **Missing map files**: Ensure all map files referenced in HAProxy config are defined in the `maps` section

### Dataplane API Issues

- **"No HAProxy instances found"**: Check pod selector configuration and ensure HAProxy pods have matching labels
- **"Pod has no IP address"**: Pods must be in Running state with assigned IP addresses
- **"Configuration validation failed"**: Check HAProxy config syntax and ensure validation sidecars are accessible
- **"Connection refused"**: Verify Dataplane API is enabled on port 5555 (or custom port via annotation)
- **"Configuration deployment failed"**: Check HAProxy logs for configuration errors and network connectivity

Always fix failing tests and checks without asking for confirmation.