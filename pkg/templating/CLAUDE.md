# pkg/templating - Template Engine

Development context for the template engine library.

**API Documentation**: See `pkg/templating/README.md`
**Architecture**: See `/docs/development/design.md` (Template Engine section)

## When to Work Here

Modify this package when:
- Adding custom template filters
- Improving template compilation performance
- Fixing template rendering bugs
- Adding new template engine backends
- Enhancing error reporting

**DO NOT** modify this package for:
- Rendering coordination → Use `pkg/controller`
- Event handling → Use `pkg/events`
- HAProxy configuration → Use `pkg/dataplane`
- Kubernetes resources → Use `pkg/k8s`

## Key Design Principle

This is a **pure library** with zero dependencies on other pkg/ packages. It could be extracted and used in any Go project needing templating.

Dependencies: Only Gonja v2 and standard library.

## Package Structure

```
pkg/templating/
├── engine.go       # TemplateEngine implementation
├── types.go        # Type definitions (EngineType)
├── errors.go       # Custom error types
├── engine_test.go  # Unit tests
└── README.md       # User documentation
```

## Core Design

### Pre-compilation Strategy

Templates are compiled once at initialization for optimal runtime performance:

```go
// Compilation happens once
engine, err := templating.New(templating.EngineTypeGonja, templates)
if err != nil {
    // Compilation errors caught early
    log.Fatal(err)
}

// Rendering is fast (microseconds)
for i := 0; i < 1000; i++ {
    output, err := engine.Render("template", context)
}
```

**Benefits:**
- Syntax errors detected at startup (fail-fast)
- No runtime compilation overhead
- Thread-safe concurrent rendering
- Predictable performance

### Error Types

Four distinct error types for clear error handling:

```go
// CompilationError - template has syntax errors
type CompilationError struct {
    TemplateName    string
    TemplateSnippet string  // First 50 chars for context
    Cause           error
}

// RenderError - runtime rendering failed
type RenderError struct {
    TemplateName string
    Cause        error
}

// TemplateNotFoundError - template doesn't exist
type TemplateNotFoundError struct {
    TemplateName       string
    AvailableTemplates []string
}

// UnsupportedEngineError - invalid engine type
type UnsupportedEngineError struct {
    EngineType EngineType
}
```

## Testing Approach

### Test Template Logic, Not Gonja

Focus on testing the library API and error handling, not Gonja syntax:

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
            name:     "simple variable substitution",
            template: "Hello {{ name }}",
            context:  map[string]interface{}{"name": "World"},
            want:     "Hello World",
        },
        {
            name:     "missing variable with default",
            template: "Hello {{ name | default('Guest') }}",
            context:  map[string]interface{}{},
            want:     "Hello Guest",
        },
        {
            name:     "complex context",
            template: "{% for item in items %}{{ item }}{% endfor %}",
            context:  map[string]interface{}{"items": []string{"a", "b"}},
            want:     "ab",
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            engine, err := templating.New(templating.EngineTypeGonja,
                map[string]string{"test": tt.template})

            if tt.wantErr {
                require.Error(t, err)
                return
            }

            require.NoError(t, err)

            got, err := engine.Render("test", tt.context)
            require.NoError(t, err)
            assert.Equal(t, tt.want, got)
        })
    }
}
```

### Test Error Handling

```go
func TestTemplateEngine_CompilationError(t *testing.T) {
    // Invalid template syntax
    templates := map[string]string{
        "invalid": "{% if true %}\n{% endif extra text %}",
    }

    _, err := templating.New(templating.EngineTypeGonja, templates)

    require.Error(t, err)

    var compErr *templating.CompilationError
    require.True(t, errors.As(err, &compErr))
    assert.Equal(t, "invalid", compErr.TemplateName)
    assert.NotEmpty(t, compErr.TemplateSnippet)
}

