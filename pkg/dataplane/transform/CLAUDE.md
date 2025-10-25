# pkg/dataplane/transform - Model Transformation

Development context for the HAProxy model transformation package.

**API Documentation**: See `pkg/dataplane/transform/README.md`

## When to Work Here

Modify this package when:
- Adding support for new HAProxy configuration sections
- Client-native or Dataplane API models change structure
- Fixing transformation bugs
- Optimizing transformation performance

**DO NOT** modify this package for:
- Configuration comparison logic → Use `pkg/dataplane/comparator`
- API client operations → Use `pkg/dataplane/client`
- Configuration parsing → Use `pkg/dataplane/parser`

## Package Purpose

This package eliminates duplicate type conversion code. Before this package existed, every section comparator contained inline conversions like:

```go
// BEFORE: Duplicated 77 times across comparator/sections/*.go
data, _ := json.Marshal(clientModel)
var apiModel dataplaneapi.ACL
json.Unmarshal(data, &apiModel)
```

Now we have centralized, tested conversion functions:

```go
// AFTER: One line per conversion
apiModel := transform.ToAPIACL(clientModel)
```

## Architecture

### Design Pattern

**Single Generic Function + Type-Specific Wrappers:**

```go
// Generic transformation engine (private)
func transform[T any](input interface{}) *T {
    if input == nil {
        return nil
    }

    data, err := json.Marshal(input)
    if err != nil {
        return nil  // Should rarely happen with valid models
    }

    var result T
    if err := json.Unmarshal(data, &result); err != nil {
        return nil  // Should rarely happen with compatible JSON
    }

    return &result
}

// Type-specific public API (35+ functions)
func ToAPIACL(model *models.ACL) *dataplaneapi.Acl {
    return transform[dataplaneapi.Acl](model)
}
```

**Why this pattern:**
- Type safety: Compile-time verification of target types
- Discoverability: IDE autocomplete shows all available transformations
- Consistency: All transformations behave identically
- Maintainability: Single generic implementation

### JSON-Based Conversion Rationale

**Why JSON instead of manual field mapping?**

1. **Maintenance burden**: HAProxy has 30+ configuration sections with 10-50 fields each. Manual mapping = 1000+ lines of boilerplate.
2. **Field name differences**: JSON marshaling handles name transformations automatically (e.g., `ACLName` → `Name`).
3. **Nested structures**: JSON handles complex nested objects without custom recursion.
4. **Future-proof**: New HAProxy fields work automatically without code changes.

**Trade-offs:**
- Performance: ~10µs overhead per transformation (acceptable for infrequent reconciliation)
- Silent failures: Structural incompatibilities return nil instead of explicit errors
- Debugging: Harder to trace which field caused conversion failure

**Mitigations:**
- Performance: Transformations only happen during reconciliation (not template rendering)
- Silent failures: Client-native and Dataplane API models are maintained to be compatible
- Debugging: Unit tests catch structural incompatibilities early

## Key Concepts

### Nil Safety

All transformation functions handle nil input gracefully:

```go
var nilModel *models.ACL = nil
result := transform.ToAPIACL(nilModel)
// result is nil (not panic)
```

**Why this matters:**

Parsed configurations may have optional fields. Forcing nil checks at call sites creates verbose code:

```go
// Without nil safety (verbose)
if frontend.Bind != nil {
    apiBind := transform.ToAPIBind(frontend.Bind)
    if apiBind != nil {
        // Use apiBind
    }
}

// With nil safety (clean)
if apiBind := transform.ToAPIBind(frontend.Bind); apiBind != nil {
    // Use apiBind
}
```

### Error Handling Strategy

The generic `transform` function returns `nil` on marshaling/unmarshaling errors instead of returning `error`.

**Rationale:**

1. **Errors should be rare**: Both models come from well-tested libraries with compatible JSON schemas
2. **Caller simplification**: No error checking at every call site
3. **Nil is sufficient signal**: Callers can check for nil and handle accordingly

**When errors occur:**

Marshaling/unmarshaling failures indicate:
- Bug in client-native library (malformed model)
- Bug in Dataplane API code generation (incompatible schema)
- Memory corruption (extremely rare)

All are programming errors, not runtime conditions. Returning nil propagates the error naturally - the comparison/sync will fail safely.

## Common Patterns

### Transforming Collections

```go
// Transform slice of ACLs
var apiACLs []*dataplaneapi.Acl
for _, acl := range frontend.ACLs {
    if apiACL := transform.ToAPIACL(acl); apiACL != nil {
        apiACLs = append(apiACLs, apiACL)
    }
}
```

### Transformation in Comparators

```go
// pkg/dataplane/comparator/sections/backend.go
func (c *BackendComparator) Compare(current, desired *models.Backend) []Operation {
    var ops []Operation

    // Transform to API models for comparison
    currentAPI := transform.ToAPIBackend(current)
    desiredAPI := transform.ToAPIBackend(desired)

    // Compare using API models
    if !reflect.DeepEqual(currentAPI, desiredAPI) {
        ops = append(ops, Operation{
            Type:     OperationUpdate,
            Resource: desiredAPI,
        })
    }

    return ops
}
```

