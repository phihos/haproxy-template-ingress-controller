# HAProxy Dataplane Sync Library

A powerful, easy-to-use Go library for synchronizing HAProxy configurations via the Dataplane API. The library handles all complexity internally and provides a simple interface: give it an endpoint and a desired configuration, and it ensures HAProxy matches that configuration.

## Features

- **Simple API**: Just provide an endpoint and desired config string
- **Connection Reuse**: Client-based API for efficient connection management
- **Intelligent Sync**: Uses fine-grained operations (create/update/delete servers, backends, ACLs, etc.)
- **Automatic Fallback**: Falls back to raw config push if fine-grained sync fails
- **Conflict Resolution**: Automatically retries on version conflicts (409 errors)
- **Detailed Results**: Returns structured information about applied changes
- **Reload Optimization**: Uses runtime API when possible to avoid HAProxy reloads
- **Actionable Errors**: Detailed error messages with hints for troubleshooting

## Installation

```bash
go get haproxy-template-ic/pkg/dataplane
```

## Quick Start

### Simple (One-Off Operations)

For quick scripts or one-off operations, use the convenience functions:

```go
package main

import (
    "context"
    "log"

    "haproxy-template-ic/pkg/dataplane"
)

func main() {
    endpoint := dataplane.Endpoint{
        URL:      "http://haproxy:5555/v2",
        Username: "admin",
        Password: "secret",
    }

    desiredConfig := `
global
    daemon
    maxconn 4096

defaults
    mode http
    timeout client 30s
    timeout server 30s
    timeout connect 5s

backend web
    balance roundrobin
    server web1 192.168.1.10:80 check
    server web2 192.168.1.11:80 check
`

    // Convenience function - creates client internally
    result, err := dataplane.Sync(context.Background(), endpoint, desiredConfig, nil, nil)
    if err != nil {
        log.Fatalf("sync failed: %v", err)
    }

    log.Printf("Applied %d operations in %v\n", len(result.AppliedOperations), result.Duration)
}
```

### Production (Reusable Client)

For production use with multiple operations, create a client explicitly:

```go
func main() {
    endpoint := dataplane.Endpoint{
        URL:      "http://haproxy:5555/v2",
        Username: "admin",
        Password: "secret",
    }

    // Create client once, reuse for multiple operations
    client, err := dataplane.NewClient(context.Background(), endpoint)
    if err != nil {
        log.Fatalf("failed to create client: %v", err)
    }
    defer client.Close()

    // Reuse client for multiple sync operations (efficient!)
    result1, err := client.Sync(ctx, config1, nil, nil)
    result2, err := client.Sync(ctx, config2, nil, nil)
    diff, err := client.DryRun(ctx, config3)
}
```

## Usage Examples

### Client Management

**Production Pattern (Recommended):**
```go
// Create client once
client, err := dataplane.NewClient(ctx, endpoint)
if err != nil {
    return err
}
defer client.Close()

// Reuse for multiple operations
result, err := client.Sync(ctx, desiredConfig, nil, nil)
```

**Simple Pattern (Quick Scripts):**
```go
// For one-off operations - creates client internally
result, err := dataplane.Sync(ctx, endpoint, desiredConfig, nil, nil)
```

### Custom Options

Configure sync behavior with options:

```go
client, err := dataplane.NewClient(ctx, endpoint)
if err != nil {
    return err
}
defer client.Close()

opts := &dataplane.SyncOptions{
    MaxRetries:      5,                 // Retry 409 conflicts up to 5 times
    Timeout:         3 * time.Minute,   // Overall timeout
    ContinueOnError: false,             // Stop on first error
    FallbackToRaw:   true,              // Fall back to raw push on errors
}

result, err := client.Sync(ctx, desiredConfig, nil, opts)
```

**Options explained:**
- `MaxRetries`: How many times to retry on 409 version conflicts (default: 3)
- `Timeout`: Overall timeout for the sync operation (default: 2 minutes)
- `ContinueOnError`: Continue applying operations even if some fail (default: false)
- `FallbackToRaw`: Automatically fall back to raw config push on non-recoverable errors (default: true)

### Dry Run (Preview Changes)

Preview what changes would be applied without actually applying them:

```go
client, err := dataplane.NewClient(ctx, endpoint)
if err != nil {
    return err
}
defer client.Close()

diff, err := client.DryRun(ctx, desiredConfig)
if err != nil {
    log.Fatal(err)
}

if !diff.HasChanges {
    fmt.Println("No changes needed")
    return
}

fmt.Printf("Would apply %d operations:\n", len(diff.PlannedOperations))
for _, op := range diff.PlannedOperations {
    fmt.Printf("  - %s %s '%s'\n", op.Type, op.Section, op.Resource)
}
```

### Detailed Diff

Get detailed information about configuration differences:

