// Copyright 2025 Philipp Hossner
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package templating

import (
	"fmt"
	"reflect"
	"sort"
	"strings"
	"time"

	"github.com/nikolalohinski/gonja/v2/builtins"
	"github.com/nikolalohinski/gonja/v2/config"
	"github.com/nikolalohinski/gonja/v2/exec"
)

// FilterFunc is a custom filter function that can be registered with the template engine.
// It receives the input value and optional arguments, and returns the filtered value or an error.
//
// Example:
//
//	func uppercase(in interface{}, args ...interface{}) (interface{}, error) {
//	    str, ok := in.(string)
//	    if !ok {
//	        return nil, fmt.Errorf("uppercase: expected string, got %T", in)
//	    }
//	    return strings.ToUpper(str), nil
//	}
type FilterFunc func(in interface{}, args ...interface{}) (interface{}, error)

// GlobalFunc is a custom global function that can be called from templates.
// It receives variadic arguments and returns a result or an error.
//
// Example:
//
//	func fail(args ...interface{}) (interface{}, error) {
//	    if len(args) != 1 {
//	        return nil, fmt.Errorf("fail() requires exactly one string argument")
//	    }
//	    message, ok := args[0].(string)
//	    if !ok {
//	        return nil, fmt.Errorf("fail() argument must be a string")
//	    }
//	    return nil, fmt.Errorf(message)
//	}
type GlobalFunc func(args ...interface{}) (interface{}, error)

// TemplateEngine provides template compilation and rendering capabilities.
// It pre-compiles all templates at initialization for optimal runtime performance
// and early detection of syntax errors.
type TemplateEngine struct {
	// engineType is the template engine used for rendering
	engineType EngineType

	// rawTemplates stores the original template strings by name
	rawTemplates map[string]string

	// compiledTemplates stores pre-compiled templates by name
	compiledTemplates map[string]*exec.Template

	// tracing controls template execution tracing
	tracing *tracingConfig
}

// tracingConfig holds template tracing configuration.
type tracingConfig struct {
	enabled bool
	depth   int // Current nesting depth for indentation
	builder *strings.Builder
}

// testInFixed implements a fixed "in" test that compares string values for lists.
//
// This fixes a Gonja limitation where the built-in "in" test uses Go's interface{} equality,
// which compares object identity rather than values. Each template expression with the ~
// concatenation operator creates a NEW *exec.Value object, so even identical string values
// fail equality checks.
//
// For lists/arrays: Iterates and compares using String() method (value comparison).
// For other types: Delegates to Contains() which works correctly for maps and strings.
func testInFixed(ctx *exec.Context, in *exec.Value, params *exec.VarArgs) (bool, error) {
	seq := params.First()

	// Use getResolvedValue() helper to properly dereference pointers
	// This mirrors the logic in Value.Contains()
	resolved := seq.Val
	if resolved.IsValid() && resolved.Kind() == reflect.Ptr {
		resolved = resolved.Elem()
	}

	// For lists/arrays: compare using String() method (value comparison)
	if resolved.Kind() == reflect.Slice || resolved.Kind() == reflect.Array {
		inStr := in.String()
		for i := 0; i < resolved.Len(); i++ {
			// Get item from list and wrap in Value
			item := exec.ToValue(resolved.Index(i))
			itemStr := item.String()
			if inStr == itemStr {
				return true, nil
			}
		}
		return false, nil
	}

	// For other types (maps, strings): delegate to Contains() which works correctly
	return seq.Contains(in), nil
}

