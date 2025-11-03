# Template Engine Library

## Overview

This package provides a Go template engine with Jinja2-like syntax through the Gonja v2 library. You create an engine with your templates, and it pre-compiles them all at initialization. This design catches syntax errors early (at startup) rather than at runtime, and makes rendering fast since templates are already compiled.

**When to use this package:**
- You need Jinja2/Django-style template syntax in Go
- You want to catch template syntax errors at application startup
- You're building a system that renders the same templates repeatedly with different data
- You need features like loops, conditionals, filters, and macros in your templates

The engine is thread-safe, so you can render templates concurrently from multiple goroutines without additional synchronization. This includes all features: rendering, tracing, and template management operations.

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

## Custom Filters

The template engine supports custom filters through the `NewWithFilters` constructor. Custom filters extend Gonja's built-in filters with domain-specific functionality.

### NewWithFilters Constructor

```go
func NewWithFilters(
    engineType EngineType,
    templates map[string]string,
    filters map[string]FilterFunc,
) (*TemplateEngine, error)
```

Creates a template engine with custom filters registered globally for all templates.

**Parameters:**
- `engineType`: Template engine to use (currently only `EngineTypeGonja`)
- `templates`: Map of template name to template content
- `filters`: Map of filter name to filter function

**Filter Function Signature:**

```go
type FilterFunc func(in interface{}, args ...interface{}) (interface{}, error)
```

- `in`: The value being filtered (left side of the pipe)
- `args`: Optional arguments passed to the filter
- Returns: Transformed value or error

**Example:**

```go
// Define custom filters
filters := map[string]templating.FilterFunc{
    "to_upper": func(in interface{}, args ...interface{}) (interface{}, error) {
        str, ok := in.(string)
        if !ok {
            return nil, fmt.Errorf("to_upper requires string input")
        }
        return strings.ToUpper(str), nil
    },
    "multiply": func(in interface{}, args ...interface{}) (interface{}, error) {
        val, ok := in.(int)
        if !ok {
            return nil, fmt.Errorf("multiply requires integer input")
        }
        if len(args) == 0 {
            return nil, fmt.Errorf("multiply requires a multiplier argument")
        }
        multiplier, ok := args[0].(int)
        if !ok {
            return nil, fmt.Errorf("multiply argument must be integer")
        }
        return val * multiplier, nil
    },
}

// Create engine with custom filters
engine, err := templating.NewWithFilters(
    templating.EngineTypeGonja,
    templates,
    filters,
)
```

**Usage in templates:**

```jinja2
{{ "hello" | to_upper }}
{# Output: HELLO #}

{{ 5 | multiply(3) }}
{# Output: 15 #}
```

### Built-in Custom Filters

The HAProxy Template Ingress Controller provides these custom filters:

**glob_match** - Pattern matching for lists:

```go
// Usage: {{ list | glob_match("pattern") }}
func GlobMatch(in interface{}, args ...interface{}) (interface{}, error)
```

Filters a list of strings using glob patterns with `*` (match any characters) and `?` (match single character) wildcards.

**Example:**
```jinja2
{% set backend_snippets = template_snippets | glob_match("backend-annotation-*") %}
{% for snippet in backend_snippets %}
  {% include snippet %}
{% endfor %}
```

**b64decode** - Base64 decoding:

```go
// Usage: {{ string | b64decode }}
func B64Decode(in interface{}, args ...interface{}) (interface{}, error)
```

Decodes base64-encoded strings. Essential for accessing Kubernetes Secret data, which is automatically base64-encoded.

**Example:**
```jinja2
{% set secret = resources.secrets.GetSingle("default", "my-secret") %}
password: {{ secret.data.password | b64decode }}
```

**get_path** - File path resolution:

```go
// Usage: {{ filename | get_path("type") }}
func (pr *PathResolver) GetPath(filename interface{}, args ...interface{}) (interface{}, error)
```

Resolves filenames to absolute paths based on file type (`"map"`, `"file"`, or `"cert"`). Used for HAProxy auxiliary file references.

**Example:**
```jinja2
use_backend %[req.hdr(host),map({{ "host.map" | get_path("map") }})]
{# Output: use_backend %[req.hdr(host),map(/etc/haproxy/maps/host.map)] #}
```

**regex_escape** - Escape strings for HAProxy regex patterns:

```go
// Usage: {{ string | regex_escape }}
func RegexEscape(in interface{}, args ...interface{}) (interface{}, error)
```

Escapes special regex characters for safe use in HAProxy ACL patterns and path matching. Essential when constructing regex patterns from user-controlled data like path prefixes.