### Pre-Transformation Validation

```go
// Optional: Validate before transforming
if backend.Name == "" {
    return fmt.Errorf("backend name required")
}

apiBackend := transform.ToAPIBackend(backend)
if apiBackend == nil {
    return fmt.Errorf("transformation failed for backend %s", backend.Name)
}

// Use apiBackend...
```

## Testing Strategy

### Unit Tests

Test nil handling and basic transformation:

```go
func TestToAPIACL(t *testing.T) {
    tests := []struct {
        name  string
        input *models.ACL
        want  *dataplaneapi.Acl
    }{
        {
            name:  "nil input",
            input: nil,
            want:  nil,
        },
        {
            name: "valid ACL",
            input: &models.ACL{
                ACLName:   "is_api",
                Criterion: "path_beg",
                Value:     "/api",
            },
            want: &dataplaneapi.Acl{
                Name:      "is_api",
                Criterion: "path_beg",
                Value:     "/api",
            },
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := transform.ToAPIACL(tt.input)

            if tt.want == nil {
                assert.Nil(t, got)
            } else {
                require.NotNil(t, got)
                assert.Equal(t, tt.want.Name, got.Name)
                assert.Equal(t, tt.want.Criterion, got.Criterion)
                assert.Equal(t, tt.want.Value, got.Value)
            }
        })
    }
}
```

### Integration Tests

Transformations are tested in context through comparator tests:

```go
// pkg/dataplane/comparator/sections/backend_test.go
func TestBackendComparator_Transform(t *testing.T) {
    // Test that transformation works correctly in comparator
    current := &models.Backend{Name: "api", Balance: "roundrobin"}
    desired := &models.Backend{Name: "api", Balance: "leastconn"}

    comparator := NewBackendComparator()
    ops := comparator.Compare(current, desired)

    require.Len(t, ops, 1)
    assert.Equal(t, OperationUpdate, ops[0].Type)

    // Verify transformed API model is in operation
    apiBackend, ok := ops[0].Resource.(*dataplaneapi.Backend)
    require.True(t, ok)
    assert.Equal(t, "leastconn", apiBackend.Balance.Algorithm)
}
```

## Adding New Transformations

### Checklist

When HAProxy adds a new configuration section:

1. **Check client-native support**: Does `haproxytech/client-native` have `models.NewType`?
2. **Check Dataplane API support**: Does code generation have `dataplaneapi.NewType`?
3. **Add transformation function**: Follow existing pattern
4. **Add unit test**: Test nil handling and basic conversion
5. **Update comparator**: Use new transformation in appropriate section comparator
6. **Update README**: Add function to API reference

### Example: Adding HTTP/3 Support

```go
// Step 1: Verify models exist
// - client-native v6.x has models.HTTP3Settings
// - Dataplane API has dataplaneapi.Http3Settings

// Step 2: Add transformation function
// transform.go
func ToAPIHTTP3Settings(model *models.HTTP3Settings) *dataplaneapi.Http3Settings {
    return transform[dataplaneapi.Http3Settings](model)
}

// Step 3: Add test
// transform_test.go
func TestToAPIHTTP3Settings(t *testing.T) {
    input := &models.HTTP3Settings{
        Enabled: true,
        MaxStreams: 100,
    }

    got := transform.ToAPIHTTP3Settings(input)

    require.NotNil(t, got)
    assert.True(t, got.Enabled)
    assert.Equal(t, int32(100), got.MaxStreams)
}

// Step 4: Use in comparator
// comparator/sections/frontend.go
func (c *FrontendComparator) compareHTTP3(current, desired *models.Frontend) []Operation {
    currentHTTP3 := transform.ToAPIHTTP3Settings(current.HTTP3)
    desiredHTTP3 := transform.ToAPIHTTP3Settings(desired.HTTP3)

    if !reflect.DeepEqual(currentHTTP3, desiredHTTP3) {
        return []Operation{{
            Type:     OperationUpdate,
            Resource: desiredHTTP3,
            Section:  "http3",
        }}
    }

    return nil
}
```

## Common Pitfalls

### Assuming Transformation Never Fails

**Problem**: Not checking for nil result.

```go
// Bad - crashes if transformation fails
apiACL := transform.ToAPIACL(parsedACL)
name := apiACL.Name  // Panic if apiACL is nil!
```

**Solution**: Check for nil.

```go
// Good
apiACL := transform.ToAPIACL(parsedACL)
if apiACL == nil {
    return fmt.Errorf("failed to transform ACL")
}
name := apiACL.Name
```

### Manual Transformation Instead of Using Package

**Problem**: Duplicating transformation logic.

