# Model Transformation Library

## Overview

This package provides transformation functions to convert client-native parser models to Dataplane API models. The client-native library (`haproxytech/client-native`) provides HAProxy configuration parsing but uses internal model types that don't always match the Dataplane API's OpenAPI schema. This package bridges that gap using JSON-based marshaling for type conversion.

**Why this package exists:**
- Client-native parser returns `models.ACL`, but Dataplane API expects `dataplaneapi.Acl`
- Field names and types may differ slightly between the two schemas
- JSON marshaling/unmarshaling handles these structural differences automatically
- Eliminates ~77 duplicate inline conversions scattered across the comparator package

**When to use this package:**
- When you have a parsed configuration element from client-native and need to send it to the Dataplane API
- When comparing configurations in the comparator/sections package
- When creating API requests for HAProxy configuration updates

## Features

- **Generic Transformation**: Single `transform[T]` function handles all conversions
- **35+ Conversion Functions**: Pre-defined converters for all HAProxy configuration sections
- **Nil Safety**: All functions handle nil input gracefully
- **Zero Dependencies**: Only requires client-native and generated API models
- **Type Safety**: Compile-time verification of target types

## Usage Examples

### Basic Transformation

```go
package main

import (
    "github.com/haproxytech/client-native/v6/models"
    "haproxy-template-ic/pkg/dataplane/transform"
)

func main() {
    // Client-native model from parser
    clientACL := &models.ACL{
        ACLName: "is_api",
        Criterion: "path_beg",
        Value: "/api",
    }

    // Transform to Dataplane API model
    apiACL := transform.ToAPIACL(clientACL)

    // Now apiACL is *dataplaneapi.Acl, ready for API calls
    // Use in Dataplane API request...
}
```

### Transforming Multiple Elements

```go
// Transform all binds in a frontend
for _, bind := range parsedFrontend.Binds {
    apiBind := transform.ToAPIBind(bind)
    // Send to Dataplane API
}

// Transform backend servers
for _, server := range parsedBackend.Servers {
    apiServer := transform.ToAPIServer(server)
    // Compare with current configuration
}
```

### Nil Handling

```go
// All transformation functions handle nil input
var nilACL *models.ACL = nil
result := transform.ToAPIACL(nilACL)
// result is nil, not a panic
```

### In Comparator Context

```go
// pkg/dataplane/comparator/sections/acl.go
import "haproxy-template-ic/pkg/dataplane/transform"

func (c *ACLComparator) compareACLs(current, desired *models.ACL) Operation {
    // Transform to API models for comparison
    currentAPI := transform.ToAPIACL(current)
    desiredAPI := transform.ToAPIACL(desired)

    // Compare API models to detect differences
    if !reflect.DeepEqual(currentAPI, desiredAPI) {
        return Operation{
            Type: OperationUpdate,
            Resource: desiredAPI,
        }
    }

    return Operation{Type: OperationNone}
}
```

## API Reference

### Core Function

```go
// transform performs generic JSON-based transformation.
// Returns nil if input is nil or transformation fails.
func transform[T any](input interface{}) *T
```

This is the internal generic function. You typically don't call it directly; instead use the type-specific convenience functions below.

### Configuration Section Transformations

All functions follow the pattern `ToAPI<Type>(model) *dataplaneapi.<Type>`:

**ACLs and Rules:**
- `ToAPIACL(*models.ACL) *dataplaneapi.Acl`
- `ToAPIBackendSwitchingRule(*models.BackendSwitchingRule) *dataplaneapi.BackendSwitchingRule`
- `ToAPIServerSwitchingRule(*models.ServerSwitchingRule) *dataplaneapi.ServerSwitchingRule`

**Frontends and Backends:**
- `ToAPIFrontend(*models.Frontend) *dataplaneapi.Frontend`
- `ToAPIBackend(*models.Backend) *dataplaneapi.Backend`
- `ToAPIDefaults(*models.Defaults) *dataplaneapi.Defaults`
- `ToAPIGlobal(*models.Global) *dataplaneapi.Global`

**Binds and Servers:**
- `ToAPIBind(*models.Bind) *dataplaneapi.Bind`
- `ToAPIServer(*models.Server) *dataplaneapi.Server`
- `ToAPIServerTemplate(*models.ServerTemplate) *dataplaneapi.ServerTemplate`

**HTTP Rules:**
- `ToAPIHTTPRequestRule(*models.HTTPRequestRule) *dataplaneapi.HttpRequestRule`
- `ToAPIHTTPResponseRule(*models.HTTPResponseRule) *dataplaneapi.HttpResponseRule`
- `ToAPIHTTPAfterResponseRule(*models.HTTPAfterResponseRule) *dataplaneapi.HttpAfterResponseRule`
- `ToAPIHTTPErrorRule(*models.HTTPErrorRule) *dataplaneapi.HttpErrorRule`

**TCP Rules:**
- `ToAPITCPRequestRule(*models.TCPRequestRule) *dataplaneapi.TcpRequestRule`
- `ToAPITCPResponseRule(*models.TCPResponseRule) *dataplaneapi.TcpResponseRule`

**Health Checks:**
- `ToAPIHTTPCheck(*models.HTTPCheck) *dataplaneapi.HttpCheck`
- `ToAPITCPCheck(*models.TCPCheck) *dataplaneapi.TcpCheck`

