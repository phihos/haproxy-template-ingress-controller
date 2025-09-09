# Monitoring Examples

This directory contains example monitoring configurations for HAProxy Template IC.

## Grafana Dashboard

The `grafana-dashboard.json` file contains a comprehensive dashboard for monitoring:

- **Template Renders**: Rate of template rendering operations
- **Config Reloads**: Frequency of configuration reloads
- **Template Render Duration**: Latency percentiles for template rendering
- **Error Rates**: Error rates by type
- **Dataplane API Status**: HAProxy Dataplane API operation metrics

### Import Instructions

1. Open Grafana UI
2. Navigate to Dashboards → Import
3. Upload the `grafana-dashboard.json` file
4. Configure data source to point to your Prometheus instance
5. Save the dashboard

## Prometheus Alerts

The `prometheus-alerts.yaml` file contains production-ready alerting rules:

### Critical Alerts
- **HAProxyTemplateICDown**: Service is completely down
- **TemplateRenderFailures**: Template rendering is failing

### Warning Alerts
- **HighTemplateRenderLatency**: Template rendering is slow (>10s)
- **FrequentConfigReloads**: Configuration changes too frequently
- **HighErrorRate**: General error rate threshold exceeded
- **DataplaneAPIErrors**: HAProxy Dataplane API integration issues

### Integration

Add the alerts to your Prometheus configuration:

```yaml
rule_files:
  - "prometheus-alerts.yaml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

## Metrics Reference

Key metrics exposed by HAProxy Template IC:

- `haproxy_template_ic_rendered_templates_total`: Total template renders by status
- `haproxy_template_ic_template_render_duration_seconds`: Template render latency
- `haproxy_template_ic_config_reload_duration_seconds`: Configuration reload timing
- `haproxy_template_ic_errors_total`: Error count by type
- `haproxy_template_ic_dataplane_api_requests_total`: Dataplane API request metrics
- `haproxy_template_ic_dataplane_api_duration_seconds`: Dataplane API operation timing
- `haproxy_template_ic_watched_resources_total`: Count of watched Kubernetes resources
- `haproxy_template_ic_haproxy_instances_total`: Number of HAProxy instances

## Best Practices

1. **Monitor template render latency** - High latency may indicate complex templates or resource constraints
2. **Watch configuration reload frequency** - Frequent reloads may indicate configuration instability
3. **Track error rates by type** - Different error types may require different remediation strategies
4. **Monitor dataplane API health** - API failures indicate HAProxy connectivity issues
5. **Monitor resource usage** - Use standard Kubernetes metrics for CPU/memory monitoring