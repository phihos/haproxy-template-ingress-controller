package templating

import "fmt"

// CompilationError represents a template compilation failure.
// This error occurs during template initialization when the template
// syntax is invalid or contains unsupported constructs.
type CompilationError struct {
	// TemplateName is the name of the template that failed to compile
	TemplateName string

	// TemplateSnippet contains the first 200 characters of the template
	TemplateSnippet string

	// Cause is the underlying compilation error from the template engine
	Cause error
}

// Error implements the error interface.
func (e *CompilationError) Error() string {
	return fmt.Sprintf("failed to compile template '%s': %v", e.TemplateName, e.Cause)
}

// Unwrap returns the underlying cause for error unwrapping.
func (e *CompilationError) Unwrap() error {
	return e.Cause
}

// RenderError represents a template rendering failure.
// This error occurs when a valid template fails during execution,
// typically due to missing context variables or runtime evaluation errors.
type RenderError struct {
	// TemplateName is the name of the template that failed to render
	TemplateName string

	// Cause is the underlying rendering error from the template engine
	Cause error
}

// Error implements the error interface.
func (e *RenderError) Error() string {
	return fmt.Sprintf("failed to render template '%s': %v", e.TemplateName, e.Cause)
}

// Unwrap returns the underlying cause for error unwrapping.
func (e *RenderError) Unwrap() error {
	return e.Cause
}

// TemplateNotFoundError represents a request for a non-existent template.
type TemplateNotFoundError struct {
	// TemplateName is the name of the requested template
	TemplateName string

	// AvailableTemplates lists all available template names
	AvailableTemplates []string
}

// Error implements the error interface.
func (e *TemplateNotFoundError) Error() string {
	return fmt.Sprintf("template '%s' not found", e.TemplateName)
}

// UnsupportedEngineError represents an unsupported template engine type.
type UnsupportedEngineError struct {
	// EngineType is the unsupported engine type
	EngineType EngineType
}

// Error implements the error interface.
func (e *UnsupportedEngineError) Error() string {
	return fmt.Sprintf("unsupported template engine type: %s", e.EngineType)
}

// Helper functions for creating errors with actionable context

// NewCompilationError creates a CompilationError for a template compilation failure.
func NewCompilationError(templateName, templateContent string, cause error) *CompilationError {
	snippet := templateContent
	if len(snippet) > 200 {
		snippet = snippet[:200] + "..."
	}

	return &CompilationError{
		TemplateName:    templateName,
		TemplateSnippet: snippet,
		Cause:           cause,
	}
}

// NewRenderError creates a RenderError for a template rendering failure.
func NewRenderError(templateName string, cause error) *RenderError {
	return &RenderError{
		TemplateName: templateName,
		Cause:        cause,
	}
}

// NewTemplateNotFoundError creates a TemplateNotFoundError with the list of available templates.
func NewTemplateNotFoundError(templateName string, availableTemplates []string) *TemplateNotFoundError {
	return &TemplateNotFoundError{
		TemplateName:       templateName,
		AvailableTemplates: availableTemplates,
	}
}

// NewUnsupportedEngineError creates an UnsupportedEngineError for an invalid engine type.
func NewUnsupportedEngineError(engineType EngineType) *UnsupportedEngineError {
	return &UnsupportedEngineError{
		EngineType: engineType,
	}
}
