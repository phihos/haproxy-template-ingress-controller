# pkg/controller/configchange

ConfigMap change handler.

## Overview

Watches specific ConfigMap and publishes change events.

## Quick Start

```go
handler := configchange.NewConfigChangeHandler(bus, k8sClient, configMapName, namespace, logger)
go handler.Start(ctx)
```

## Events

- Publishes: ConfigResourceChangedEvent

## License

See main repository for license information.
