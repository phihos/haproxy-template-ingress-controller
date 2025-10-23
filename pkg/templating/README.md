# Template Engine Library

## Overview

This package provides a Go template engine with Jinja2-like syntax through the Gonja v2 library. You create an engine with your templates, and it pre-compiles them all at initialization. This design catches syntax errors early (at startup) rather than at runtime, and makes rendering fast since templates are already compiled.

**When to use this package:**
- You need Jinja2/Django-style template syntax in Go
- You want to catch template syntax errors at application startup
- You're building a system that renders the same templates repeatedly with different data
- You need features like loops, conditionals, filters, and macros in your templates

The engine is thread-safe, so you can render templates concurrently from multiple goroutines without additional synchronization.

## Features

- **Pre-compilation**: All templates are compiled at initialization for fast rendering
- **Jinja2 Syntax**: Uses Gonja v2 for familiar Jinja2/Django template syntax
- **Type-Safe**: Strongly-typed API with custom error types
- **Early Validation**: Syntax errors detected at initialization, not runtime
- **Named Templates**: Manage multiple templates with string identifiers
- **Rich Features**: Full Jinja2 feature set (loops, conditionals, filters, macros)
- **Zero Dependencies**: Pure Go implementation via Gonja v2

## Installation

```bash
go get github.com/nikolalohinski/gonja/v2@v2.4.1
```

The package is part of the `haproxy-template-ic` project and located at `pkg/templating`.

## Quick Start

```go
package main

import (
    "log"

    "haproxy-template-ic/pkg/templating"
)

func main() {
    // Define templates
    templates := map[string]string{
        "greeting": "Hello {{ name }}!",
        "config":   "server {{ host }}:{{ port }}",
    }

    // Create engine with Gonja
    engine, err := templating.New(templating.EngineTypeGonja, templates)
    if err != nil {
        log.Fatalf("failed to create engine: %v", err)
    }

    // Render template
    output, err := engine.Render("greeting", map[string]interface{}{
        "name": "World",
    })
    if err != nil {
        log.Fatal(err)
    }

    log.Println(output) // Output: Hello World!
}
```

## Usage Examples

### Creating a Template Engine

The engine compiles all templates at initialization:

```go
templates := map[string]string{
    "haproxy.cfg": `
global
    daemon
    maxconn {{ max_connections }}

defaults
    timeout connect {{ timeouts.connect }}
    timeout client {{ timeouts.client }}
    timeout server {{ timeouts.server }}
`,
    "backend": `
backend {{ name }}
    balance {{ algorithm }}
{% for server in servers %}
    server {{ server.name }} {{ server.address }}:{{ server.port }} check
{% endfor %}
`,
}

engine, err := templating.New(templating.EngineTypeGonja, templates)
if err != nil {
    log.Fatalf("compilation error: %v", err)
}
```

### Rendering Templates

Render templates with context data:

```go
// Simple context
output, err := engine.Render("greeting", map[string]interface{}{
    "name": "Alice",
})

// Nested context
output, err := engine.Render("haproxy.cfg", map[string]interface{}{
    "max_connections": 4096,
    "timeouts": map[string]interface{}{
        "connect": "5s",
        "client":  "30s",
        "server":  "30s",
    },
})

// Complex context with arrays
output, err := engine.Render("backend", map[string]interface{}{
    "name":      "web_backend",
    "algorithm": "roundrobin",
    "servers": []map[string]interface{}{
        {"name": "web1", "address": "192.168.1.10", "port": 80},
        {"name": "web2", "address": "192.168.1.11", "port": 80},
    },
})
```

### Error Handling

Handle different error types appropriately:

```go
import "errors"

engine, err := templating.New(templating.EngineTypeGonja, templates)
if err != nil {
    var compErr *templating.CompilationError
    if errors.As(err, &compErr) {
        log.Printf("Template '%s' has syntax error", compErr.TemplateName)
        log.Printf("Snippet: %s", compErr.TemplateSnippet)
    }
    return err
}

output, err := engine.Render("mytemplate", context)
if err != nil {
    var renderErr *templating.RenderError
    if errors.As(err, &renderErr) {
        log.Printf("Failed to render '%s': %v", renderErr.TemplateName, renderErr.Cause)
    }

    var notFoundErr *templating.TemplateNotFoundError
    if errors.As(err, &notFoundErr) {
        log.Printf("Template '%s' not found", notFoundErr.TemplateName)
        log.Printf("Available: %v", notFoundErr.AvailableTemplates)
    }

    return err
}
```

### Checking Template Existence

Verify templates before rendering:

```go
if engine.HasTemplate("greeting") {
    output, err := engine.Render("greeting", context)
}

// Get list of all templates
names := engine.TemplateNames()
fmt.Printf("Available templates: %v\n", names)

// Get count
count := engine.TemplateCount()
fmt.Printf("Loaded %d templates\n", count)
```

### Accessing Raw Templates

Retrieve original template strings:

```go
raw, err := engine.GetRawTemplate("greeting")
if err != nil {
    log.Fatal(err)
}

fmt.Println("Original template:", raw)
```

### Complex Gonja Features

The engine supports full Jinja2/Gonja syntax:

**Loops:**
```go
templates := map[string]string{
    "list": `
{% for item in items %}
  - {{ item.name }}: {{ item.value }}
{% endfor %}
`,
}

output, err := engine.Render("list", map[string]interface{}{
    "items": []map[string]interface{}{
        {"name": "A", "value": 1},
        {"name": "B", "value": 2},
    },
})
```

**Conditionals:**
```go
templates := map[string]string{
    "conditional": `
{% if count > 10 %}
    mode: high
{% elif count > 5 %}
    mode: medium
{% else %}
    mode: low
{% endif %}
`,
}

output, err := engine.Render("conditional", map[string]interface{}{
    "count": 7,
})
```

**Filters:**
```go
templates := map[string]string{
    "filters": `
Name: {{ name | upper }}
Items: {{ items | join(", ") }}
Default: {{ missing | default("N/A") }}
`,
}

output, err := engine.Render("filters", map[string]interface{}{
    "name":  "alice",
    "items": []string{"a", "b", "c"},
})
```

**Macros:**
```go
templates := map[string]string{
    "macros": `
{% macro render_server(name, address, port) %}
    server {{ name }} {{ address }}:{{ port }} check
{% endmacro %}

{% for srv in servers %}
{{ render_server(srv.name, srv.address, srv.port) }}
{% endfor %}
`,
}
```

**Loop Variables:**
```go
templates := map[string]string{
    "loop_vars": `
{% for item in items %}
{{ loop.index }}: {{ item }}{% if not loop.last %}, {% endif %}
{% endfor %}
`,
}
```

## API Reference

### Constructor

#### `New(engineType EngineType, templates map[string]string) (*TemplateEngine, error)`

Creates a new template engine and compiles all templates.

**Parameters:**
- `engineType`: Template engine to use (currently only `EngineTypeGonja`)
- `templates`: Map of template name to template content

**Returns:**
- `*TemplateEngine`: Initialized engine with compiled templates
- `error`: Compilation error if any template has syntax errors

**Example:**
```go
engine, err := templating.New(templating.EngineTypeGonja, map[string]string{
    "hello": "Hello {{ name }}!",
})
```

### Rendering

#### `Render(templateName string, context map[string]interface{}) (string, error)`

Executes a template with the provided context and returns the rendered output.

**Parameters:**
- `templateName`: Name of the template to render
- `context`: Data to pass to the template

**Returns:**
- `string`: Rendered template output
- `error`: Error if template not found or rendering fails

**Example:**
```go
output, err := engine.Render("hello", map[string]interface{}{
    "name": "World",
})
```

### Helper Methods

#### `HasTemplate(templateName string) bool`

Checks if a template exists.

#### `TemplateNames() []string`

Returns a list of all available template names.

#### `TemplateCount() int`

Returns the number of loaded templates.

#### `GetRawTemplate(templateName string) (string, error)`

Returns the original (uncompiled) template string.

#### `EngineType() EngineType`

Returns the template engine type used by this instance.

#### `String() string`

Returns a string representation for debugging.

### Types

#### `EngineType`

```go
type EngineType int

const (
    EngineTypeGonja EngineType = iota
)
```

Enum for template engine selection. Currently supports:
- `EngineTypeGonja`: Gonja template engine (Jinja2-like)

#### `TemplateEngine`

```go
type TemplateEngine struct {
    // Has unexported fields
}
```

Main template engine struct. Create instances using `New()`.

### Error Types

#### `CompilationError`

```go
type CompilationError struct {
    TemplateName    string
    TemplateSnippet string
    Cause           error
}
```

Returned when a template has syntax errors during compilation.

#### `RenderError`

```go
type RenderError struct {
    TemplateName string
    Cause        error
}
```

Returned when template rendering fails at runtime.

#### `TemplateNotFoundError`

```go
type TemplateNotFoundError struct {
    TemplateName       string
    AvailableTemplates []string
}
```

Returned when attempting to render a non-existent template.