// New creates a new TemplateEngine with the specified engine type, templates,
// custom filters, and custom global functions.
//
// All templates are compiled during initialization. Returns an error if any
// template fails to compile or if the engine type is not supported.
//
// Custom filters and functions are optional - pass nil if not needed.
//
// The engine automatically includes a fixed "in" test that compares string values
// instead of object identity for list membership checks, solving a Gonja limitation.
//
// Example with custom filters and functions:
//
//	filters := map[string]templating.FilterFunc{
//	    "uppercase": func(in interface{}, args ...interface{}) (interface{}, error) {
//	        return strings.ToUpper(in.(string)), nil
//	    },
//	}
//	functions := map[string]templating.GlobalFunc{
//	    "fail": func(args ...interface{}) (interface{}, error) {
//	        return nil, fmt.Errorf("%v", args[0])
//	    },
//	}
//	engine, err := templating.New(templating.EngineTypeGonja, templates, filters, functions)
//	if err != nil {
//	    log.Fatal(err)
//	}
//
// Example without custom filters/functions:
//
//	engine, err := templating.New(templating.EngineTypeGonja, templates, nil, nil)
//	if err != nil {
//	    log.Fatal(err)
//	}
func New(engineType EngineType, templates map[string]string, customFilters map[string]FilterFunc, customFunctions map[string]GlobalFunc) (*TemplateEngine, error) {
	// Validate engine type
	if engineType != EngineTypeGonja {
		return nil, NewUnsupportedEngineError(engineType)
	}

	engine := &TemplateEngine{
		engineType:        engineType,
		rawTemplates:      make(map[string]string, len(templates)),
		compiledTemplates: make(map[string]*exec.Template, len(templates)),
	}

	// Create simple in-memory loader with all templates so they can reference each other
	// via {% include "template-name" %} directives (no '/' prefix required)
	loader := NewSimpleLoader(templates)

	// Create custom config with whitespace control enabled
	// TrimBlocks removes the first newline after a block (e.g., {% if %})
	// LeftStripBlocks strips leading spaces/tabs before a block
	// Note: LeftStripBlocks also sets RemoveTrailingWhiteSpaceFromLastLine on Data nodes,
	// but this can be overridden using {%+ instead of {% on specific blocks
	cfg := &config.Config{
		BlockStartString:    "{%",
		BlockEndString:      "%}",
		VariableStartString: "{{",
		VariableEndString:   "}}",
		CommentStartString:  "{#",
		CommentEndString:    "#}",
		AutoEscape:          false,
		StrictUndefined:     false,
		TrimBlocks:          true, // Remove newlines after blocks for cleaner output
		LeftStripBlocks:     true, // Strip leading spaces before blocks for proper indentation
	}

	// Create environment with default builtins (filters, tests, control structures, methods, functions)
	// Start with builtin filters and register custom filters
	filters := builtins.Filters

	// Register custom filters if provided
	if len(customFilters) > 0 {
		// Create a new filter set with built-ins
		filterMap := make(map[string]exec.FilterFunction)
		// Gonja v2 doesn't expose iteration over FilterSet, so we start fresh
		// This is acceptable since we only add custom filters on top of builtins
		for name, customFilter := range customFilters {
			// Wrap FilterFunc in Gonja's FilterFunction signature
			filterMap[name] = wrapCustomFilter(customFilter)
		}
		customFilterSet := exec.NewFilterSet(filterMap)
		// Update builtin filters with custom ones
		filters = filters.Update(customFilterSet)
	}

	// Start with builtin global functions and register custom functions
	globalFunctions := builtins.GlobalFunctions

	// Register custom global functions if provided
	if len(customFunctions) > 0 {
		// Create a new context with builtins plus custom functions
		functionMap := make(map[string]interface{})

		// Add custom functions (wrapped in Gonja's signature)
		for name, customFunc := range customFunctions {
			functionMap[name] = wrapGlobalFunction(customFunc)
		}

		customFunctionContext := exec.NewContext(functionMap)
		// Update builtin functions with custom ones
		globalFunctions = globalFunctions.Update(customFunctionContext)
	}

	// Always override the "in" test with our fixed version
	// This fixes a Gonja limitation where list membership checks use object identity
	// instead of value comparison for computed template expressions
	testMap := map[string]exec.TestFunction{
		"in": testInFixed,
	}
	customTestSet := exec.NewTestSet(testMap)
	tests := builtins.Tests.Update(customTestSet)

	customMethods := createCustomMethods()

	environment := &exec.Environment{
		Filters:           filters,
		Tests:             tests, // Use tests with fixed "in" operator
		ControlStructures: builtins.ControlStructures,
		Methods:           customMethods, // Use custom methods with fixed append()
		Context:           globalFunctions,
	}

	// Store raw templates and compile each one through the loader
	for name, content := range templates {
		engine.rawTemplates[name] = content

		// Compile the template with custom config for proper whitespace handling
		compiled, err := exec.NewTemplate(name, cfg, loader, environment)
		if err != nil {
			return nil, NewCompilationError(name, content, err)
		}

		engine.compiledTemplates[name] = compiled
	}

	return engine, nil
}

// createCustomMethods creates custom method sets for list and dict types with fixed behavior.
func createCustomMethods() exec.Methods {
	return exec.Methods{
		Bool:  builtins.Methods.Bool,
		Str:   builtins.Methods.Str,
		Int:   builtins.Methods.Int,
		Float: builtins.Methods.Float,
		Dict:  createCustomDictMethods(),
		List:  createCustomListMethods(),
	}
}

