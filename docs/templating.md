# Templating Guide

## Overview

The HAProxy Template Ingress Controller uses Gonja v2, a Jinja2-like template engine for Go, to generate HAProxy configurations from Kubernetes resources. You define templates that access watched Kubernetes resources, and the controller renders these templates whenever resources change, validates the output, and deploys it to HAProxy instances.

**Why use templates:**
- Complete control over HAProxy configuration without annotation limitations
- Access to all HAProxy features (ACLs, stick tables, rate limiting, custom error pages)
- Define your own data model using any Kubernetes resources
- Reusable template snippets for common patterns
- Type-safe template rendering with early error detection

Templates are rendered automatically when any watched resource changes, during initial synchronization, or periodically for drift detection.

## What You Can Template

The controller supports five types of templatable components, each serving a specific purpose in HAProxy configuration.

### HAProxy Configuration

The main `haproxy_config` template generates the complete HAProxy configuration file (`/etc/haproxy/haproxy.cfg`).

```yaml
haproxy_config:
  template: |
    global
        log stdout len 4096 local0 info
        daemon
        maxconn 4096

    defaults
        mode http
        timeout connect 5s
        timeout client 50s
        timeout server 50s

    frontend http
        bind *:80
        # Use map files for routing
        use_backend %[req.hdr(host),lower,map({{ "host.map" | get_path("map") }})]

    {% for ingress in resources.ingresses.List() %}
    backend {{ ingress.metadata.name }}
        balance roundrobin
        # Backend configuration here
    {% endfor %}
```

> [!IMPORTANT]
> All auxiliary file references in HAProxy configuration must use **absolute paths** from `/etc/haproxy/`. For example, use `/etc/haproxy/maps/host.map` for map files, `/etc/haproxy/ssl/cert.pem` for SSL certificates, and `/etc/haproxy/general/error.http` for general files. This requirement exists because the HAProxy Dataplane API validation needs absolute paths to verify files exist before applying configuration changes.

### Map Files

Map files (`maps`) generate HAProxy map files for backend routing, ACL matching, and other lookup operations. Maps are stored in `/etc/haproxy/maps/` and referenced in HAProxy configuration using absolute paths like `/etc/haproxy/maps/host.map`.

```yaml
maps:
  host.map:
    template: |
      # Map host headers to normalized host values
      {%- for ingress in resources.ingresses.List() %}
      {%- for rule in (ingress.spec.rules | default([]) | selectattr("http", "defined")) %}
      {{ rule.host }} {{ rule.host }}
      {%- endfor %}
      {%- endfor %}

  path-prefix.map:
    template: |
      # Map host+path to backend names using prefix matching
      {%- for ingress in resources.ingresses.List() %}
      {%- for rule in (ingress.spec.rules | default([])) %}
      {%- for path in (rule.http.paths | default([])) %}
      {{ rule.host }}{{ path.path }}/ backend_{{ ingress.metadata.name }}
      {%- endfor %}
      {%- endfor %}
      {%- endfor %}
```

**Use maps for:**
- Host-based backend selection
- Path-based routing with prefix or exact matching
- ACL lookups for access control
- Rate limiting based on client characteristics

### General Files

General files (`files`) generate auxiliary files like custom error pages. Files are stored in `/etc/haproxy/general/` and referenced in HAProxy configuration using absolute paths like `/etc/haproxy/general/503.http`.

```yaml
files:
  503.http:
    template: |
      HTTP/1.0 503 Service Unavailable
      Cache-Control: no-cache
      Connection: close
      Content-Type: text/html

      <html><body><h1>503 Service Unavailable</h1>
      <p>No server is available to handle this request.</p>
      </body></html>

  maintenance.html:
    template: |
      <html><body>
      <h1>Maintenance Mode</h1>
      <p>System will be back online at {{ maintenance_end_time }}.</p>
      </body></html>
```

**Use general files for:**
- Custom error pages (400, 403, 404, 500, 503, etc.)
- Maintenance mode pages
- Health check responses
- Static content served by HAProxy

### SSL Certificates

SSL certificates (`ssl_certificates`) generate SSL/TLS certificate files from Kubernetes Secret data. Certificates are stored in `/etc/haproxy/ssl/` and referenced in HAProxy configuration using absolute paths like `/etc/haproxy/ssl/example-com.pem`.

