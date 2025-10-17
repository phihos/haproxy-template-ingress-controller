# pkg/controller - Controller Orchestration

Development context for the controller coordination layer.

**API Documentation**: See `pkg/controller/README.md`
**Architecture**: See `/docs/development/design.md` (Controller Internal Architecture section)

## When to Work Here

This package is the **coordination layer** - it orchestrates pure components via event-driven patterns.

Modify this package when:
- Adding new controller components (validators, renderers, deployers)
- Modifying event coordination logic
- Changing startup sequencing
- Adding new event types (in `controller/events/`)
- Implementing new event adapters

**DO NOT** modify this package for:
- Template rendering logic → Use `pkg/templating`
- Kubernetes client code → Use `pkg/k8s`
- HAProxy sync logic → Use `pkg/dataplane`
- Event bus infrastructure → Use `pkg/events`

## Package Structure

```
pkg/controller/
├── commentator/          # Event observability (logs all events)
├── configchange/         # Configuration change handler
├── configloader/         # ConfigMap parsing and loading
├── credentialsloader/    # Secret parsing and loading
├── events/               # Domain event type catalog (~50 types)
├── validator/            # Config validation components
│   ├── basic.go         # Structural validation
│   ├── template.go      # Template syntax validation
│   ├── jsonpath.go      # JSONPath expression validation
│   └── coordinator.go   # Scatter-gather coordinator
└── controller.go         # Main controller with staged startup

```

## Key Design Pattern: Event Adapters

This package wraps pure components in event adapters to coordinate them:

```
Pure Component              Event Adapter
(pkg/templating)           (pkg/controller/renderer)
     ↓                            ↓
TemplateEngine  ────wraps──→  RendererComponent
  .Render()                    - Subscribes to events
                               - Calls .Render()
                               - Publishes result events
```

### Example Event Adapter

```go
// pkg/controller/renderer/component.go
package renderer

import (
    "haproxy-template-ic/pkg/controller/events"
    "haproxy-template-ic/pkg/templating"
    "haproxy-template-ic/pkg/events"
)

type Component struct {
    engine   *templating.TemplateEngine  // Pure component
    eventBus *events.EventBus            // Event coordination
}

func (c *Component) Run(ctx context.Context) error {
    eventChan := c.eventBus.Subscribe(100)

    for {
        select {
        case event := <-eventChan:
            switch e := event.(type) {
            case events.ReconciliationTriggeredEvent:
                // Extract primitives for pure component
                templates := c.extractTemplates(e.Config)
                context := c.buildContext(e.Resources)

                // Call pure component
                output, err := c.engine.Render("haproxy.cfg", context)

                // Publish result event
                if err != nil {
                    c.eventBus.Publish(events.RenderFailedEvent{
                        Error: err.Error(),
                    })
                } else {
                    c.eventBus.Publish(events.RenderCompletedEvent{
                        Output: output,
                        Size:   len(output),
                    })
                }
            }
        case <-ctx.Done():
            return ctx.Err()
        }
    }
}
```

## Sub-Package Guidelines

### events/ - Domain Event Catalog

All domain-specific event types live here:

```go
// pkg/controller/events/types.go
package events

import "haproxy-template-ic/pkg/events"

// Lifecycle events
type ControllerStartedEvent struct {
    ConfigVersion string
}
func (e ControllerStartedEvent) EventType() string { return "controller.started" }

// Configuration events
type ConfigParsedEvent struct {
    Config  Config
    Version string
}
func (e ConfigParsedEvent) EventType() string { return "config.parsed" }

// ~50 more event types...
```

**When adding new event:**

1. Define struct with event data
2. Implement EventType() method
3. Document when event is published
4. Update commentator to log it
5. Add to relevant component tests

### commentator/ - Event Observability

Subscribes to all events and produces domain-aware logs:

