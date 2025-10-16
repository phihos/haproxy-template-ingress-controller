package templating

import (
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNew_Success(t *testing.T) {
	templates := map[string]string{
		"greeting": "Hello {{ name }}!",
		"farewell": "Goodbye {{ name }}!",
	}

	engine, err := New(EngineTypeGonja, templates)
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
	engine, err := New(invalidEngine, templates)

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

	engine, err := New(EngineTypeGonja, templates)

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

	engine, err := New(EngineTypeGonja, templates)
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

	engine, err := New(EngineTypeGonja, templates)
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

	engine, err := New(EngineTypeGonja, templates)
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

	engine, err := New(EngineTypeGonja, templates)
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

	engine, err := New(EngineTypeGonja, templates)
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

	engine, err := New(EngineTypeGonja, templates)
	require.NoError(t, err)

	assert.True(t, engine.HasTemplate("existing"))
	assert.False(t, engine.HasTemplate("nonexistent"))
}

func TestString(t *testing.T) {
	templates := map[string]string{
		"template1": "Content 1",
		"template2": "Content 2",
	}

	engine, err := New(EngineTypeGonja, templates)
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
		"with_loop":   `{% for item in items %}{{ item }}{% if not loop.last %}, {% endif %}{% endfor %}`,
		"with_if":     `{% if count > 5 %}Many{% else %}Few{% endif %}`,
		"with_filter": `{{ text | upper }}`,
	}

	engine, err := New(EngineTypeGonja, templates)
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

	engine, err := New(EngineTypeGonja, templates)
	require.NoError(t, err)
	require.NotNil(t, engine)

	assert.Equal(t, 0, engine.TemplateCount())
	assert.Empty(t, engine.TemplateNames())
}
