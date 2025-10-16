package indexer

import (
	"fmt"
	"reflect"
	"strings"

	"k8s.io/client-go/util/jsonpath"
)

// JSONPathEvaluator evaluates JSONPath expressions against Kubernetes resources.
type JSONPathEvaluator struct {
	expression string
	parser     *jsonpath.JSONPath
}

// NewJSONPathEvaluator creates a new JSONPath evaluator for the given expression.
//
// The expression should follow JSONPath syntax without the surrounding braces.
// For example: "metadata.namespace" or "metadata.labels['app']"
//
// Returns an error if the expression is invalid (fail-fast).
func NewJSONPathEvaluator(expression string) (*JSONPathEvaluator, error) {
	if expression == "" {
		return nil, fmt.Errorf("empty JSONPath expression")
	}

	// Create JSONPath parser
	jp := jsonpath.New("evaluator")

	// Wrap expression in braces for jsonpath library
	// The library expects: {.metadata.namespace}
	wrappedExpr := "{." + strings.TrimPrefix(expression, ".") + "}"

	// Parse expression (fail-fast validation)
	if err := jp.Parse(wrappedExpr); err != nil {
		return nil, &JSONPathError{
			Expression: expression,
			Operation:  "parse",
			Err:        err,
		}
	}

	return &JSONPathEvaluator{
		expression: expression,
		parser:     jp,
	}, nil
}

// Evaluate executes the JSONPath expression against the provided resource.
//
// Returns:
//   - The extracted value as a string
//   - An error if evaluation fails or the result is not a string
//
// If the expression matches multiple values, only the first is returned.
func (e *JSONPathEvaluator) Evaluate(resource interface{}) (string, error) {
	// Execute JSONPath query
	results, err := e.parser.FindResults(resource)
	if err != nil {
		return "", &JSONPathError{
			Expression: e.expression,
			Operation:  "execute",
			Err:        err,
		}
	}

	// Check if we got any results
	if len(results) == 0 || len(results[0]) == 0 {
		return "", &JSONPathError{
			Expression: e.expression,
			Operation:  "execute",
			Err:        fmt.Errorf("no results found"),
		}
	}

	// Get first result
	value := results[0][0]

	// Convert to string
	return reflectValueToString(value), nil
}

// Expression returns the JSONPath expression used by this evaluator.
func (e *JSONPathEvaluator) Expression() string {
	return e.expression
}

// reflectValueToString converts a reflect.Value to a string representation.
func reflectValueToString(v reflect.Value) string {
	// Handle invalid values
	if !v.IsValid() {
		return ""
	}

	// Dereference pointers
	for v.Kind() == reflect.Ptr || v.Kind() == reflect.Interface {
		if v.IsNil() {
			return ""
		}
		v = v.Elem()
	}

	// Convert based on kind
	switch v.Kind() {
	case reflect.String:
		return v.String()
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
		return fmt.Sprintf("%d", v.Int())
	case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64:
		return fmt.Sprintf("%d", v.Uint())
	case reflect.Float32, reflect.Float64:
		return fmt.Sprintf("%f", v.Float())
	case reflect.Bool:
		return fmt.Sprintf("%t", v.Bool())
	default:
		// For complex types, use fmt.Sprint
		return fmt.Sprint(v.Interface())
	}
}

// JSONPathError represents an error during JSONPath evaluation.
type JSONPathError struct {
	Expression string
	Operation  string
	Err        error
}

func (e *JSONPathError) Error() string {
	return fmt.Sprintf("JSONPath error in %s for expression '%s': %v",
		e.Operation, e.Expression, e.Err)
}

func (e *JSONPathError) Unwrap() error {
	return e.Err
}
