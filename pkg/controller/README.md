# pkg/controller

Event-driven controller orchestration for haproxy-template-ingress-controller.

## Overview

The `pkg/controller` package provides the main controller logic and component coordination using an event-driven architecture. All components communicate through the EventBus from `pkg/events`, enabling loose coupling, testability, and observability.

**Key Features:**

- **Event-Driven Architecture**: Components communicate via EventBus pub/sub and request-response patterns
- **Startup Orchestration**: Coordinated multi-stage startup ensuring dependencies are met
- **Configuration Management**: Watches and validates controller ConfigMap and credentials Secret
- **Pure Business Logic**: Core components are event-agnostic for easy testing
- **Comprehensive Observability**: Event Commentator provides domain-aware logging with event correlation

## Architecture

The controller follows the **pure components + event adapters** pattern:

```
Event Flow:

  EventBus (pkg/events)
       │
       ├─> ConfigLoader ──────> Parse & Validate ──> ConfigParsedEvent
       │
       ├─> CredentialsLoader ─> Load & Validate ──> CredentialsUpdatedEvent
       │
       ├─> Validator Components (3 validators respond via scatter-gather)
       │   ├── BasicValidator ──> Structural validation
       │   ├── TemplateValidator ──> Template syntax validation
       │   └── JSONPathValidator ──> JSONPath expression validation
       │   All respond with ConfigValidationResponse ──> ConfigValidatedEvent
       │
       └─> EventCommentator ──> Domain-aware logging with event correlation
```

## Package Structure

```
pkg/controller/
├── commentator/         # Event commentator for observability
│   ├── commentator.go   # Subscribes to all events, produces rich logs
│   └── ringbuffer.go    # Ring buffer for event correlation
├── configchange/        # Configuration change handler
│   └── handler.go       # Handles config resource change events
├── configloader/        # Configuration loading and parsing
│   └── loader.go        # Loads ConfigMap, parses config, publishes ConfigParsedEvent
├── credentialsloader/   # Credentials loading and validation
│   └── loader.go        # Loads Secret, validates credentials, publishes CredentialsUpdatedEvent
├── events/              # Domain-specific event type definitions
│   └── types.go         # ~30+ event types covering controller lifecycle
├── validator/           # Configuration validation components
│   ├── basic.go         # Structural validation (ports, required fields)
│   ├── template.go      # Template syntax validation using pkg/templating
│   └── jsonpath.go      # JSONPath expression validation
└── controller.go        # Main controller with startup orchestration
```

## Core Components

### EventCommentator

Subscribes to all EventBus events and produces domain-aware log messages with contextual insights.

**Features:**
- Ring buffer maintains recent event history for correlation
- Produces insights like "triggered by config change 234ms ago"
- Centralized logging strategy - pure components remain clean
- Fully asynchronous - no performance impact on business logic

**Example:**
```go
import (
    "haproxy-template-ic/pkg/controller/commentator"
    "haproxy-template-ic/pkg/events"
)

eventBus := events.NewEventBus(1000)
logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))

// Start commentator early to capture all events
commentator := commentator.NewEventCommentator(eventBus, logger, 100)
go commentator.Run(ctx)
```

### ConfigLoader

Loads and parses controller configuration from ConfigMap resources.

**Responsibilities:**
- Subscribes to ConfigResourceChangedEvent
- Parses ConfigMap data using pkg/core/config.ParseConfig()
- Applies default values using pkg/core/config.SetDefaults()
- Publishes ConfigParsedEvent on success

**Example:**
```go
import (
    "haproxy-template-ic/pkg/controller/configloader"
    "haproxy-template-ic/pkg/events"
)

loader := configloader.New(eventBus)
go loader.Run(ctx)
```

### CredentialsLoader

Loads and validates credentials from Secret resources.

**Responsibilities:**
- Subscribes to SecretResourceChangedEvent
- Loads credentials using pkg/core/config.LoadCredentials()
- Validates credentials using pkg/core/config.ValidateCredentials()
- Publishes CredentialsUpdatedEvent on success, CredentialsInvalidEvent on failure

### Validator Components

Three validators respond to ConfigValidationRequest using scatter-gather pattern:

1. **BasicValidator**: Structural validation (pkg/core/config.ValidateStructure)
2. **TemplateValidator**: Template syntax validation (pkg/templating.ValidateTemplates)
3. **JSONPathValidator**: JSONPath expression validation (pkg/k8s/indexer)