```go
// pkg/controller/commentator/commentator.go
func (c *EventCommentator) Run(ctx context.Context) error {
    eventChan := c.eventBus.Subscribe(500)  // Large buffer - high volume

    for {
        select {
        case event := <-eventChan:
            c.ringBuffer.Add(event)  // Track recent events

            // Domain-aware logging
            switch e := event.(type) {
            case ConfigValidatedEvent:
                c.logger.Info("configuration validated successfully",
                    "version", e.Version,
                    "templates", len(e.Config.Templates),
                )

            case ReconciliationStartedEvent:
                // Add contextual insights
                lastRecon := c.ringBuffer.FindLast("reconciliation.started")
                if lastRecon != nil {
                    timeSince := e.Timestamp.Sub(lastRecon.Timestamp)
                    c.logger.Info("reconciliation started",
                        "trigger", e.Trigger,
                        "since_last", timeSince,
                    )
                }

            // ~50 more event types with rich context...
            }
        case <-ctx.Done():
            return ctx.Err()
        }
    }
}
```

**When to update commentator:**
- New event type added → Add logging case
- Need better insights → Add ring buffer correlation
- Performance issues → Reduce log verbosity

### validator/ - Configuration Validation

Implements scatter-gather pattern for multi-phase validation:

```go
// coordinator.go orchestrates validation
func (v *ValidationCoordinator) Run(ctx context.Context) error {
    eventChan := v.eventBus.Subscribe(50)

    for {
        select {
        case event := <-eventChan:
            if parsed, ok := event.(ConfigParsedEvent); ok {
                // Create validation request
                req := NewConfigValidationRequest(parsed.Config, parsed.Version)

                // Scatter-gather: wait for all validators
                result, err := v.eventBus.Request(ctx, req, events.RequestOptions{
                    Timeout:            10 * time.Second,
                    ExpectedResponders: []string{"basic", "template", "jsonpath"},
                })

                // Aggregate results
                if err != nil || !allValid(result) {
                    v.eventBus.Publish(ConfigInvalidEvent{
                        Version: parsed.Version,
                        Errors:  extractErrors(result),
                    })
                } else {
                    v.eventBus.Publish(ConfigValidatedEvent{
                        Config:  parsed.Config,
                        Version: parsed.Version,
                    })
                }
            }
        case <-ctx.Done():
            return ctx.Err()
        }
    }
}

// Each validator responds independently
func (v *TemplateValidator) Run(ctx context.Context) error {
    eventChan := v.eventBus.Subscribe(10)

    for {
        select {
        case event := <-eventChan:
            if req, ok := event.(ConfigValidationRequest); ok {
                // Extract primitives for pure validation
                templates := extractTemplates(req.Config)

                // Call pure validator function
                errs := templating.ValidateTemplates(templates)

                // Publish response
                v.eventBus.Publish(NewConfigValidationResponse(
                    req.RequestID(),
                    "template",
                    len(errs) == 0,
                    formatErrors(errs),
                ))
            }
        case <-ctx.Done():
            return ctx.Err()
        }
    }
}
```

## Staged Startup Pattern

The controller uses a 5-stage startup sequence coordinated via events:

```go
// controller.go
func (c *Controller) Run(ctx context.Context) error {
    // Stage 1: Config Management
    log.Info("Stage 1: Config management")
    configWatcher := configloader.New(c.client, c.eventBus)
    configValidator := validator.NewCoordinator(c.eventBus)
    go configWatcher.Run(ctx)
    go configValidator.Run(ctx)

    c.eventBus.Start()  // Release buffered events

    // Stage 2: Wait for Valid Config
    log.Info("Stage 2: Waiting for valid config")
    config := c.waitForEvent(ctx, "config.validated")

    // Stage 3: Resource Watchers
    log.Info("Stage 3: Resource watchers")
    resourceWatcher := c.createResourceWatcher(config)
    go resourceWatcher.Run(ctx)

    // Stage 4: Wait for Index Sync
    log.Info("Stage 4: Waiting for index sync")
    c.waitForEvent(ctx, "index.synchronized")

    // Stage 5: Reconciliation
    log.Info("Stage 5: Reconciliation components")
    reconciler := reconciler.New(c.eventBus)
    executor := executor.New(c.eventBus, config)
    go reconciler.Run(ctx)
    go executor.Run(ctx)

    log.Info("Controller fully operational")

    // Wait for shutdown
    <-ctx.Done()
    return nil
}
```

**Why staged startup?**

1. **Prevents partial state**: Don't reconcile until all resources loaded
2. **Clear dependencies**: Each stage waits for previous stage
3. **Debuggable**: Clear log progression shows where startup blocked
4. **Testable**: Can test each stage independently

## Testing Strategies

### Testing Event Adapters

