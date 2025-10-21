# pkg/controller/executor

Executor component - orchestrates reconciliation cycles.

## Overview

Stage 5 component that coordinates Renderer, Validator, and Deployer components to complete reconciliation cycles.

**Current State**: Minimal stub implementation establishing event flow.

## Quick Start

```go
import "haproxy-template-ic/pkg/controller/executor"

executor := executor.New(bus, logger)
go executor.Start(ctx)
```

## Events

### Subscribes To

- **ReconciliationTriggeredEvent**: Starts reconciliation

### Publishes

- **ReconciliationStartedEvent**: Cycle begins
- **ReconciliationCompletedEvent**: Cycle completes
- (TODO) **TemplateRenderedEvent**: Rendering done
- (TODO) **ValidationCompletedEvent**: Validation done
- (TODO) **DeploymentCompletedEvent**: Deployment done

## License

See main repository for license information.