```yaml
ssl_certificates:
  example-com.pem:
    template: |
      {%- for secret in resources.secrets.Get("default", "kubernetes.io/tls") %}
      {%- if secret.metadata.name == "example-com-tls" %}
      {{ secret.data.tls_crt | b64decode }}
      {{ secret.data.tls_key | b64decode }}
      {%- endif %}
      {%- endfor %}
```

**Use SSL certificates for:**
- TLS termination at HAProxy
- Client certificate authentication
- Backend SSL connections

> [!NOTE]
> Certificate data in Secrets is base64-encoded. Use the `b64decode` filter to decode it in your templates.

### Template Snippets

Template snippets (`template_snippets`) define reusable template fragments that can be included in other templates. This promotes code reuse and keeps templates maintainable.

```yaml
template_snippets:
  backend-name:
    name: backend-name
    template: >-
      ing_{{ ingress.metadata.namespace }}_{{ ingress.metadata.name }}_{{ path.backend.service.name }}

  backend-servers:
    name: backend-servers
    template: |
      {%- for endpoint_slice in resources.endpoints.Get(service_name) %}
      {%- for endpoint in (endpoint_slice.endpoints | default([])) %}
      {%- for address in (endpoint.addresses | default([])) %}
      server {{ endpoint.targetRef.name }} {{ address }}:{{ port }} check
      {%- endfor %}
      {%- endfor %}
      {%- endfor %}
```

Include snippets using `{% include "snippet-name" %}`:

```jinja2
backend {% include "backend-name" %}
    balance roundrobin
    {% include "backend-servers" %}
```

## Template Syntax

Templates use Gonja v2, which provides Jinja2-like syntax for Go. The syntax is familiar if you've used Jinja2, Django templates, or Ansible.

### Control Structures

**Loops** iterate over collections:

```jinja2
{% for ingress in resources.ingresses.List() %}
  backend {{ ingress.metadata.name }}
      server srv1 192.168.1.10:80
{% endfor %}
```

**Conditionals** control template logic:

```jinja2
{% if ingress.spec.tls %}
  {% set cert_name = ingress.metadata.name ~ ".pem" %}
  bind *:443 ssl crt {{ cert_name | get_path("cert") }}
{% else %}
  bind *:80
{% endif %}
```

**Variables** store values for reuse:

```jinja2
{% set service_name = path.backend.service.name %}
{% set port = path.backend.service.port.number | default(80) %}
```

**Comments** document your templates:

```jinja2
{# This backend handles all traffic for the production namespace #}
backend production_backend
    balance roundrobin
```

