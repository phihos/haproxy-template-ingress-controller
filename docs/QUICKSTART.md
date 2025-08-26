# Quick Start

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

### 3. Deploy Controller

First deploy the controller that will manage HAProxy configurations:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: haproxy-template-ic
spec:
  selector:
    matchLabels:
      app: haproxy-template-ic
  template:
    metadata:
      labels:
        app: haproxy-template-ic
    spec:
      serviceAccountName: haproxy-template-ic
      containers:
      - name: controller
        image: haproxy-template-ic:dev
        env:
        - name: CONFIGMAP_NAME
          value: haproxy-config
        - name: VERBOSE
          value: "1"
        command: ["haproxy-template-ic", "run", "--configmap-name=haproxy-config"]
        ports:
        - containerPort: 8080
        - containerPort: 9090
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: haproxy-template-ic
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: haproxy-template-ic
rules:
- apiGroups: [""]
  resources: ["configmaps", "services", "endpoints", "pods", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["networking.k8s.io"]
  resources: ["ingresses"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: haproxy-template-ic
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: haproxy-template-ic
subjects:
- kind: ServiceAccount
  name: haproxy-template-ic
  namespace: default
EOF
```

### 4. Deploy HAProxy Instances

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

### 5. Configure Controller

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
    
    watched_resources:
      services:
        api_version: v1
        kind: Service
    
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
            # Simple routing - use first service found
            {% set first_svc = resources.get('services', {}).values() | first %}
            {% if first_svc %}
            default_backend {{ first_svc.metadata.name }}
            {% endif %}
        
        {% for _, svc in resources.get('services', {}).items() %}
        backend {{ svc.metadata.name }}
            balance roundrobin
            {% for port in svc.spec.ports %}
            server {{ svc.metadata.name }}-{{ port.port }} {{ svc.spec.clusterIP }}:{{ port.port }} check
            {% endfor %}
        {% endfor %}
EOF
```

### 6. Verify

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