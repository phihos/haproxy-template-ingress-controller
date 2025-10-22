# pkg/controller/indextracker

Index synchronization tracker.

## Overview

Tracks when all resource types have completed initial synchronization.

## Quick Start

```go
tracker := indextracker.NewIndexTracker(bus, logger, resourceTypes)
go tracker.Start(ctx)
```

## Events

- Subscribes: ResourceSyncCompleteEvent
- Publishes: IndexSynchronizedEvent

## License

See main repository for license information.
