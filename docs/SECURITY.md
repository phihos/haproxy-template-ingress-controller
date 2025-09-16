# Security

This document outlines essential security practices for deploying the HAProxy Ingress Controller in production
environments. It covers RBAC configuration, network policies, secret management, pod security, and TLS setup to ensure
a secure and compliant deployment.

Follow these guidelines to minimize attack surfaces, protect sensitive data, and enforce security best practices for
your ingress infrastructure.

## Contents

- [RBAC Configuration](#rbac-configuration)
- [Network Policies](#network-policies)
- [Secrets Management](#secrets-management)
- [Pod Security](#pod-security)
- [Webhook TLS](#webhook-tls)
- [Security Checklist](#security-checklist)
- [Security Scanning](#security-scanning)

## RBAC Configuration

### Minimum Required Permissions

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: haproxy-template-ic
rules:
# Read ConfigMaps for configuration
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch"]
# Read Services and Endpoints for backend discovery  
- apiGroups: [""]
  resources: ["services", "endpoints"]
  verbs: ["get", "list", "watch"]
# Read Pods for HAProxy instance discovery
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
# Read Secrets for TLS certificates (if needed)
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list", "watch"]
# Read Ingresses for routing rules
- apiGroups: ["networking.k8s.io"]
  resources: ["ingresses"]
  verbs: ["get", "list", "watch"]
```

### Namespace-Scoped Deployment

For better isolation, use namespace-scoped roles:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: haproxy-template-ic
  namespace: haproxy-system
rules:
- apiGroups: [""]
  resources: ["configmaps", "services", "endpoints", "pods", "secrets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: haproxy-template-ic
  namespace: haproxy-system
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: haproxy-template-ic
subjects:
- kind: ServiceAccount
  name: haproxy-template-ic
  namespace: haproxy-system
```

## Network Policies

### Controller Isolation

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: haproxy-template-ic
  namespace: haproxy-system
spec:
  podSelector:
    matchLabels:
      app: haproxy-template-ic
  policyTypes:
  - Ingress
  - Egress
  
  ingress:
  # Prometheus scraping
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - port: 9090
      protocol: TCP
  
  # Webhook from API server
  - from:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - port: 9443
      protocol: TCP
  
  egress:
  # Kubernetes API
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - port: 443
      protocol: TCP
  
  # HAProxy Dataplane API
  - to:
    - podSelector:
        matchLabels:
          app: haproxy
    ports:
    - port: 5555
      protocol: TCP
  
  # DNS
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - port: 53
      protocol: UDP
```

### HAProxy Pod Isolation

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: haproxy
  namespace: haproxy-system
spec:
  podSelector:
    matchLabels:
      app: haproxy
  policyTypes:
  - Ingress
  
  ingress:
  # Allow traffic on service ports
  - from:
    - podSelector: {}
    - namespaceSelector: {}
    ports:
    - port: 80
      protocol: TCP
    - port: 443
      protocol: TCP
  
  # Health checks
  - from:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - port: 8404
      protocol: TCP
  
  # Dataplane API from controller only
  - from:
    - podSelector:
        matchLabels:
          app: haproxy-template-ic
    ports:
    - port: 5555
      protocol: TCP
```

## Secrets Management

### TLS Certificates

Store certificates as Kubernetes Secrets:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: haproxy-tls
  namespace: haproxy-system
type: kubernetes.io/tls
data:
  tls.crt: <base64-encoded-cert>
  tls.key: <base64-encoded-key>
```

### Dataplane API Credentials

Use Secrets for authentication:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: dataplane-credentials
  namespace: haproxy-system
type: Opaque
stringData:
  username: admin
  password: <strong-password>
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: haproxy
spec:
  template:
    spec:
      containers:
      - name: dataplane
        env:
        - name: DATAPLANE_USER
          valueFrom:
            secretKeyRef:
              name: dataplane-credentials
              key: username
        - name: DATAPLANE_PASS
          valueFrom:
            secretKeyRef:
              name: dataplane-credentials
              key: password
```

## Pod Security

### Security Context

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: haproxy-template-ic
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: controller
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
          readOnlyRootFilesystem: true
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: socket
          mountPath: /run/haproxy-template-ic
      volumes:
      - name: tmp
        emptyDir: {}
      - name: socket
        emptyDir: {}
```

### Pod Security Standards

Apply restricted policy:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: haproxy-system
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

## Webhook TLS

### Certificate Generation

For production, use cert-manager or external CA:

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: haproxy-template-ic-webhook
  namespace: haproxy-system
spec:
  secretName: webhook-tls
  issuerRef:
    name: internal-ca
    kind: ClusterIssuer
  dnsNames:
  - haproxy-template-ic-webhook.haproxy-system.svc
  - haproxy-template-ic-webhook.haproxy-system.svc.cluster.local
```

### Webhook Configuration

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: haproxy-template-ic
webhooks:
- name: configmap.haproxy-template-ic
  clientConfig:
    service:
      name: haproxy-template-ic-webhook
      namespace: haproxy-system
      path: /validate
    caBundle: <base64-encoded-ca>
  rules:
  - apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["configmaps"]
    operations: ["CREATE", "UPDATE"]
  sideEffects: None
  admissionReviewVersions: ["v1"]
  failurePolicy: Fail
```


## Security Checklist

- [ ] RBAC configured with minimum required permissions
- [ ] Network policies enforced
- [ ] Secrets used for sensitive data
- [ ] Pod security context configured
- [ ] Read-only root filesystem
- [ ] Non-root user
- [ ] Capabilities dropped
- [ ] Webhook TLS configured
- [ ] Resource limits set
- [ ] Security scanning in CI/CD
- [ ] Regular security updates

## Security Scanning

### Container Scanning

```bash
# Scan image for vulnerabilities
trivy image haproxy-template-ic:latest

# Scan running deployment
kubectl get pods -n haproxy-system -o jsonpath="{.items[*].spec.containers[*].image}" | \
  xargs -n1 trivy image
```

### Configuration Scanning

```bash
# Scan Kubernetes manifests
kubesec scan deployment.yaml

# Check RBAC permissions
kubectl auth can-i --list --as=system:serviceaccount:haproxy-system:haproxy-template-ic
```