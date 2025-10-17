package indexer

import (
	"fmt"
	"reflect"
	"strings"
)

// FieldFilter removes fields from Kubernetes resources based on JSONPath expressions.
//
// This is used to reduce memory usage by removing unnecessary fields before storing
// resources in the index (e.g., metadata.managedFields).
type FieldFilter struct {
	patterns []string
}

// For example: "metadata.managedFields", "metadata.annotations".
func NewFieldFilter(patterns []string) *FieldFilter {
	return &FieldFilter{
		patterns: patterns,
	}
}

// Filter removes matching fields from the resource.
//
// The resource is modified in-place for efficiency.
// Returns an error if filtering fails.
//
// Example:
//
//	filter := NewFieldFilter([]string{"metadata.managedFields"})
//	err := filter.Filter(resource)
func (f *FieldFilter) Filter(resource interface{}) error {
	if len(f.patterns) == 0 {
		return nil
	}

	// Get reflect.Value for the resource
	rv := reflect.ValueOf(resource)

	// Dereference pointers
	for rv.Kind() == reflect.Ptr || rv.Kind() == reflect.Interface {
		if rv.IsNil() {
			return nil
		}
		rv = rv.Elem()
	}

	// Apply each pattern
	for _, pattern := range f.patterns {
		if err := f.removeField(rv, pattern); err != nil {
			return &FilterError{
				Pattern: pattern,
				Err:     err,
			}
		}
	}

	return nil
}

// removeField removes a field from the resource based on a JSONPath expression.
func (f *FieldFilter) removeField(rv reflect.Value, pattern string) error {
	// Split pattern into segments
	// Example: "metadata.labels['app']" -> ["metadata", "labels", "app"]
	segments := parseJSONPathPattern(pattern)
	if len(segments) == 0 {
		return fmt.Errorf("empty pattern")
	}

	// Navigate to parent of target field
	parent := rv
	for i := 0; i < len(segments)-1; i++ {
		var err error
		parent, err = f.navigateToField(parent, segments[i])
		if err != nil {
			// Field doesn't exist, nothing to remove
			return nil
		}
	}

	// Remove the target field
	targetField := segments[len(segments)-1]
	return f.deleteField(parent, targetField)
}

// navigateToField navigates to a field in the resource structure.
func (f *FieldFilter) navigateToField(rv reflect.Value, fieldName string) (reflect.Value, error) {
	// Dereference pointers
	for rv.Kind() == reflect.Ptr || rv.Kind() == reflect.Interface {
		if rv.IsNil() {
			return reflect.Value{}, fmt.Errorf("nil pointer")
		}
		rv = rv.Elem()
	}

	switch rv.Kind() {
	case reflect.Map:
		// Map field access
		key := reflect.ValueOf(fieldName)
		value := rv.MapIndex(key)
		if !value.IsValid() {
			return reflect.Value{}, fmt.Errorf("field not found: %s", fieldName)
		}
		return value, nil

	case reflect.Struct:
		// Struct field access
		value := rv.FieldByName(fieldName)
		if !value.IsValid() {
			// Try case-insensitive match (common in Kubernetes API objects)
			for i := 0; i < rv.NumField(); i++ {
				field := rv.Type().Field(i)
				if strings.EqualFold(field.Name, fieldName) {
					return rv.Field(i), nil
				}
			}
			return reflect.Value{}, fmt.Errorf("field not found: %s", fieldName)
		}
		return value, nil

	default:
		return reflect.Value{}, fmt.Errorf("cannot navigate into %s", rv.Kind())
	}
}

// deleteField removes a field from a map or struct.
func (f *FieldFilter) deleteField(parent reflect.Value, fieldName string) error {
	// Dereference pointers
	for parent.Kind() == reflect.Ptr || parent.Kind() == reflect.Interface {
		if parent.IsNil() {
			return nil
		}
		parent = parent.Elem()
	}

	switch parent.Kind() {
	case reflect.Map:
		// Delete from map
		key := reflect.ValueOf(fieldName)
		if parent.MapIndex(key).IsValid() {
			parent.SetMapIndex(key, reflect.Value{})
		}
		return nil

	case reflect.Struct:
		// Cannot delete struct fields, can only zero them
		value := parent.FieldByName(fieldName)
		if !value.IsValid() {
			// Try case-insensitive match
			for i := 0; i < parent.NumField(); i++ {
				field := parent.Type().Field(i)
				if strings.EqualFold(field.Name, fieldName) {
					value = parent.Field(i)
					break
				}
			}
		}

		if value.IsValid() && value.CanSet() {
			// Zero the field
			value.Set(reflect.Zero(value.Type()))
		}
		return nil

	default:
		return fmt.Errorf("cannot delete field from %s", parent.Kind())
	}
}

// parseJSONPathPattern parses a JSONPath pattern into segments.
//
// Examples:
//   - "metadata.name" -> ["metadata", "name"]
//   - "metadata.labels['app']" -> ["metadata", "labels", "app"]
//   - "spec.rules[0].host" -> ["spec", "rules", "0", "host"]
func parseJSONPathPattern(pattern string) []string {
	var segments []string

	// Remove leading dot if present
	pattern = strings.TrimPrefix(pattern, ".")

	// Split by dots, but handle brackets specially
	current := ""
	inBracket := false

	for i := 0; i < len(pattern); i++ {
		ch := pattern[i]

		switch ch {
		case '.':
			if !inBracket && current != "" {
				segments = append(segments, current)
				current = ""
			} else if !inBracket {
				// Skip leading dots
			} else {
				current += string(ch)
			}

		case '[':
			if current != "" {
				segments = append(segments, current)
				current = ""
			}
			inBracket = true

		case ']':
			if inBracket && current != "" {
				// Remove quotes if present
				current = strings.Trim(current, "'\"")
				segments = append(segments, current)
				current = ""
			}
			inBracket = false

		default:
			current += string(ch)
		}
	}

	// Add remaining segment
	if current != "" {
		segments = append(segments, current)
	}

	return segments
}

// FilterError represents an error during field filtering.
type FilterError struct {
	Pattern string
	Err     error
}

func (e *FilterError) Error() string {
	return fmt.Sprintf("filter error for pattern '%s': %v", e.Pattern, e.Err)
}

func (e *FilterError) Unwrap() error {
	return e.Err
}
