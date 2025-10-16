// Package templating provides template rendering capabilities with support for
// multiple templating engines.
//
// This package offers a unified interface for compiling and rendering templates
// using different template engines. Currently supports:
// - Gonja (Jinja2-like templating for Go)
//
// The package pre-compiles all templates at initialization for optimal runtime
// performance and early detection of syntax errors.
package templating

// EngineType represents the template engine to use for rendering.
type EngineType int

const (
	// EngineTypeGonja uses the Gonja template engine (Jinja2-like syntax).
	// This is the recommended engine for HAProxy configuration templating
	// due to its rich feature set and familiar syntax.
	EngineTypeGonja EngineType = iota
)

// String returns the string representation of the engine type.
func (e EngineType) String() string {
	switch e {
	case EngineTypeGonja:
		return "gonja"
	default:
		return "unknown"
	}
}