```go
func TestRendererComponent(t *testing.T) {
    bus := events.NewEventBus(100)
    engine, _ := templating.New(templating.EngineTypeGonja, testTemplates)
    renderer := NewRendererComponent(bus, engine)

    // Subscribe to output events
    eventChan := bus.Subscribe(10)
    bus.Start()

    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    // Start component
    go renderer.Run(ctx)

    // Trigger event
    bus.Publish(ReconciliationTriggeredEvent{
        Config:    testConfig,
        Resources: testResources,
    })

    // Verify response event
    select {
    case event := <-eventChan:
        if completed, ok := event.(RenderCompletedEvent); ok {
            assert.Contains(t, completed.Output, "expected haproxy config")
        } else {
            t.Fatalf("expected RenderCompletedEvent, got %T", event)
        }
    case <-time.After(1 * time.Second):
        t.Fatal("timeout waiting for render event")
    }
}
```

### Testing Scatter-Gather Validation

```go
func TestValidationCoordinator(t *testing.T) {
    bus := events.NewEventBus(100)

    // Start all validators
    basicValidator := validator.NewBasicValidator(bus)
    templateValidator := validator.NewTemplateValidator(bus)
    jsonpathValidator := validator.NewJSONPathValidator(bus)
    coordinator := validator.NewCoordinator(bus)

    go basicValidator.Run(ctx)
    go templateValidator.Run(ctx)
    go jsonpathValidator.Run(ctx)
    go coordinator.Run(ctx)

    // Subscribe to validation result
    eventChan := bus.Subscribe(10)
    bus.Start()

    // Trigger validation
    bus.Publish(ConfigParsedEvent{
        Config:  validConfig,
        Version: "v1",
    })

    // Verify all validators responded and config validated
    select {
    case event := <-eventChan:
        validated, ok := event.(ConfigValidatedEvent)
        require.True(t, ok)
        assert.Equal(t, "v1", validated.Version)
    case <-time.After(2 * time.Second):
        t.Fatal("validation timeout")
    }
}
```

## Common Pitfalls

### Putting Business Logic in Event Adapters

**Problem**: Event adapter contains complex logic.

```go
// Bad - business logic in adapter
func (c *Component) Run(ctx context.Context) error {
    for event := range eventChan {
        if req, ok := event.(ReconciliationTriggeredEvent); ok {
            // Complex template processing logic (50 lines)
            output := complexTemplateProcessing(req.Config)
            c.eventBus.Publish(RenderCompletedEvent{Output: output})
        }
    }
}
```

**Solution**: Extract to pure component.

```go
// Good - delegate to pure component
func (c *Component) Run(ctx context.Context) error {
    for event := range eventChan {
        if req, ok := event.(ReconciliationTriggeredEvent); ok {
            // Adapter just coordinates
            output, err := c.renderer.Process(req.Config)
            if err != nil {
                c.eventBus.Publish(RenderFailedEvent{Error: err})
            } else {
                c.eventBus.Publish(RenderCompletedEvent{Output: output})
            }
        }
    }
}
```

### Event Type in Wrong Package

**Problem**: Domain events in `pkg/events` instead of `pkg/controller/events`.

```go
// Wrong location
pkg/events/types.go:
    type ReconciliationTriggeredEvent struct { ... }
```

**Solution**: Domain events belong in controller.

```go
// Correct location
pkg/controller/events/types.go:
    type ReconciliationTriggeredEvent struct { ... }
```

### Not Using Scatter-Gather for Validation

**Problem**: Manual timeout management for multi-validator coordination.

```go
// Bad - manual coordination
func (v *Coordinator) validate(config Config) bool {
    responses := make(map[string]bool)
    timeout := time.After(10 * time.Second)

    // Publish validation request
    v.bus.Publish(ValidationRequest{config: config})

    // Manually collect responses
    for len(responses) < 3 {
        select {
        case event := <-v.eventChan:
            if resp, ok := event.(ValidationResponse); ok {
                responses[resp.Validator] = resp.Valid
            }
        case <-timeout:
            return false
        }
    }

    return allTrue(responses)
}
```

**Solution**: Use EventBus.Request() scatter-gather.

```go
// Good - use built-in scatter-gather
func (v *Coordinator) validate(ctx context.Context, config Config) bool {
    req := NewValidationRequest(config)

    result, err := v.bus.Request(ctx, req, events.RequestOptions{
        Timeout:            10 * time.Second,
        ExpectedResponders: []string{"basic", "template", "jsonpath"},
    })

    if err != nil {
        return false
    }

    return allResponsesValid(result.Responses)
}
```

