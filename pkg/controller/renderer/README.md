# pkg/controller/renderer

Renderer component - template rendering for HAProxy configuration.

## Overview

Event-driven component that renders HAProxy configuration from templates using current resource state.

## Quick Start

```go
renderer := renderer.NewRendererComponent(bus, engine, logger)
go renderer.Start(ctx)
```

## Events

- Subscribes: ReconciliationTriggeredEvent
- Publishes: TemplateRenderedEvent, TemplateRenderFailedEvent

## Template Context

The renderer builds a context with all watched Kubernetes resources:

```
{
  "resources": {
    "ingresses": StoreWrapper,    // Provides List() and Get()
    "services": StoreWrapper,
    "endpoints": StoreWrapper,
    // ... other watched resources
  }
}
```

### StoreWrapper Performance

StoreWrapper unwraps `unstructured.Unstructured` objects to plain maps for template access:

- **List()**: Lazy-cached - unwraps all resources on first call, caches for subsequent calls within the same reconciliation
- **Get(keys...)**: On-demand - unwraps matched resources each call (typically small result sets)

This ensures templates pay the unwrapping cost only once per reconciliation, regardless of how many times `List()` is called.

## License

See main repository for license information.
