# pkg/controller/configloader - Configuration Loader

Development context for the ConfigLoader component.

**API Documentation**: See `pkg/controller/configloader/README.md`

## When to Work Here

Work in this package when:
- Modifying ConfigMap parsing logic
- Changing how configuration is extracted from Kubernetes resources
- Adding validation before config parsing
- Debugging configuration loading issues

**DO NOT** work here for:
- Configuration schema definition → Use `pkg/core/config`
- Configuration validation → Use `pkg/controller/validator`
- ConfigMap watching → Use `pkg/controller/resourcewatcher` or `pkg/controller/configchange`

## Package Purpose

Pure event-driven component that subscribes to ConfigResourceChangedEvent and parses ConfigMap data into config.Config structures. This is part of Stage 1 (Config Management) in the controller lifecycle.

Key responsibilities:
- Extract YAML from ConfigMap data field
- Parse YAML into config.Config
- Publish ConfigParsedEvent on success
- Log errors for invalid YAML

## Architecture

```
ConfigResourceChangedEvent (from watcher)
    ↓
ConfigLoaderComponent
    ├─ Extract ConfigMap.Data["config"]
    ├─ Parse YAML → config.Config
    └─ Publish ConfigParsedEvent
            ↓
    ValidationCoordinator (Stage 1)
```

Event-driven with no direct Kubernetes or watcher dependencies.

## Component Lifecycle

```go
func main() {
    loader := configloader.NewConfigLoaderComponent(bus, logger)
    go loader.Start(ctx)

    // Component runs until context cancelled
    // Processes ConfigResourceChangedEvent → ConfigParsedEvent
}
```

## Usage Patterns

### Basic Integration

```go
// Create component
loader := configloader.NewConfigLoaderComponent(bus, logger)

// Start in goroutine
go loader.Start(ctx)

// Component subscribes to ConfigResourceChangedEvent
// Publishes ConfigParsedEvent when valid config found
```

### Event Flow

```go
// 1. Watcher publishes ConfigResourceChangedEvent
bus.Publish(&events.ConfigResourceChangedEvent{
    Resource: configMap,  // *unstructured.Unstructured
})

// 2. ConfigLoader processes event
// - Extracts data["config"]
// - Parses YAML
// - Publishes ConfigParsedEvent

// 3. ValidationCoordinator receives ConfigParsedEvent
eventChan := bus.Subscribe(50)
for event := range eventChan {
    if parsed, ok := event.(*events.ConfigParsedEvent); ok {
        // Trigger validation
    }
}
```

## Common Pitfalls

### Missing "config" Key

**Problem**: ConfigMap doesn't have `data.config` field.

```yaml
# Bad - wrong key name
apiVersion: v1
kind: ConfigMap
data:
  configuration: |  # Wrong key!
    templates: ...
```

**Solution**: Use "config" key.

```yaml
# Good
apiVersion: v1
kind: ConfigMap
data:
  config: |  # Correct key
    templates: ...
```

### Invalid YAML Syntax

**Problem**: YAML parsing fails, no event published.

```yaml
# Bad - invalid YAML
config: |
  templates:
    main: |
      global
        maxconn 2000
      # Missing closing quote or indent error
```

**Solution**: Component logs error but doesn't publish event. Fix YAML syntax.

### Resource Type Mismatch

**Problem**: ConfigResourceChangedEvent contains non-ConfigMap resource.

**Solution**: This should not happen if watcher is configured correctly. Check watcher configuration.

## Integration with Controller

Controller creates and starts component in Stage 1:

```go
// pkg/controller/controller.go - Stage 1
func (c *Controller) runIteration(...) {
    // Stage 1: Config Management
    logger.Info("Stage 1: Config management")

    configLoader := configloader.NewConfigLoaderComponent(bus, logger)
    go configLoader.Start(ctx)

    // Component runs until ctx cancelled
}
```

## Resources

- Configuration schema: `pkg/core/config/CLAUDE.md`
- Event types: `pkg/controller/events/CLAUDE.md`
- Controller lifecycle: `pkg/controller/CLAUDE.md`
