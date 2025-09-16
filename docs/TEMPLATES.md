# Templates

This document provides a comprehensive guide to using Jinja2 templates in the HAProxy Ingress Controller. It covers
syntax, available variables, filters, resource access patterns, and common template patterns for configuring HAProxy
dynamically.

Learn how to efficiently create and debug templates that transform Kubernetes resources into HAProxy configurations.

## Contents

- [Jinja2 Basics](#jinja2-basics)
- [Available Variables](#available-variables)
- [Available Filters](#available-filters)
- [Resource Access Patterns](#resource-access-patterns)
- [Reusable Snippets](#reusable-snippets)
- [Common Patterns](#common-patterns)
- [Debugging Templates](#debugging-templates)

## Jinja2 Basics

Templates use standard Jinja2 syntax with custom filters and variables.

### Variables

```jinja2
{{ variable }}                  # Output variable
{% set name = "value" %}       # Set variable
{% include "snippet-name" %}   # Include snippet
```

### Control Flow

```jinja2
{% if condition %}
  ...
{% elif other %}
  ...
{% else %}
  ...
{% endif %}

{% for item in items %}
  {{ item }}
{% endfor %}
```

## Available Variables

### resources

Indexed Kubernetes resources by type:

```jinja2
# Iterate all resources of a type
{% for _, service in resources.get('services', {}).items() %}
  {{ service.metadata.name }}
{% endfor %}

# Get specific resource (O(1) lookup)
{% set svc = resources.get('services').get_indexed_single('my-service') %}

# Get resources by index key
{% for pod in resources.get('pods').get_indexed('default', 'my-app') %}
  {{ pod.status.podIP }}
{% endfor %}
```

### register_error

Internal error registration function (advanced use only):

```jinja2
# Used internally by the controller for error tracking
# Not typically used in user templates
```

## Available Filters

### b64decode

Decode base64 strings:

```jinja2
{{ secret.data['tls.crt'] | b64decode }}
```

### get_path

Safe nested field access:

```jinja2
{{ ingress | get_path('spec.rules.0.host', 'default.local') }}
```

### Standard Jinja2

All standard filters available:

```jinja2
{{ name | lower }}
{{ name | upper }}
{{ name | replace('old', 'new') }}
{{ items | length }}
{{ items | first }}
{{ items | last }}
{{ items | join(', ') }}
```

## Resource Access Patterns

The `resources` variable contains IndexedResourceCollection objects for each watched resource type. There are two main
access patterns:

### Basic Iteration

Iterate through all resources of a type (O(n) performance):

```jinja2
{% for _, ingress in resources.get('ingresses', {}).items() %}
  # Process each ingress
  {% for rule in ingress.spec.rules %}
    Host: {{ rule.host }}
  {% endfor %}
{% endfor %}

# Alternative syntax for values only
{% for svc in resources.get('services', {}).values() %}
  Service: {{ svc.metadata.name }}
{% endfor %}
```

### Indexed Lookups

Fast O(1) lookups using custom indexing configured in your ConfigMap:

```jinja2
# First configure indexing in ConfigMap:
watched_resources:
  services:
    index_by: ["metadata.labels['app']"]

# Then use in template (O(1) lookup)
{% set service = resources.get('services').get_indexed_single('frontend') %}
{% if service %}
  server {{ service.metadata.name }} {{ service.spec.clusterIP }}:80
{% endif %}

# Get multiple resources with same index key
{% for pod in resources.get('pods').get_indexed('default', 'my-app') %}
  Pod {{ pod.metadata.name }} at {{ pod.status.podIP }}
{% endfor %}

# Memory-efficient iteration for large result sets
{% for endpoint in resources.get('endpoints').get_indexed_iter('production', 'web') %}
  Endpoint: {{ endpoint.metadata.name }}
{% endfor %}
```

**Performance Notes:**

- `items()` and `values()`: O(n) - iterate all resources
- `get_indexed_single()`: O(1) - fast lookup, returns one resource or None
- `get_indexed()`: O(1) - fast lookup, returns list of matching resources
- `get_indexed_iter()`: O(1) - memory-efficient iterator for large results

### Cross-Resource Matching

```jinja2
# Match services to ingresses
{% for _, ingress in resources.get('ingresses', {}).items() %}
  {% for rule in ingress.spec.rules %}
    {% set service_name = rule.backend.service.name %}
    {% set service = resources.get('services').get_indexed_single(service_name) %}
    {% if service %}
      backend {{ service_name }}
        server srv {{ service.spec.clusterIP }}:{{ rule.backend.service.port.number }}
    {% endif %}
  {% endfor %}
{% endfor %}
```

### Safe Navigation

```jinja2
# Handle missing fields gracefully
{% if ingress.spec.tls %}
  {% for tls in ingress.spec.tls %}
    {% if tls.hosts %}
      {% for host in tls.hosts %}
        {{ host }} uses TLS
      {% endfor %}
    {% endif %}
  {% endfor %}
{% endif %}

# Handle empty resource collections
{% set services = resources.get('services', {}) %}
{% if services %}
  {% for _, svc in services.items() %}
    # Process service {{ svc.metadata.name }}
  {% endfor %}
{% else %}
  # No services found - provide fallback
  default_backend unavailable
{% endif %}

# Safe field access with defaults
{% set backend_port = rule.backend.service.port.number | default(80) %}
{% set service_name = rule.backend.service.name | default('unknown') %}
```

## Reusable Snippets

### Define Snippets

```yaml
template_snippets:
  backend-header: |
    backend {{ name }}
        balance {{ balance | default('roundrobin') }}
        option httpchk GET /health

  rate-limit: |
    stick-table type ip size 100k expire 30s store http_req_rate(10s)
    http-request track-sc0 src
    http-request deny if { sc_http_req_rate(0) gt {{ limit | default(20) }} }
```

### Use Snippets

```jinja2
{% set name = "api-backend" %}
{% set balance = "leastconn" %}
{% include "backend-header" %}
    server api1 10.0.0.1:8080 check
    server api2 10.0.0.2:8080 check
    
    {% set limit = 100 %}
    {% include "rate-limit" %}
```

## Common Patterns

### HAProxy Backend from Service

```jinja2
{% for _, service in resources.get('services', {}).items() %}
backend {{ service.metadata.name }}
    balance roundrobin
    {% for port in service.spec.ports %}
    # Use endpoints for pod IPs
    {% set endpoints = resources.get('endpoints').get_indexed_single(service.metadata.name) %}
    {% if endpoints and endpoints.subsets %}
      {% for subset in endpoints.subsets %}
        {% for address in subset.addresses %}
    server {{ address.targetRef.name }} {{ address.ip }}:{{ port.port }} check
        {% endfor %}
      {% endfor %}
    {% else %}
    # Fallback to service ClusterIP
    server {{ service.metadata.name }} {{ service.spec.clusterIP }}:{{ port.port }} check
    {% endif %}
    {% endfor %}
{% endfor %}
```

### TLS Certificate Bundle

```jinja2
{% for _, secret in resources.get('secrets', {}).items() %}
{% if secret.type == "kubernetes.io/tls" %}
# Certificate for {{ secret.metadata.name }}
{{ secret.data['tls.crt'] | b64decode }}
{{ secret.data['tls.key'] | b64decode }}

{% endif %}
{% endfor %}
```

### Host-based Routing Map

```jinja2
# /etc/haproxy/maps/hosts.map
{% for _, ingress in resources.get('ingresses', {}).items() %}
{% for rule in ingress.spec.rules %}
{% if rule.host %}
{{ rule.host }} backend_{{ rule.backend.service.name }}
{% endif %}
{% endfor %}
{% endfor %}
```

### ACL-based Routing

```jinja2
frontend main
    bind *:80
    
    {% for _, ingress in resources.get('ingresses', {}).items() %}
    {% for rule in ingress.spec.rules %}
    acl host_{{ rule.backend.service.name }} hdr(host) -i {{ rule.host }}
    use_backend backend_{{ rule.backend.service.name }} if host_{{ rule.backend.service.name }}
    {% endfor %}
    {% endfor %}
    
    default_backend default_backend
```

## Debugging Templates

### Add Comments

```jinja2
# Debug: Processing service {{ service.metadata.name }}
# ClusterIP: {{ service.spec.clusterIP }}
# Ports: {{ service.spec.ports | length }}
```

### Use Template Variables

```jinja2
{% set debug_info = [] %}
{% for _, svc in resources.get('services', {}).items() %}
  {% set _ = debug_info.append(svc.metadata.name) %}
{% endfor %}
# Found services: {{ debug_info | join(', ') }}
```

### Conditional Debug Output

```jinja2
{% if env.get('DEBUG') == 'true' %}
# === DEBUG INFO ===
# Total ingresses: {{ resources.get('ingresses', {}) | length }}
# Total services: {{ resources.get('services', {}) | length }}
# ==================
{% endif %}
```