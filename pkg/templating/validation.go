package templating

import (
	"github.com/nikolalohinski/gonja/v2"
)

// ValidateTemplate validates template syntax without executing it.
//
// This is a generic validation function that can be used anywhere template
// validation is needed. It only checks syntax correctness and does not
// execute the template or require context variables.
//
// Parameters:
//   - templateStr: The template string to validate
//   - engineType: The template engine to use (currently only EngineTypeGonja is supported)
//
// Returns:
//   - An error if the template syntax is invalid or engine is unsupported
//   - nil if the template is valid
//
// Example:
//
//	err := templating.ValidateTemplate(templateStr, templating.EngineTypeGonja)
//	if err != nil {
//	    log.Printf("Invalid template: %v", err)
//	}
func ValidateTemplate(templateStr string, engineType EngineType) error {
	// Validate engine type
	if engineType != EngineTypeGonja {
		return NewUnsupportedEngineError(engineType)
	}

	// Attempt to compile the template (validation-only, no execution)
	_, err := gonja.FromString(templateStr)
	if err != nil {
		// Use a generic name for validation-only compilation errors
		return NewCompilationError("template", templateStr, err)
	}

	return nil
}
