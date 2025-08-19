# Deployment Configuration

This directory contains Kustomize-based deployment configurations for the HAProxy Template Ingress Controller.

## Structure

```
deploy/
├── base/                    # Base configuration files
│   ├── configmap.yaml      # Controller configuration
│   ├── deployment.yaml     # Main controller with validation sidecars
│   ├── deployment-haproxy.yaml  # Production HAProxy pods
│   ├── configmap-universal.yaml # Unified HAProxy startup scripts
│   └── ...                 # Other resources
├── overlays/
│   ├── dev/               # Development environment
│   └── production/        # Production environment
└── README.md              # This file
```

## Quick Start

### Development
```bash
# Apply dev configuration
kubectl apply -k deploy/overlays/dev

# Check status
kubectl get pods -n haproxy-template-ic
```

### Production
```bash
# Apply production configuration
kubectl apply -k deploy/overlays/production

# Verify deployment
kubectl get all -n haproxy-template-ic
```

## Key Requirements

### HAProxy Version
- **Required**: HAProxy 3.1+ for fast dataplaneapi startup (3-5 seconds)
- **Avoid**: Version 3.0 has 30-60 second dataplaneapi startup time
- **Image**: `haproxytech/haproxy-alpine:3.1`
- **Note**: HAProxy core starts quickly in both versions; only dataplaneapi was affected

### Port Configuration
- **Controller**: 8080 (health), 9090 (metrics), 9443 (webhook)
- **Validation HAProxy**: 8404 (health)
- **Validation Dataplane**: 5555 (API)
- **Production HAProxy**: 80 (HTTP), 443 (HTTPS), 8404 (health)
- **Production Dataplane**: 5555 (API)

### Authentication
- **Production**: `admin`/`adminpass`
- **Validation**: `admin`/`validationpass`

## Architecture

### Controller Pod (1 pod, 3 containers)
- **Controller**: Main logic, watches Kubernetes resources
- **Validation HAProxy**: Tests configs before deployment
- **Validation Dataplane**: Manages validation instance

### Production HAProxy Pods (N pods, 2 containers each)
- **HAProxy**: Serves production traffic
- **Dataplane**: Receives configurations from controller
- Must match `pod_selector.match_labels` in ConfigMap

## Configuration Variables

The base configuration uses Kustomize variables for consistency:

```yaml
configMapGenerator:
- name: haproxy-config
  literals:
    - DATAPLANE_PORT=5555
    - PRODUCTION_PASSWORD=adminpass
    - VALIDATION_PASSWORD=validationpass
    - PRODUCTION_HEALTHZ_PORT=8404
    - VALIDATION_HEALTHZ_PORT=8404
```

## Customization

### Environment-Specific Overlays
Create custom overlays in `deploy/overlays/` for different environments:

```yaml
# deploy/overlays/staging/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: haproxy-template-ic-staging
resources:
  - ../../base

patches:
  - patch: |-
      - op: replace
        path: /spec/replicas
        value: 3
    target:
      kind: Deployment
      name: haproxy-production
```

### Resource Requirements
Add resource limits via patches:

```yaml
patches:
  - patch: |-
      - op: add
        path: /spec/template/spec/containers/0/resources
        value:
          limits:
            cpu: 500m
            memory: 512Mi
          requests:
            cpu: 100m
            memory: 128Mi
    target:
      kind: Deployment
      name: haproxy-template-ic
```

## Troubleshooting

### Common Issues

1. **Pods not starting**: Check HAProxy version is 3.1+
2. **Health check failures**: Ensure port 8404 health endpoint in config
3. **Authentication errors**: Verify dataplane passwords match environment
4. **Template errors**: Check controller logs for validation failures

### Debugging Commands

```bash
# Check pod status
kubectl get pods -n haproxy-template-ic

# View controller logs
kubectl logs -n haproxy-template-ic deployment/haproxy-template-ic -c controller

# Check HAProxy config
kubectl exec -n haproxy-template-ic deployment/haproxy-production -c haproxy -- cat /etc/haproxy/haproxy.cfg

# Test dataplane API
kubectl port-forward -n haproxy-template-ic svc/haproxy-production-dataplane 5555:5555
curl -u admin:adminpass http://localhost:5555/v3/info
```

## Security Considerations

- Use secrets for production passwords instead of literals
- Enable network policies to restrict access
- Consider using cert-manager for webhook certificates
- Regularly update HAProxy images for security patches