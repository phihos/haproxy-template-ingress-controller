# HAProxy Template Ingress Controller - Development Context

This file contains cross-cutting development context for working on this codebase. For package-specific context, see CLAUDE.md files in relevant subdirectories.

## Project Overview

Event-driven Kubernetes operator that manages HAProxy configurations through template-driven approaches. Uses pure components wrapped in event adapters for clean separation of concerns.

Architecture documentation: `docs/development/design.md`

## Coding Standards

### Go Idioms

- Follow standard Go conventions (effective Go, Go proverbs)
- Use `gofmt` and `goimports` for formatting
- Run linters before commits: `make lint`
- Table-driven tests for multiple scenarios
- Early returns for error cases
- **NEVER use //nolint directives** - Fix linting issues properly by refactoring code, not by suppressing warnings

### Error Handling

```go
// Wrap errors with context
if err != nil {
    return fmt.Errorf("failed to parse config: %w", err)
}

// Custom error types for different failure modes
type ValidationError struct {
    Field   string
    Message string
    Err     error
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation failed on %s: %s", e.Field, e.Message)
}

func (e *ValidationError) Unwrap() error {
    return e.Err
}
```

### Context Propagation

Always propagate context through the call chain:

```go
func ProcessResource(ctx context.Context, resource Resource) error {
    // Pass context to all calls
    result, err := fetchData(ctx, resource.ID)
    if err != nil {
        return err
    }

    // Use context for timeouts
    ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
    defer cancel()

    return deploy(ctx, result)
}
```

## Event-Driven Architecture Principles

### Pure Components Pattern

Business logic should be pure (no event dependencies):

```go
// pkg/templating/engine.go - Pure component
type TemplateEngine struct {
    // No EventBus dependency
}

func (e *TemplateEngine) Render(templateName string, context map[string]interface{}) (string, error) {
    // Pure business logic
    return e.render(templateName, context)
}
```

### Event Adapter Pattern

Only controller package contains event adapters:

```go
// pkg/controller/renderer/renderer.go - Event adapter
type RendererComponent struct {
    engine   *templating.TemplateEngine  // Pure component
    eventBus *events.EventBus
}

func (r *RendererComponent) Run(ctx context.Context) error {
    eventChan := r.eventBus.Subscribe(100)

    for {
        select {
        case event := <-eventChan:
            if req, ok := event.(ReconciliationTriggeredEvent); ok {
                // Call pure component
                output, err := r.engine.Render("haproxy.cfg", req.Context)

                // Publish result event
                if err != nil {
                    r.eventBus.Publish(RenderFailedEvent{Error: err.Error()})
                } else {
                    r.eventBus.Publish(RenderCompletedEvent{Output: output})
                }
            }
        case <-ctx.Done():
            return ctx.Err()
        }
    }
}
```

### When to Use Events vs Direct Calls

**Use EventBus (async pub/sub):**
- Component coordination across packages
- Observability and logging
- Extensibility (new features can subscribe to existing events)
- Fire-and-forget notifications

**Use Request() (scatter-gather):**
- Configuration validation (multiple validators must respond)
- Distributed queries
- Coordinated operations requiring multiple confirmations

**Use direct function calls:**
- Within the same package
- Pure components calling other pure components
- No need for decoupling or observability

## Import Path Conventions

### Internal Organization

```go
// Core packages (minimal dependencies)
import "haproxy-template-ic/pkg/core/config"
import "haproxy-template-ic/pkg/core/logging"

// Infrastructure (no domain knowledge)
import "haproxy-template-ic/pkg/events"

// Domain packages (depends on core + infrastructure)
import "haproxy-template-ic/pkg/templating"
import "haproxy-template-ic/pkg/k8s"
import "haproxy-template-ic/pkg/dataplane"

// Coordination (depends on everything)
import "haproxy-template-ic/pkg/controller"
import "haproxy-template-ic/pkg/controller/events"  // Event type catalog
```

### Dependency Rules

- `pkg/events` should have no dependencies on other pkg/ packages
- `pkg/templating`, `pkg/k8s`, `pkg/dataplane` should be pure libraries (no cross-dependencies)
- `pkg/controller` can import everything (coordination layer)
- `pkg/core` provides shared primitives (config types, logging setup)
- Domain-specific event types go in `pkg/controller/events`, not `pkg/events`

## Testing Strategy

### Unit Tests

Test pure components without event infrastructure:

```go
func TestTemplateEngine_Render(t *testing.T) {
    tests := []struct {
        name     string
        template string
        context  map[string]interface{}
        want     string
        wantErr  bool
    }{
        {
            name:     "simple variable",
            template: "Hello {{ name }}",
            context:  map[string]interface{}{"name": "World"},
            want:     "Hello World",
        },
        // More test cases...
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            engine, err := templating.New(templating.EngineTypeGonja,
                map[string]string{"test": tt.template})
            require.NoError(t, err)

            got, err := engine.Render("test", tt.context)
            if tt.wantErr {
                require.Error(t, err)
                return
            }

            require.NoError(t, err)
            assert.Equal(t, tt.want, got)
        })
    }
}
```

### Integration Tests

Located in `tests/` directory. Require kind cluster:

```bash
# Run integration tests
make test-integration

# Run specific integration test
KEEP_CLUSTER=true go test ./tests/... -run TestSyncFrontendAdd -v
```

Tests use real Kubernetes clusters (kind) and HAProxy pods. The `KEEP_CLUSTER=true` environment variable prevents cluster cleanup for debugging.

