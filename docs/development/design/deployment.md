# Deployment Diagrams

## Kubernetes Deployment Architecture

```mermaid
graph TB
    subgraph "Kubernetes Cluster"
        subgraph "kube-system Namespace"
            API[Kubernetes API Server]
        end

        subgraph "haproxy-system Namespace"
            subgraph "Controller Deployment"
                CTRL_POD[Controller Pod<br/>Single Container<br/>- Resource Watching<br/>- Template Rendering<br/>- Config Validation<br/>- Deployment]
            end

            CM[ConfigMap<br/>haproxy-config<br/>Templates & Settings]

            subgraph "HAProxy StatefulSet"
                subgraph "haproxy-0"
                    HAP1[HAProxy Container<br/>:80, :443, :8404]
                    DP1[Dataplane API<br/>:5555]
                end

                subgraph "haproxy-1"
                    HAP2[HAProxy Container<br/>:80, :443, :8404]
                    DP2[Dataplane API<br/>:5555]
                end

                subgraph "haproxy-N"
                    HAPN[HAProxy Container<br/>:80, :443, :8404]
                    DPN[Dataplane API<br/>:5555]
                end
            end

            SVC[Service<br/>haproxy<br/>LoadBalancer/NodePort]
        end

        subgraph "Application Namespace"
            ING[Ingress Resources]
            APPSVC[Service Resources]
            PODS[Application Pods]
        end

        subgraph "Monitoring Namespace"
            PROM[Prometheus<br/>Metrics Collection]
            JAEGER[Jaeger<br/>Trace Collection]
        end
    end

    USERS[External Users] --> SVC
    SVC --> HAP1
    SVC --> HAP2
    SVC --> HAPN

    API --> CTRL_POD
    CM --> CTRL_POD
    ING -.Watch.-> CTRL_POD
    APPSVC -.Watch.-> CTRL_POD

    CTRL_POD --> DP1
    CTRL_POD --> DP2
    CTRL_POD --> DPN

    DP1 --> HAP1
    DP2 --> HAP2
    DPN --> HAPN

    HAP1 --> PODS
    HAP2 --> PODS
    HAPN --> PODS

    CTRL_POD -.Metrics.-> PROM
    CTRL_POD -.Traces.-> JAEGER

    style CTRL_POD fill:#4CAF50
    style HAP1 fill:#FF9800
    style HAP2 fill:#FF9800
    style HAPN fill:#FF9800
    style CM fill:#2196F3
```

**Deployment Components:**

1. **Controller Deployment**: Single replica deployment running the operator
   - Watches Kubernetes resources cluster-wide
   - Renders templates and validates configurations
   - Deploys to HAProxy instances via Dataplane API
   - Exposes metrics and health endpoints

2. **HAProxy StatefulSet**: Multiple replicas for high availability
   - Each pod runs HAProxy + Dataplane API sidecar
   - Service selector targets HAProxy pods for traffic routing
   - Scales horizontally based on load

3. **ConfigMap**: Contains controller configuration
   - Template definitions (haproxy.cfg, maps, certificates)
   - Watched resource types and indexing configuration
   - Rendering and deployment settings

## Container Architecture

```mermaid
graph TB
    subgraph "Controller Pod"
        CTRL_MAIN[Controller Process<br/>Port 8080: Health<br/>Port 9090: Metrics<br/>Port 9443: Webhook]

        CTRL_VOL1[ConfigMap Volume<br/>/config]
    end

    subgraph "HAProxy Pod (StatefulSet Member)"
        HAP_PROC[HAProxy Process<br/>Port 80: HTTP<br/>Port 443: HTTPS<br/>Port 8404: Stats]

        DP_PROC[Dataplane API<br/>Port 5555: API<br/>Port 8080: Health]

        HAP_VOL1[Config Volume<br/>/etc/haproxy]
        HAP_VOL2[Maps Volume<br/>/etc/haproxy/maps]
        HAP_VOL3[Certs Volume<br/>/etc/haproxy/certs]
    end

    CM_SRC[ConfigMap<br/>haproxy-config] --> CTRL_VOL1
    CTRL_VOL1 --> CTRL_MAIN

    DP_PROC -.API.-> HAP_PROC
    HAP_VOL1 --> HAP_PROC
    HAP_VOL2 --> HAP_PROC
    HAP_VOL3 --> HAP_PROC

    style CTRL_MAIN fill:#4CAF50
    style HAP_PROC fill:#FF9800
    style DP_PROC fill:#FFB74D
```

**Resource Requirements:**

Controller Pod:
- CPU: 100m request, 500m limit
- Memory: 128Mi request, 512Mi limit
- Volumes: ConfigMap mount for configuration

HAProxy Pod:
- HAProxy Container: 200m CPU, 256Mi memory (per instance)
- Dataplane API Container: 100m CPU, 128Mi memory
- Volumes: EmptyDir for dynamic configs, maps, and certificates

## Network Topology

```mermaid
graph LR
    subgraph "External Network"
        INET[Internet]
    end

    subgraph "Kubernetes Cluster Network"
        LB[LoadBalancer Service<br/>External IP]

        subgraph "Pod Network"
            subgraph "Controller"
                CTRL[Controller<br/>ClusterIP only]
            end

            subgraph "HAProxy Instances"
                subgraph "haproxy-0 Pod<br/>10.0.1.10"
                    HAP1[HAProxy Process<br/>:80, :443, :8404]
                    DP1[Dataplane API<br/>:5555]
                end

                subgraph "haproxy-1 Pod<br/>10.0.1.11"
                    HAP2[HAProxy Process<br/>:80, :443, :8404]
                    DP2[Dataplane API<br/>:5555]
                end
            end

            subgraph "Application Pods"
                APP1[app-pod-1<br/>10.0.2.10]
                APP2[app-pod-2<br/>10.0.2.11]
            end
        end

        KUBE_API[Kubernetes API<br/>443]
    end

    INET --> LB
    LB --> HAP1
    LB --> HAP2

    CTRL --> KUBE_API
    CTRL --> DP1
    CTRL --> DP2

    HAP1 --> APP1
    HAP1 --> APP2
    HAP2 --> APP1
    HAP2 --> APP2

    DP1 -.API.-> HAP1
    DP2 -.API.-> HAP2

    style CTRL fill:#4CAF50
    style HAP1 fill:#FF9800
    style HAP2 fill:#FF9800
    style LB fill:#2196F3
```

**Network Flow:**

1. **Ingress Traffic**: Internet → LoadBalancer → HAProxy Pods → Application Pods
2. **Control Plane**: Controller → Kubernetes API (resource watching)
3. **Configuration Deployment**: Controller → Dataplane API endpoints (HTTP)
4. **Service Discovery**: Controller watches HAProxy pods via Kubernetes API

**Scaling Considerations:**

- **Horizontal Scaling**: Increase HAProxy StatefulSet replicas for more capacity
- **Controller Scaling**: Single active controller (leader election for HA in future)
- **Resource Limits**: Adjust based on number of watched resources and template complexity
- **Network**: Ensure LoadBalancer can distribute traffic across all HAProxy replicas