For complete syntax reference, see the [Gonja documentation](https://github.com/nikolalohinski/gonja).

### Filters

Filters transform values in templates using the pipe (`|`) operator.

**Common filters:**

```jinja2
{# Provide default values for missing data #}
{{ path.backend.service.port.number | default(80) }}

{# String manipulation #}
{{ rule.host | lower }}
{{ ingress.metadata.name | upper }}

{# Get collection length #}
{{ ingress.spec.rules | length }}

{# Indent text blocks #}
{%- filter indent(2, first=True) %}
{% include "backend-servers" %}
{%- endfilter %}
```

**Custom filter - get_path:**

The `get_path` filter resolves filenames to absolute paths based on file type. This simplifies template writing by automatically constructing correct absolute paths for HAProxy auxiliary files.

```jinja2
{# Map files - resolve to maps directory #}
use_backend %[req.hdr(host),lower,map({{ "host.map" | get_path("map") }})]
{# Output: use_backend %[req.hdr(host),lower,map(/etc/haproxy/maps/host.map)] #}

{# General files - resolve to general directory #}
errorfile 504 {{ "504.http" | get_path("file") }}
{# Output: errorfile 504 /etc/haproxy/general/504.http #}

{# SSL certificates - resolve to SSL directory #}
bind *:443 ssl crt {{ "example.com.pem" | get_path("cert") }}
{# Output: bind *:443 ssl crt /etc/haproxy/ssl/example.com.pem #}

{# Use with variables #}
{% set cert_name = ingress.metadata.name ~ ".pem" %}
bind *:443 ssl crt {{ cert_name | get_path("cert") }}
```

**Arguments:**
- **filename** (required): The base filename without directory path
- **type** (required): File type - `"map"`, `"file"`, or `"cert"`

The filter uses the paths configured in `dataplane.maps_dir`, `dataplane.ssl_certs_dir`, and `dataplane.general_storage_dir` from your controller configuration.

For the complete list of built-in filters, see [Gonja filters](https://github.com/nikolalohinski/gonja#filters).

### Functions

Gonja provides built-in functions for common operations. See the [Gonja documentation](https://github.com/nikolalohinski/gonja#functions) for available functions.

## Available Template Data

Templates have access to the `resources` variable, which contains stores for all watched Kubernetes resource types.

### The `resources` Variable

The `resources` variable is a collection of stores, one for each resource type you configure in `watched_resources`. Each store provides `List()` and `Get()` methods for accessing resources.

**Structure:**

```yaml
resources:
  ingresses:    # Store for Ingress resources (if configured)
  services:     # Store for Service resources (if configured)
  endpoints:    # Store for EndpointSlice resources (if configured)
  secrets:      # Store for Secret resources (if configured)
  # ... any other configured resource types
```

The store names match the keys in your `watched_resources` configuration.

### Using List() Method

The `List()` method returns all resources of a specific type. Use this to iterate over all resources.

**Example:**

```jinja2
{# Iterate over all Ingress resources #}
{% for ingress in resources.ingresses.List() %}
backend {{ ingress.metadata.name }}
    balance roundrobin
    server srv1 192.168.1.10:80
{% endfor %}
```

**When to use List():**
- Generate configuration for all resources of a type
- Build map files with all hosts/paths
- Count resources for capacity planning

### Using Get() Method

The `Get()` method returns resources matching specific index keys. The parameters you provide to `Get()` are determined by the `index_by` configuration for that resource type.

**How indexing works:**

```yaml
watched_resources:
  ingresses:
    api_version: networking.k8s.io/v1
    kind: Ingress
    index_by: ["metadata.namespace", "metadata.name"]
    # Get() expects: Get(namespace, name)

  endpoints:
    api_version: discovery.k8s.io/v1
    kind: EndpointSlice
    index_by: ["metadata.labels.kubernetes\\.io/service-name"]
    # Get() expects: Get(service_name)
```

**Examples:**

```jinja2
{# Get specific ingress by namespace and name #}
{% for ingress in resources.ingresses.Get("default", "my-ingress") %}
  {# Usually returns 0 or 1 items #}
{% endfor %}

{# Get all endpoint slices for a service #}
{% set service_name = path.backend.service.name %}
{% for endpoint_slice in resources.endpoints.Get(service_name) %}
  {# Returns all endpoint slices labeled with this service name #}
{% endfor %}
```

**When to use Get():**
- Look up specific resources by key
- Find related resources (e.g., endpoints for a service)
- Implement cross-resource matching patterns

### Index Configuration

The `index_by` field in `watched_resources` determines:
1. How resources are indexed in the store
2. What parameters `Get()` expects
3. Query performance (O(1) lookups with proper indexing)

**Common indexing patterns:**

```yaml
# By namespace and name (most resources)
index_by: ["metadata.namespace", "metadata.name"]
# Get(namespace, name) returns specific resource

# By service name (endpoint slices)
index_by: ["metadata.labels.kubernetes\\.io/service-name"]
# Get(service_name) returns all endpoint slices for that service

# By type (secrets)
index_by: ["metadata.namespace", "type"]
# Get(namespace, type) returns all secrets of that type in namespace
```

> [!TIP]
> Escape dots in JSONPath expressions for labels: `kubernetes\\.io/service-name`

## Tips & Tricks

These patterns solve common challenges when templating HAProxy configurations.

### Reserved Server Slots Pattern (Avoid Reloads)

**Problem**: Adding or removing servers in HAProxy backends requires a process reload, which can briefly interrupt existing connections.

**Solution**: Pre-allocate a fixed number of server slots with static names. Active endpoints fill slots with real addresses, while unused slots contain disabled placeholders.

**How it works:**

```jinja2
{%- set initial_slots = 10 %}  {# Adjust based on expected endpoints #}

{# Collect active endpoints #}
{%- set ns = namespace(active_endpoints=[]) %}
{%- for endpoint_slice in resources.endpoints.Get(service_name) %}
  {%- for endpoint in (endpoint_slice.endpoints | default([])) %}
    {%- for address in (endpoint.addresses | default([])) %}
      {%- set ns.active_endpoints = ns.active_endpoints + [{'name': endpoint.targetRef.name, 'address': address, 'port': port}] %}
    {%- endfor %}
  {%- endfor %}
{%- endfor %}

{# Generate fixed server slots #}
{%- for i in range(1, initial_slots + 1) %}
  {%- if loop.index0 < ns.active_endpoints|length %}
    {# Active server with real endpoint #}
    {%- set endpoint = ns.active_endpoints[loop.index0] %}
server SRV_{{ i }} {{ endpoint.address }}:{{ endpoint.port }} check
  {%- else %}
    {# Disabled placeholder server #}
server SRV_{{ i }} 127.0.0.1:1 disabled
  {%- endif %}
{%- endfor %}
```

**Benefits:**
- Endpoint changes only update server addresses via runtime API (no reload)
- Server names remain stable (`SRV_1`, `SRV_2`, etc.)
- HAProxy can update addresses without dropping connections

**Auto-expansion:**
You can implement automatic slot doubling when all slots are filled:

```jinja2
{%- set active_count = ns.active_endpoints|length %}
{%- if active_count > initial_slots %}
  {%- set max_servers = initial_slots * 2 %}  {# Double when full #}
{%- else %}
  {%- set max_servers = initial_slots %}
{%- endif %}
```

### Matching Resources Across Types

**Pattern**: Use fields from one resource type to query another resource type, enabling cross-resource relationships.

**Example**: Matching Ingress resources with their corresponding EndpointSlices:

```jinja2
{# Step 1: Iterate over ingresses #}
{% for ingress in resources.ingresses.List() %}
{% for rule in (ingress.spec.rules | default([])) %}
{% for path in (rule.http.paths | default([])) %}

  {# Step 2: Extract service name from ingress #}
  {% set service_name = path.backend.service.name %}
  {% set port = path.backend.service.port.number | default(80) %}

  {# Step 3: Look up endpoint slices for this service #}
  backend ing_{{ ingress.metadata.name }}_{{ service_name }}
      balance roundrobin
      {%- for endpoint_slice in resources.endpoints.Get(service_name) %}
      {%- for endpoint in (endpoint_slice.endpoints | default([])) %}
      {%- for address in (endpoint.addresses | default([])) %}
      server {{ endpoint.targetRef.name }} {{ address }}:{{ port }} check
      {%- endfor %}
      {%- endfor %}
      {%- endfor %}

{% endfor %}
{% endfor %}
{% endfor %}
```

**Key insight**: The index configuration enables this pattern. EndpointSlices are indexed by `metadata.labels.kubernetes\.io/service-name`, so `Get(service_name)` returns all endpoint slices for that service.

**Other cross-resource patterns:**

**Services with Endpoints:**
```jinja2
{% for service in resources.services.List() %}
  {% set service_name = service.metadata.name %}
  {# Look up endpoints #}
  {% for endpoint_slice in resources.endpoints.Get(service_name) %}
    {# Process endpoints #}
  {% endfor %}
{% endfor %}
```

**Ingresses with TLS Secrets:**
```jinja2
{% for ingress in resources.ingresses.List() %}
  {% if ingress.spec.tls %}
    {% for tls in ingress.spec.tls %}
      {% set secret_name = tls.secretName %}
      {% set namespace = ingress.metadata.namespace %}
      {# Look up TLS secret #}
      {% for secret in resources.secrets.Get(namespace, secret_name) %}
        {# Use cert data: secret.data.tls_crt | b64decode #}
      {% endfor %}
    {% endfor %}
  {% endif %}
{% endfor %}
```

**Required index configuration:**
```yaml
watched_resources:
  ingresses:
    index_by: ["metadata.namespace", "metadata.name"]

  endpoints:
    index_by: ["metadata.labels.kubernetes\\.io/service-name"]

  secrets:
    index_by: ["metadata.namespace", "metadata.name"]
```

### Safe Iteration with default Filter

Always use the `default` filter when iterating over optional fields to prevent template errors when fields are missing or null.

```jinja2
{# Safe: Returns empty array if field is missing #}
{% for endpoint in (endpoint_slice.endpoints | default([])) %}
  {% for address in (endpoint.addresses | default([])) %}
    server srv {{ address }}:80
  {% endfor %}
{% endfor %}

{# Unsafe: Fails if endpoints field is null #}
{% for endpoint in endpoint_slice.endpoints %}
  {# ERROR if endpoints is null #}
{% endfor %}
```

### Filtering with selectattr

Use `selectattr` to filter resources that have specific attributes, useful for optional Kubernetes fields.

```jinja2
{# Only process rules that have HTTP configuration #}
{% for rule in (ingress.spec.rules | default([]) | selectattr("http", "defined")) %}
  {# rule.http is guaranteed to exist #}
  {% for path in rule.http.paths %}
    {# Process paths #}
  {% endfor %}
{% endfor %}

{# Only process paths with specific pathType #}
{% set path_types = ["Prefix", "Exact"] %}
{% for path in (rule.http.paths | default([]) | selectattr("pathType", "in", path_types)) %}
  {# Only Prefix and Exact paths #}
{% endfor %}
```

### Maintaining Variables Across Loop Scopes

Jinja2/Gonja scoping rules prevent modifying variables inside loops. Use `namespace()` to create a mutable container for accumulating values across iterations.

```jinja2
{# Create namespace for mutable list #}
{% set ns = namespace(active_endpoints=[]) %}

{# Append items inside loops #}
{% for endpoint_slice in resources.endpoints.Get(service_name) %}
  {% for endpoint in (endpoint_slice.endpoints | default([])) %}
    {% for address in (endpoint.addresses | default([])) %}
      {% set ns.active_endpoints = ns.active_endpoints + [{'address': address, 'port': port}] %}
    {% endfor %}
  {% endfor %}
{% endfor %}

{# Use accumulated list #}
{% for endpoint in ns.active_endpoints %}
  server srv{{ loop.index }} {{ endpoint.address }}:{{ endpoint.port }}
{% endfor %}
```

### Template Snippet Composition

Break complex templates into reusable snippets for better maintainability and code reuse.

**Define snippets:**

```yaml
template_snippets:
  backend-name:
    name: backend-name
    template: >-
      ing_{{ ingress.metadata.namespace }}_{{ ingress.metadata.name }}_{{ path.backend.service.name }}

  backend-servers:
    name: backend-servers
    template: |
      {% set service_name = path.backend.service.name %}
      {% set port = path.backend.service.port.number %}
      {% include "reserved-server-slots" %}
```

**Use snippets:**

```jinja2
{# Include snippet inline #}
backend {% include "backend-name" %}
    balance roundrobin
    {%- filter indent(4) %}
    {% include "backend-servers" %}
    {%- endfilter %}
```

**Pass variables to snippets:**

```jinja2
{# Set variables before including snippet #}
{% set service_name = "my-service" %}
{% set port = 8080 %}
{% include "backend-servers" %}
```

### Indentation Control

Control whitespace in generated output using the `-` marker to strip whitespace.

```jinja2
{# Strip whitespace before tag #}
{%- for item in items %}
  {{ item }}
{%- endfor %}

{# Strip whitespace after tag #}
{% for item in items -%}
  {{ item }}
{% endfor -%}

{# Indent included content #}
backend my_backend
    {%- filter indent(4, first=True) %}
    {% include "server-list" %}
    {%- endfilter %}
```

**Result with indentation:**
```
backend my_backend
    server srv1 192.168.1.10:80
    server srv2 192.168.1.11:80
```

## Complete Examples

### Example 1: Simple Host-Based Routing

Basic Ingress to backend mapping with map-based routing:

```yaml
# Configuration
watched_resources:
  ingresses:
    api_version: networking.k8s.io/v1
    kind: Ingress
    index_by: ["metadata.namespace", "metadata.name"]

maps:
  host.map:
    template: |
      {%- for ingress in resources.ingresses.List() %}
      {%- for rule in (ingress.spec.rules | default([])) %}
      {{ rule.host }} backend_{{ ingress.metadata.name }}
      {%- endfor %}
      {%- endfor %}

haproxy_config:
  template: |
    global
        daemon

    defaults
        mode http
        timeout connect 5s
        timeout client 50s
        timeout server 50s

    frontend http
        bind *:80
        # Use map for host-based routing
        use_backend %[req.hdr(host),lower,map({{ "host.map" | get_path("map") }})]

    {% for ingress in resources.ingresses.List() %}
    backend backend_{{ ingress.metadata.name }}
        balance roundrobin
        server srv1 192.168.1.10:80 check
    {% endfor %}
```

### Example 2: Path-Based Routing with Maps

Using map files for both host and path-based routing:

```yaml
maps:
  host.map:
    template: |
      {%- for ingress in resources.ingresses.List() %}
      {%- for rule in (ingress.spec.rules | default([])) %}
      {{ rule.host }} {{ rule.host }}
      {%- endfor %}
      {%- endfor %}

  path-prefix.map:
    template: |
      {%- for ingress in resources.ingresses.List() %}
      {%- for rule in (ingress.spec.rules | default([])) %}
      {%- for path in (rule.http.paths | default([]) | selectattr("pathType", "equalto", "Prefix")) %}
      {{ rule.host }}{{ path.path }}/ backend_{{ ingress.metadata.name }}_{{ path.backend.service.name }}
      {%- endfor %}
      {%- endfor %}
      {%- endfor %}

haproxy_config:
  template: |
    frontend http
        bind *:80

        # Normalize host header
        http-request set-var(txn.host) req.hdr(Host),field(1,:),lower
        http-request set-var(txn.host_match) var(txn.host),map({{ "host.map" | get_path("map") }})

        # Path-based routing with prefix matching
        http-request set-var(txn.backend) var(txn.host_match),concat(,txn.path,),map_beg({{ "path-prefix.map" | get_path("map") }})

        use_backend %[var(txn.backend)]
        default_backend default_backend

    {% for ingress in resources.ingresses.List() %}
    {% for rule in (ingress.spec.rules | default([])) %}
    {% for path in (rule.http.paths | default([])) %}
    backend backend_{{ ingress.metadata.name }}_{{ path.backend.service.name }}
        balance roundrobin
        server srv1 192.168.1.10:80 check
    {% endfor %}
    {% endfor %}
    {% endfor %}

    backend default_backend
        http-request return status 404
```

### Example 3: Dynamic Backend Servers with Cross-Resource Lookups

Complete ingress → service → endpoints chain using reserved slots pattern:

```yaml
watched_resources:
  ingresses:
    api_version: networking.k8s.io/v1
    kind: Ingress
    index_by: ["metadata.namespace", "metadata.name"]

  endpoints:
    api_version: discovery.k8s.io/v1
    kind: EndpointSlice
    index_by: ["metadata.labels.kubernetes\\.io/service-name"]

template_snippets:
  backend-servers-with-slots:
    name: backend-servers-with-slots
    template: |
      {%- set initial_slots = 10 %}

      {# Collect active endpoints using indexed lookup #}
      {%- set ns = namespace(active_endpoints=[]) %}
      {%- for endpoint_slice in resources.endpoints.Get(service_name) %}
        {%- for endpoint in (endpoint_slice.endpoints | default([])) %}
          {%- for address in (endpoint.addresses | default([])) %}
            {%- set ns.active_endpoints = ns.active_endpoints + [{'name': endpoint.targetRef.name, 'address': address, 'port': port}] %}
          {%- endfor %}
        {%- endfor %}
      {%- endfor %}

      {# Generate fixed server slots #}
      {%- for i in range(1, initial_slots + 1) %}
        {%- if loop.index0 < ns.active_endpoints|length %}
          {%- set endpoint = ns.active_endpoints[loop.index0] %}
      server SRV_{{ i }} {{ endpoint.address }}:{{ endpoint.port }} check
        {%- else %}
      server SRV_{{ i }} 127.0.0.1:1 disabled
        {%- endif %}
      {%- endfor %}

haproxy_config:
  template: |
    global
        daemon
        maxconn 4096

    defaults
        mode http
        timeout connect 5s
        timeout client 50s
        timeout server 50s
        option httpchk GET /healthz

    frontend http
        bind *:80
        use_backend %[req.hdr(host),lower,map({{ "host.map" | get_path("map") }})]

    {% for ingress in resources.ingresses.List() %}
    {% for rule in (ingress.spec.rules | default([])) %}
    {% for path in (rule.http.paths | default([])) %}
    {%- set service_name = path.backend.service.name %}
    {%- set port = path.backend.service.port.number | default(80) %}

    backend ing_{{ ingress.metadata.name }}_{{ service_name }}
        balance roundrobin
        default-server check inter 2s
        {%- filter indent(4, first=True) %}
        {% include "backend-servers-with-slots" %}
        {%- endfilter %}

    {% endfor %}
    {% endfor %}
    {% endfor %}
```

**Result**: Endpoint changes only update server addresses via HAProxy runtime API without reloads. Server slot names (`SRV_1`, `SRV_2`, etc.) remain stable.

## See Also

- [Template Engine Reference](../pkg/templating/README.md) - Detailed templating API and error handling
- [Configuration Reference](supported-configuration.md) - Complete configuration schema
- [Gonja Documentation](https://github.com/nikolalohinski/gonja) - Full template syntax reference
- [Helm Chart Values](../charts/haproxy-template-ic/values.yaml) - Production-ready template examples
- [HAProxy Configuration Manual](https://docs.haproxy.org/2.9/configuration.html) - HAProxy configuration reference
