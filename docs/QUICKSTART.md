# Quick Start

This guide provides a step-by-step introduction to deploying the controller in a Kubernetes
environment. It covers the prerequisites, installation process, and basic configuration to get you up and
running quickly.

By the end of this guide, you'll have a functional HAProxy Ingress Controller managing traffic in your local cluster.

## Prerequisites

- Docker
- kubectl  
- kind or minikube

## Installation

### 1. Create Cluster

```bash
kind create cluster --name haproxy-ic
```

### 2. Deploy Controller

```bash
# Build and deploy locally
docker build -t haproxy-template-ic:dev .
kind load docker-image haproxy-template-ic:dev --name haproxy-ic
kubectl apply -k deploy/overlays/dev
```

### 3. Deploy HAProxy Instances

Now deploy the HAProxy instances that will be managed:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: haproxy
spec:
  selector:
    matchLabels:
      app: haproxy
  template:
    metadata:
      labels:
        app: haproxy
    spec:
      containers:
      - name: haproxy
        image: haproxytech/haproxy-alpine:3.1  # 3.1+ required for fast startup
        ports:
        - containerPort: 80
        - containerPort: 8404
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8404
          initialDelaySeconds: 5
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8404
          initialDelaySeconds: 10
          periodSeconds: 10
      - name: dataplane
        image: haproxytech/haproxy-alpine:3.1  # 3.1+ required for fast startup
        command: ["/usr/bin/dataplaneapi"]
        args:
        - --host=0.0.0.0
        - --port=5555
        - --haproxy-bin=/usr/sbin/haproxy
        - --config-file=/etc/haproxy/haproxy.cfg
        - --reload-cmd="kill -SIGUSR2 1"
        - --username=admin
        - --password=adminpass
        ports:
        - containerPort: 5555
        volumeMounts:
        - name: haproxy-config
          mountPath: /etc/haproxy
        readinessProbe:
          tcpSocket:
            port: 5555
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: haproxy-config
        emptyDir: {}
EOF
```


### 4. Create Configuration

Apply the configuration that tells the controller what to watch and how to configure HAProxy:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: haproxy-config
data:
  config: |
    pod_selector:
      match_labels:
        app: haproxy
        component: loadbalancer
    
    watched_resources:
      services:
        api_version: v1
        kind: Service
        index_by: ["metadata.name"]
    
    haproxy_config:
      template: |
        global
            daemon
        defaults
            mode http
            timeout connect 5s
        frontend health
            bind *:8404
            http-request return status 200 if { path /healthz }
        frontend main
            bind *:80
            default_backend services
        backend services
            balance roundrobin
            {% for _, svc in resources.get('services', {}).items() %}
            {% for port in svc.spec.ports %}
            server {{ svc.metadata.name }}-{{ port.port }} {{ svc.spec.clusterIP }}:{{ port.port }} check
            {% endfor %}
            {% endfor %}
---
apiVersion: v1
kind: Secret
metadata:
  name: haproxy-credentials
type: Opaque
data:
  dataplane_username: YWRtaW4=  # admin
  dataplane_password: YWRtaW5wYXNz  # adminpass
  validation_username: YWRtaW4=  # admin  
  validation_password: dmFsaWRhdGlvbnBhc3M=  # validationpass
EOF
```

### 5. Verify

```bash
# Check controller logs
kubectl logs -l app=haproxy-template-ic

# Check HAProxy status
kubectl exec deployment/haproxy -c dataplane -- \
  curl -u admin:adminpass http://localhost:5555/v3/services/haproxy/configuration/global

# Port forward and test
kubectl port-forward deployment/haproxy 8080:80
curl http://localhost:8080
```

## Next Steps

- [Configuration Guide](CONFIGURATION.md) - Advanced ConfigMap options
- [Templates Guide](TEMPLATES.md) - Jinja2 syntax and patterns
- [Operations Guide](OPERATIONS.md) - Production deployment