```go
// Bad - reinventing the wheel
data, _ := json.Marshal(clientACL)
var apiACL dataplaneapi.Acl
json.Unmarshal(data, &apiACL)
```

**Solution**: Use existing transformation.

```go
// Good - use tested, consistent transformation
apiACL := transform.ToAPIACL(clientACL)
```

### Transforming in Hot Paths

**Problem**: Unnecessary transformations in loops.

```go
// Bad - transforms same model 1000 times
for i := 0; i < 1000; i++ {
    apiBackend := transform.ToAPIBackend(backend)
    doSomething(apiBackend)
}
```

**Solution**: Transform once, reuse.

```go
// Good - transform once
apiBackend := transform.ToAPIBackend(backend)
for i := 0; i < 1000; i++ {
    doSomething(apiBackend)
}
```

### Not Updating Transform Package

**Problem**: Adding new model type without adding transformation.

```go
// Bad - other developers will duplicate this logic
data, _ := json.Marshal(newModel)
var apiModel dataplaneapi.NewType
json.Unmarshal(data, &apiModel)
```

**Solution**: Add to transform package first.

```go
// Good - add to transform package
// transform.go
func ToAPINewType(model *models.NewType) *dataplaneapi.NewType {
    return transform[dataplaneapi.NewType](model)
}

// Then use it
apiModel := transform.ToAPINewType(newModel)
```

## Performance Considerations

### Benchmarking

Transformation performance (typical values on modern hardware):

```
BenchmarkToAPIACL-8           100000    10.2 µs/op    3.2 KB/op    45 allocs/op
BenchmarkToAPIBackend-8        50000    18.7 µs/op    6.1 KB/op    78 allocs/op
BenchmarkToAPIFrontend-8       50000    19.3 µs/op    6.4 KB/op    81 allocs/op
BenchmarkToAPIServer-8        100000    12.1 µs/op    3.8 KB/op    52 allocs/op
```

### When Performance Matters

Transformations occur during:
- Configuration comparison (once per reconciliation)
- Operation generation (once per changed element)
- API request preparation (once per operation)

Performance is NOT a concern because:
- Reconciliation happens infrequently (seconds to minutes apart)
- Microsecond-level overhead is negligible compared to API latency (milliseconds)
- Template rendering doesn't use transformations

### Memory Usage

Each transformation allocates temporary JSON bytes and result struct. For a typical configuration with 100 elements:

```
100 frontends × 20µs = 2ms transformation time
100 frontends × 6KB = 600KB temporary allocations
```

Go's garbage collector handles this efficiently since allocations are short-lived.

## Troubleshooting

### Transformation Returns Nil

**Diagnosis:**

1. Check if input is nil
2. Verify model types are compatible
3. Check for marshaling errors (rare)

```go
// Debug transformation failure
if apiACL := transform.ToAPIACL(clientACL); apiACL == nil {
    // Try manual transformation to see error
    data, err := json.Marshal(clientACL)
    if err != nil {
        log.Error("marshal failed", "error", err, "model", clientACL)
    }

    var apiACL dataplaneapi.Acl
    if err := json.Unmarshal(data, &apiACL); err != nil {
        log.Error("unmarshal failed", "error", err, "data", string(data))
    }
}
```

### Field Values Lost After Transformation

**Diagnosis:**

1. Check JSON tags on both model types
2. Verify field name compatibility
3. Check for type mismatches (e.g., `string` vs `*string`)

```go
// Example incompatibility
type ClientModel struct {
    Value string `json:"value"`  // Client-native
}

type APIModel struct {
    Value *string `json:"val"`   // Different JSON tag!
}

// Transformation will lose Value field
```

### Unexpected Nil Fields in Result

**Diagnosis:**

1. Check if source field is pointer vs value
2. Verify JSON omitempty tags
3. Check zero value handling

```go
// Debug field loss
clientACL := &models.ACL{ACLName: "test", Criterion: "path_beg"}
apiACL := transform.ToAPIACL(clientACL)

// Log both to compare
log.Info("transformation",
    "input", fmt.Sprintf("%+v", clientACL),
    "output", fmt.Sprintf("%+v", apiACL))
```

## Future Improvements

### Potential Enhancements

1. **Error reporting**: Return detailed errors instead of nil
2. **Transformation cache**: Cache frequently-transformed models
3. **Validation**: Add schema validation before/after transformation
4. **Performance**: Direct struct mapping for hot paths

### When to Refactor

Consider refactoring if:
- Transformation failures become common
- Performance becomes measurable bottleneck (profile first!)
- Client-native and Dataplane API models diverge significantly
- Need for custom field mapping increases

## Resources

- API documentation: `pkg/dataplane/transform/README.md`
- Comparator usage: `pkg/dataplane/comparator/sections/*.go`
- Client-native models: https://github.com/haproxytech/client-native
- Dataplane API docs: https://www.haproxy.com/documentation/haproxy-data-plane-api/