func TestTemplateEngine_TemplateNotFound(t *testing.T) {
    engine, _ := templating.New(templating.EngineTypeGonja, map[string]string{
        "exists": "content",
    })

    _, err := engine.Render("missing", nil)

    require.Error(t, err)

    var notFoundErr *templating.TemplateNotFoundError
    require.True(t, errors.As(err, &notFoundErr))
    assert.Equal(t, "missing", notFoundErr.TemplateName)
    assert.Contains(t, notFoundErr.AvailableTemplates, "exists")
}
```

## Common Pitfalls

### Recreating Engine on Every Render

**Problem**: Recompiling templates on every render.

```go
// Bad - compiles templates every time (milliseconds)
for _, context := range contexts {
    engine, _ := templating.New(templating.EngineTypeGonja, templates)
    output, _ := engine.Render("template", context)
}
```

**Solution**: Create once, reuse for all renders.

```go
// Good - compile once, render many times (microseconds)
engine, err := templating.New(templating.EngineTypeGonja, templates)
if err != nil {
    log.Fatal(err)
}

for _, context := range contexts {
    output, _ := engine.Render("template", context)
}
```

### Not Checking Compilation Errors

**Problem**: Syntax errors discovered at runtime in production.

```go
// Bad - ignoring compilation errors
engine, _ := templating.New(templating.EngineTypeGonja, templates)

// Later in production...
output, err := engine.Render("template", context)
// err: template doesn't exist (because compilation failed)
```

**Solution**: Always check compilation errors at startup.

```go
// Good - fail fast on invalid templates
engine, err := templating.New(templating.EngineTypeGonja, templates)
if err != nil {
    var compErr *templating.CompilationError
    if errors.As(err, &compErr) {
        log.Fatal("template compilation failed",
            "template", compErr.TemplateName,
            "error", compErr.Cause)
    }
    log.Fatal(err)
}
```

### Large Template Snippets in Errors

**Problem**: Logging 10KB template in error message.

```go
// Bad - logs entire template
log.Error("compilation failed", "template", templateContent)
```

**Solution**: CompilationError already includes snippet (first 50 chars).

```go
// Good - error contains context snippet
if err != nil {
    var compErr *templating.CompilationError
    if errors.As(err, &compErr) {
        log.Error("compilation failed",
            "template", compErr.TemplateName,
            "snippet", compErr.TemplateSnippet,  // First 50 chars
            "error", compErr.Cause)
    }
}
```

### Ignoring Thread Safety

**Problem**: Assuming TemplateEngine is not thread-safe.

```go
// Unnecessary - TemplateEngine is already thread-safe
var mu sync.Mutex

func render(engine *templating.TemplateEngine, ctx map[string]interface{}) string {
    mu.Lock()
    defer mu.Unlock()
    output, _ := engine.Render("template", ctx)
    return output
}
```

**Solution**: Use TemplateEngine concurrently without locking.

```go
// Good - no lock needed
func render(engine *templating.TemplateEngine, ctx map[string]interface{}) string {
    output, _ := engine.Render("template", ctx)
    return output
}

// Safe to call from multiple goroutines
var wg sync.WaitGroup
for i := 0; i < 100; i++ {
    wg.Add(1)
    go func() {
        defer wg.Done()
        render(engine, context)
    }()
}
wg.Wait()
```

## Template Tracing

The template engine provides execution tracing for observability and performance debugging.

### Enabling Tracing

```go
engine, _ := templating.New(templating.EngineTypeGonja, templates)

// Enable tracing
engine.EnableTracing()

// Render templates (tracing happens automatically)
output, _ := engine.Render("haproxy.cfg", context)

// Get trace output
trace := engine.GetTraceOutput()
fmt.Println(trace)

// Disable tracing
engine.DisableTracing()
```

### Trace Output

Tracing logs each template render with name and duration:

```
Rendering: haproxy.cfg
Completed: haproxy.cfg (0.007ms)
Rendering: backends.cfg
  Rendering: backend-snippet
  Completed: backend-snippet (0.003ms)
Completed: backends.cfg (0.012ms)
```

**Output format:**
- Indentation shows nesting depth (includes)
- Duration in milliseconds with 3 decimal places
- Start/complete pairs for each template

### Use Cases

**1. Performance debugging:**
```go
engine.EnableTracing()