// createCustomListMethods creates custom list method set with fixed append() that returns modified list.
func createCustomListMethods() *exec.MethodSet[[]interface{}] {
	return exec.NewMethodSet[[]interface{}](map[string]exec.Method[[]interface{}]{
		"append": func(_ []interface{}, selfValue *exec.Value, arguments *exec.VarArgs) (interface{}, error) {
			var x interface{}
			if err := arguments.Take(
				exec.PositionalArgument("x", nil, exec.AnyArgument(&x)),
			); err != nil {
				return nil, exec.ErrInvalidCall(err)
			}

			// Modify list in-place (same as builtin)
			*selfValue = *exec.ToValue(reflect.Append(selfValue.Val, reflect.ValueOf(exec.ToValue(x))))

			// RETURN the modified list instead of nil (our fix)
			return selfValue.Interface(), nil
		},

		// Copy other builtin list methods unchanged from Gonja
		"reverse": func(_ []interface{}, selfValue *exec.Value, arguments *exec.VarArgs) (interface{}, error) {
			if err := arguments.Take(); err != nil {
				return nil, exec.ErrInvalidCall(err)
			}
			reversed := reflect.MakeSlice(selfValue.Val.Type(), 0, 0)
			for i := selfValue.Val.Len() - 1; i >= 0; i-- {
				reversed = reflect.Append(reversed, selfValue.Val.Index(i))
			}
			for i := 0; i < selfValue.Val.Len(); i++ {
				selfValue.Val.Index(i).Set(reversed.Index(i))
			}
			return selfValue.Interface(), nil
		},

		"copy": func(self []interface{}, selfValue *exec.Value, arguments *exec.VarArgs) (interface{}, error) {
			if err := arguments.Take(); err != nil {
				return nil, exec.ErrInvalidCall(err)
			}
			return self, nil
		},
	})
}

// createCustomDictMethods creates custom dict method set with fixed update() that returns modified dict.
func createCustomDictMethods() *exec.MethodSet[map[string]interface{}] {
	return exec.NewMethodSet[map[string]interface{}](map[string]exec.Method[map[string]interface{}]{
		// Copy builtin dict methods unchanged from Gonja
		"keys": func(self map[string]interface{}, selfValue *exec.Value, arguments *exec.VarArgs) (interface{}, error) {
			if err := arguments.Take(); err != nil {
				return nil, exec.ErrInvalidCall(err)
			}
			keys := make([]string, 0)
			for key := range self {
				keys = append(keys, key)
			}
			sort.Strings(keys)
			return keys, nil
		},

		"items": func(self map[string]interface{}, selfValue *exec.Value, arguments *exec.VarArgs) (interface{}, error) {
			if err := arguments.Take(); err != nil {
				return nil, exec.ErrInvalidCall(err)
			}
			items := make([]interface{}, 0)
			for _, item := range self {
				items = append(items, item)
			}
			return items, nil
		},

		// Custom update() method that returns the modified dict
		"update": func(self map[string]interface{}, selfValue *exec.Value, arguments *exec.VarArgs) (interface{}, error) {
			var otherAny interface{}
			if err := arguments.Take(
				exec.PositionalArgument("other", nil, exec.AnyArgument(&otherAny)),
			); err != nil {
				return nil, exec.ErrInvalidCall(err)
			}

			// Handle both map[string]interface{} and *exec.Dict
			var pairs map[string]interface{}

			switch v := otherAny.(type) {
			case map[string]interface{}:
				pairs = v
			case *exec.Dict:
				// Convert *exec.Dict to map[string]interface{}
				pairs = make(map[string]interface{})
				for _, pair := range v.Pairs {
					pairs[pair.Key.String()] = pair.Value.Interface()
				}
			default:
				return nil, fmt.Errorf("update() expects a dict, got %T", otherAny)
			}

			// Update dict in-place
			for k, v := range pairs {
				self[k] = v
			}

			// RETURN the modified dict instead of nil (our fix)
			return self, nil
		},
	})
}

// Render executes the named template with the provided context and returns the
// rendered output. Returns an error if the template does not exist or if
// rendering fails.
//
// Example:
//
//	context := map[string]interface{}{
//	    "name": "World",
//	}
//	output, err := engine.Render("greeting", context)
//	if err != nil {
//	    log.Fatal(err)
//	}
//	fmt.Println(output) // Output: Hello World!
func (e *TemplateEngine) Render(templateName string, context map[string]interface{}) (string, error) {
	// Tracing: log render start
	if e.tracing != nil && e.tracing.enabled {
		e.tracef("Rendering: %s", templateName)
		e.tracing.depth++
		startTime := time.Now()
		defer func() {
			duration := time.Since(startTime)
			e.tracing.depth--
			e.tracef("Completed: %s (%.3fms)", templateName, float64(duration.Microseconds())/1000.0)
		}()
	}

	// Look up the compiled template
	template, exists := e.compiledTemplates[templateName]
	if !exists {
		// Collect available template names for the error message
		availableNames := make([]string, 0, len(e.compiledTemplates))
		for name := range e.compiledTemplates {
			availableNames = append(availableNames, name)
		}
		return "", NewTemplateNotFoundError(templateName, availableNames)
	}

	// Execute the template with the provided context
	ctx := exec.NewContext(context)
	output, err := template.ExecuteToString(ctx)
	if err != nil {
		return "", NewRenderError(templateName, err)
	}

	return output, nil
}

