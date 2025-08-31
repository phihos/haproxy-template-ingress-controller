# API Reference

## CLI Commands

### haproxy-template-ic

```bash
haproxy-template-ic [OPTIONS] COMMAND
```

Global options:
- `--verbose` - Logging level (0=WARNING, 1=INFO, 2=DEBUG)
- `--structured-logging` - Enable JSON logging
- `--help` - Show help

### run

Start the operator:

```bash
haproxy-template-ic run [OPTIONS]
```

Options:
- `--configmap-name` - ConfigMap containing configuration (required)
- `--healthz-port` - Health check port (default: 8080)
- `--metrics-port` - Prometheus metrics port (default: 9090)
- `--socket-path` - Management socket path (default: /run/haproxy-template-ic/management.sock)
- `--tracing-enabled` - Enable OpenTelemetry tracing

### version

Show version information:

```bash
haproxy-template-ic version
```

## Environment Variables

### Required

| Variable | Description | Default |
|----------|-------------|---------|
| `CONFIGMAP_NAME` | ConfigMap name | - |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `VERBOSE` | Log level (0/1/2) | 0 |
| `STRUCTURED_LOGGING` | JSON logging | false |
| `HEALTHZ_PORT` | Health port | 8080 |
| `METRICS_PORT` | Metrics port | 9090 |
| `SOCKET_PATH` | Socket path | /run/haproxy-template-ic/management.sock |
| `WEBHOOK_ENABLED` | Enable webhooks | false |
| `WEBHOOK_PORT` | Webhook port | 9443 |
| `WEBHOOK_CERT_DIR` | TLS cert directory | /etc/webhook/certs |
| `TRACING_ENABLED` | Enable tracing | false |
| `JAEGER_ENDPOINT` | Jaeger collector | http://localhost:14268/api/traces |
| `TRACING_SAMPLE_RATE` | Sample rate (0-1) | 1.0 |
| `TRACING_CONSOLE_EXPORT` | Console export | false |

## HTTP Endpoints

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
- `haproxy_template_ic_reconciliations_total` - Reconciliation count
- `haproxy_template_ic_reconciliation_duration_seconds` - Reconciliation time
- `haproxy_template_ic_template_render_duration_seconds` - Template render time
- `haproxy_template_ic_dataplane_sync_duration_seconds` - Dataplane sync time
- `haproxy_template_ic_watched_resources_total` - Resource count by type
- `haproxy_template_ic_errors_total` - Error count by type
- `haproxy_template_ic_haproxy_pods_total` - HAProxy pod count
- `haproxy_template_ic_config_reloads_total` - Config reload count
- `haproxy_template_ic_validation_failures_total` - Validation failure count

### Webhook Validation

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
    "object": {...}
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
    "warnings": ["..."]
  }
}
```

## Management Socket

**Security Warning**: The management socket exposes sensitive configuration and resource data. Ensure proper RBAC and pod security policies are in place.

### Connection

```bash
socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock
```

### Commands

#### dump all

Get complete state:

```
dump all
```

Response:
```json
{
  "config": {...},
  "haproxy_config_context": {...},
  "metadata": {...},
  "indices": {...}
}
```

#### dump indices

Get resource indices:

```
dump indices
```

Response:
```json
{
  "services_index": {...},
  "ingresses_index": {...},
  "secrets_index": {...}
}
```

#### dump index

Get specific index:

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

#### dump config

Get rendered configuration:

```
dump config
```

Response:
```json
{
  "haproxy_config": "...",
  "maps": {...},
  "certificates": {...}
}
```

#### get maps

Get specific map:

```
get maps /etc/haproxy/maps/hosts.map
```

Response:
```
example.com backend_web
api.example.com backend_api
```

#### get template_snippets

Get specific snippet:

```
get template_snippets backend-name
```

Response:
```
backend_{{ service }}_{{ port }}
```

## Dataplane API

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

### Operator

```python
from haproxy_template_ic.operator import run_operator

await run_operator(
    configmap_name="haproxy-config",
    verbose=1,
    structured_logging=False
)
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