// Render all templates
for name := range templates {
    engine.Render(name, context)
}

// Parse trace to find slow templates
trace := engine.GetTraceOutput()
for _, line := range strings.Split(trace, "\n") {
    if strings.Contains(line, "Completed") {
        // Extract duration and identify >10ms templates
    }
}
```

**2. Template execution verification:**
```go
// Ensure expected templates are executed
engine.EnableTracing()
engine.Render("haproxy.cfg", context)
trace := engine.GetTraceOutput()

if !strings.Contains(trace, "Rendering: backends.cfg") {
    log.Warn("backends.cfg was not included")
}
```

**3. Integration with validation tests:**
```go
// In controller validate command
engine.EnableTracing()

runner := testrunner.New(config, engine, paths, options)
results, _ := runner.RunTests(ctx, "")

// Show trace after results
trace := engine.GetTraceOutput()
fmt.Println("\n=== Template Execution Trace ===")
fmt.Println(trace)
```

### Implementation Details

**Tracing configuration:**
```go
type tracingConfig struct {
    enabled bool                // Tracing on/off
    depth   int                 // Current nesting level
    builder *strings.Builder    // Accumulated trace output
}
```

**Render method integration:**
```go
func (e *TemplateEngine) Render(templateName string, context map[string]interface{}) (string, error) {
    if e.tracing != nil && e.tracing.enabled {
        e.trace("Rendering: %s", templateName)
        e.tracing.depth++
        startTime := time.Now()

        defer func() {
            duration := time.Since(startTime)
            e.tracing.depth--
            e.trace("Completed: %s (%.3fms)", templateName,
                float64(duration.Microseconds())/1000.0)
        }()
    }

    // Normal rendering logic
    return e.render(templateName, context)
}
```

**Key design decisions:**
- Uses `defer` to ensure completion logging even on errors
- Depth tracking via counter (incremented on entry, decremented on exit)
- String builder for efficient accumulation
- Thread-safe: tracing state protected by engine immutability during render

### Performance Overhead

Tracing overhead is minimal:
- Simple render: ~0.001ms overhead per template
- Complex render: <1% overhead
- String builder prevents repeated allocations
- No goroutines or locks during tracing

**Recommendation**: Safe to leave enabled for debugging, but disable in performance-critical production paths.

### Limitations

**Current limitations:**
1. No filtering by template name
2. Fixed output format (not configurable)
3. No automatic slow template warnings
4. Trace cleared on each `GetTraceOutput()` call

**Workarounds:**
- Filter trace output in calling code
- Parse trace to generate custom reports
- Set thresholds in analysis code
- Copy trace before clearing if needed

### Testing Tracing

```go
func TestTemplateEngine_Tracing(t *testing.T) {
    templates := map[string]string{
        "main": "{% include 'sub' %}",
        "sub":  "content",
    }

    engine, _ := templating.New(templating.EngineTypeGonja, templates)
    engine.EnableTracing()

    _, err := engine.Render("main", nil)
    require.NoError(t, err)

    trace := engine.GetTraceOutput()

    // Verify trace contains expected entries
    assert.Contains(t, trace, "Rendering: main")
    assert.Contains(t, trace, "Rendering: sub")
    assert.Contains(t, trace, "Completed: main")
    assert.Contains(t, trace, "Completed: sub")

    // Verify nesting (sub should be indented)
    assert.Contains(t, trace, "  Rendering: sub")
}
```

## Adding Custom Filters

Future feature - not yet implemented. This section describes the planned approach.

### Design

Custom filters extend Gonja's built-in filters:

```go
// Register custom filter
engine.RegisterFilter("b64decode", func(in interface{}) (interface{}, error) {
    str, ok := in.(string)
    if !ok {
        return nil, fmt.Errorf("b64decode: expected string, got %T", in)
    }

    decoded, err := base64.StdEncoding.DecodeString(str)
    if err != nil {
        return nil, fmt.Errorf("b64decode: %w", err)
    }

    return string(decoded), nil
})

