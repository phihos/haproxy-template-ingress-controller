# Basic Sync Example

This example demonstrates how to use the dataplane Client API to synchronize HAProxy configurations.

## What It Demonstrates

- Creating a dataplane Client with connection reuse
- Syncing a simple HAProxy configuration
- Configuring sync options (retries, timeouts, fallback behavior)
- Proper error handling with detailed sync errors
- Inspecting sync results (operations applied, reload status, etc.)
- Using DryRun to preview changes without applying them

## Prerequisites

Before running this example, you need:

1. **HAProxy with Dataplane API enabled**

   The Dataplane API must be configured in HAProxy. Add to your `haproxy.cfg`:

   ```
   program api
       command dataplaneapi -f /etc/haproxy/dataplaneapi.yml
   ```

2. **Dataplane API Configuration**

   Create `/etc/haproxy/dataplaneapi.yml`:

   ```yaml
   dataplaneapi:
     host: 0.0.0.0
     port: 5555
     user:
       - insecure: true
         password: admin
         name: admin
   ```

3. **Network Access**

   Ensure the Dataplane API is accessible from where you run this example.

## Configuration

Configure the connection using environment variables:

```bash
export HAPROXY_URL="http://localhost:5555/v2"
export HAPROXY_USER="admin"
export HAPROXY_PASS="admin"
```

Or modify the defaults in `main.go`.

## Running the Example

```bash
# Build
go build -o basic-sync main.go

# Run
./basic-sync
```

Or run directly:

```bash
go run main.go
```

## Expected Output

```
Creating dataplane client...
Connected to HAProxy at http://localhost:5555/v2

Syncing HAProxy configuration...

Sync completed successfully!
Duration: 1.234s
Operations applied: 5
HAProxy reloaded: reload-123

Applied operations:
  1. [create] backend 'web-servers': Created backend
  2. [create] server 'web-servers/web1': Created server
  3. [create] server 'web-servers/web2': Created server
  4. [create] frontend 'http-in': Created frontend
  5. [update] global: Updated global settings

--- Dry Run Example ---
Would apply 1 operations:
  1. [create] server 'web-servers/web3': Would create server

Example completed successfully!
```

## Key Patterns Demonstrated

### 1. Client Creation and Reuse

```go
// Create client once
client, err := dataplane.NewClient(ctx, endpoint)
if err != nil {
    return err
}
defer client.Close()

// Reuse for multiple operations
result1, err := client.Sync(ctx, config1, nil, nil)
result2, err := client.Sync(ctx, config2, nil, nil)
```

### 2. Error Handling

```go
result, err := client.Sync(ctx, desiredConfig, nil, opts)
if err != nil {
    var syncErr *dataplane.SyncError
    if errors.As(err, &syncErr) {
        log.Printf("Failed at stage '%s': %s\n", syncErr.Stage, syncErr.Message)
        for _, hint := range syncErr.Hints {
            log.Printf("  Hint: %s\n", hint)
        }
    }
    return err
}
```

### 3. Inspecting Results

```go
fmt.Printf("Applied %d operations in %v\n",
    len(result.AppliedOperations), result.Duration)

if result.ReloadTriggered {
    fmt.Printf("HAProxy reloaded: %s\n", result.ReloadID)
}

for _, op := range result.AppliedOperations {
    fmt.Printf("%s %s: %s\n", op.Type, op.Resource, op.Description)
}
```

### 4. Dry Run

```go
// Preview changes without applying
diff, err := client.DryRun(ctx, modifiedConfig)
if diff.HasChanges {
    fmt.Printf("Would apply %d operations\n", len(diff.PlannedOperations))
}
```

## Next Steps

- See `pkg/dataplane/README.md` for complete API documentation
- Check integration tests in `tests/integration/` for more advanced examples
- Explore auxiliary file sync (SSL certificates, map files, custom error pages)