#### `UnsupportedEngineError`

```go
type UnsupportedEngineError struct {
    EngineType EngineType
}
```

Returned when using an invalid engine type.

## Template Syntax

The library uses Gonja, which implements Jinja2-like syntax. Here's a quick reference:

### Variables

```jinja2
{{ variable_name }}
{{ user.name }}
{{ items[0] }}
```

### Filters

```jinja2
{{ text | upper }}
{{ items | join(", ") }}
{{ value | default("N/A") }}
{{ number | round(2) }}
```

Common filters: `upper`, `lower`, `title`, `capitalize`, `trim`, `length`, `join`, `default`, `round`, `abs`, `first`, `last`, `sort`, `unique`

### Control Structures

**If/Elif/Else:**
```jinja2
{% if condition %}
    ...
{% elif other_condition %}
    ...
{% else %}
    ...
{% endif %}
```

**For Loops:**
```jinja2
{% for item in items %}
    {{ item }}
{% endfor %}

{% for key, value in dict.items() %}
    {{ key }}: {{ value }}
{% endfor %}
```

**Loop Variables:**
- `loop.index` - Current iteration (1-indexed)
- `loop.index0` - Current iteration (0-indexed)
- `loop.first` - True if first iteration
- `loop.last` - True if last iteration
- `loop.length` - Total number of iterations

### Comments

```jinja2
{# This is a comment #}
```

### Macros

```jinja2
{% macro render_item(name, value) %}
    {{ name }}: {{ value }}
{% endmacro %}

{{ render_item("key", "val") }}
```

### Whitespace Control

```jinja2
{%- if true -%}
    No whitespace before or after
{%- endif -%}
```

For complete syntax documentation, see [Gonja Documentation](https://github.com/nikolalohinski/gonja).

## Best Practices

### 1. Pre-compile at Initialization

**Always create the engine once and reuse it:**

```go
// Good - compile once
engine, err := templating.New(templating.EngineTypeGonja, templates)
if err != nil {
    log.Fatal(err)
}

// Reuse for multiple renders (efficient!)
for _, context := range contexts {
    output, err := engine.Render("template", context)
}
```

**Avoid:**
```go
// Bad - recompiles every time
for _, context := range contexts {
    engine, err := templating.New(templating.EngineTypeGonja, templates)
    output, err := engine.Render("template", context)
}
```

### 2. Validate Templates Early

Compile templates at application startup to catch errors early:

```go
func main() {
    // Load templates at startup
    engine, err := templating.New(templating.EngineTypeGonja, loadTemplates())
    if err != nil {
        log.Fatalf("template compilation failed: %v", err)
    }

    // Application continues with valid templates
    startServer(engine)
}
```

### 3. Use Type-Safe Context

Define context structs for better maintainability:

```go
type BackendConfig struct {
    Name      string
    Algorithm string
    Servers   []Server
}

type Server struct {
    Name    string
    Address string
    Port    int
}

config := BackendConfig{
    Name:      "web",
    Algorithm: "roundrobin",
    Servers: []Server{
        {Name: "web1", Address: "192.168.1.10", Port: 80},
    },
}

// Convert to map[string]interface{} for rendering
contextMap := map[string]interface{}{
    "name":      config.Name,
    "algorithm": config.Algorithm,
    "servers":   config.Servers,
}

output, err := engine.Render("backend", contextMap)
```

### 4. Handle Errors Gracefully

Always check for specific error types:

```go
output, err := engine.Render("template", context)
if err != nil {
    var renderErr *templating.RenderError
    if errors.As(err, &renderErr) {
        // Runtime error - might be missing variable
        log.Printf("render error: %v", renderErr.Cause)
        return handleRenderError(renderErr)
    }

    var notFoundErr *templating.TemplateNotFoundError
    if errors.As(err, &notFoundErr) {
        // Programming error - fix template name
        log.Printf("template not found: %s", notFoundErr.TemplateName)
        return handleNotFound(notFoundErr)
    }

    return err
}
```

### 5. Template Organization

Organize templates by purpose:

```go
templates := map[string]string{
    // Main templates
    "haproxy.cfg":    loadFile("templates/haproxy.cfg.j2"),

    // Snippets (included by main templates)
    "backend-name":   loadFile("templates/snippets/backend-name.j2"),
    "server-pool":    loadFile("templates/snippets/server-pool.j2"),

    // Error pages
    "400.http":       loadFile("templates/errors/400.http.j2"),
    "500.http":       loadFile("templates/errors/500.http.j2"),

    // Maps
    "host.map":       loadFile("templates/maps/host.map.j2"),
}
```

### 6. Use Default Filters

Provide fallback values for optional context variables:

```go
templates := map[string]string{
    "config": `
timeout connect {{ timeout_connect | default("5s") }}
maxconn {{ max_connections | default("4096") }}
`,
}

// Works even with empty context
output, err := engine.Render("config", map[string]interface{}{})
```

## Troubleshooting

### Compilation Errors

**Problem**: Template fails to compile at initialization

**Solutions**:
- Check template syntax against Jinja2/Gonja documentation
- Look for unmatched tags (`{% if %}` without `{% endif %}`)
- Verify filter names are correct
- Test template in isolation with minimal context
- Check for invalid macro definitions

**Example error handling:**
```go
engine, err := templating.New(templating.EngineTypeGonja, templates)
if err != nil {
    var compErr *templating.CompilationError
    if errors.As(err, &compErr) {
        fmt.Printf("Template: %s\n", compErr.TemplateName)
        fmt.Printf("Snippet: %s\n", compErr.TemplateSnippet)
        fmt.Printf("Error: %v\n", compErr.Cause)
    }
}
```

### Rendering Errors

**Problem**: Template renders successfully sometimes but fails with certain context

**Solutions**:
- Check for missing variables in context
- Use `default` filter for optional variables: `{{ var | default("fallback") }}`
- Verify data types match template expectations
- Check for nil/null values in nested structures
- Add defensive checks in templates with `{% if var is defined %}`

**Example:**
```go
// Template that handles missing values
template := `
{% if user is defined %}
    User: {{ user.name | default("Unknown") }}
{% else %}
    No user provided
{% endif %}
`
```

### Template Not Found Errors

**Problem**: `TemplateNotFoundError` at runtime

**Solutions**:
- Verify template name spelling matches exactly
- Use `HasTemplate()` to check existence before rendering
- List available templates with `TemplateNames()`
- Check template name is not empty string

**Example:**
```go
if !engine.HasTemplate(templateName) {
    availableTemplates := engine.TemplateNames()
    return fmt.Errorf("template '%s' not found, available: %v",
        templateName, availableTemplates)
}
```

### Performance Issues

**Problem**: Slow rendering performance

**Solutions**:
- Ensure you're reusing the same `TemplateEngine` instance (don't recreate)
- Avoid calling `New()` repeatedly (templates are already compiled)
- Consider splitting very large templates into smaller, reusable parts
- Profile your template rendering to find bottlenecks
- Use macros instead of duplicating template logic

