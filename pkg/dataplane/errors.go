package dataplane

import "fmt"

// SyncError represents a synchronization failure with actionable context.
// It provides detailed information about what stage failed and suggestions
// for how to fix the problem.
type SyncError struct {
	// Stage indicates where the failure occurred:
	// "connect", "fetch", "parse-current", "parse-desired", "compare", "apply", "commit", "fallback"
	Stage string

	// Message provides a detailed error description
	Message string

	// Cause is the underlying error that caused the failure
	Cause error

	// Hints provides actionable suggestions for fixing the problem
	Hints []string
}

// Error implements the error interface.
func (e *SyncError) Error() string {
	msg := fmt.Sprintf("%s stage failed: %s", e.Stage, e.Message)
	if e.Cause != nil {
		msg += fmt.Sprintf(": %v", e.Cause)
	}
	return msg
}

// Unwrap returns the underlying cause for error unwrapping.
func (e *SyncError) Unwrap() error {
	return e.Cause
}

// ConnectionError represents a failure to connect to the Dataplane API.
type ConnectionError struct {
	// Endpoint is the URL that failed to connect
	Endpoint string

	// Cause is the underlying connection error
	Cause error
}

// Error implements the error interface.
func (e *ConnectionError) Error() string {
	return fmt.Sprintf("failed to connect to dataplane API at %s: %v", e.Endpoint, e.Cause)
}

// Unwrap returns the underlying cause for error unwrapping.
func (e *ConnectionError) Unwrap() error {
	return e.Cause
}

// ParseError represents a configuration parsing failure.
type ParseError struct {
	// ConfigType indicates which config failed: "current" or "desired"
	ConfigType string

	// ConfigSnippet contains the first 200 characters of the problematic config
	ConfigSnippet string

	// Line indicates the approximate line number where parsing failed (if available)
	Line int

	// Cause is the underlying parsing error
	Cause error
}

// Error implements the error interface.
func (e *ParseError) Error() string {
	msg := fmt.Sprintf("failed to parse %s configuration", e.ConfigType)
	if e.Line > 0 {
		msg += fmt.Sprintf(" near line %d", e.Line)
	}
	msg += fmt.Sprintf(": %v", e.Cause)
	return msg
}

// Unwrap returns the underlying cause for error unwrapping.
func (e *ParseError) Unwrap() error {
	return e.Cause
}

// ValidationError represents semantic validation failure from HAProxy.
type ValidationError struct {
	// Message is the validation error message from HAProxy
	Message string

	// Cause is the underlying error
	Cause error
}

// Error implements the error interface.
func (e *ValidationError) Error() string {
	return fmt.Sprintf("HAProxy validation failed: %s: %v", e.Message, e.Cause)
}

// Unwrap returns the underlying cause for error unwrapping.
func (e *ValidationError) Unwrap() error {
	return e.Cause
}

// ConflictError represents unresolved version conflicts after exhausting retries.
type ConflictError struct {
	// Retries is the number of retry attempts made
	Retries int

	// ExpectedVersion is the version we tried to use
	ExpectedVersion int64

	// ActualVersion is the version that exists on the server
	ActualVersion string
}

// Error implements the error interface.
func (e *ConflictError) Error() string {
	return fmt.Sprintf("version conflict after %d retries: expected version %d, server has %s",
		e.Retries, e.ExpectedVersion, e.ActualVersion)
}

// OperationError represents a failure of a specific configuration operation.
type OperationError struct {
	// OperationType is "create", "update", or "delete"
	OperationType string

	// Section is the configuration section (e.g., "backend", "server")
	Section string

	// Resource is the resource identifier (e.g., backend name, server name)
	Resource string

	// Cause is the underlying error
	Cause error
}

// Error implements the error interface.
func (e *OperationError) Error() string {
	return fmt.Sprintf("failed to %s %s '%s': %v", e.OperationType, e.Section, e.Resource, e.Cause)
}

// Unwrap returns the underlying cause for error unwrapping.
func (e *OperationError) Unwrap() error {
	return e.Cause
}