// EngineType returns the template engine type used by this instance.
func (e *TemplateEngine) EngineType() EngineType {
	return e.engineType
}

// TemplateNames returns a list of all available template names.
func (e *TemplateEngine) TemplateNames() []string {
	names := make([]string, 0, len(e.rawTemplates))
	for name := range e.rawTemplates {
		names = append(names, name)
	}
	return names
}

// HasTemplate returns true if a template with the given name exists.
func (e *TemplateEngine) HasTemplate(templateName string) bool {
	_, exists := e.compiledTemplates[templateName]
	return exists
}

// GetRawTemplate returns the original (uncompiled) template string for the given name.
// Returns an error if the template does not exist.
func (e *TemplateEngine) GetRawTemplate(templateName string) (string, error) {
	template, exists := e.rawTemplates[templateName]
	if !exists {
		availableNames := make([]string, 0, len(e.rawTemplates))
		for name := range e.rawTemplates {
			availableNames = append(availableNames, name)
		}
		return "", NewTemplateNotFoundError(templateName, availableNames)
	}
	return template, nil
}

// TemplateCount returns the number of templates in this engine.
func (e *TemplateEngine) TemplateCount() int {
	return len(e.compiledTemplates)
}

// String returns a string representation of the engine for debugging.
func (e *TemplateEngine) String() string {
	return fmt.Sprintf("TemplateEngine{type=%s, templates=%d}", e.engineType, e.TemplateCount())
}

// wrapCustomFilter wraps a FilterFunc into Gonja's FilterFunction signature.
// This adapter converts between our simple FilterFunc interface and Gonja's
// more complex signature that includes the evaluator and typed values.
func wrapCustomFilter(customFilter FilterFunc) exec.FilterFunction {
	return func(e *exec.Evaluator, in *exec.Value, params *exec.VarArgs) *exec.Value {
		// Extract the input value as Go interface{}
		inputValue := in.Interface()

		// Extract arguments from VarArgs as interface{} slice
		var args []interface{}
		if params != nil && len(params.Args) > 0 {
			// Get all positional arguments from Args slice
			for _, arg := range params.Args {
				args = append(args, arg.Interface())
			}
		}

		// Call the custom filter
		result, err := customFilter(inputValue, args...)
		if err != nil {
			// Return error wrapped in Value
			return exec.AsValue(err)
		}

		// Return result as Value
		return exec.AsValue(result)
	}
}

// wrapGlobalFunction wraps a GlobalFunc into a function callable from Gonja templates.
// This adapter converts between our simple GlobalFunc interface and the signature
// expected by Gonja's global function system.
func wrapGlobalFunction(customFunc GlobalFunc) func(_ *exec.Evaluator, params *exec.VarArgs) *exec.Value {
	return func(_ *exec.Evaluator, params *exec.VarArgs) *exec.Value {
		// Extract arguments from VarArgs as interface{} slice
		var args []interface{}
		if params != nil && len(params.Args) > 0 {
			for _, arg := range params.Args {
				args = append(args, arg.Interface())
			}
		}

		// Call the custom global function
		result, err := customFunc(args...)
		if err != nil {
			// Return error wrapped in Value using ErrInvalidCall
			// This will cause template rendering to fail with the error message
			return exec.AsValue(exec.ErrInvalidCall(err))
		}

		// Return result as Value
		return exec.AsValue(result)
	}
}

// EnableTracing enables template execution tracing.
// Trace output can be retrieved with GetTraceOutput().
func (e *TemplateEngine) EnableTracing() {
	if e.tracing == nil {
		e.tracing = &tracingConfig{
			enabled: true,
			depth:   0,
			builder: &strings.Builder{},
		}
	} else {
		e.tracing.enabled = true
		e.tracing.depth = 0
		e.tracing.builder.Reset()
	}
}

// DisableTracing disables template execution tracing.
func (e *TemplateEngine) DisableTracing() {
	if e.tracing != nil {
		e.tracing.enabled = false
	}
}

// GetTraceOutput returns the accumulated trace output and resets the trace buffer.
func (e *TemplateEngine) GetTraceOutput() string {
	if e.tracing == nil || e.tracing.builder == nil {
		return ""
	}

	output := e.tracing.builder.String()
	e.tracing.builder.Reset()
	return output
}

// trace logs a trace message with proper indentation based on nesting depth.
func (e *TemplateEngine) tracef(format string, args ...interface{}) {
	if e.tracing == nil || !e.tracing.enabled {
		return
	}

	// Create indentation based on depth
	indent := strings.Repeat("  ", e.tracing.depth)

	// Format and write the trace message
	msg := fmt.Sprintf(format, args...)
	fmt.Fprintf(e.tracing.builder, "%s%s\n", indent, msg)
}