**Example:**
```jinja2
{# Escape path for regex matching #}
{% set path_pattern = path.path | regex_escape %}
acl path_match path_reg ^{{ path_pattern }}

{# Example: "/api/v1" becomes "\/api\/v1" #}
{% set api_path = "/api/v1" | regex_escape %}
{# Output: \/api\/v1 #}
```

**extract** - Extract values from objects using JSONPath expressions:

```go
// Usage: {{ items | extract("$.path.to.field") }}
func Extract(in interface{}, args ...interface{}) (interface{}, error)
```

Extracts values from objects or arrays using JSONPath-like expressions. Supports array indexing (`[*]`), nested access (`$.a.b.c`), and automatic flattening of nested arrays.

**Example:**
```jinja2
{# Extract all HTTP methods from routes #}
{% set methods = routes | extract("$.rules[*].matches[*].method") %}
{# Returns: ["GET", "POST", "PUT"] #}

{# Extract single field #}
{% set names = ingresses | extract("$.metadata.name") %}
{# Returns: ["app1", "app2", "app3"] #}

{# Extract nested values #}
{% set ports = services | extract("$.spec.ports[*].port") %}
{# Returns: [80, 443, 8080] #}
```

**sort_by** - Sort items by JSONPath expressions with multiple criteria:

```go
// Usage: {{ items | sort_by(["$.field1", "$.field2:desc"]) }}
func SortBy(in interface{}, args ...interface{}) (interface{}, error)
```

Sorts arrays of objects using one or more JSONPath expressions as sort keys. Supports modifiers: `:desc` (descending order), `:exists` (check field presence), and `| length` (sort by collection size).

**Example:**
```jinja2
{# Sort routes by priority (descending) then name #}
{% set sorted_routes = routes | sort_by(["$.priority:desc", "$.name"]) %}

{# Gateway API route precedence (method > headers > query > path) #}
{% set sorted = routes | sort_by([
    "$.match.method:exists:desc",
    "$.match.headers | length:desc",
    "$.match.queryParams | length:desc",
    "$.match.path.value | length:desc"
]) %}

{# Sort by field existence #}
{% set with_tls_first = ingresses | sort_by(["$.spec.tls:exists:desc"]) %}
```

**Modifiers:**
- `:desc` - Sort in descending order
- `:exists` - Check if field exists (true sorts before false)
- `| length` - Sort by collection or string length

**group_by** - Group items by JSONPath expression values:

```go
// Usage: {{ items | group_by("$.field") }}
func GroupBy(in interface{}, args ...interface{}) (interface{}, error)
```

Groups array items by the value of a JSONPath expression. Returns a map where keys are the extracted values and values are arrays of items with that value.

**Example:**
```jinja2
{# Group ingresses by namespace #}
{% set by_namespace = ingresses | group_by("$.metadata.namespace") %}
{% for namespace, ing_list in by_namespace.items() %}
  {# Process {{ ing_list|length }} ingresses in {{ namespace }} #}
{% endfor %}

{# Group routes by priority #}
{% set by_priority = routes | group_by("$.priority") %}
{% for priority, routes in by_priority.items() %}
  {# Routes with priority {{ priority }}: {{ routes|length }} #}
{% endfor %}
```

**transform** - Transform string values with regex substitution:

```go
// Usage: {{ items | transform("pattern", "replacement") }}
func Transform(in interface{}, args ...interface{}) (interface{}, error)
```

Applies regex substitution to array elements, replacing matches of a pattern with a replacement string. Supports capture group references (`$1`, `$2`, etc.).

**Example:**
```jinja2
{# Strip prefixes from paths #}
{% set paths = ["/api/v1/users", "/api/v1/posts"] %}
{% set stripped = paths | transform("^/api/v1", "") %}
{# Returns: ["/users", "/posts"] #}

{# Extract version from names #}
{% set versions = ["app-v1", "app-v2"] | transform("app-(v\\d+)", "$1") %}
{# Returns: ["v1", "v2"] #}
```

**debug** - Dump variable structure as HAProxy comments:

```go
// Usage: {{ variable | debug("label") }}
func Debug(in interface{}, args ...interface{}) (interface{}, error)
```

Formats variables as JSON and outputs them as HAProxy comments (prefixed with `#`). Useful for template debugging without breaking configuration syntax.

**Example:**
```jinja2
{# Inspect route structure #}
{{ routes | debug("all-routes") }}

{# Output:
# DEBUG all-routes:
# [
#   {
#     "name": "api-route",
#     "priority": 10,
#     "match": {"method": "GET"}
#   }
# ]
#}

{# Debug transformation results #}
{% set sorted = routes | sort_by(["$.priority:desc"]) %}
{{ sorted | debug("after-sorting") }}
```

**eval** - Evaluate JSONPath expressions for debugging:

```go
// Usage: {{ item | eval("$.path.to.field") }}
func Eval(in interface{}, args ...interface{}) (interface{}, error)
```