```go
client, err := dataplane.NewClient(ctx, endpoint)
if err != nil {
    return err
}
defer client.Close()

diff, err := client.Diff(ctx, desiredConfig)
if err != nil {
    log.Fatal(err)
}

fmt.Printf("Backends added: %v\n", diff.Details.BackendsAdded)
fmt.Printf("Backends modified: %v\n", diff.Details.BackendsModified)
fmt.Printf("Servers deleted: %v\n", diff.Details.ServersDeleted)
```

### Inspecting Results

The sync result contains detailed information:

```go
client, err := dataplane.NewClient(ctx, endpoint)
if err != nil {
    return err
}
defer client.Close()

result, err := client.Sync(ctx, desiredConfig, nil, nil)
if err != nil {
    log.Fatal(err)
}

// Check applied operations
for _, op := range result.AppliedOperations {
    fmt.Printf("%s %s '%s': %s\n", op.Type, op.Section, op.Resource, op.Description)
}

// Check reload status
if result.ReloadTriggered {
    fmt.Printf("HAProxy reloaded with ID: %s\n", result.ReloadID)
}

// Check if fallback was used
if result.FallbackToRaw {
    fmt.Println("Warning: Had to use raw config push (fallback)")
}
```

### Error Handling

The library provides detailed, actionable error messages:

```go
client, err := dataplane.NewClient(ctx, endpoint)
if err != nil {
    return err
}
defer client.Close()

result, err := client.Sync(ctx, desiredConfig, nil, nil)
if err != nil {
    // Check for specific error types
    var syncErr *dataplane.SyncError
    if errors.As(err, &syncErr) {
        fmt.Printf("Failed at stage: %s\n", syncErr.Stage)
        fmt.Printf("Error: %s\n", syncErr.Message)
        fmt.Println("\nTroubleshooting hints:")
        for _, hint := range syncErr.Hints {
            fmt.Printf("  • %s\n", hint)
        }
    }

    return
}
```

### Context and Timeout

Use context for cancellation and timeouts:

```go
// Timeout via context
ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()

client, err := dataplane.NewClient(ctx, endpoint)
if err != nil {
    return err
}
defer client.Close()

result, err := client.Sync(ctx, desiredConfig, nil, nil)

// Or timeout via options (overrides context timeout)
opts := &dataplane.SyncOptions{
    Timeout: 1 * time.Minute,
}
result, err := client.Sync(ctx, desiredConfig, nil, opts)
```

## How It Works

The library performs the following steps:

1. **Fetch Current Config**: Retrieves the current HAProxy configuration from the Dataplane API
2. **Parse Configurations**: Parses both current and desired configs into structured objects
3. **Compare**: Generates fine-grained operations (create server, delete ACL, update backend, etc.)
4. **Execute**: Applies operations with automatic retry on version conflicts (409 errors)
5. **Fallback**: If fine-grained sync fails, automatically falls back to raw config push
6. **Results**: Returns detailed information about what was changed

### Fine-Grained vs Raw Sync

**Fine-Grained Sync** (default):
- Individual operations for each change
- Minimal HAProxy reloads
- Uses runtime API when possible (server weight/status changes)
- Detailed operation tracking

**Raw Config Push** (fallback):
- Pushes complete configuration
- Always triggers reload
- Used when fine-grained sync fails
- Simple but less efficient

## API Reference

### Main Functions

#### `Sync(ctx, endpoint, desiredConfig, opts) (*SyncResult, error)`

Synchronizes the desired configuration to HAProxy.

**Parameters:**
- `ctx`: Context for cancellation and timeout
- `endpoint`: Dataplane API connection info
- `desiredConfig`: Desired HAProxy configuration as string
- `opts`: Sync options (use `nil` for defaults)

**Returns:**
- `*SyncResult`: Detailed sync results
- `error`: Error with actionable hints if sync fails

#### `DryRun(ctx, endpoint, desiredConfig) (*DiffResult, error)`

Previews changes without applying them.

**Parameters:**
- `ctx`: Context for cancellation and timeout
- `endpoint`: Dataplane API connection info
- `desiredConfig`: Desired HAProxy configuration as string

**Returns:**
- `*DiffResult`: Planned operations and diff details
- `error`: Error if comparison fails

#### `Diff(ctx, endpoint, desiredConfig) (*DiffResult, error)`

Alias for `DryRun()` - compares configurations and returns differences.

### Types

#### `Endpoint`

```go
type Endpoint struct {
    URL      string  // Dataplane API URL (e.g., "http://haproxy:5555/v2")
    Username string  // Basic auth username
    Password string  // Basic auth password
}
```

#### `SyncOptions`

