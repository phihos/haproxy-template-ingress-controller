# pkg/controller/discovery

HAProxy pod discovery component.

## Overview

Discovers and tracks HAProxy pods in the cluster for configuration deployment.

## Quick Start

```go
discovery := discovery.NewDiscoveryComponent(bus, k8sClient, config, logger)
go discovery.Start(ctx)
```

## Events

- Subscribes: ConfigValidatedEvent
- Publishes: HAProxyPodsDiscoveredEvent, HAProxyPodAddedEvent, HAProxyPodRemovedEvent

## License

See main repository for license information.
