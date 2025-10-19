package templating

import (
	"fmt"
	"regexp"
	"strings"
)

// errorLocation represents the location of an error in a template.
type errorLocation struct {
	Line   int
	Column int
}

// parsedError represents a parsed template rendering error with structured information.
type parsedError struct {
	Location *errorLocation
	Problem  string
	Context  string
	Hints    []string
}

// Common error patterns in gonja template errors.
var (
	// Pattern: "at line X: ... at Line=Y Col=Z".
	lineColPattern = regexp.MustCompile(`Line=(\d+)\s+Col=(\d+)`)

	// Pattern: "unable to execute template: ..." or "Unable to execute controlStructure at line X:".
	locationPattern = regexp.MustCompile(`at line (\d+)`)

	// Pattern: "unknown method 'X'".
	unknownMethodPattern = regexp.MustCompile(`unknown method '([^']+)'`)

	// Pattern: "undefined variable 'X'".
	undefinedVarPattern = regexp.MustCompile(`undefined variable '([^']+)'`)

	// Pattern: "invalid call to method 'X'".
	invalidCallPattern = regexp.MustCompile(`invalid call to method '([^']+)'`)

	// Pattern: "type mismatch" or "expected X, got Y".
	typeMismatchPattern = regexp.MustCompile(`expected (\w+), got (\w+)`)
)

// FormatRenderError formats a template rendering error into a human-readable multi-line string.
//
// This function parses gonja error messages to extract:
//   - Line and column numbers
//   - The actual problem (e.g., "unknown method", "undefined variable")
//   - Contextual information
//
// And returns a nicely formatted multi-line error message with:
//   - Clear section headers
//   - Template snippet showing the error location
//   - Actionable hints for fixing the error
//
// Parameters:
//   - err: The error from template rendering (typically a *RenderError)
//   - templateName: Name of the template that failed
//   - templateContent: Full template content for extracting context
//
// Returns:
//   - Formatted multi-line error string
func FormatRenderError(err error, templateName, templateContent string) string {
	if err == nil {
		return ""
	}

	// Parse the error to extract structured information
	parsed := parseTemplateError(err.Error())

	var builder strings.Builder

	// Header
	builder.WriteString(fmt.Sprintf("Template Rendering Error: %s\n", templateName))
	builder.WriteString(strings.Repeat("─", 60))
	builder.WriteString("\n")

	// Location
	if parsed.Location != nil {
		builder.WriteString(fmt.Sprintf("Location: Line %d, Column %d\n",
			parsed.Location.Line, parsed.Location.Column))
	}

	// Problem
	if parsed.Problem != "" {
		builder.WriteString(fmt.Sprintf("Problem:  %s\n", parsed.Problem))
	} else {
		// Fallback: show truncated original error
		problem := err.Error()
		if len(problem) > 100 {
			problem = problem[:97] + "..."
		}
		builder.WriteString(fmt.Sprintf("Problem:  %s\n", problem))
	}

	// Template context (show the line with the error)
	if parsed.Location != nil && templateContent != "" {
		context := extractTemplateContext(templateContent, parsed.Location.Line, parsed.Location.Column)
		if context != "" {
			builder.WriteString("\n")
			builder.WriteString("Template Context:\n")
			builder.WriteString(context)
		}
	}

	// Hints
	if len(parsed.Hints) > 0 {
		builder.WriteString("\n")
		builder.WriteString("Hint: ")
		builder.WriteString(strings.Join(parsed.Hints, "\n      "))
		builder.WriteString("\n")
	}

	return builder.String()
}

// parseTemplateError parses a gonja error string to extract structured information.
func parseTemplateError(errorStr string) parsedError {
	parsed := parsedError{}

	// Extract line and column numbers
	parsed.Location = extractLocation(errorStr)

	// Extract the actual problem
	parsed.Problem = extractProblem(errorStr)

	// Generate hints based on error patterns
	parsed.Hints = generateHints(errorStr)

	return parsed
}

// extractLocation extracts line and column numbers from the error string.
func extractLocation(errorStr string) *errorLocation {
	// Try Line=X Col=Y pattern first (most specific)
	if matches := lineColPattern.FindStringSubmatch(errorStr); len(matches) == 3 {
		var line, col int
		_, _ = fmt.Sscanf(matches[1], "%d", &line)
		_, _ = fmt.Sscanf(matches[2], "%d", &col)
		return &errorLocation{Line: line, Column: col}
	}

	// Fallback to "at line X" pattern
	if matches := locationPattern.FindStringSubmatch(errorStr); len(matches) == 2 {
		var line int
		_, _ = fmt.Sscanf(matches[1], "%d", &line)
		return &errorLocation{Line: line, Column: 0}
	}

	return nil
}