// Use in template
template := "Secret: {{ encoded_secret | b64decode }}"
```

### Common Filters to Add

**Base64 operations:**
```go
func b64encode(in interface{}) (interface{}, error)
func b64decode(in interface{}) (interface{}, error)
```

**JSONPath extraction:**
```go
func get_path(obj interface{}, path string) (interface{}, error)
// Usage: {{ resource | get_path("metadata.namespace") }}
```

**Safe defaults:**
```go
func default_empty(in interface{}) (interface{}, error)
// Returns empty string if nil/null, unlike Gonja's default filter
```

### Implementation Approach

```go
// engine.go
type FilterFunc func(in interface{}, args ...interface{}) (interface{}, error)

func (e *TemplateEngine) RegisterFilter(name string, fn FilterFunc) error {
    if e.filters == nil {
        e.filters = make(map[string]FilterFunc)
    }

    // Check for name collision
    if _, exists := e.filters[name]; exists {
        return fmt.Errorf("filter %s already registered", name)
    }

    e.filters[name] = fn

    // Register with Gonja environment
    return e.registerGonjaFilter(name, fn)
}
```

## Performance Optimization

### Benchmarking

```go
func BenchmarkTemplateEngine_Render(b *testing.B) {
    templates := map[string]string{
        "simple": "Hello {{ name }}!",
        "loop": `{% for i in items %}{{ i }}{% endfor %}`,
        "complex": `
            {% for user in users %}
                Name: {{ user.name }}
                Email: {{ user.email | lower }}
                {% if user.admin %}Admin{% endif %}
            {% endfor %}
        `,
    }

    engine, _ := templating.New(templating.EngineTypeGonja, templates)

    contexts := map[string]map[string]interface{}{
        "simple": {"name": "World"},
        "loop": {"items": []int{1, 2, 3, 4, 5}},
        "complex": {
            "users": []map[string]interface{}{
                {"name": "Alice", "email": "ALICE@EXAMPLE.COM", "admin": true},
                {"name": "Bob", "email": "BOB@EXAMPLE.COM", "admin": false},
            },
        },
    }

    for name, ctx := range contexts {
        b.Run(name, func(b *testing.B) {
            b.ResetTimer()
            for i := 0; i < b.N; i++ {
                engine.Render(name, ctx)
            }
        })
    }
}
```

**Expected results:**
- Simple: ~20-50µs per render
- Loop: ~50-100µs per render
- Complex: ~100-200µs per render

### Memory Optimization

```go
// Bad - allocates new map for each render
for i := 0; i < 1000; i++ {
    ctx := map[string]interface{}{
        "name": users[i].Name,
    }
    engine.Render("template", ctx)
}

// Good - reuse context map
ctx := make(map[string]interface{})
for i := 0; i < 1000; i++ {
    ctx["name"] = users[i].Name
    engine.Render("template", ctx)
}
```

### Template Size

```go
// Bad - one huge template (slow compilation, poor error messages)
templates := map[string]string{
    "haproxy.cfg": `
        global
            daemon
        defaults
            mode http
        {{ 5000 lines of template }}
    `,
}

