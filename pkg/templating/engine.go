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
	"encoding/json"
	"fmt"
	"path/filepath"
	"reflect"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/nikolalohinski/gonja/v2/builtins"
	"github.com/nikolalohinski/gonja/v2/config"
	"github.com/nikolalohinski/gonja/v2/exec"
	"github.com/nikolalohinski/gonja/v2/nodes"
	"github.com/nikolalohinski/gonja/v2/parser"
	"github.com/nikolalohinski/gonja/v2/tokens"
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
// Per-render trace state (depth, builder) is stored in the execution context to ensure thread-safety.
type tracingConfig struct {
	enabled bool
	mu      sync.Mutex
	traces  []string // Accumulated trace outputs from all renders
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
		tracing: &tracingConfig{
			enabled: false,
			traces:  make([]string, 0),
		},
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
	// Clone builtin filters to avoid modifying global state when adding custom filters.
	// The builtins.Filters.Update() method modifies the FilterSet in-place, which causes
	// race conditions when multiple engines are created concurrently with different custom filters.
	filters := cloneFilterSet(builtins.Filters)

	// Register custom filters if provided
	if len(customFilters) > 0 {
		// Create a new filter set with custom filters
		filterMap := make(map[string]exec.FilterFunction)
		for name, customFilter := range customFilters {
			// Wrap FilterFunc in Gonja's FilterFunction signature
			filterMap[name] = wrapCustomFilter(customFilter)
		}
		customFilterSet := exec.NewFilterSet(filterMap)
		// Update cloned filters with custom ones (safe since filters is now a copy)
		filters = filters.Update(customFilterSet)
	}

	// Always register generic data manipulation filters
	genericFilterMap := map[string]exec.FilterFunction{
		"sort_by":    sortByFilter,
		"group_by":   groupByFilter,
		"transform":  transformFilter,
		"extract":    extractFilter,
		"glob_match": globMatchFilter,
	}
	genericFilterSet := exec.NewFilterSet(genericFilterMap)
	filters = filters.Update(genericFilterSet)

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

	// Always override the "in" test with our fixed version and add generic tests
	// This fixes a Gonja limitation where list membership checks use object identity
	// instead of value comparison for computed template expressions
	testMap := map[string]exec.TestFunction{
		"in":           testInFixed,
		"conflicts_by": conflictsByTest,
	}
	customTestSet := exec.NewTestSet(testMap)
	tests := builtins.Tests.Update(customTestSet)

	customMethods := createCustomMethods()

	// Register custom control structures (tags)
	customControlStructures := map[string]parser.ControlStructureParser{
		"compute_once": computeOnceParser,
	}
	customControlStructureSet := exec.NewControlStructureSet(customControlStructures)
	controlStructures := builtins.ControlStructures.Update(customControlStructureSet)

	environment := &exec.Environment{
		Filters:           filters,
		Tests:             tests,             // Use tests with fixed "in" operator
		ControlStructures: controlStructures, // Use builtins + custom tags
		Methods:           customMethods,     // Use custom methods with fixed append()
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

	// Create execution context
	// Ensure context is not nil to avoid panic in Set()
	if context == nil {
		context = make(map[string]interface{})
	}
	ctx := exec.NewContext(context)

	// Check if tracing is enabled (thread-safe snapshot)
	e.tracing.mu.Lock()
	tracingEnabled := e.tracing.enabled
	e.tracing.mu.Unlock()

	// If tracing is enabled, attach per-render trace state to context
	var traceBuilder *strings.Builder
	if tracingEnabled {
		traceBuilder = &strings.Builder{}
		ctx.Set("_trace_depth", 0)
		ctx.Set("_trace_builder", traceBuilder)
		ctx.Set("_trace_enabled", true) // Store enabled flag in context

		// Log render start
		e.tracef(ctx, "Rendering: %s", templateName)
		// Increment depth
		if depth, ok := ctx.Get("_trace_depth"); ok {
			ctx.Set("_trace_depth", depth.(int)+1)
		}

		startTime := time.Now()
		defer func() {
			duration := time.Since(startTime)
			// Decrement depth
			if depth, ok := ctx.Get("_trace_depth"); ok {
				ctx.Set("_trace_depth", depth.(int)-1)
			}
			e.tracef(ctx, "Completed: %s (%.3fms)", templateName, float64(duration.Microseconds())/1000.0)

			// After render completes, collect trace output and store it thread-safely
			if traceBuilder != nil && traceBuilder.Len() > 0 {
				e.tracing.mu.Lock()
				e.tracing.traces = append(e.tracing.traces, traceBuilder.String())
				e.tracing.mu.Unlock()
			}
		}()
	}

	// Execute the template with the provided context
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

// Generic template functions for advanced data manipulation

// sortByFilter implements multi-field sorting with JSONPath-like expressions.
// Supports special operators:
// - ":desc" for descending order
// - ":exists" for boolean existence check
// - "| length" for array/string length
// Usage: items | sort_by(["$.path.type", "$.path.value | length:desc"]).
func sortByFilter(e *exec.Evaluator, in *exec.Value, params *exec.VarArgs) *exec.Value {
	// Extract items array
	items := in.Interface()
	itemsSlice, ok := convertToSlice(items)
	if !ok {
		return exec.AsValue(fmt.Errorf("sort_by: expected array/slice, got %T", items))
	}
	if len(itemsSlice) == 0 {
		return in
	}

	// Extract criteria from params
	var criteria []string
	criteriaArg := params.First()
	if criteriaArg == nil {
		return exec.AsValue(fmt.Errorf("sort_by: missing criteria argument"))
	}

	criteriaSlice, ok := convertToSlice(criteriaArg.Interface())
	if !ok {
		return exec.AsValue(fmt.Errorf("sort_by: criteria must be an array of strings"))
	}

	for _, c := range criteriaSlice {
		switch v := c.(type) {
		case string:
			criteria = append(criteria, v)
		case *exec.Value:
			// Handle *exec.Value wrapped strings (from template literals)
			criteria = append(criteria, v.String())
		default:
			return exec.AsValue(fmt.Errorf("sort_by: criteria must be strings, got %T", c))
		}
	}

	// Create a sortable wrapper
	sortable := &sortableItems{
		items:    itemsSlice,
		criteria: criteria,
	}

	// Sort using the criteria
	sort.Stable(sortable)

	return exec.AsValue(sortable.items)
}

// groupByFilter groups items by evaluated key expression.
// Usage: items | group_by("$.hostname ~ '|' ~ $.path.type ~ '|' ~ $.path.value").
func groupByFilter(e *exec.Evaluator, in *exec.Value, params *exec.VarArgs) *exec.Value {
	// Extract items array
	items := in.Interface()
	itemsSlice, ok := convertToSlice(items)
	if !ok {
		return exec.AsValue(fmt.Errorf("group_by: expected array/slice, got %T", items))
	}

	// Extract key expression
	keyExpr := params.First()
	if keyExpr == nil {
		return exec.AsValue(fmt.Errorf("group_by: missing key expression"))
	}
	keyExprStr, ok := keyExpr.Interface().(string)
	if !ok {
		return exec.AsValue(fmt.Errorf("group_by: key expression must be string, got %T", keyExpr.Interface()))
	}

	// Group items
	// Use map[string]interface{} for better Gonja compatibility
	groups := make(map[string]interface{})
	for _, item := range itemsSlice {
		key := evaluateExpression(item, keyExprStr)
		keyStr := fmt.Sprint(key)
		if existing, ok := groups[keyStr]; ok {
			// Append to existing group
			if existingSlice, ok := existing.([]interface{}); ok {
				groups[keyStr] = append(existingSlice, item)
			}
		} else {
			// Create new group
			groups[keyStr] = []interface{}{item}
		}
	}

	return exec.AsValue(groups)
}

// transformFilter batch transforms objects with computed fields.
// Usage: items | transform({"path_key": "$.hostname ~ $.path.value", "priority": "$.headers | length"}).
func transformFilter(e *exec.Evaluator, in *exec.Value, params *exec.VarArgs) *exec.Value {
	// Extract items array
	items := in.Interface()
	itemsSlice, ok := convertToSlice(items)
	if !ok {
		return exec.AsValue(fmt.Errorf("transform: expected array/slice, got %T", items))
	}

	// Extract transforms map
	transformsArg := params.First()
	if transformsArg == nil {
		return exec.AsValue(fmt.Errorf("transform: missing transforms argument"))
	}

	transforms, ok := convertToMap(transformsArg.Interface())
	if !ok {
		return exec.AsValue(fmt.Errorf("transform: transforms must be a map/dict"))
	}

	// Transform each item
	result := make([]interface{}, len(itemsSlice))
	for i, item := range itemsSlice {
		// Deep copy the item
		newItem := deepCopyValue(item)

		// Ensure it's a map
		itemMap, ok := convertToMap(newItem)
		if !ok {
			itemMap = make(map[string]interface{})
			itemMap["_original"] = newItem
		}

		// Apply transforms
		for fieldName, expression := range transforms {
			exprStr, ok := expression.(string)
			if !ok {
				return exec.AsValue(fmt.Errorf("transform: expression must be string, got %T", expression))
			}
			value := evaluateExpression(item, exprStr)
			itemMap[fieldName] = value
		}

		result[i] = itemMap
	}

	return exec.AsValue(result)
}

// extractFilter extracts values using JSONPath-like expressions.
// Usage: routes | extract("$.rules[*].matches[*].method").
func extractFilter(e *exec.Evaluator, in *exec.Value, params *exec.VarArgs) *exec.Value {
	// Get the path expression
	pathArg := params.First()
	if pathArg == nil {
		return exec.AsValue(fmt.Errorf("extract: missing path argument"))
	}
	pathStr, ok := pathArg.Interface().(string)
	if !ok {
		return exec.AsValue(fmt.Errorf("extract: path must be string, got %T", pathArg.Interface()))
	}

	items := in.Interface()

	// Handle single item vs array
	if itemsSlice, ok := convertToSlice(items); ok {
		result := []interface{}{}
		for _, item := range itemsSlice {
			extracted := evaluateExpression(item, pathStr)
			if extracted != nil {
				// If extracted is also a slice, flatten it
				if extractedSlice, ok := convertToSlice(extracted); ok {
					result = append(result, extractedSlice...)
				} else {
					result = append(result, extracted)
				}
			}
		}
		return exec.AsValue(result)
	}

	// Single item
	return exec.AsValue(evaluateExpression(items, pathStr))
}

// globMatchFilter filters a list of strings by glob pattern.
// Usage: template_snippets | glob_match("map-entry-*").
func globMatchFilter(e *exec.Evaluator, in *exec.Value, params *exec.VarArgs) *exec.Value {
	// Get the glob pattern
	patternArg := params.First()
	if patternArg == nil {
		return exec.AsValue(fmt.Errorf("glob_match: missing pattern argument"))
	}
	pattern, ok := patternArg.Interface().(string)
	if !ok {
		return exec.AsValue(fmt.Errorf("glob_match: pattern must be string, got %T", patternArg.Interface()))
	}

	// Get input list
	items := in.Interface()
	itemsSlice, ok := convertToSlice(items)
	if !ok {
		return exec.AsValue(fmt.Errorf("glob_match: expected array/slice, got %T", items))
	}

	// Filter items matching glob pattern
	var result []interface{}
	for _, item := range itemsSlice {
		itemStr := fmt.Sprint(item)
		matched, err := filepath.Match(pattern, itemStr)
		if err != nil {
			// Invalid pattern
			return exec.AsValue(fmt.Errorf("glob_match: invalid pattern %q: %w", pattern, err))
		}
		if matched {
			result = append(result, item)
		}
	}

	return exec.AsValue(result)
}

// conflictsByTest detects conflicts when grouped by key.
// Usage: routes | conflicts_by("$.path", "$.method ~ $.headers").
func conflictsByTest(ctx *exec.Context, in *exec.Value, params *exec.VarArgs) (bool, error) {
	// Extract items array
	items := in.Interface()
	itemsSlice, ok := convertToSlice(items)
	if !ok {
		return false, fmt.Errorf("conflicts_by: expected array/slice, got %T", items)
	}

	// Extract group expression and compare expression
	args := params.Args
	if len(args) < 2 {
		return false, fmt.Errorf("conflicts_by: requires 2 arguments, got %d", len(args))
	}

	// Get group expression (first arg)
	groupExpr := args[0].String()

	// Get compare expression (second arg)
	compareExpr := args[1].String()

	// Group items
	groups := make(map[string][]interface{})
	for _, item := range itemsSlice {
		key := evaluateExpression(item, groupExpr)
		keyStr := fmt.Sprint(key)
		groups[keyStr] = append(groups[keyStr], item)
	}

	// Check for conflicts within each group
	for _, group := range groups {
		if len(group) <= 1 {
			continue
		}

		// Check if items in group have different comparison values
		firstValue := evaluateExpression(group[0], compareExpr)
		firstStr := fmt.Sprint(firstValue)

		for _, item := range group[1:] {
			value := evaluateExpression(item, compareExpr)
			valueStr := fmt.Sprint(value)
			if firstStr != valueStr {
				return true, nil // Conflict found
			}
		}
	}

	return false, nil
}

// Helper types and functions for the generic functions

type sortableItems struct {
	items    []interface{}
	criteria []string
}

func (s *sortableItems) Len() int {
	return len(s.items)
}

func (s *sortableItems) Less(i, j int) bool {
	for _, criterion := range s.criteria {
		cmp := compareByExpression(s.items[i], s.items[j], criterion)
		if cmp != 0 {
			return cmp < 0
		}
	}
	return false
}

func (s *sortableItems) Swap(i, j int) {
	s.items[i], s.items[j] = s.items[j], s.items[i]
}

// evaluateExpression evaluates a JSONPath-like expression against an item.
// Supports:
// - Basic paths: "$.field.subfield"
// - Array access: "$.items[0]" or "$.items[*]"
// - Length operator: "$.items | length"
// - Concatenation: "$.field1 ~ '-' ~ $.field2"
// - Existence check: "$.field:exists".
func evaluateExpression(item interface{}, expr string) interface{} {
	expr = strings.TrimSpace(expr)
	if expr == "" {
		return nil
	}

	// Handle concatenation operator ~
	if strings.Contains(expr, " ~ ") {
		return handleConcatenation(item, expr)
	}

	// Handle pipe operator |
	if strings.Contains(expr, " | ") {
		return handlePipeOperator(item, expr)
	}

	// Handle existence check
	if strings.HasSuffix(expr, ":exists") {
		return handleExistenceCheck(item, expr)
	}

	// Handle JSONPath-like navigation
	if strings.HasPrefix(expr, "$.") || expr == "$" {
		return navigateJSONPath(item, expr)
	}

	// Treat as field name without $. prefix
	return navigateJSONPath(item, "$."+expr)
}

// handleConcatenation processes the ~ concatenation operator.
func handleConcatenation(item interface{}, expr string) interface{} {
	parts := strings.Split(expr, " ~ ")
	var result strings.Builder

	for _, part := range parts {
		part = strings.TrimSpace(part)

		// Check if it's a literal string
		if (strings.HasPrefix(part, "'") && strings.HasSuffix(part, "'")) ||
			(strings.HasPrefix(part, "\"") && strings.HasSuffix(part, "\"")) {
			// Remove quotes and append literal
			result.WriteString(strings.Trim(part, "'\""))
		} else {
			// Evaluate as expression
			value := evaluateExpression(item, part)
			if value != nil {
				result.WriteString(fmt.Sprint(value))
			}
		}
	}

	return result.String()
}

// handlePipeOperator processes the | pipe operator for filters.
func handlePipeOperator(item interface{}, expr string) interface{} {
	parts := strings.Split(expr, " | ")
	value := evaluateExpression(item, strings.TrimSpace(parts[0]))

	for i := 1; i < len(parts); i++ {
		value = applyPipeOperation(value, strings.TrimSpace(parts[i]))
	}

	return value
}

// applyPipeOperation applies a single pipe operation to a value.
func applyPipeOperation(value interface{}, operation string) interface{} {
	// Handle length operator
	if operation == "length" {
		return calculateLength(value)
	}

	// Handle default operator
	if strings.HasPrefix(operation, "default(") && strings.HasSuffix(operation, ")") {
		if value == nil || value == "" {
			defaultValue := strings.TrimSuffix(strings.TrimPrefix(operation, "default("), ")")
			return strings.Trim(defaultValue, "'\"")
		}
	}

	return value
}

// calculateLength returns the length of a value.
func calculateLength(value interface{}) int {
	switch v := value.(type) {
	case string:
		return len(v)
	default:
		if slice, ok := convertToSlice(value); ok {
			return len(slice)
		}
		if m, ok := convertToMap(value); ok {
			return len(m)
		}
		return 0
	}
}

// handleExistenceCheck checks if a value exists (is not nil).
func handleExistenceCheck(item interface{}, expr string) interface{} {
	expr = strings.TrimSuffix(expr, ":exists")
	value := evaluateExpression(item, expr)
	return value != nil
}

// navigateJSONPath navigates through an object using JSONPath-like syntax.
func navigateJSONPath(item interface{}, path string) interface{} {
	// Remove leading $. if present
	if strings.HasPrefix(path, "$.") {
		path = strings.TrimPrefix(path, "$.")
	} else if path == "$" {
		return item
	}

	if path == "" {
		return item
	}

	// Split path into segments, handling array indices
	segments := parsePathSegments(path)
	current := item

	for i, segment := range segments {
		if current == nil {
			return nil
		}

		// Handle array index access
		if strings.HasPrefix(segment, "[") && strings.HasSuffix(segment, "]") {
			result, done := processArrayIndex(current, segment, segments, i)
			if done {
				return result
			}
			current = result
		} else {
			// Regular field access
			current = processFieldAccess(current, segment)
		}
	}

	return current
}

// processArrayIndex handles array index access including wildcards and numeric indices.
func processArrayIndex(current interface{}, segment string, segments []string, segmentIndex int) (interface{}, bool) {
	indexStr := strings.TrimPrefix(strings.TrimSuffix(segment, "]"), "[")

	// Handle wildcard [*]
	if indexStr == "*" {
		return processWildcardIndex(current, segments, segmentIndex)
	}

	// Handle numeric index
	return processNumericIndex(current, indexStr)
}

// processWildcardIndex handles wildcard array access [*].
func processWildcardIndex(current interface{}, segments []string, segmentIndex int) (interface{}, bool) {
	slice, ok := convertToSlice(current)
	if !ok {
		return nil, true
	}

	// If there are more segments, collect results from all elements
	if segmentIndex < len(segments)-1 {
		remainingPath := strings.Join(segments[segmentIndex+1:], ".")
		var results []interface{}
		for _, elem := range slice {
			result := navigateJSONPath(elem, "$."+remainingPath)
			if result != nil {
				if resultSlice, ok := convertToSlice(result); ok {
					results = append(results, resultSlice...)
				} else {
					results = append(results, result)
				}
			}
		}
		return results, true
	}

	// Just return all elements
	return slice, true
}

// processNumericIndex handles numeric array index access.
func processNumericIndex(current interface{}, indexStr string) (interface{}, bool) {
	index, err := strconv.Atoi(indexStr)
	if err != nil {
		return current, false // Not a numeric index, continue
	}

	slice, ok := convertToSlice(current)
	if !ok {
		return nil, true
	}

	if index >= 0 && index < len(slice) {
		return slice[index], false
	}

	return nil, true
}

// processFieldAccess handles regular field access.
func processFieldAccess(current interface{}, segment string) interface{} {
	if m, ok := convertToMap(current); ok {
		return m[segment]
	}

	// Try reflection for struct fields
	return getFieldByReflection(current, segment)
}

// parsePathSegments parses a JSONPath into navigable segments.
func parsePathSegments(path string) []string {
	var segments []string
	var current strings.Builder
	inBracket := false

	for i, char := range path {
		switch {
		case char == '[':
			segments, inBracket = processLeftBracket(segments, &current)
		case char == ']':
			segments, inBracket = processRightBracket(segments, &current, inBracket)
		case char == '.' && !inBracket:
			segments = processDot(segments, &current)
		default:
			current.WriteRune(char)
		}

		// Handle last segment
		if i == len(path)-1 && current.Len() > 0 {
			segments = append(segments, current.String())
		}
	}

	return segments
}

// processLeftBracket handles '[' character when parsing path segments.
func processLeftBracket(segments []string, current *strings.Builder) ([]string, bool) {
	if current.Len() > 0 {
		segments = append(segments, current.String())
		current.Reset()
	}
	current.WriteByte('[')
	return segments, true
}

// processRightBracket handles ']' character when parsing path segments.
func processRightBracket(segments []string, current *strings.Builder, inBracket bool) ([]string, bool) {
	current.WriteByte(']')
	if inBracket {
		segments = append(segments, current.String())
		current.Reset()
		return segments, false
	}
	return segments, inBracket
}

// processDot handles '.' character when parsing path segments.
func processDot(segments []string, current *strings.Builder) []string {
	if current.Len() > 0 {
		segments = append(segments, current.String())
		current.Reset()
	}
	return segments
}

// compareByExpression compares two items based on an expression with optional modifiers.
func compareByExpression(a, b interface{}, criterion string) int {
	// Parse modifiers
	descending := false
	checkExists := false
	checkLength := false

	parts := strings.Split(criterion, ":")
	expr := parts[0]

	for i := 1; i < len(parts); i++ {
		modifier := strings.TrimSpace(parts[i])
		switch modifier {
		case "desc":
			descending = true
		case "exists":
			checkExists = true
		}
	}

	// Check for length operator
	if strings.Contains(expr, " | length") {
		checkLength = true
		expr = strings.Split(expr, " | ")[0]
	}

	// Evaluate expressions
	valA := evaluateExpression(a, expr)
	valB := evaluateExpression(b, expr)

	// Handle special checks
	if checkExists {
		existsA := valA != nil
		existsB := valB != nil
		result := 0
		if existsA && !existsB {
			result = -1
		} else if !existsA && existsB {
			result = 1
		}
		if descending {
			result = -result
		}
		return result
	}

	if checkLength {
		lenA := getLength(valA)
		lenB := getLength(valB)
		result := lenA - lenB
		if descending {
			result = -result
		}
		return result
	}

	// Standard comparison
	result := compareValues(valA, valB)
	if descending {
		result = -result
	}
	return result
}

// compareValues compares two values of potentially different types.
func compareValues(a, b interface{}) int {
	// Handle nil values
	if a == nil && b == nil {
		return 0
	}
	if a == nil {
		return 1 // nil is considered greater (sorts to end)
	}
	if b == nil {
		return -1
	}

	// Try numeric comparison first
	if numA, okA := toFloat64(a); okA {
		if numB, okB := toFloat64(b); okB {
			if numA < numB {
				return -1
			} else if numA > numB {
				return 1
			}
			return 0
		}
	}

	// Fall back to string comparison
	strA := fmt.Sprint(a)
	strB := fmt.Sprint(b)
	return strings.Compare(strA, strB)
}

// Helper functions

func convertToSlice(v interface{}) ([]interface{}, bool) {
	if v == nil {
		return nil, false
	}

	// Direct slice conversion
	if slice, ok := v.([]interface{}); ok {
		return slice, true
	}

	// Use reflection for other slice types
	val := reflect.ValueOf(v)
	if val.Kind() == reflect.Slice || val.Kind() == reflect.Array {
		result := make([]interface{}, val.Len())
		for i := 0; i < val.Len(); i++ {
			result[i] = val.Index(i).Interface()
		}
		return result, true
	}

	return nil, false
}

func convertToMap(v interface{}) (map[string]interface{}, bool) {
	if v == nil {
		return nil, false
	}

	// Direct map conversion
	if m, ok := v.(map[string]interface{}); ok {
		return m, true
	}

	// Try reflection for other map types
	val := reflect.ValueOf(v)
	if val.Kind() == reflect.Map {
		result := make(map[string]interface{})
		for _, key := range val.MapKeys() {
			keyStr := fmt.Sprint(key.Interface())
			result[keyStr] = val.MapIndex(key).Interface()
		}
		return result, true
	}

	return nil, false
}

func getFieldByReflection(v interface{}, field string) interface{} {
	if v == nil {
		return nil
	}

	val := reflect.ValueOf(v)

	// Dereference pointers
	for val.Kind() == reflect.Ptr {
		if val.IsNil() {
			return nil
		}
		val = val.Elem()
	}

	if val.Kind() != reflect.Struct {
		return nil
	}

	// Try to find field (case-insensitive)
	typ := val.Type()
	for i := 0; i < val.NumField(); i++ {
		fieldType := typ.Field(i)
		if strings.EqualFold(fieldType.Name, field) {
			fieldVal := val.Field(i)
			if fieldVal.CanInterface() {
				return fieldVal.Interface()
			}
		}
	}

	return nil
}

func getLength(v interface{}) int {
	if v == nil {
		return 0
	}

	if s, ok := v.(string); ok {
		return len(s)
	}

	if slice, ok := convertToSlice(v); ok {
		return len(slice)
	}

	if m, ok := convertToMap(v); ok {
		return len(m)
	}

	// Use reflection as fallback
	val := reflect.ValueOf(v)
	if val.Kind() == reflect.Slice || val.Kind() == reflect.Array || val.Kind() == reflect.Map {
		return val.Len()
	}

	return 0
}

func toFloat64(v interface{}) (float64, bool) {
	switch val := v.(type) {
	case float64:
		return val, true
	case float32:
		return float64(val), true
	case int:
		return float64(val), true
	case int8:
		return float64(val), true
	case int16:
		return float64(val), true
	case int32:
		return float64(val), true
	case int64:
		return float64(val), true
	case uint:
		return float64(val), true
	case uint8:
		return float64(val), true
	case uint16:
		return float64(val), true
	case uint32:
		return float64(val), true
	case uint64:
		return float64(val), true
	case string:
		if f, err := strconv.ParseFloat(val, 64); err == nil {
			return f, true
		}
	}
	return 0, false
}

func deepCopyValue(v interface{}) interface{} {
	if v == nil {
		return nil
	}

	// Use JSON marshal/unmarshal for deep copy
	// This is simple and handles most cases correctly
	data, err := json.Marshal(v)
	if err != nil {
		// Fallback to shallow copy
		return v
	}

	var result interface{}
	if err := json.Unmarshal(data, &result); err != nil {
		// Fallback to shallow copy
		return v
	}

	return result
}

// cloneFilterSet creates a deep copy of a FilterSet to avoid modifying global state.
// This is necessary because gonja's FilterSet.Update() modifies the filter map in-place,
// which causes race conditions when multiple engines are created concurrently.
func cloneFilterSet(original *exec.FilterSet) *exec.FilterSet {
	// Create empty FilterSet and populate it by updating with original.
	// This creates a new instance with copied filters.
	filterMap := make(map[string]exec.FilterFunction)
	cloned := exec.NewFilterSet(filterMap)
	cloned.Update(original)
	return cloned
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
// Tracing is thread-safe - concurrent Render() calls will each produce independent traces.
func (e *TemplateEngine) EnableTracing() {
	e.tracing.mu.Lock()
	e.tracing.enabled = true
	e.tracing.traces = make([]string, 0)
	e.tracing.mu.Unlock()
}

// DisableTracing disables template execution tracing.
func (e *TemplateEngine) DisableTracing() {
	e.tracing.mu.Lock()
	e.tracing.enabled = false
	e.tracing.mu.Unlock()
}

// GetTraceOutput returns the accumulated trace output from all renders and resets the trace buffer.
// When multiple renders execute concurrently, traces are aggregated in the order they complete.
func (e *TemplateEngine) GetTraceOutput() string {
	e.tracing.mu.Lock()
	defer e.tracing.mu.Unlock()

	if len(e.tracing.traces) == 0 {
		return ""
	}

	output := strings.Join(e.tracing.traces, "")
	e.tracing.traces = make([]string, 0)
	return output
}

// tracef logs a trace message with proper indentation based on nesting depth.
// The depth and builder are read from the execution context for thread-safety.
func (e *TemplateEngine) tracef(ctx *exec.Context, format string, args ...interface{}) {
	// Check if tracing is enabled for this render (stored in context)
	if enabled, ok := ctx.Get("_trace_enabled"); !ok || !enabled.(bool) {
		return
	}

	// Get depth from context (per-render state)
	depth := 0
	if d, ok := ctx.Get("_trace_depth"); ok {
		depth = d.(int)
	}

	// Get builder from context (per-render state)
	var builder *strings.Builder
	if b, ok := ctx.Get("_trace_builder"); ok {
		builder = b.(*strings.Builder)
	}
	if builder == nil {
		return
	}

	// Create indentation based on depth
	indent := strings.Repeat("  ", depth)

	// Format and write the trace message
	msg := fmt.Sprintf(format, args...)
	fmt.Fprintf(builder, "%s%s\n", indent, msg)
}

// ============================================================================
// Custom Gonja Tag: compute_once
// ============================================================================

// ComputeOnceControlStructure implements a custom Gonja tag that executes expensive
// template computations only once per render, caching the result for subsequent includes.
//
// Syntax - the variable must be created in the parent context BEFORE compute_once:
//
//	{%-  set analysis = namespace(path_groups={}, sorted_routes=[], all_routes=[]) %}
//	{%- compute_once analysis %}
//	  {%- from "analyze_routes" import analyze_routes %}
//	  {{- analyze_routes(analysis, resources) -}}
//	{% endcompute_once %}
//
// The tag checks if 'variable_name' has been modified (has any attribute set).
// - If modified: skips the body (already computed)
// - If not modified: executes the body which modifies the namespace
//
// Why this design: Gonja's {% set %} inside blocks creates local variables that don't
// persist to the parent context. By requiring the namespace to be created BEFORE
// compute_once, we work with Gonja's scoping rules instead of against them.
//
// Use case: Gateway library's analyze_routes macro is called 4 times per render.
// With compute_once, it runs only once and the result is reused across all includes.
type ComputeOnceControlStructure struct {
	location *tokens.Token
	varName  string         // Variable name to check before executing body
	wrapper  *nodes.Wrapper // Template body to execute
}

// Position returns the token position for error reporting.
func (cs *ComputeOnceControlStructure) Position() *tokens.Token {
	return cs.location
}

// String returns a string representation for debugging.
func (cs *ComputeOnceControlStructure) String() string {
	t := cs.Position()
	return fmt.Sprintf("ComputeOnceControlStructure(var=%s, Line=%d Col=%d)",
		cs.varName, t.Line, t.Col)
}

// Execute implements the compute_once logic.
func (cs *ComputeOnceControlStructure) Execute(r *exec.Renderer, tag *nodes.ControlStructureBlock) error {
	// Use a marker variable to track if computation has been done
	// Marker is named "_computed_<varname>" and stored in the context
	markerName := "_computed_" + cs.varName

	// Check if computation already happened
	if r.Environment.Context.Has(markerName) {
		// Marker exists - computation already done, skip body
		return nil
	}

	// Get the variable value - it MUST exist before compute_once
	_, exists := r.Environment.Context.Get(cs.varName)
	if !exists {
		return fmt.Errorf("compute_once: variable '%s' must be created before compute_once block (use {%% set %s = namespace(...) %%} before compute_once)", cs.varName, cs.varName)
	}

	// Variable exists and computation hasn't been done - execute body
	err := r.ExecuteWrapper(cs.wrapper)
	if err != nil {
		return err
	}

	// Mark computation as done
	r.Environment.Context.Set(markerName, true)

	return nil
}

// computeOnceParser parses the compute_once tag syntax.
//
// Expected syntax: {% compute_once variable_name %}.
func computeOnceParser(p, args *parser.Parser) (nodes.ControlStructure, error) {
	cs := &ComputeOnceControlStructure{
		location: p.Current(),
	}

	// Parse variable name
	varToken := args.Match(tokens.Name)
	if varToken == nil {
		return nil, args.Error("compute_once requires variable name", nil)
	}
	cs.varName = varToken.Val

	// Ensure no extra arguments
	if !args.Stream().End() {
		return nil, args.Error("compute_once takes only variable name, no additional arguments", nil)
	}

	// Parse body until {% endcompute_once %}
	wrapper, _, err := p.WrapUntil("endcompute_once")
	if err != nil {
		return nil, err
	}
	cs.wrapper = wrapper

	return cs, nil
}