// extractProblem extracts the core problem description from the error.
func extractProblem(errorStr string) string {
	// Try to find the most specific error message by working backwards
	// from nested error chains

	// Check for unknown method
	if matches := unknownMethodPattern.FindStringSubmatch(errorStr); len(matches) == 2 {
		methodName := matches[1]
		// Try to find what type it was called on
		if strings.Contains(errorStr, "invalid call to method") {
			return fmt.Sprintf("Unknown method '%s' - cannot call methods on this type", methodName)
		}
		return fmt.Sprintf("Unknown method '%s'", methodName)
	}

	// Check for undefined variable
	if matches := undefinedVarPattern.FindStringSubmatch(errorStr); len(matches) == 2 {
		return fmt.Sprintf("Undefined variable '%s'", matches[1])
	}

	// Check for invalid method call
	if matches := invalidCallPattern.FindStringSubmatch(errorStr); len(matches) == 2 {
		return fmt.Sprintf("Invalid method call '%s()' on this type", matches[1])
	}

	// Check for type mismatch
	if matches := typeMismatchPattern.FindStringSubmatch(errorStr); len(matches) == 3 {
		return fmt.Sprintf("Type mismatch: expected %s, got %s", matches[1], matches[2])
	}

	// Generic patterns
	if strings.Contains(errorStr, "unable to evaluate") {
		// Extract the part after "unable to evaluate"
		if idx := strings.Index(errorStr, "unable to evaluate"); idx >= 0 {
			rest := errorStr[idx+len("unable to evaluate"):]
			// Find the next colon to get the expression
			if colonIdx := strings.Index(rest, ":"); colonIdx > 0 {
				expr := strings.TrimSpace(rest[:colonIdx])
				return fmt.Sprintf("Unable to evaluate expression: %s", expr)
			}
		}
	}

	return ""
}

// generateHints generates actionable hints based on common error patterns.
func generateHints(errorStr string) []string {
	var hints []string

	// Unknown method on map/dict
	if strings.Contains(errorStr, "unknown method 'get'") || strings.Contains(errorStr, "invalid call to method 'get'") {
		hints = append(hints,
			"Map access should use dot notation (e.g., 'map.key') or",
			"bracket syntax (e.g., 'map[\"key\"]'), not method calls like '.get()'.")
	}

	// Undefined variable
	if strings.Contains(errorStr, "undefined variable") {
		hints = append(hints,
			"Check that the variable is defined in the rendering context.",
			"Verify spelling and that the variable exists in the data passed to the template.")
	}

	// Method call on wrong type
	if strings.Contains(errorStr, "invalid call to method") && !strings.Contains(errorStr, "get") {
		hints = append(hints,
			"You may be trying to call a method on a type that doesn't support it.",
			"Check the type of the variable and use appropriate syntax for that type.")
	}

	// Type mismatch
	if strings.Contains(errorStr, "expected") && strings.Contains(errorStr, "got") {
		hints = append(hints,
			"The template expects a different data type than what was provided.",
			"Verify the types of variables in your rendering context.")
	}

	// Control structure errors
	if strings.Contains(errorStr, "controlStructure") || strings.Contains(errorStr, "ForControlStructure") {
		hints = append(hints,
			"Check the syntax of your loop or conditional statement.",
			"Ensure you're iterating over a list/array, not a single value.")
	}

	// Generic hint if no specific hint matched
	if len(hints) == 0 {
		hints = append(hints,
			"Check your template syntax and the data passed to the template.",
			"See Jinja2 template documentation for syntax help.")
	}

	return hints
}

// extractTemplateContext extracts a few lines of template around the error location.
func extractTemplateContext(templateContent string, line, column int) string {
	lines := strings.Split(templateContent, "\n")

	if line < 1 || line > len(lines) {
		return ""
	}

	var builder strings.Builder

	// Show the error line (1-indexed)
	lineIndex := line - 1
	errorLine := lines[lineIndex]

	// Format: line number | content
	builder.WriteString(fmt.Sprintf("%d | %s\n", line, errorLine))

	// Add caret pointing to the column if we have it
	if column > 0 && column <= len(errorLine)+1 {
		// Calculate padding: line number + " | " + spaces to column
		lineNumWidth := len(fmt.Sprintf("%d", line))
		padding := lineNumWidth + 3 + column - 1
		builder.WriteString(strings.Repeat(" ", padding))
		builder.WriteString("^\n")
	}

	return builder.String()
}

// FormatRenderErrorShort returns a shortened single-line version of the error.
// Useful for logging contexts where multi-line output isn't appropriate.
func FormatRenderErrorShort(err error, templateName string) string {
	if err == nil {
		return ""
	}

	parsed := parseTemplateError(err.Error())

	var parts []string

	// Template name
	parts = append(parts, fmt.Sprintf("Template: %s", templateName))

	// Location
	if parsed.Location != nil {
		parts = append(parts, fmt.Sprintf("Line %d Col %d", parsed.Location.Line, parsed.Location.Column))
	}

	// Problem
	if parsed.Problem != "" {
		parts = append(parts, parsed.Problem)
	} else {
		// Fallback to truncated error
		problem := err.Error()
		if len(problem) > 60 {
			problem = problem[:57] + "..."
		}
		parts = append(parts, problem)
	}

	return strings.Join(parts, " | ")
}
