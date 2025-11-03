package templating

import (
	"fmt"
	"strings"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNew_Success(t *testing.T) {
	templates := map[string]string{
		"greeting": "Hello {{ name }}!",
		"farewell": "Goodbye {{ name }}!",
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)
	require.NotNil(t, engine)

	assert.Equal(t, EngineTypeGonja, engine.EngineType())
	assert.Equal(t, 2, engine.TemplateCount())
	assert.True(t, engine.HasTemplate("greeting"))
	assert.True(t, engine.HasTemplate("farewell"))
	assert.False(t, engine.HasTemplate("nonexistent"))
}

func TestNew_UnsupportedEngine(t *testing.T) {
	templates := map[string]string{
		"test": "Hello {{ name }}",
	}

	// Use an invalid engine type
	invalidEngine := EngineType(999)
	engine, err := New(invalidEngine, templates, nil, nil)

	assert.Nil(t, engine)
	require.Error(t, err)

	var unsupportedErr *UnsupportedEngineError
	assert.ErrorAs(t, err, &unsupportedErr)
	assert.Equal(t, invalidEngine, unsupportedErr.EngineType)
}

func TestNew_CompilationError(t *testing.T) {
	templates := map[string]string{
		"valid":   "Hello {{ name }}",
		"invalid": "Hello {{ name",
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)

	assert.Nil(t, engine)
	require.Error(t, err)

	var compilationErr *CompilationError
	assert.ErrorAs(t, err, &compilationErr)
	assert.Equal(t, "invalid", compilationErr.TemplateName)
}

func TestRender_Success(t *testing.T) {
	templates := map[string]string{
		"greeting": "Hello {{ name }}!",
		"info":     "Name: {{ user.name }}, Age: {{ user.age }}",
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	// Test simple rendering
	output, err := engine.Render("greeting", map[string]interface{}{
		"name": "World",
	})
	require.NoError(t, err)
	assert.Equal(t, "Hello World!", output)

	// Test nested context
	output, err = engine.Render("info", map[string]interface{}{
		"user": map[string]interface{}{
			"name": "Alice",
			"age":  30,
		},
	})
	require.NoError(t, err)
	assert.Equal(t, "Name: Alice, Age: 30", output)
}

func TestRender_TemplateNotFound(t *testing.T) {
	templates := map[string]string{
		"greeting": "Hello {{ name }}!",
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	output, err := engine.Render("nonexistent", map[string]interface{}{})

	assert.Empty(t, output)
	require.Error(t, err)

	var notFoundErr *TemplateNotFoundError
	assert.ErrorAs(t, err, &notFoundErr)
	assert.Equal(t, "nonexistent", notFoundErr.TemplateName)
	assert.Contains(t, notFoundErr.AvailableTemplates, "greeting")
}

func TestRender_RenderError(t *testing.T) {
	templates := map[string]string{
		// Template with undefined filter (will cause runtime error in gonja)
		"with_error": "{{ value | undefined_filter }}",
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	output, err := engine.Render("with_error", map[string]interface{}{
		"value": "test",
	})

	assert.Empty(t, output)
	require.Error(t, err)

	var renderErr *RenderError
	assert.ErrorAs(t, err, &renderErr)
	assert.Equal(t, "with_error", renderErr.TemplateName)
}

func TestTemplateNames(t *testing.T) {
	templates := map[string]string{
		"template1": "Content 1",
		"template2": "Content 2",
		"template3": "Content 3",
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	names := engine.TemplateNames()
	assert.Len(t, names, 3)
	assert.Contains(t, names, "template1")
	assert.Contains(t, names, "template2")
	assert.Contains(t, names, "template3")
}

func TestGetRawTemplate(t *testing.T) {
	templateContent := "Hello {{ name }}!"
	templates := map[string]string{
		"greeting": templateContent,
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	// Test existing template
	raw, err := engine.GetRawTemplate("greeting")
	require.NoError(t, err)
	assert.Equal(t, templateContent, raw)

	// Test non-existent template
	raw, err = engine.GetRawTemplate("nonexistent")
	assert.Empty(t, raw)
	require.Error(t, err)

	var notFoundErr *TemplateNotFoundError
	assert.ErrorAs(t, err, &notFoundErr)
}

func TestHasTemplate(t *testing.T) {
	templates := map[string]string{
		"existing": "Content",
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	assert.True(t, engine.HasTemplate("existing"))
	assert.False(t, engine.HasTemplate("nonexistent"))
}

func TestString(t *testing.T) {
	templates := map[string]string{
		"template1": "Content 1",
		"template2": "Content 2",
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	str := engine.String()
	assert.Contains(t, str, "TemplateEngine")
	assert.Contains(t, str, "gonja")
	assert.Contains(t, str, "templates=2")
}

func TestEngineType_String(t *testing.T) {
	tests := []struct {
		name       string
		engineType EngineType
		expected   string
	}{
		{
			name:       "Gonja engine",
			engineType: EngineTypeGonja,
			expected:   "gonja",
		},
		{
			name:       "Unknown engine",
			engineType: EngineType(999),
			expected:   "unknown",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			assert.Equal(t, tt.expected, tt.engineType.String())
		})
	}
}

func TestCompilationError_ErrorMessage(t *testing.T) {
	err := NewCompilationError("test-template", "template content here", assert.AnError)

	assert.Contains(t, err.Error(), "test-template")
	assert.Contains(t, err.Error(), "compile")
}

func TestCompilationError_SnippetTruncation(t *testing.T) {
	longContent := strings.Repeat("a", 300)
	err := NewCompilationError("test", longContent, assert.AnError)

	assert.Len(t, err.TemplateSnippet, 203) // 200 + "..."
	assert.True(t, strings.HasSuffix(err.TemplateSnippet, "..."))
}

func TestRenderError_ErrorMessage(t *testing.T) {
	err := NewRenderError("test-template", assert.AnError)

	assert.Contains(t, err.Error(), "test-template")
	assert.Contains(t, err.Error(), "render")
}

func TestTemplateNotFoundError_ErrorMessage(t *testing.T) {
	err := NewTemplateNotFoundError("missing", []string{"template1", "template2"})

	assert.Contains(t, err.Error(), "missing")
	assert.Contains(t, err.Error(), "not found")
	assert.Equal(t, []string{"template1", "template2"}, err.AvailableTemplates)
}

func TestGonja_ComplexFeatures(t *testing.T) {
	templates := map[string]string{
		"with_loop":   `{%+ for item in items +%}{{ item }}{%+ if not loop.last +%}, {%+ endif +%}{%+ endfor +%}`,
		"with_if":     `{% if count > 5 %}Many{% else %}Few{% endif %}`,
		"with_filter": `{{ text | upper }}`,
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	// Test loop
	output, err := engine.Render("with_loop", map[string]interface{}{
		"items": []string{"a", "b", "c"},
	})
	require.NoError(t, err)
	assert.Equal(t, "a, b, c", output)

	// Test conditional
	output, err = engine.Render("with_if", map[string]interface{}{
		"count": 10,
	})
	require.NoError(t, err)
	assert.Equal(t, "Many", output)

	// Test filter
	output, err = engine.Render("with_filter", map[string]interface{}{
		"text": "hello",
	})
	require.NoError(t, err)
	assert.Equal(t, "HELLO", output)
}

func TestNew_EmptyTemplates(t *testing.T) {
	templates := map[string]string{}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)
	require.NotNil(t, engine)

	assert.Equal(t, 0, engine.TemplateCount())
	assert.Empty(t, engine.TemplateNames())
}

func TestTemplateIncludes(t *testing.T) {
	tests := []struct {
		name      string
		templates map[string]string
		render    string
		context   map[string]interface{}
		want      string
		wantErr   bool
	}{
		{
			name: "simple include",
			templates: map[string]string{
				"header": "Header: {{ title }}",
				"footer": "Footer text",
				"main":   `{%+ include "header" +%}` + "\nBody\n" + `{%+ include "footer" +%}`,
			},
			render:  "main",
			context: map[string]interface{}{"title": "Test"},
			want:    "Header: Test\nBody\nFooter text",
		},
		{
			name: "nested includes",
			templates: map[string]string{
				"base":   "{{ content }}",
				"middle": `Start-{% include "base" %}-End`,
				"top":    `Outer({% include "middle" %})`,
			},
			render:  "top",
			context: map[string]interface{}{"content": "INNER"},
			want:    "Outer(Start-INNER-End)",
		},
		{
			name: "include with loop",
			templates: map[string]string{
				"item": "- {{ name }}\n",
				"list": `Items:` + "\n" + `{% for i in items %}{% set name = i.name %}{% include "item" %}{% endfor %}`,
			},
			render: "list",
			context: map[string]interface{}{
				"items": []map[string]interface{}{
					{"name": "First"},
					{"name": "Second"},
				},
			},
			want: "Items:\n- First\n- Second\n",
		},
		{
			name: "include non-existent template",
			templates: map[string]string{
				"main": `{% include "missing" %}`,
			},
			render:  "main",
			context: map[string]interface{}{},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			engine, err := New(EngineTypeGonja, tt.templates, nil, nil)
			require.NoError(t, err)

			output, err := engine.Render(tt.render, tt.context)

			if tt.wantErr {
				require.Error(t, err)
				return
			}

			require.NoError(t, err)
			assert.Equal(t, tt.want, output)
		})
	}
}

func TestNewWithFilters_GetPathFilter(t *testing.T) {
	tests := []struct {
		name      string
		template  string
		context   map[string]interface{}
		want      string
		wantErr   bool
		errString string
	}{
		{
			name:     "map file path",
			template: `{{ "host.map" | get_path("map") }}`,
			context:  map[string]interface{}{},
			want:     "/etc/haproxy/maps/host.map",
		},
		{
			name:     "general file path",
			template: `{{ "504.http" | get_path("file") }}`,
			context:  map[string]interface{}{},
			want:     "/etc/haproxy/general/504.http",
		},
		{
			name:     "SSL certificate path",
			template: `{{ "example.com.pem" | get_path("cert") }}`,
			context:  map[string]interface{}{},
			want:     "/etc/haproxy/ssl/example.com.pem",
		},
		{
			name:     "map file from variable",
			template: `{{ filename | get_path("map") }}`,
			context: map[string]interface{}{
				"filename": "backend.map",
			},
			want: "/etc/haproxy/maps/backend.map",
		},
		{
			name:     "dynamic file type",
			template: `{{ filename | get_path(filetype) }}`,
			context: map[string]interface{}{
				"filename": "error.http",
				"filetype": "file",
			},
			want: "/etc/haproxy/general/error.http",
		},
		{
			name:      "missing file type argument",
			template:  `{{ "test.map" | get_path }}`,
			context:   map[string]interface{}{},
			wantErr:   true,
			errString: "file type argument required",
		},
		{
			name:      "invalid file type",
			template:  `{{ "test.txt" | get_path("invalid") }}`,
			context:   map[string]interface{}{},
			wantErr:   true,
			errString: "invalid file type",
		},
	}

	// Create path resolver with test paths
	pathResolver := &PathResolver{
		MapsDir:    "/etc/haproxy/maps",
		SSLDir:     "/etc/haproxy/ssl",
		GeneralDir: "/etc/haproxy/general",
	}

	// Register custom filter
	filters := map[string]FilterFunc{
		"get_path": pathResolver.GetPath,
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			templates := map[string]string{
				"test": tt.template,
			}

			engine, err := New(EngineTypeGonja, templates, filters, nil)
			require.NoError(t, err)

			output, err := engine.Render("test", tt.context)

			if tt.wantErr {
				require.Error(t, err)
				if tt.errString != "" {
					assert.Contains(t, err.Error(), tt.errString)
				}
				return
			}

			require.NoError(t, err)
			assert.Equal(t, tt.want, output)
		})
	}
}

func TestNewWithFilters_CustomPathsConfiguration(t *testing.T) {
	// Test with custom directory paths
	pathResolver := &PathResolver{
		MapsDir:    "/custom/maps",
		SSLDir:     "/custom/certs",
		GeneralDir: "/custom/files",
	}

	filters := map[string]FilterFunc{
		"get_path": pathResolver.GetPath,
	}

	templates := map[string]string{
		"test": `{{ "test.map" | get_path("map") }}`,
	}

	engine, err := New(EngineTypeGonja, templates, filters, nil)
	require.NoError(t, err)

	output, err := engine.Render("test", nil)
	require.NoError(t, err)
	assert.Equal(t, "/custom/maps/test.map", output)
}

func TestNewWithFilters_MultipleFilters(t *testing.T) {
	// Test registering multiple custom filters
	pathResolver := &PathResolver{
		MapsDir:    "/etc/haproxy/maps",
		SSLDir:     "/etc/haproxy/ssl",
		GeneralDir: "/etc/haproxy/general",
	}

	// Custom uppercase filter for testing
	uppercaseFilter := func(in interface{}, args ...interface{}) (interface{}, error) {
		str, ok := in.(string)
		if !ok {
			return nil, assert.AnError
		}
		return strings.ToUpper(str), nil
	}

	filters := map[string]FilterFunc{
		"get_path":  pathResolver.GetPath,
		"uppercase": uppercaseFilter,
	}

	templates := map[string]string{
		"test": `{{ filename | uppercase | get_path("map") }}`,
	}

	engine, err := New(EngineTypeGonja, templates, filters, nil)
	require.NoError(t, err)

	output, err := engine.Render("test", map[string]interface{}{
		"filename": "host.map",
	})
	require.NoError(t, err)
	assert.Equal(t, "/etc/haproxy/maps/HOST.MAP", output)
}

func TestNewWithFilters_NilFilters(t *testing.T) {
	// Test that nil filters works (same as New())
	templates := map[string]string{
		"test": "Hello {{ name }}",
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	output, err := engine.Render("test", map[string]interface{}{
		"name": "World",
	})
	require.NoError(t, err)
	assert.Equal(t, "Hello World", output)
}

// ============================================================================
// compute_once tag tests
// ============================================================================

func TestComputeOnce_ExecutesOnlyOnce(t *testing.T) {
	// This test verifies that compute_once executes the body only once,
	// even when the template is included multiple times
	templates := map[string]string{
		"main": `
{%- set counter = namespace(value=0) %}
{%- include "use_counter" -%}
{%- include "use_counter" -%}
{%- include "use_counter" -%}
Result: {{ counter.value }}`,
		"use_counter": `
{%- compute_once counter %}
  {%- set counter.value = counter.value + 1 %}
{%- endcompute_once -%}`,
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	output, err := engine.Render("main", nil)
	require.NoError(t, err)

	// If compute_once works correctly, counter.value should be 1
	// If it executed 3 times, counter.value would be 3
	assert.Contains(t, output, "Result: 1")
}

func TestComputeOnce_SharesResultAcrossTemplates(t *testing.T) {
	// This test verifies that the result is available across different template includes
	templates := map[string]string{
		"main": `
{%- set data = namespace(value="", count=0) %}
{%- include "compute" -%}
{%- include "compute" -%}
{%- include "use_result" -%}`,
		"compute": `
{%- compute_once data %}
  {%- set data.value = "computed" %}
  {%- set data.count = 42 %}
{%- endcompute_once -%}`,
		"use_result": `
Value: {{ data.value }}, Count: {{ data.count }}`,
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	output, err := engine.Render("main", nil)
	require.NoError(t, err)

	assert.Contains(t, output, "Value: computed")
	assert.Contains(t, output, "Count: 42")
}

func TestComputeOnce_RequiresResultVariable(t *testing.T) {
	// This test verifies that an error is returned if the variable doesn't exist before compute_once
	templates := map[string]string{
		"main": `
{%- compute_once data %}
  {%- set data = "value" %}
{%- endcompute_once -%}`,
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	_, err = engine.Render("main", nil)
	require.Error(t, err)
	assert.Contains(t, err.Error(), "variable 'data' must be created before compute_once block")
}

func TestComputeOnce_IsolatedBetweenRenders(t *testing.T) {
	// This test verifies that the cache is cleared between different Render() calls
	templates := map[string]string{
		"main": `
{%- set data = namespace(value="") %}
{%- compute_once data %}
  {%- set data.value = input_value %}
{%- endcompute_once -%}
Result: {{ data.value }}`,
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	// First render with input_value = "first"
	output1, err := engine.Render("main", map[string]interface{}{
		"input_value": "first",
	})
	require.NoError(t, err)
	assert.Contains(t, output1, "Result: first")

	// Second render with input_value = "second"
	// Should get "second", not "first" (proves cache was cleared)
	output2, err := engine.Render("main", map[string]interface{}{
		"input_value": "second",
	})
	require.NoError(t, err)
	assert.Contains(t, output2, "Result: second")
	assert.NotContains(t, output2, "Result: first")
}

func TestComputeOnce_ComplexComputation(t *testing.T) {
	// This test verifies that compute_once works with complex nested operations
	templates := map[string]string{
		"main": `
{%- set analysis = namespace(items=[], total=0) %}
{%- include "use_analysis" -%}
{%- include "use_analysis" -%}`,
		"use_analysis": `
{%- compute_once analysis %}
  {%- for item in input_items %}
    {%- set analysis.items = analysis.items.append(item.name) %}
    {%- set analysis.total = analysis.total + item.value %}
  {%- endfor %}
{%- endcompute_once -%}
Total: {{ analysis.total }}, Count: {{ analysis.items | length }}`,
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	output, err := engine.Render("main", map[string]interface{}{
		"input_items": []map[string]interface{}{
			{"name": "item1", "value": 10},
			{"name": "item2", "value": 20},
			{"name": "item3", "value": 30},
		},
	})
	require.NoError(t, err)

	// Both includes should show the same totals (proof it ran once)
	// Count the occurrences
	totalCount := strings.Count(output, "Total: 60")
	itemCount := strings.Count(output, "Count: 3")
	assert.Equal(t, 2, totalCount, "Should appear twice (once per include)")
	assert.Equal(t, 2, itemCount, "Should appear twice (once per include)")
}

func TestComputeOnce_WithMacro(t *testing.T) {
	// This test simulates the real-world gateway.yaml use case with a macro
	templates := map[string]string{
		"main": `
{%- set analysis = namespace(output="") %}
{%- include "snippet1" -%}
{%- include "snippet2" -%}`,
		"macros": `
{%- macro analyze(data) -%}
  {%- for item in data %}
    {{- item.name -}}
  {%- endfor %}
{%- endmacro -%}`,
		"snippet1": `
{%- compute_once analysis %}
  {%- from "macros" import analyze %}
  {%- set analysis.output = analyze(resources) %}
{%- endcompute_once -%}
Snippet1: {{ analysis.output }}`,
		"snippet2": `
{%- compute_once analysis %}
  {%- from "macros" import analyze %}
  {%- set analysis.output = analyze(resources) %}
{%- endcompute_once -%}
Snippet2: {{ analysis.output }}`,
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	output, err := engine.Render("main", map[string]interface{}{
		"resources": []map[string]interface{}{
			{"name": "route1"},
			{"name": "route2"},
		},
	})
	require.NoError(t, err)

	// Both snippets should have the same analysis output
	assert.Contains(t, output, "Snippet1: route1route2")
	assert.Contains(t, output, "Snippet2: route1route2")
}

func TestComputeOnce_SyntaxError_MissingVariableName(t *testing.T) {
	// This test verifies proper error when variable name is missing
	templates := map[string]string{
		"main": `
{%- compute_once %}
  {%- set data = "value" %}
{%- endcompute_once -%}`,
	}

	_, err := New(EngineTypeGonja, templates, nil, nil)
	require.Error(t, err)
	assert.Contains(t, err.Error(), "compute_once requires variable name")
}

func TestComputeOnce_SyntaxError_ExtraArguments(t *testing.T) {
	// This test verifies proper error when extra arguments are provided
	templates := map[string]string{
		"main": `
{%- compute_once data extra_arg %}
  {%- set data = "value" %}
{%- endcompute_once -%}`,
	}

	_, err := New(EngineTypeGonja, templates, nil, nil)
	require.Error(t, err)
	assert.Contains(t, err.Error(), "no additional arguments")
}

func TestComputeOnce_Integration_WithTracing(t *testing.T) {
	// This integration test verifies compute_once behavior and demonstrates tracing functionality
	templates := map[string]string{
		"main": `
{%- set routes = namespace(analyzed=[], count=0) %}
{%- include "frontend-1" -%}
{%- include "frontend-2" -%}
{%- include "frontend-3" -%}
Total analyzed: {{ routes.count }}`,
		"frontend-1": `
{%- include "analyze" -%}
Frontend 1 routes: {{ routes.count }}
`,
		"frontend-2": `
{%- include "analyze" -%}
Frontend 2 routes: {{ routes.count }}
`,
		"frontend-3": `
{%- include "analyze" -%}
Frontend 3 routes: {{ routes.count }}
`,
		"analyze": `
{%- compute_once routes %}
  {%- include "expensive-analysis" %}
{%- endcompute_once -%}`,
		"expensive-analysis": `
{%- for route in input_routes %}
  {%- set routes.analyzed = routes.analyzed.append(route.name) %}
  {%- set routes.count = routes.count + 1 %}
{%- endfor -%}`,
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	// Enable tracing to observe template execution
	engine.EnableTracing()

	output, err := engine.Render("main", map[string]interface{}{
		"input_routes": []map[string]interface{}{
			{"name": "route1"},
			{"name": "route2"},
			{"name": "route3"},
		},
	})
	require.NoError(t, err)

	// CRITICAL: Verify the computation ran ONCE and all frontends see the same result
	// If compute_once didn't work, count would be 9 (3 routes × 3 frontends)
	// With compute_once working, count is 3 (computed once, shared across all frontends)
	assert.Contains(t, output, "Total analyzed: 3")
	assert.Contains(t, output, "Frontend 1 routes: 3")
	assert.Contains(t, output, "Frontend 2 routes: 3")
	assert.Contains(t, output, "Frontend 3 routes: 3")

	// Verify tracing captured the main render
	trace := engine.GetTraceOutput()
	assert.Contains(t, trace, "Rendering: main")
	assert.Contains(t, trace, "Completed: main")

	// Note: Tracing only captures top-level Render() calls, not internal Gonja includes.
	// The important verification is the output above - compute_once prevented redundant
	// computation as evidenced by count=3 instead of count=9.
}

func TestComputeOnce_Integration_MultipleRenders(t *testing.T) {
	// This test demonstrates tracing across multiple independent renders
	templates := map[string]string{
		"template1": `{%- set data = namespace(value="") %}{%- compute_once data %}{%- set data.value = "template1" %}{%- endcompute_once -%}Result: {{ data.value }}`,
		"template2": `{%- set data = namespace(value="") %}{%- compute_once data %}{%- set data.value = "template2" %}{%- endcompute_once -%}Result: {{ data.value }}`,
		"template3": `{%- set data = namespace(value="") %}{%- compute_once data %}{%- set data.value = "template3" %}{%- endcompute_once -%}Result: {{ data.value }}`,
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	// Enable tracing
	engine.EnableTracing()

	// Render multiple templates
	output1, err := engine.Render("template1", nil)
	require.NoError(t, err)
	assert.Contains(t, output1, "Result: template1")

	output2, err := engine.Render("template2", nil)
	require.NoError(t, err)
	assert.Contains(t, output2, "Result: template2")

	output3, err := engine.Render("template3", nil)
	require.NoError(t, err)
	assert.Contains(t, output3, "Result: template3")

	// Get trace - should show all three renders
	trace := engine.GetTraceOutput()
	assert.Contains(t, trace, "Rendering: template1")
	assert.Contains(t, trace, "Completed: template1")
	assert.Contains(t, trace, "Rendering: template2")
	assert.Contains(t, trace, "Completed: template2")
	assert.Contains(t, trace, "Rendering: template3")
	assert.Contains(t, trace, "Completed: template3")

	// Each render should have its own compute_once cache (verified by correct output values)
	// This proves compute_once markers are cleared between renders
}

func TestTracing_ConcurrentRenders(t *testing.T) {
	// This test verifies that tracing is thread-safe when multiple goroutines
	// call Render() concurrently. Run with: go test -race
	templates := map[string]string{
		"template1": `Result: {{ value }}`,
		"template2": `Output: {{ value | upper }}`,
		"template3": `Value: {{ value | length }}`,
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	// Enable tracing
	engine.EnableTracing()

	// Run concurrent renders
	const numGoroutines = 10
	done := make(chan bool, numGoroutines)

	for i := 0; i < numGoroutines; i++ {
		go func(id int) {
			defer func() { done <- true }()

			// Each goroutine renders multiple templates
			for j := 0; j < 5; j++ {
				tmpl := fmt.Sprintf("template%d", (j%3)+1)
				context := map[string]interface{}{
					"value": fmt.Sprintf("goroutine-%d-iteration-%d", id, j),
				}

				output, err := engine.Render(tmpl, context)
				assert.NoError(t, err)
				assert.NotEmpty(t, output)
			}
		}(i)
	}

	// Wait for all goroutines to complete
	for i := 0; i < numGoroutines; i++ {
		<-done
	}

	// Get trace output (should contain entries from all renders)
	trace := engine.GetTraceOutput()
	assert.NotEmpty(t, trace)

	// Verify trace contains entries for all three templates
	assert.Contains(t, trace, "Rendering: template1")
	assert.Contains(t, trace, "Rendering: template2")
	assert.Contains(t, trace, "Rendering: template3")

	// Verify trace contains completion entries
	assert.Contains(t, trace, "Completed: template1")
	assert.Contains(t, trace, "Completed: template2")
	assert.Contains(t, trace, "Completed: template3")

	// Count total render entries (should be 50: 10 goroutines * 5 renders each)
	renderCount := strings.Count(trace, "Rendering:")
	assert.Equal(t, 50, renderCount, "Should have 50 render entries")

	completedCount := strings.Count(trace, "Completed:")
	assert.Equal(t, 50, completedCount, "Should have 50 completion entries")
}

func TestTracing_ConcurrentEnableDisable(t *testing.T) {
	// This test verifies that EnableTracing/DisableTracing are thread-safe
	// when called concurrently with Render()
	templates := map[string]string{
		"test": `Value: {{ value }}`,
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	done := make(chan bool)

	// Goroutine 1: Continuously enable/disable tracing
	go func() {
		for i := 0; i < 100; i++ {
			engine.EnableTracing()
			time.Sleep(time.Microsecond)
			engine.DisableTracing()
			time.Sleep(time.Microsecond)
		}
		done <- true
	}()

	// Goroutine 2: Continuously render templates
	go func() {
		for i := 0; i < 100; i++ {
			_, err := engine.Render("test", map[string]interface{}{
				"value": i,
			})
			assert.NoError(t, err)
			time.Sleep(time.Microsecond)
		}
		done <- true
	}()

	// Wait for both goroutines
	<-done
	<-done

	// If we get here without panics or race conditions, the test passes
}

func TestTracing_FilterOperations(t *testing.T) {
	// Test that filter operations are captured in trace output
	templates := map[string]string{
		"test": `{%- set items = [
			{"name": "low", "priority": 1},
			{"name": "high", "priority": 10},
			{"name": "medium", "priority": 5}
		] %}
{%- set sorted = items | sort_by(["priority:desc"]) %}
{%- set grouped = items | group_by("priority") %}
{%- set extracted = items | extract("name") %}`,
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	// Enable tracing
	engine.EnableTracing()

	// Render template
	_, err = engine.Render("test", nil)
	require.NoError(t, err)

	// Get trace output
	trace := engine.GetTraceOutput()

	// Verify filter operations are captured
	assert.Contains(t, trace, "Filter: sort_by")
	assert.Contains(t, trace, "priority:desc")
	assert.Contains(t, trace, "Filter: group_by")
	assert.Contains(t, trace, "priority")
	assert.Contains(t, trace, "Filter: extract")
	assert.Contains(t, trace, "name")

	// Verify trace includes item counts
	assert.Contains(t, trace, "3 items")
}

func TestFilterDebug_EnableDisable(t *testing.T) {
	// Test that filter debug can be enabled and disabled
	templates := map[string]string{
		"test": `{%- set items = [{"priority": 2}, {"priority": 1}] -%}
{%- set sorted = items | sort_by(["priority"]) -%}
sorted_count={{ sorted | length }}`,
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	// Enable filter debug
	engine.EnableFilterDebug()

	// Render should succeed (debug logging happens via slog, not in template output)
	output, err := engine.Render("test", nil)
	require.NoError(t, err)
	assert.Equal(t, "sorted_count=2", output)

	// Disable filter debug
	engine.DisableFilterDebug()

	// Rendering should still work
	output, err = engine.Render("test", nil)
	require.NoError(t, err)
	assert.Equal(t, "sorted_count=2", output)
}

func TestIsTracingEnabled(t *testing.T) {
	templates := map[string]string{
		"test": `{{ value }}`,
	}

	engine, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)

	// Initially tracing should be disabled
	assert.False(t, engine.IsTracingEnabled())

	// Enable tracing
	engine.EnableTracing()
	assert.True(t, engine.IsTracingEnabled())

	// Disable tracing
	engine.DisableTracing()
	assert.False(t, engine.IsTracingEnabled())
}

func TestAppendTraces(t *testing.T) {
	// Test that traces from one engine can be appended to another
	templates := map[string]string{
		"test1": `{{ value1 }}`,
		"test2": `{{ value2 }}`,
	}

	// Create two engines
	engine1, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)
	engine1.EnableTracing()

	engine2, err := New(EngineTypeGonja, templates, nil, nil)
	require.NoError(t, err)
	engine2.EnableTracing()

	// Render with both engines
	_, err = engine1.Render("test1", map[string]interface{}{"value1": "a"})
	require.NoError(t, err)

	_, err = engine2.Render("test2", map[string]interface{}{"value2": "b"})
	require.NoError(t, err)

	// Append engine2's traces to engine1
	engine1.AppendTraces(engine2)

	// engine1 should now have both traces
	trace := engine1.GetTraceOutput()
	assert.Contains(t, trace, "test1")
	assert.Contains(t, trace, "test2")

	// engine2's traces should have been cleared by AppendTraces (via GetTraceOutput)
	trace2 := engine2.GetTraceOutput()
	assert.Empty(t, trace2)
}