**Advanced Features:**
- `ToAPICache(*models.Cache) *dataplaneapi.Cache`
- `ToAPICapture(*models.Capture) *dataplaneapi.Capture`
- `ToAPIFilter(*models.Filter) *dataplaneapi.Filter`
- `ToAPIStickRule(*models.StickRule) *dataplaneapi.StickRule`
- `ToAPILogTarget(*models.LogTarget) *dataplaneapi.LogTarget`

**Special Sections:**
- `ToAPIFCGIApp(*models.FCGIApp) *dataplaneapi.FcgiApp`
- `ToAPICrtStore(*models.CrtStore) *dataplaneapi.CrtStore`
- `ToAPIHTTPErrorsSection(*models.HTTPErrorsSection) *dataplaneapi.HttpErrorsSection`
- `ToAPILogForward(*models.LogForward) *dataplaneapi.LogForward`

**Mailers, Peers, and Resolvers:**
- `ToAPIMailersSection(*models.MailersSection) *dataplaneapi.MailersSection`
- `ToAPIMailerEntry(*models.MailerEntry) *dataplaneapi.MailerEntry`
- `ToAPIPeerSection(*models.PeerSection) *dataplaneapi.PeerSection`
- `ToAPIPeerEntry(*models.PeerEntry) *dataplaneapi.PeerEntry`
- `ToAPIResolver(*models.Resolver) *dataplaneapi.Resolver`
- `ToAPINameserver(*models.Nameserver) *dataplaneapi.Nameserver`

**Programs and Rings:**
- `ToAPIProgram(*models.Program) *dataplaneapi.Program`
- `ToAPIRing(*models.Ring) *dataplaneapi.Ring`

**Userlists:**
- `ToAPIUserlist(*models.Userlist) *dataplaneapi.Userlist`
- `ToAPIUser(*models.User) *dataplaneapi.User`

## Design Rationale

### Why JSON-Based Conversion?

The package uses JSON marshaling/unmarshaling instead of manual field mapping:

**Advantages:**
- Automatic handling of field name differences (e.g., `ACLName` → `Name`)
- No maintenance burden when HAProxy adds new fields
- Handles nested structures automatically
- Type conversion happens naturally through JSON

**Trade-offs:**
- Small performance overhead (typically <10µs per conversion)
- Silent failures if JSON structure diverges significantly
- Less explicit than manual mapping

For this use case, the maintenance benefits outweigh the minor performance cost. Configuration transformations happen infrequently (only during reconciliation), so microsecond-level overhead is acceptable.

### Nil Handling Strategy

All transformation functions return `nil` for `nil` input rather than panicking. This simplifies caller code:

```go
// No nil check needed
apiACL := transform.ToAPIACL(parsedACL)
if apiACL != nil {
    // Use apiACL
}

// vs manual approach requiring:
if parsedACL != nil {
    apiACL := manualConvert(parsedACL)
    // Use apiACL
}
```

## Integration with Other Packages

### Comparator Package

The comparator uses transform functions extensively to prepare models for comparison:

```
pkg/dataplane/comparator/sections/*.go
    ↓ uses
pkg/dataplane/transform
    ↓ converts
client-native models → Dataplane API models
```

See `pkg/dataplane/comparator/sections/` for usage examples in each section comparator.

### Client Package

The client package uses Dataplane API models directly, so transformation happens before client calls:

```go
// In synchronizer or executor
apiBackend := transform.ToAPIBackend(parsedBackend)
err := client.CreateBackend(tx, apiBackend)
```

## Performance Characteristics

Transformation performance (typical values):

- **Simple types** (ACL, Bind): ~5-10µs
- **Medium types** (Frontend, Backend): ~10-20µs
- **Complex types** (Global with many fields): ~20-40µs

These are one-time costs during reconciliation. Template rendering doesn't involve transformations, so rendering performance is unaffected.

## When NOT to Use This Package

Don't use transform functions when:

- **Already have API models**: If you're constructing models from scratch for the API, use `dataplaneapi.*` types directly
- **Need custom field mapping**: If the automatic conversion doesn't handle your case, write custom conversion logic
- **Performance critical path**: For hot paths (inside tight loops), consider caching transformed results

## Extending the Package

### Adding a New Transformation

When HAProxy adds a new configuration section:

1. Verify client-native support exists (`models.NewType`)
2. Verify Dataplane API model exists (`dataplaneapi.NewType`)
3. Add transformation function:

```go
// ToAPINewType converts a client-native models.NewType to dataplaneapi.NewType.
func ToAPINewType(model *models.NewType) *dataplaneapi.NewType {
    return transform[dataplaneapi.NewType](model)
}
```

4. Add test case in `transform_test.go`
5. Use in appropriate section comparator

## Testing

The package includes unit tests for nil handling and basic transformation:

```bash
go test ./pkg/dataplane/transform -v
```

For integration testing, see `pkg/dataplane/comparator/sections/*_test.go` which test transformations in context.

## See Also

- [Dataplane Package](../README.md) - HAProxy integration overview
- [Comparator Package](../comparator/README.md) - Configuration comparison using transforms
- [Client-Native Documentation](https://github.com/haproxytech/client-native) - Source model reference
- [Dataplane API Documentation](https://www.haproxy.com/documentation/haproxy-data-plane-api/) - Target API reference