// FallbackError represents a failure during raw config fallback.
type FallbackError struct {
	// OriginalError is the error that triggered the fallback
	OriginalError error

	// FallbackCause is the error that occurred during fallback
	FallbackCause error
}

// Error implements the error interface.
func (e *FallbackError) Error() string {
	return fmt.Sprintf("fine-grained sync failed (%v) and fallback to raw config also failed (%v)",
		e.OriginalError, e.FallbackCause)
}

// Unwrap returns the fallback cause for error unwrapping.
func (e *FallbackError) Unwrap() error {
	return e.FallbackCause
}

// Helper functions to create common error scenarios

// NewConnectionError creates a ConnectionError.
func NewConnectionError(endpoint string, cause error) *SyncError {
	return &SyncError{
		Stage:   "connect",
		Message: fmt.Sprintf("failed to connect to dataplane API at %s", endpoint),
		Cause:   &ConnectionError{Endpoint: endpoint, Cause: cause},
		Hints: []string{
			"Verify the dataplane API URL is correct",
			"Check that HAProxy is running and accessible",
			"Ensure network connectivity to the HAProxy host",
			"Verify credentials are correct",
		},
	}
}

// NewParseError creates a ParseError.
func NewParseError(configType, configSnippet string, cause error) *SyncError {
	hints := []string{
		"Check the HAProxy configuration syntax",
		"Validate the configuration with: haproxy -c -f <config>",
	}

	if configType == "current" {
		hints = append(hints, "The current config from dataplane API may be corrupted")
	} else {
		hints = append(hints, "Review the desired configuration for syntax errors")
	}

	return &SyncError{
		Stage:   fmt.Sprintf("parse-%s", configType),
		Message: fmt.Sprintf("failed to parse %s configuration", configType),
		Cause:   &ParseError{ConfigType: configType, ConfigSnippet: configSnippet, Cause: cause},
		Hints:   hints,
	}
}

// NewValidationError creates a ValidationError.
func NewValidationError(message string, cause error) *SyncError {
	return &SyncError{
		Stage:   "apply",
		Message: "HAProxy rejected the configuration",
		Cause:   &ValidationError{Message: message, Cause: cause},
		Hints: []string{
			"Review the validation error message from HAProxy",
			"Check for references to non-existent backends or servers",
			"Verify all directives are compatible with your HAProxy version",
			"Ensure resource dependencies are satisfied",
		},
	}
}

// NewConflictError creates a ConflictError.
func NewConflictError(retries int, expectedVersion int64, actualVersion string) *SyncError {
	return &SyncError{
		Stage:   "commit",
		Message: fmt.Sprintf("version conflict after %d retries", retries),
		Cause:   &ConflictError{Retries: retries, ExpectedVersion: expectedVersion, ActualVersion: actualVersion},
		Hints: []string{
			"Another process is modifying the HAProxy configuration concurrently",
			"Consider increasing MaxRetries in SyncOptions",
			"Coordinate configuration updates to avoid conflicts",
			"Check if there are other automation tools modifying HAProxy",
		},
	}
}

// NewOperationError creates an OperationError.
func NewOperationError(opType, section, resource string, cause error) *SyncError {
	return &SyncError{
		Stage:   "apply",
		Message: fmt.Sprintf("failed to %s %s '%s'", opType, section, resource),
		Cause:   &OperationError{OperationType: opType, Section: section, Resource: resource, Cause: cause},
		Hints: []string{
			fmt.Sprintf("Check if %s '%s' exists and is accessible", section, resource),
			"Review the operation details for invalid values",
			"Verify resource dependencies are satisfied",
		},
	}
}

// NewFallbackError creates a FallbackError.
func NewFallbackError(originalErr, fallbackCause error) *SyncError {
	return &SyncError{
		Stage:   "fallback",
		Message: "both fine-grained sync and raw config fallback failed",
		Cause:   &FallbackError{OriginalError: originalErr, FallbackCause: fallbackCause},
		Hints: []string{
			"The desired configuration may have fundamental issues",
			"Check HAProxy logs for detailed error messages",
			"Validate the configuration with: haproxy -c -f <config>",
			"Review both the fine-grained sync error and fallback error",
		},
	}
}