```go
type SyncOptions struct {
    MaxRetries      int           // Retry limit for 409 conflicts (default: 3)
    Timeout         time.Duration // Overall timeout (default: 2 minutes)
    ContinueOnError bool          // Continue on operation failure (default: false)
    FallbackToRaw   bool          // Auto-fallback to raw push (default: true)
}
```

#### `SyncResult`

```go
type SyncResult struct {
    Success           bool              // Whether sync succeeded
    AppliedOperations []AppliedOperation // Structured operations applied
    ReloadTriggered   bool              // Whether reload was triggered
    ReloadID          string            // Reload ID (if triggered)
    FallbackToRaw     bool              // Whether fallback was used
    Duration          time.Duration     // Operation duration
    Retries           int               // Number of retries
    Details           DiffDetails       // Detailed diff information
    Message           string            // Summary message
}
```

#### `DiffResult`

```go
type DiffResult struct {
    HasChanges        bool                // Whether any differences exist
    PlannedOperations []PlannedOperation  // Operations that would be executed
    Details           DiffDetails         // Detailed diff information
}
```

## Best Practices

### 1. Use Client for Multiple Operations

**Production code should reuse clients:**
```go
// Good - create once, reuse
client, err := dataplane.NewClient(ctx, endpoint)
if err != nil {
    return err
}
defer client.Close()

// Efficient - reuses connection
diff, err := client.DryRun(ctx, newConfig)
if diff.HasChanges {
    result, err := client.Sync(ctx, newConfig, nil, nil)
}
```

**Avoid recreating clients:**
```go
// Bad - creates new connection each time
for _, config := range configs {
    result, err := dataplane.Sync(ctx, endpoint, config, nil, nil)  // inefficient!
}

// Good - reuses connection
client, err := dataplane.NewClient(ctx, endpoint)
defer client.Close()

for _, config := range configs {
    result, err := client.Sync(ctx, config, nil, nil)  // efficient!
}
```

### 2. Use Dry Run Before Applying

Always preview changes in production:

```go
client, err := dataplane.NewClient(ctx, endpoint)
if err != nil {
    return err
}
defer client.Close()

// Preview
diff, err := client.DryRun(ctx, newConfig)
if err != nil {
    return err
}

if diff.HasChanges {
    fmt.Printf("About to apply %d changes\n", len(diff.PlannedOperations))
    // Show to human operator for confirmation

    // Apply
    result, err := client.Sync(ctx, newConfig, nil, nil)
}
```

### 3. Handle Errors Properly

Check for specific error types and provide context:

```go
client, err := dataplane.NewClient(ctx, endpoint)
if err != nil {
    return err
}
defer client.Close()

result, err := client.Sync(ctx, config, nil, nil)
if err != nil {
    var syncErr *dataplane.SyncError
    if errors.As(err, &syncErr) {
        log.Printf("Sync failed at %s stage: %s", syncErr.Stage, syncErr.Message)
        // Log hints for debugging
        for _, hint := range syncErr.Hints {
            log.Printf("Hint: %s", hint)
        }
    }
    return fmt.Errorf("failed to sync HAProxy: %w", err)
}
```

### 4. Configure Appropriate Timeouts

Set timeouts based on your environment:

```go
opts := &dataplane.SyncOptions{
    Timeout:    5 * time.Minute,  // Longer for large configs
    MaxRetries: 5,                // More retries in busy environments
}

client, err := dataplane.NewClient(ctx, endpoint)
defer client.Close()

result, err := client.Sync(ctx, config, nil, opts)
```

### 5. Monitor Fallback Usage

Alert on fallback to raw config:

```go
client, err := dataplane.NewClient(ctx, endpoint)
defer client.Close()

result, err := client.Sync(ctx, config, nil, nil)
if err == nil && result.FallbackToRaw {
    log.Warn("Had to use raw config push - investigate fine-grained sync failure")
    // Send alert to monitoring system
}
```

## Troubleshooting

### Connection Errors

**Problem**: Can't connect to Dataplane API

**Solutions**:
- Verify endpoint URL is correct
- Check HAProxy is running and accessible
- Verify credentials
- Check network connectivity
- Ensure Dataplane API is enabled in HAProxy config

### Parse Errors

**Problem**: Configuration parsing fails

**Solutions**:
- Validate config syntax: `haproxy -c -f config.cfg`
- Check for syntax errors in desired config
- Verify config is compatible with HAProxy version

### Version Conflicts

**Problem**: Getting 409 errors even with retries

**Solutions**:
- Increase `MaxRetries` in options
- Coordinate config updates to avoid concurrent modifications
- Check for other automation tools modifying HAProxy

### Validation Errors

**Problem**: HAProxy rejects the configuration

**Solutions**:
- Check for references to non-existent backends/servers
- Verify all directives are compatible with HAProxy version
- Ensure resource dependencies are satisfied
- Review validation error messages from HAProxy

## License

This library is part of the haproxy-template-ic project.