### Memory Usage

**Problem**: High memory consumption

**Solutions**:
- Load only templates you need
- Don't store large data structures in context unnecessarily
- Consider streaming for very large outputs (use custom implementation)
- Profile memory usage with `pprof`

## Advanced Features

### Custom Filters

Gonja supports custom filters. For project-specific filters, consider creating a wrapper:

```go
// Future enhancement - custom filter support
// engine.RegisterFilter("custom_filter", filterFunc)
```

### Template Inheritance

Gonja supports template inheritance (not yet exposed in this API):

```jinja2
{# base.j2 #}
<html>
{% block content %}{% endblock %}
</html>

{# page.j2 #}
{% extends "base.j2" %}
{% block content %}
<p>Page content</p>
{% endblock %}
```

### Template Includes

Include other templates within a template:

```jinja2
{% include "header.j2" %}

Main content here

{% include "footer.j2" %}
```

**Note**: The current API requires all templates to be provided at initialization. Plan your template structure accordingly.

## Performance

The library is designed for high performance:

- **Compilation**: Templates are compiled once at initialization (~1-10ms per template)
- **Rendering**: Pre-compiled templates render in microseconds (~10-100µs for typical templates)
- **Memory**: Compiled templates are cached in memory for zero-cost lookups
- **Concurrency**: The `TemplateEngine` is safe for concurrent use from multiple goroutines

**Benchmark example:**
```go
func BenchmarkRender(b *testing.B) {
    engine, _ := templating.New(templating.EngineTypeGonja, map[string]string{
        "test": "Hello {{ name }}!",
    })

    context := map[string]interface{}{"name": "World"}

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        engine.Render("test", context)
    }
}
// Typical result: ~20-50µs per operation
```

## Related Documentation

- [Gonja v2 Documentation](https://github.com/nikolalohinski/gonja)
- [Jinja2 Template Designer Documentation](https://jinja.palletsprojects.com/en/stable/templates/)
- [HAProxy Template IC Design Document](../../docs/development/design.md)

## License

This library is part of the haproxy-template-ic project.