Evaluates a JSONPath expression and returns the result with type information. Useful for testing sort_by criteria and understanding why items are ordered a certain way.

**Example:**
```jinja2
{# Test sort criteria before using in sort_by #}
{% for route in routes %}
  {{ route.name }}: {{ route | eval("$.priority:desc") }}
  {# Output: api-route: 10 (int) #}
  {{ route | eval("$.match.method:exists") }}
  {# Output: true (bool) #}
{% endfor %}

{# Debug complex expressions #}
{{ route | eval("$.match.headers | length") }}
{# Output: 3 (int) #}
```

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

### Custom Tags

#### compute_once - Optimize Expensive Computations

The `compute_once` custom tag prevents redundant execution of expensive template computations. When a template section is wrapped in `compute_once`, it executes only on the first call and skips execution on subsequent calls during the same render.

**Syntax:**

```jinja2
{%- set result = namespace(data=[], processed=False) %}
{%- compute_once result %}
  {# Expensive computation that only runs once #}
  {%- set result.processed = True %}
  {%- for item in large_dataset %}
    {%- set result.data = result.data.append(process(item)) %}
  {%- endfor %}
{%- endcompute_once %}
```

**Key points:**
- Variable MUST be created before the `compute_once` block
- Use `namespace()` to create mutable state that persists across includes
- The tag tracks execution with a marker variable
- Cache is automatically cleared between `Render()` calls

**Use Cases:**

**1. Prevent redundant analysis across multiple includes:**

```jinja2
{# main.cfg #}
{%- set analysis = namespace(routes=[], groups={}) %}
{%- include "frontend-http" %}
{%- include "frontend-https" %}
{%- include "backend-routing" %}

{# frontend-http #}
{%- compute_once analysis %}
  {# Analyze all routes once instead of 3 times #}
  {%- from "route-analyzer" import analyze_routes %}
  {{- analyze_routes(analysis, all_routes) -}}
{%- endcompute_once %}
Use analysis here...

{# frontend-https #}
{%- compute_once analysis %}
  {# Skipped - already computed #}
  {%- from "route-analyzer" import analyze_routes %}
  {{- analyze_routes(analysis, all_routes) -}}
{%- endcompute_once %}
Use same analysis results...
```

**2. Real-world example from Gateway API:**

The Gateway API template library uses `compute_once` to optimize route analysis. Without it, the `analyze_routes` macro would run 4 times per configuration render, each time iterating over all HTTPRoutes and GRPCRoutes:

```jinja2
{# gateway.yaml library #}
{%- set analysis = namespace(path_groups={}, sorted_routes=[], all_routes=[]) %}

{# Used in multiple places - only analyzes once #}
{%- compute_once analysis %}
  {%- from "analyze_routes" import analyze_routes %}
  {{- analyze_routes(analysis, resources) -}}
{%- endcompute_once %}

{# All subsequent uses see the same analysis results #}
{% for route in analysis.sorted_routes %}
  {# Generate HAProxy configuration from analyzed routes #}
{% endfor %}
```

This optimization reduces the work by 75% in scenarios with many routes.

**3. Cache expensive filtering or sorting:**

```jinja2
{%- set filtered = namespace(items=[]) %}
{%- compute_once filtered %}
  {%- for item in large_list %}
    {%- if expensive_condition(item) %}
      {%- set filtered.items = filtered.items.append(item) %}
    {%- endif %}
  {%- endfor %}
{%- endcompute_once %}

{# Use filtered.items multiple times without recomputing #}
```

**Performance Impact:**

With `compute_once`, expensive computations execute exactly once regardless of how many templates include them. Without it, each include would re-execute the computation.

**Example impact** (4 call sites with 100 HTTPRoutes):
- Without `compute_once`: 400 route iterations
- With `compute_once`: 100 route iterations (75% reduction)

**Debugging:**

Enable template tracing to verify compute_once optimization:

```go
engine.EnableTracing()
output, _ := engine.Render("main", context)
trace := engine.GetTraceOutput()

// Verify expensive computation only appears once
fmt.Println(trace)
```

**Limitations:**

- Variable must exist before `compute_once` block (the tag cannot create it)
- Only works within a single `Render()` call (cache cleared between renders)
- Not suitable for computations that should run multiple times with different inputs

## Performance

The library is designed for high performance:

- **Compilation**: Templates are compiled once at initialization (~1-10ms per template)
- **Rendering**: Pre-compiled templates render in microseconds (~10-100µs for typical templates)
- **Memory**: Compiled templates are cached in memory for zero-cost lookups
- **Concurrency**: The `TemplateEngine` is safe for concurrent use from multiple goroutines. All operations (rendering, tracing, template lookups) use proper synchronization and have been validated with Go's race detector.

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