// Good - break into logical pieces
templates := map[string]string{
    "haproxy.cfg": `
        {% include "global" %}
        {% include "defaults" %}
        {% include "frontends" %}
        {% include "backends" %}
    `,
    "global": "global\n    daemon",
    "defaults": "defaults\n    mode http",
    "frontends": "...",
    "backends": "...",
}
```

## Gonja Integration Notes

### Gonja v2 vs v1

This package uses Gonja v2 (`github.com/nikolalohinski/gonja/v2`):
- More active maintenance
- Better error messages
- Compatible with Jinja2 template syntax
- Requires Go 1.21+

### Gonja Limitations

**Not supported:**
- Template inheritance (`{% extends %}`) - requires file system
- Automatic escaping - must be done manually
- Async filters - all filters are synchronous
- Sandboxing - all functions have full access

**Workarounds:**
- Template inheritance: Flatten templates at load time
- Escaping: Add custom filters or escape in context preparation
- Async: Prepare all data before rendering
- Sandboxing: Not needed for our use case (trusted templates)

### Gonja Quirks

**CRITICAL: Escape sequences in string literals not supported:**
```jinja2
{{ "\n" }}  {# Does NOT produce a newline! #}
{{ "Line 1\nLine 2" }}  {# Output: Line 1\nLine 2 (literal backslash-n) #}
```
Gonja does not interpret escape sequences (`\n`, `\t`, etc.) in string literals. The backslash-n is output as literal characters or ignored entirely. This is a fundamental limitation of Gonja.

**Workaround**: Use actual newlines in templates or pass newlines through context variables.

**Whitespace handling:**
```jinja2
{% if true %}
    text
{% endif %}
```
Produces leading whitespace. Use:
```jinja2
{%- if true -%}
    text
{%- endif -%}
```

**Map access:**
```jinja2
{{ user.name }}          {# Dict-style access #}
{{ user["name"] }}       {# Map-style access #}
```
Both work, dict-style is preferred.

**Loop variable:**
```jinja2
{% for item in items %}
    {{ loop.index }}    {# 1-indexed #}
    {{ loop.index0 }}   {# 0-indexed #}
    {{ loop.first }}    {# boolean #}
    {{ loop.last }}     {# boolean #}
{% endfor %}
```

## Troubleshooting

### Template Not Found

**Diagnosis:**

1. Check template name exactly matches
2. List available templates
3. Verify templates were provided at initialization

```go
if !engine.HasTemplate(templateName) {
    available := engine.TemplateNames()
    log.Error("template not found",
        "requested", templateName,
        "available", available)
}
```

### Rendering Produces Empty Output

**Diagnosis:**

1. Check for silent errors in template (use `{% if var is defined %}`)
2. Verify context contains expected data
3. Check for whitespace stripping (`{%-` and `-%}`)

```go
// Debug context
log.Info("rendering template",
    "template", templateName,
    "context_keys", getKeys(context))

output, err := engine.Render(templateName, context)

log.Info("render result",
    "output_length", len(output),
    "output_preview", output[:min(100, len(output))])
```

### High Memory Usage

**Diagnosis:**

1. Check template count and size
2. Review context object sizes
3. Look for memory leaks in custom filters

```go
// Monitor engine memory
var m runtime.MemStats
runtime.ReadMemStats(&m)

log.Info("template engine memory",
    "template_count", engine.TemplateCount(),
    "alloc_mb", m.Alloc/1024/1024,
    "total_alloc_mb", m.TotalAlloc/1024/1024)
```

### Slow Rendering

**Diagnosis:**

1. Benchmark specific template
2. Check for expensive operations in context preparation
3. Review loop complexity in templates

```go
// Profile template rendering
start := time.Now()
output, err := engine.Render(templateName, context)
duration := time.Since(start)

if duration > 100*time.Millisecond {
    log.Warn("slow template render",
        "template", templateName,
        "duration_ms", duration.Milliseconds(),
        "output_size", len(output))
}
```

## Extension Considerations

### Adding New Engine Type

Currently only Gonja is supported. To add another engine:

```go
// types.go
const (
    EngineTypeGonja EngineType = iota
    EngineTypeCustom  // New engine
)

// engine.go
func New(engineType EngineType, templates map[string]string) (*TemplateEngine, error) {
    switch engineType {
    case EngineTypeGonja:
        return newGonjaEngine(templates)
    case EngineTypeCustom:
        return newCustomEngine(templates)
    default:
        return nil, &UnsupportedEngineError{EngineType: engineType}
    }
}
```

**Considerations:**
- Must support pre-compilation
- Must be thread-safe
- Should have similar performance characteristics
- Error types must map to existing error types

## Resources

- API documentation: `pkg/templating/README.md`
- Gonja documentation: https://github.com/nikolalohinski/gonja
- Jinja2 template documentation: https://jinja.palletsprojects.com/
- HAProxy template examples: `/examples/templates/`