### Event-Driven Component Tests

Test event adapters with mock EventBus:

```go
func TestRendererComponent(t *testing.T) {
    bus := events.NewEventBus(100)
    engine, _ := templating.New(templating.EngineTypeGonja, templates)
    renderer := NewRendererComponent(bus, engine)

    // Subscribe to output events
    eventChan := bus.Subscribe(10)
    bus.Start()

    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    // Start component
    go renderer.Run(ctx)

    // Trigger reconciliation
    bus.Publish(ReconciliationTriggeredEvent{Context: testContext})

    // Verify output event
    select {
    case event := <-eventChan:
        if completed, ok := event.(RenderCompletedEvent); ok {
            assert.Contains(t, completed.Output, "expected content")
        } else {
            t.Fatalf("expected RenderCompletedEvent, got %T", event)
        }
    case <-time.After(1 * time.Second):
        t.Fatal("timeout waiting for event")
    }
}
```

## Build Commands

```bash
# Build binary
make build

# Run all tests
make test

# Run linting (golangci-lint)
make lint

# Run all checks (tests + linting)
make check-all

# Integration tests (requires kind)
make test-integration

# Coverage report
make test-coverage

# Build Docker image
make docker-build
```

## Development Environment

### Local Kind Cluster

**IMPORTANT**: Always use the `kind-haproxy-template-ic-dev` context for development work.

```bash
# Verify you're using the correct cluster
kubectl config current-context
# Should output: kind-haproxy-template-ic-dev

# If not, switch to it
kubectl config use-context kind-haproxy-template-ic-dev

# Start the dev environment (creates cluster if needed)
./scripts/start-dev-env.sh

# Build and deploy changes to dev cluster
# IMPORTANT: Always use this script - do not run manual build commands
./scripts/start-dev-env.sh restart

# View controller logs
./scripts/start-dev-env.sh logs

# Check deployment status
./scripts/start-dev-env.sh status

# Test ingress functionality
./scripts/start-dev-env.sh test

# Check HAProxy configuration
kubectl -n echo get pods -l app=haproxy
kubectl -n echo exec <haproxy-pod> -- cat /etc/haproxy/haproxy.cfg

# Clean up dev environment
./scripts/start-dev-env.sh down
```

**Cluster Names:**
- **Dev cluster**: `kind-haproxy-template-ic-dev` - Use this for development
- **Test cluster**: `kind-haproxy-test` - Used by integration tests only

## Common Patterns

### Graceful Shutdown

```go
func main() {
    ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
    defer stop()

    // Create components
    components := []Component{
        watcher,
        reconciler,
        executor,
    }

    // Start components with errgroup
    g, gCtx := errgroup.WithContext(ctx)
    for _, comp := range components {
        comp := comp  // Capture loop variable
        g.Go(func() error {
            return comp.Run(gCtx)
        })
    }

    // Wait for shutdown signal or error
    <-ctx.Done()
    log.Info("Shutdown signal received, stopping components...")

    // Wait for components to finish (with timeout)
    done := make(chan error)
    go func() {
        done <- g.Wait()
    }()

    select {
    case err := <-done:
        if err != nil {
            log.Error("Component error during shutdown", "error", err)
        }
    case <-time.After(30 * time.Second):
        log.Error("Shutdown timeout exceeded")
    }
}
```

### Structured Logging

```go
import "log/slog"

// Create logger with structured fields
logger := slog.Default().With(
    "component", "reconciler",
    "namespace", resource.Namespace,
)

// Log with structured attributes
logger.Info("reconciliation started",
    "resource", resource.Name,
    "trigger", "config_change",
)

logger.Error("reconciliation failed",
    "error", err,
    "duration_ms", time.Since(start).Milliseconds(),
)
```

## Common Pitfalls

### Event Bus

- **Don't block in event handlers** - Process events quickly or spawn goroutines
- **Buffer sizing matters** - Small buffers (10-50) for control events, large buffers (200+) for high-volume events
- **Always call EventBus.Start()** after all components subscribe (prevents lost events during startup)

### Context

- **Always respect context cancellation** - Check `ctx.Done()` in loops
- **Don't ignore context timeout errors** - They indicate system overload
- **Pass context through the call chain** - Don't create new contexts except for timeouts

### Testing

- **Don't use real Kubernetes API in unit tests** - Use fake clients from `k8s.io/client-go/kubernetes/fake`
- **Integration tests are slow** - Keep them focused and minimal
- **Mock EventBus carefully** - Subscribe before publishing to avoid race conditions

### Kubernetes

- **Wait for initial sync** - Don't process resources before all informers sync
- **Handle resource versions** - They're not monotonic across resource types
- **Field selectors are limited** - Not all fields support field selectors (use label selectors instead)

## Resources

- Architecture: `docs/development/design.md`
- Package READMEs: `pkg/*/README.md`
- Linting guidelines: `docs/development/linting.md`
- Configuration reference: `docs/supported-configuration.md`

## Package-Specific Context

For detailed development context on specific packages, see:
- `pkg/CLAUDE.md` - Package organization principles
- `pkg/events/CLAUDE.md` - Event bus infrastructure
- `pkg/controller/CLAUDE.md` - Controller orchestration
- `pkg/k8s/CLAUDE.md` - Kubernetes integration
- `pkg/dataplane/CLAUDE.md` - HAProxy integration
- `pkg/templating/CLAUDE.md` - Template engine
- `pkg/core/CLAUDE.md` - Core functionality
- `cmd/controller/CLAUDE.md` - Entry point and startup
