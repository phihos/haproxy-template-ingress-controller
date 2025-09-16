# API Reference

This document serves as a comprehensive guide to all APIs offered by the Ingress Controller.

It includes detailed coverage of the API itself, Python interfaces, and documentation for HaProxy components.

## Contents

- [CLI Commands](#cli-commands)
- [HTTP Endpoints](#http-endpoints)
- [Management Socket](#management-socket)
- [Dataplane API](#dataplane-api)
- [Python API](#python-api)

## CLI Commands

This section covers all available command-line interface (CLI) commands for configuring and managing the HAProxy Ingress
Controller.

### haproxy-template-ic

```bash
haproxy-template-ic COMMAND [OPTIONS]
```

**Note**: Runtime settings (logging, tracing, ports, etc.) are configured via ConfigMap rather than CLI options.

### run

Start the operator:

```bash
haproxy-template-ic run [OPTIONS]
```

Options:

- `--configmap-name` / `-c` - ConfigMap containing configuration (required)
- `--secret-name` / `-s` - Secret containing HAProxy credentials (required)

Environment variables:

- `CONFIGMAP_NAME` - ConfigMap name (alternative to --configmap-name)
- `SECRET_NAME` - Secret name (alternative to --secret-name)

### version

Show version information:

```bash
haproxy-template-ic version
```

## Environment Variables

### Required (Bootstrap Only)

| Variable         | Description                                         | Default |
|------------------|-----------------------------------------------------|---------|
| `CONFIGMAP_NAME` | ConfigMap name containing all runtime configuration | -       |
| `SECRET_NAME`    | Secret name containing HAProxy credentials          | -       |

### Runtime Configuration

**Important**: All runtime settings (logging, tracing, ports, etc.) are configured via the ConfigMap specified by
`CONFIGMAP_NAME`.

Example ConfigMap structure for runtime settings:

```yaml
data:
  config: |
    # Operator runtime settings
    operator:
      healthz_port: 8080
      metrics_port: 9090

    # Logging configuration
    logging:
      verbose: 1                # Log level (0=WARNING, 1=INFO, 2=DEBUG)
      structured: false         # Enable JSON structured logging

    # Distributed tracing configuration
    tracing:
      enabled: false            # Enable OpenTelemetry tracing
      service_name: haproxy-template-ic
      jaeger_endpoint: ""       # e.g., "jaeger-collector:14268"
      sample_rate: 1.0         # Tracing sample rate (0.0 to 1.0)
      console_export: false    # Export traces to console

    # Validation sidecar configuration
    validation:
      dataplane_host: localhost
      dataplane_port: 5555
```

## HTTP Endpoints

This section outlines the HTTP endpoints exposed by the HAProxy Ingress Controller. These endpoints enable programmatic
interaction with the controller for configuration, monitoring, and management tasks.

### Health Check

```http
GET /healthz
```

Response:

```json
{
  "status": "healthy"
}
```

### Prometheus Metrics

```http
GET /metrics
```

Metrics:

- `haproxy_template_ic_info` - Version info
- `haproxy_template_ic_rendered_templates_total` - Template render count by status
- `haproxy_template_ic_template_render_duration_seconds` - Template render time
- `haproxy_template_ic_config_reload_duration_seconds` - Configuration reload time
- `haproxy_template_ic_dataplane_api_requests_total` - Dataplane API request count by operation and status
- `haproxy_template_ic_dataplane_api_duration_seconds` - Dataplane API operation time
- `haproxy_template_ic_watched_resources_total` - Resource count by type and namespace
- `haproxy_template_ic_haproxy_instances_total` - HAProxy instance count by type
- `haproxy_template_ic_haproxy_sync_results_total` - HAProxy sync results by outcome
- `haproxy_template_ic_webhook_requests_total` - Webhook validation request count
- `haproxy_template_ic_webhook_request_duration_seconds` - Webhook processing time
- `haproxy_template_ic_errors_total` - Error count by type and component
- `haproxy_template_ic_management_socket_connections_total` - Management socket connections
- `haproxy_template_ic_management_socket_commands_total` - Management socket commands
- `haproxy_template_ic_debouncer_triggers_total` - Debouncer trigger events
- `haproxy_template_ic_debouncer_renders_total` - Template renders by trigger type

### Validation Webhook

```http
POST /validate
```

Admission webhook endpoint for validating resources.

Request:

```json
{
  "apiVersion": "admission.k8s.io/v1",
  "kind": "AdmissionReview",
  "request": {
    "uid": "...",
    "object": {
      ...
    }
  }
}
```

Response:

```json
{
  "apiVersion": "admission.k8s.io/v1",
  "kind": "AdmissionReview",
  "response": {
    "uid": "...",
    "allowed": true,
    "warnings": [
      "..."
    ]
  }
}
```

## Management Socket

The **management socket** provides a low-level interface for runtime configuration, monitoring, and control of
HAProxy instances. It allows dynamic adjustments without restarting the service.

> **Security Warning**: The management socket exposes sensitive configuration and resource data. Ensure proper RBAC and
> pod security policies are in place.

### Connection

```bash
socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock
```

### Commands

#### dump all

Get a complete state:

```
dump all
```

Response:

```json
{
  "config": {
    ...
  },
  "haproxy_config_context": {
    ...
  },
  "metadata": {
    ...
  },
  "indices": {
    ...
  }
}
```

#### Dump indices

Get resource indices:

```
dump indices
```

Response:

```json
{
  "services_index": {
    ...
  },
  "ingresses_index": {
    ...
  },
  "secrets_index": {
    ...
  }
}
```

#### Dump index

Get a specific index:

```
dump index services
```

Response:

```json
{
  "('default', 'web'): {...},
  "('default', 'api'): {...}
}
```

#### Dump config

Get rendered configuration:

```
dump config
```

Response:

```json
{
  "haproxy_config": "...",
  "maps": {
    ...
  },
  "certificates": {
    ...
  }
}
```

#### Get host maps

Get specific map:

```
get maps /etc/haproxy/maps/hosts.map
```

Response:

```
example.com backend_web
api.example.com backend_api
```

#### Get template snippets

Get a specific snippet:

```
get template_snippets backend-name
```

Response:

```
backend_{{ service }}_{{ port }}
```

## Dataplane API

The Data Plane API enables real-time updates to HAProxy's configuration, including load balancing rules, server
management, and runtime adjustments. It bridges the Ingress Controller with HAProxy's core functionality for seamless
orchestration.

### Authentication

Production pods:

```bash
curl -u admin:adminpass http://haproxy:5555/v3/
```

Validation sidecar:

```bash
curl -u admin:validationpass http://localhost:5555/v3/
```


### Key Endpoints

#### Configuration

```http
GET /v3/services/haproxy/configuration/global
GET /v3/services/haproxy/configuration/frontends
GET /v3/services/haproxy/configuration/backends
```

#### Maps

```http
GET /v3/services/haproxy/runtime/maps
POST /v3/services/haproxy/runtime/maps
PUT /v3/services/haproxy/runtime/maps/{name}
```

#### Certificates

```http
GET /v3/services/haproxy/storage/ssl_certificates
POST /v3/services/haproxy/storage/ssl_certificates
PUT /v3/services/haproxy/storage/ssl_certificates/{name}
```

#### Reload

```http
PUT /v3/services/haproxy/actions/reload
```

## Python API

For developers and contributors, the **Python API** covers the python code for the controller.

### Import Paths

The codebase uses a modular package structure with backward compatibility:

#### Legacy Imports (Deprecated but Functional)

```python
# Old flat structure - still works via wrapper modules
from haproxy_template_ic.config_models import Config
from haproxy_template_ic.dataplane import DataplaneClient
from haproxy_template_ic.debouncer import Debouncer
```

#### Modern Modular Imports (Recommended)

```python
# New organized structure
from haproxy_template_ic.models.config import Config
from haproxy_template_ic.k8s.kopf_utils import IndexedResourceCollection
from haproxy_template_ic.dataplane.client import DataplaneClient
from haproxy_template_ic.dataplane.synchronizer import ConfigSynchronizer
from haproxy_template_ic.k8s.resource_utils import validate_resource
from haproxy_template_ic.operator.utils import get_current_namespace
```

### Testing Utilities

#### LocalOperatorRunner

Context manager for running operators locally during tests:

```python
from tests.e2e.utils import LocalOperatorRunner

with LocalOperatorRunner(
        configmap_name="test-config",
        secret_name="test-secret",
        namespace="test-ns",
        verbose=2,
        collect_coverage=True
) as operator:
    # Operator process management
    assert operator.is_running()

    # Log analysis with millisecond precision  
    position = operator.get_log_position_at_time(500)  # 500ms ago
    logs = operator.get_logs(since_index=position)

    # Socket communication
    response = operator.send_socket_command("dump all")
```

**Constructor Parameters:**

- `configmap_name: str` - ConfigMap containing operator configuration
- `secret_name: str` - Secret containing credentials
- `namespace: str` - Kubernetes namespace to operate in
- `verbose: int` - Logging level (0=WARNING, 1=INFO, 2=DEBUG)
- `collect_coverage: bool` - Enable code coverage collection
- `kubeconfig_path: Optional[str]` - Custom kubeconfig file path

**Methods:**

- `start() -> None` - Start operator process
- `stop() -> None` - Stop operator process gracefully
- `is_running() -> bool` - Check if process is active
- `get_logs(since_index: int = 0) -> str` - Get operator logs
- `get_log_position() -> int` - Current number of log lines
- `get_log_position_at_time(milliseconds_ago: float) -> int` - Log position N milliseconds ago
- `wait_for_log(pattern: str, timeout: float = 30, since_index: int = 0) -> bool` - Wait for log pattern
- `send_socket_command(command: str, retries: int = 3) -> Optional[Dict[str, Any]]` - Send socket command

#### Log Assertion Helpers

```python
from tests.e2e.utils import assert_log_line, send_socket_command, count_log_occurrences

# Wait for specific log with millisecond timing
assert_log_line(
    operator,
    "✅ Configuration loaded successfully",
    timeout=10,
    since_milliseconds=200  # Include logs from last 200ms
)

# Socket-based state inspection
response = send_socket_command(operator, "dump all")
config = response["config"]

# Count log occurrences for loop detection
reload_count = count_log_occurrences(operator, "Config has changed")
```

**assert_log_line Parameters:**

- `operator: LocalOperatorRunner` - Operator instance
- `expected_log_line: str` - Log text to search for (substring match)
- `timeout: float = 5` - Maximum wait time in seconds
- `since_milliseconds: float = 0` - Include logs from last N milliseconds

### Method Signature Changes

#### Time Resolution Changes

Previous versions used seconds; current version uses milliseconds for higher precision:

```python
# Old (deprecated)
operator.get_log_position_at_time(seconds_ago=1.5)
assert_log_line(operator, "message", since_seconds=1)

# New (current) 
operator.get_log_position_at_time(milliseconds_ago=1500)
assert_log_line(operator, "message", since_milliseconds=1000)
```


### Operator

```python
from haproxy_template_ic.operator import run_operator_loop

# Runtime settings are now configured via ConfigMap, not function parameters
cli_options = CliOptions(
    configmap_name="haproxy-config",
    secret_name="haproxy-credentials"
)

run_operator_loop(cli_options)
```

### Configuration

```python
from haproxy_template_ic.models import Config

config = Config.from_dict(config_dict)
```

### Template Rendering

```python
from haproxy_template_ic.templating import TemplateCompiler

compiler = TemplateCompiler(template_snippets)
template = compiler.compile_template(template_string)
rendered = template.render(context)
```

### Dataplane Client

```python
from haproxy_template_ic.dataplane import DataplaneClient

client = DataplaneClient(
    base_url="http://haproxy:5555",
    username="admin",
    password="adminpass"
)

# Get configuration
config = await client.get_configuration_global()

# Deploy map
await client.create_or_update_map("hosts.map", content)

# Reload HAProxy
await client.reload_haproxy()
```

### Resource Collection

```python
from haproxy_template_ic.models import IndexedResourceCollection

collection = IndexedResourceCollection(
    index_by=["metadata.name"]
)

# Add resource
collection.add_resource(resource)

# Get by index
service = collection.get_indexed_single("my-service")

# Iterate
for key, resource in collection.items():
    print(resource.metadata.name)
```