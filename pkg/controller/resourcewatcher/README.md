# pkg/controller/resourcewatcher

Resource watcher lifecycle management.

## Overview

Manages lifecycle of Kubernetes resource watchers based on controller configuration.

## Quick Start

```go
watcher := resourcewatcher.NewResourceWatcherComponent(bus, k8sClient, logger)
go watcher.Start(ctx)
```

## Events

- Subscribes: ConfigValidatedEvent
- Publishes: ResourceIndexUpdatedEvent, ResourceSyncCompleteEvent

## License

See main repository for license information.