**Scatter-Gather Pattern:**
```go
// Coordinator publishes request
req := events.NewConfigValidationRequest(config, version)
result, err := eventBus.Request(ctx, req, events.RequestOptions{
    Timeout:            10 * time.Second,
    ExpectedResponders: []string{"basic", "template", "jsonpath"},
})

// Each validator responds independently
for _, resp := range result.Responses {
    validResp := resp.(events.ConfigValidationResponse)
    if !validResp.Valid {
        // Handle validation error
    }
}
```

## Startup Sequence

The controller uses a multi-stage startup sequence coordinated via EventBus:

### Stage 1: Config Management

```go
eventBus := events.NewEventBus(1000)

// Create config management components
configWatcher := NewConfigWatcher(client, eventBus)
configLoader := NewConfigLoader(eventBus)
configValidator := NewConfigValidator(eventBus)

// Start components
go configWatcher.Run(ctx)
go configLoader.Run(ctx)
go configValidator.Run(ctx)

// Start EventBus to replay buffered events
eventBus.Start()
```

### Stage 2: Wait for Valid Config

```go
events := eventBus.Subscribe(100)

for {
    select {
    case event := <-events:
        if validatedEvent, ok := event.(events.ConfigValidatedEvent); ok {
            config = validatedEvent.Config
            goto ConfigReady
        }
    case <-ctx.Done():
        return ctx.Err()
    }
}

ConfigReady:
eventBus.Publish(events.ControllerStartedEvent{
    ConfigVersion: config.Version,
})
```

### Stage 3: Resource Watchers

```go
// Start resource watchers based on validated config
stores := make(map[string]types.Store)
resourceWatcher := NewResourceWatcher(client, eventBus, config.WatchedResources, stores)
go resourceWatcher.Run(ctx)

// Track when all indices are synchronized
indexTracker := NewIndexSynchronizationTracker(eventBus, config.WatchedResources)
go indexTracker.Run(ctx)
```

### Stage 4: Wait for Index Sync

```go
for {
    select {
    case event := <-events:
        if _, ok := event.(events.IndexSynchronizedEvent); ok {
            goto IndexReady
        }
    case <-time.After(30 * time.Second):
        return fmt.Errorf("index sync timeout")
    }
}

IndexReady:
// All resource indices populated, safe to proceed
```

### Stage 5: Reconciliation

```go
reconciler := NewReconciliationComponent(eventBus)
executor := NewReconciliationExecutor(eventBus, config, stores)

go reconciler.Run(ctx)
go executor.Run(ctx)

log.Info("All components started")
```

## Event-Driven Patterns

### Async Pub/Sub (Fire and Forget)

Used for notifications and observability:

```go
// Publisher
eventBus.Publish(events.ConfigParsedEvent{
    Config:  config,
    Version: version,
})

// Subscriber
eventChan := eventBus.Subscribe(100)
for event := range eventChan {
    switch e := event.(type) {
    case events.ConfigParsedEvent:
        // Handle event
    }
}
```

### Sync Request-Response (Scatter-Gather)

Used for coordinated validation:

```go
// Requester
req := events.NewConfigValidationRequest(config, version)
result, err := eventBus.Request(ctx, req, events.RequestOptions{
    Timeout:            10 * time.Second,
    ExpectedResponders: []string{"basic", "template", "jsonpath"},
})

// Responders
for event := range eventChan {
    if req, ok := event.(events.ConfigValidationRequest); ok {
        valid, errors := validate(req.Config)

        resp := events.NewConfigValidationResponse(
            req.RequestID(),
            "template",
            valid,
            errors,
        )
        eventBus.Publish(resp)
    }
}
```

## Event Types

The `pkg/controller/events` package defines ~30+ event types organized into categories:

**Lifecycle Events:**
- ControllerStartedEvent
- ControllerShutdownEvent

**Configuration Events:**
- ConfigResourceChangedEvent
- ConfigParsedEvent
- ConfigValidationRequest (Request)
- ConfigValidationResponse (Response)
- ConfigValidatedEvent
- ConfigInvalidEvent

**Credentials Events:**
- SecretResourceChangedEvent
- CredentialsUpdatedEvent
- CredentialsInvalidEvent

