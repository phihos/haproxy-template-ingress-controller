package validator

// Validator names used in the scatter-gather validation pattern.
//
// These constants ensure consistency between:
// - Validator responder names (in ConfigValidationResponse)
// - Expected responders list (in ConfigChangeHandler)
//
// Using constants prevents typos and silent failures where the scatter-gather
// pattern would timeout waiting for a validator that uses a different name.
const (
	// ValidatorNameBasic is the name for the basic structure validator.
	ValidatorNameBasic = "basic"

	// ValidatorNameTemplate is the name for the template syntax validator.
	ValidatorNameTemplate = "template"

	// ValidatorNameJSONPath is the name for the JSONPath expression validator.
	ValidatorNameJSONPath = "jsonpath"
)

// AllValidatorNames returns a slice of all validator names.
// Use this when registering validators in the ConfigChangeHandler.
func AllValidatorNames() []string {
	return []string{
		ValidatorNameBasic,
		ValidatorNameTemplate,
		ValidatorNameJSONPath,
	}
}
