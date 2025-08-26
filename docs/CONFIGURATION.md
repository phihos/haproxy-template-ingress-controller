# Configuration

## ConfigMap Structure

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
```

## Pod Selector

Identifies target HAProxy pods:

```yaml
pod_selector:
  match_labels:
    app: haproxy
    environment: production
```

## Watched Resources

### Basic Configuration

```yaml
watched_resources:
  ingresses:
    api_version: networking.k8s.io/v1
    kind: Ingress
  
  services:
    api_version: v1
    kind: Service
```

### Custom Indexing

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
    index_by: ["metadata.labels['app']"]
  
  endpoints:
    api_version: v1
    kind: Endpoints
    index_by: ["metadata.labels['kubernetes.io/service-name']"]
```

### Field Filtering

Reduce memory usage by ignoring unnecessary fields:

```yaml
watched_resources_ignore_fields:
  - metadata.managedFields      # Default, very large
  - metadata.resourceVersion    # Changes frequently
  - status                      # If not used in templates
  - metadata.annotations['kubectl.kubernetes.io/last-applied-configuration']
```

### Webhook Validation

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
    backend_{{ namespace }}_{{ service }}_{{ port }}
  
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