**Resource Events:**
- ResourceIndexUpdatedEvent
- ResourceSyncCompleteEvent
- IndexSynchronizedEvent

**Reconciliation Events:**
- ReconciliationTriggeredEvent
- ReconciliationStartedEvent
- ReconciliationCompletedEvent
- ReconciliationFailedEvent

**Template Events:**
- TemplateRenderedEvent
- TemplateRenderFailedEvent

**Validation Events:**
- ValidationStartedEvent
- ValidationCompletedEvent
- ValidationFailedEvent

**Deployment Events:**
- DeploymentStartedEvent
- InstanceDeployedEvent
- InstanceDeploymentFailedEvent
- DeploymentCompletedEvent

**Storage Events:**
- StorageSyncStartedEvent
- StorageSyncCompletedEvent
- StorageSyncFailedEvent

**HAProxy Pod Events:**
- HAProxyPodsDiscoveredEvent
- HAProxyPodAddedEvent
- HAProxyPodRemovedEvent

See `pkg/controller/events/types.go` for complete event definitions.

## Design Principles

### 1. Pure Components

Business logic has no event dependencies:

```go
// GOOD: Pure function in pkg/templating
func ValidateTemplates(templates map[string]string) []error {
    // No dependency on events package
    // Easy to test
    return errors
}

// Event adapter in pkg/controller/validator
func (v *TemplateValidator) handleValidationRequest(req events.ConfigValidationRequest) {
    // Extract primitive types
    templates := extractTemplates(req.Config)

    // Call pure function
    errors := templating.ValidateTemplates(templates)

    // Publish response
    v.eventBus.Publish(events.NewConfigValidationResponse(...))
}
```

### 2. Single Event Layer

Only controller package knows about events:

```
pkg/core/config/     Pure functions, no events
pkg/templating/      Pure functions, no events
pkg/k8s/indexer/     Pure functions, no events
pkg/controller/      Event adapters wrapping pure functions
```

### 3. Observability Through Events

All state changes flow through EventBus:

```go
// EventCommentator sees everything
type EventCommentator struct {
    eventBus *events.EventBus
    logger   *slog.Logger
}

func (c *EventCommentator) Run(ctx context.Context) error {
    events := c.eventBus.Subscribe(1000)

    for event := range events {
        // Produce domain-aware log messages
        c.commentate(ctx, event)
    }
}
```

### 4. Testability

Pure components tested without event infrastructure:

```go
// Test pure function directly
func TestValidateTemplates(t *testing.T) {
    templates := map[string]string{
        "test": "{{ invalid syntax",
    }

    errors := templating.ValidateTemplates(templates)
    assert.NotEmpty(t, errors)
}
```

## Integration Example

Complete controller setup:

```go
package main

import (
    "context"
    "log/slog"

    "haproxy-template-ic/pkg/controller"
    "haproxy-template-ic/pkg/controller/commentator"
    "haproxy-template-ic/pkg/events"
    "haproxy-template-ic/pkg/k8s/client"
)

func main() {
    ctx := context.Background()

    // Create EventBus
    eventBus := events.NewEventBus(1000)

    // Create logger
    logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))

    // Create Kubernetes client
    k8sClient, err := client.New(client.Config{})
    if err != nil {
        log.Fatal(err)
    }

    // Start EventCommentator early (captures all events)
    commentator := commentator.NewEventCommentator(eventBus, logger, 100)
    go commentator.Run(ctx)

    // Run controller (handles multi-stage startup)
    ctrl := controller.New(eventBus, k8sClient, logger)
    if err := ctrl.Run(ctx); err != nil {
        log.Fatal(err)
    }
}
```

## Related Documentation

- [pkg/events/README.md](../events/README.md) - Event bus infrastructure
- [pkg/core/README.md](../core/README.md) - Configuration parsing and validation
- [pkg/k8s/README.md](../k8s/README.md) - Kubernetes resource watching
- [docs/design.md](../../docs/development/design.md) - Complete architecture overview

## Testing

The controller package is designed for testability:

```bash
# Run controller package tests
go test ./pkg/controller/...

# Run with coverage
go test -cover ./pkg/controller/...

# Run integration tests
go test -tags=integration ./pkg/controller/...
```

## License

Part of haproxy-template-ingress-controller project.
