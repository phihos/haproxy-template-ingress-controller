# Configuration

This document offers a complete guide to setting up the HAProxy Ingress Controller using a ConfigMap, including its
structure and key sections.

## Contents

- [High-level Structure](#high-level-structure)
- [Template Snippets](#template-snippets)
- [Maps](#maps)
- [Certificates](#certificates)
- [Template Rendering Configuration](#template-rendering-configuration)
- [HAProxy Configuration](#haproxy-configuration)
- [Complete Example](#complete-example)

## High-level Structure

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: haproxy-config
data:
  config: |
    # Required sections
    pod_selector: {}
    haproxy_config: {}

    # Optional sections
    watched_resources: {}
    watched_resources_ignore_fields: []
    template_snippets: {}
    maps: {}
    certificates: {}
    template_rendering: {}
```

### Pod Selector

Identifies target HAProxy pods:

```yaml
pod_selector:
  match_labels:
    app: haproxy
    environment: production
```

### Watched Resources

#### Basic Configuration

```yaml
watched_resources:
  ingresses:
    api_version: networking.k8s.io/v1
    kind: Ingress

  services:
    api_version: v1
    kind: Service
```

#### Custom Indexing

Default indexing by namespace and name:

```yaml
watched_resources:
  services:
    api_version: v1
    kind: Service
    # Default: ["metadata.namespace", "metadata.name"]
```

Custom indexing for O(1) lookups:

```yaml
watched_resources:
  services:
    api_version: v1
    kind: Service
    index_by: [ "metadata.labels['app']" ]

  endpoints:
    api_version: v1
    kind: Endpoints
    index_by: [ "metadata.labels['kubernetes.io/service-name']" ]
```

#### Field Filtering

Reduce memory usage by ignoring unnecessary fields:

```yaml
watched_resources_ignore_fields:
  - metadata.managedFields      # Default, very large
  - metadata.resourceVersion    # Changes frequently
  - status                      # If not used in templates
  - metadata.annotations['kubectl.kubernetes.io/last-applied-configuration']
```

#### Webhook Validation

Enable validation for specific resources:

```yaml
watched_resources:
  ingresses:
    api_version: networking.k8s.io/v1
    kind: Ingress
    enable_validation_webhook: true  # Validate before apply

  endpointslices:
    api_version: discovery.k8s.io/v1
    kind: EndpointSlice
    enable_validation_webhook: false # Critical, don't block
```

## Template Snippets

Reusable template components:

```yaml
template_snippets:
  backend-name: |
    backend_{{ service }}_{{ port }}

  server-line: |
    server {{ name }} {{ ip }}:{{ port }} check inter 2s

  rate-limit: |
    stick-table type ip size 100k expire 30s store http_req_rate(10s)
    http-request track-sc0 src
    http-request deny if { sc_http_req_rate(0) gt 20 }
```

## Maps

HAProxy map files:

```yaml
maps:
  /etc/haproxy/maps/hosts.map:
    template: |
      {% for _, ingress in resources.get('ingresses', {}).items() %}
      {% for rule in ingress.spec.rules %}
      {{ rule.host }} backend_{{ rule.backend.service.name }}
      {% endfor %}
      {% endfor %}

  /etc/haproxy/maps/paths.map:
    template: |
      {% for _, ingress in resources.get('ingresses', {}).items() %}
      {% for rule in ingress.spec.rules %}
      {% for path in rule.http.paths %}
      {{ rule.host }}{{ path.path }} backend_{{ path.backend.service.name }}
      {% endfor %}
      {% endfor %}
      {% endfor %}
```

## Certificates

TLS certificates from Secrets:

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

## Runtime Configuration

All runtime settings configured via ConfigMap using grouped structure:

```yaml
# Operator runtime settings
operator:
  healthz_port: 8080                    # Health check port  
  metrics_port: 9090                    # Prometheus metrics port
  index_initialization_timeout: 5       # Index sync timeout for zero-resource cases (seconds)

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

### Index Initialization Timeout

The `index_initialization_timeout` setting controls how long the operator waits for index initialization when no resources exist for a given type (zero-resource edge case).

**Default**: 5 seconds

**Range**: 1-300 seconds

**Purpose**: During startup, prevents infinite waiting when watched resource types have zero matching objects in the cluster.

**Example scenarios**:
- No Ingress objects exist yet, but watched_resources includes ingresses
- HAProxy pods not yet created during initial deployment
- Custom resource types configured but no instances applied

**Tuning guidelines**:
- **1-3 seconds**: Fast startup, suitable for development
- **5 seconds (default)**: Balanced for most environments  
- **10+ seconds**: Conservative for slow clusters or complex deployments

### Logging Configuration

**Structured Logging**: Enable JSON output for production environments:

```yaml
logging:
  structured: true    # Enables JSON structured logging
  verbose: 1         # INFO level logging
```

**Log Levels**:
- `0`: WARNING and above
- `1`: INFO and above (default)
- `2`: DEBUG and above (verbose)

### Tracing Configuration

**Development Setup**:

```yaml
tracing:
  enabled: true
  console_export: true    # Output traces to console
  sample_rate: 1.0       # Trace all operations
```

**Production Setup**:

```yaml
tracing:
  enabled: true
  jaeger_endpoint: "jaeger-collector:14268"
  sample_rate: 0.1       # Sample 10% for performance
  console_export: false
```

## Template Rendering Configuration

Control template rendering behavior for optimal performance:

```yaml
template_rendering:
  min_render_interval: 5   # Minimum seconds between renders (rate limiting)
  max_render_interval: 60  # Maximum seconds without render (guaranteed refresh)
```

### Performance Guidelines

**Recommended Settings by Environment:**

1. **Development/Testing:**
   ```yaml
   template_rendering:
     min_render_interval: 1   # Fast feedback
     max_render_interval: 30  # Frequent updates
   ```

2. **Production (High Change Rate):**
   ```yaml
   template_rendering:
     min_render_interval: 5   # Protect against rapid changes
     max_render_interval: 60  # Balance freshness with stability
   ```

3. **Production (Low Change Rate):**
   ```yaml
   template_rendering:
     min_render_interval: 10  # Conservative rate limiting
     max_render_interval: 300 # 5 minutes for stable environments
   ```

### Impact on Performance

- **min_render_interval < 3s**: May cause high CPU usage during rapid resource changes
- **max_render_interval > 3600s**: Templates may become stale in quiet periods
- **Batching Effect**: Multiple resource changes within min_render_interval are batched into a single render

### Monitoring

View debouncer statistics:

```bash
# Prometheus metrics
curl localhost:9090/metrics | grep debouncer
```

Metrics available:

- `haproxy_template_ic_debouncer_triggers_total`: Total trigger events
- `haproxy_template_ic_debouncer_renders_total`: Renders by type (resource_changes/periodic_refresh)
- `haproxy_template_ic_debouncer_batched_changes`: Histogram of changes batched per render
- `haproxy_template_ic_debouncer_time_since_last_render_seconds`: Time since last render

## HAProxy Configuration

Main configuration template:

```yaml
haproxy_config:
  template: |
    global
        daemon
        maxconn 4096

    defaults
        mode http
        timeout connect 5s
        timeout client 30s
        timeout server 30s

    frontend health
        bind *:8404
        http-request return status 200 if { path /healthz }

    frontend main
        bind *:80
        bind *:443 ssl crt /etc/haproxy/certs/

        # Use map for host-based routing
        use_backend %[req.hdr(host),lower,map_str(/etc/haproxy/maps/hosts.map)]

    {% for _, ingress in resources.get('ingresses', {}).items() %}
    {% for rule in ingress.spec.rules %}
    {% set backend_name %}{% include "backend-name" %}{% endset %}
    {{ backend_name }}
        balance roundrobin
        {% set service = resources.get('services').get_indexed_single(rule.backend.service.name) %}
        {% if service %}
        {% for port in service.spec.ports %}
        {% if port.port == rule.backend.service.port.number %}
        server {{ service.metadata.name }} {{ service.spec.clusterIP }}:{{ port.port }} check
        {% endif %}
        {% endfor %}
        {% endif %}
    {% endfor %}
    {% endfor %}
```

## Complete Example

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: haproxy-config
data:
  config: |
    pod_selector:
      match_labels: {app: haproxy}

    watched_resources:
      ingresses:
        api_version: networking.k8s.io/v1
        kind: Ingress
        enable_validation_webhook: true

      services:
        api_version: v1
        kind: Service
        index_by: ["metadata.name"]

      secrets:
        api_version: v1
        kind: Secret
        index_by: ["metadata.namespace", "metadata.name"]

    watched_resources_ignore_fields:
      - metadata.managedFields

    template_snippets:
      backend-name: |
        backend {{ service }}_{{ port }}

    maps:
      /etc/haproxy/maps/hosts.map:
        template: |
          {% for _, ing in resources.get('ingresses', {}).items() %}
          {% for rule in ing.spec.rules %}
          {{ rule.host }} {{ rule.backend.service.name }}_{{ rule.backend.service.port.number }}
          {% endfor %}
          {% endfor %}

    certificates:
      /etc/haproxy/certs/bundle.pem:
        template: |
          {% for _, secret in resources.get('secrets', {}).items() %}
          {% if secret.type == "kubernetes.io/tls" %}
          {{ secret.data['tls.crt'] | b64decode }}
          {{ secret.data['tls.key'] | b64decode }}
          {% endif %}
          {% endfor %}

    haproxy_config:
      template: |
        global
            daemon

        defaults
            mode http
            timeout connect 5s
            timeout client 30s
            timeout server 30s

        frontend health
            bind *:8404
            http-request return status 200 if { path /healthz }

        frontend main
            bind *:80
            bind *:443 ssl crt /etc/haproxy/certs/
            use_backend %[req.hdr(host),lower,map_str(/etc/haproxy/maps/hosts.map)]

        {% for _, ing in resources.get('ingresses', {}).items() %}
        {% for rule in ing.spec.rules %}
        {% set backend_port = rule.backend.service.port.number %}
        backend {{ rule.backend.service.name }}_{{ backend_port }}
            {% set svc = resources.get('services').get_indexed_single(rule.backend.service.name) %}
            {% if svc %}
            server srv {{ svc.spec.clusterIP }}:{{ backend_port }} check
            {% endif %}
        {% endfor %}
        {% endfor %}
```