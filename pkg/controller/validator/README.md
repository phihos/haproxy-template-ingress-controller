# pkg/controller/validator

Configuration validation components using scatter-gather pattern.

## Overview

Validates controller configuration using multiple independent validators coordinated via scatter-gather EventBus pattern.

## Validators

- **BasicValidator**: Structural validation
- **TemplateValidator**: Template syntax
- **JSONPathValidator**: JSONPath expressions

## Quick Start

```go
// Start all validators
basicValidator := validator.NewBasicValidator(bus, logger)
templateValidator := validator.NewTemplateValidator(bus, logger, engine)
jsonpathValidator := validator.NewJSONPathValidator(bus, logger)

go basicValidator.Start(ctx)
go templateValidator.Start(ctx)
go jsonpathValidator.Start(ctx)
```

## Events

### Subscribes To

- **ConfigValidationRequest**: Scatter-gather validation request

### Publishes

- **ConfigValidationResponse**: Individual validator response
- **ConfigValidatedEvent**: All validators passed (from coordinator)
- **ConfigInvalidEvent**: Any validator failed (from coordinator)

## License

See main repository for license information.