### Forgetting to Add Commentator Logging

**Problem**: New event added but commentator doesn't log it.

**Solution**: Always update commentator when adding events.

```go
// pkg/controller/commentator/commentator.go
func (c *EventCommentator) Run(ctx context.Context) error {
    for event := range eventChan {
        switch e := event.(type) {
        // ... existing cases ...

        case NewEventType:  // Add case for new event
            c.logger.Info("new event occurred",
                "field1", e.Field1,
                "field2", e.Field2,
            )
        }
    }
}
```

## Adding New Components

### Checklist

1. **Identify pure component**: What business logic do you need? (e.g., `pkg/templating`)
2. **Define events**: What events trigger this component? What events does it publish?
3. **Create event adapter**: Wrap pure component in controller package
4. **Add to startup**: Integrate into staged startup sequence
5. **Update commentator**: Add logging for new events
6. **Write tests**: Test event adapter behavior
7. **Update README.md**: Document new component

### Example: Adding Cache Warming Component

```go
// Step 1: Pure component exists (pkg/cache)
package cache
func (c *Cache) Warm(keys []string) error { ... }

// Step 2: Define events (pkg/controller/events)
type CacheWarmingTriggeredEvent struct {}
type CacheWarmingCompletedEvent struct { Count int }

// Step 3: Create adapter (pkg/controller/cache)
package cache

type CacheWarmerComponent struct {
    cache    *cache.Cache
    eventBus *events.EventBus
}

func (c *CacheWarmerComponent) Run(ctx context.Context) error {
    eventChan := c.eventBus.Subscribe(50)

    for {
        select {
        case event := <-eventChan:
            if _, ok := event.(CacheWarmingTriggeredEvent); ok {
                keys := c.extractKeys()
                err := c.cache.Warm(keys)

                if err != nil {
                    c.eventBus.Publish(CacheWarmingFailedEvent{Error: err})
                } else {
                    c.eventBus.Publish(CacheWarmingCompletedEvent{Count: len(keys)})
                }
            }
        case <-ctx.Done():
            return ctx.Err()
        }
    }
}

// Step 4: Add to controller.go startup
warmer := cache.NewCacheWarmerComponent(c.cache, c.eventBus)
go warmer.Run(ctx)

// Step 5: Update commentator
case CacheWarmingCompletedEvent:
    c.logger.Info("cache warming completed", "keys", e.Count)
```

## Event Coordination Patterns

### Debounced Reconciliation

```go
type ReconciliationComponent struct {
    eventBus  *events.EventBus
    debouncer *time.Timer
    interval  time.Duration
}

func (r *ReconciliationComponent) Run(ctx context.Context) error {
    eventChan := r.eventBus.Subscribe(100)

    for {
        select {
        case event := <-eventChan:
            if _, ok := event.(ResourceIndexUpdatedEvent); ok {
                // Reset debounce timer on each change
                r.debouncer.Reset(r.interval)
            }

        case <-r.debouncer.C:
            // Timer expired, trigger reconciliation
            r.eventBus.Publish(ReconciliationTriggeredEvent{
                Reason: "debounce_timer",
            })

        case <-ctx.Done():
            return ctx.Err()
        }
    }
}
```

### Conditional Event Publishing

```go
// Publish different events based on result
output, err := c.engine.Render(template, context)
if err != nil {
    c.eventBus.Publish(RenderFailedEvent{
        Template: template,
        Error:    err.Error(),
    })
} else {
    c.eventBus.Publish(RenderCompletedEvent{
        Template: template,
        Output:   output,
        Size:     len(output),
    })
}
```

### Event Filtering

```go
// Only handle events matching specific criteria
for event := range eventChan {
    if update, ok := event.(ResourceIndexUpdatedEvent); ok {
        // Only handle ingress updates
        if update.ResourceType == "ingress" {
            handleIngressUpdate(update)
        }
    }
}
```

## Resources

- Event infrastructure: `pkg/events/CLAUDE.md`
- Package organization: `pkg/CLAUDE.md`
- Architecture: `/docs/development/design.md`
- API documentation: `pkg/controller/README.md`
