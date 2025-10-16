// Package store provides storage implementations for indexed Kubernetes resources.
//
// This package offers two store types:
// - Memory store: Fast in-memory storage with complete resources
// - Cached store: Memory-efficient storage with API-backed retrieval and caching
package store

import (
	"fmt"
	"strings"
)

// makeKeyString creates a composite key from multiple key parts.
//
// Example:
//
//	makeKeyString("default", "my-ingress") -> "default/my-ingress"
func makeKeyString(keys []string) string {
	return strings.Join(keys, "/")
}

// StoreError represents a generic store operation error.
type StoreError struct {
	Operation string
	Keys      []string
	Err       error
}

func (e *StoreError) Error() string {
	keyStr := strings.Join(e.Keys, "/")
	if keyStr == "" {
		return fmt.Sprintf("store error during %s: %v", e.Operation, e.Err)
	}
	return fmt.Sprintf("store error during %s for key '%s': %v", e.Operation, keyStr, e.Err)
}

func (e *StoreError) Unwrap() error {
	return e.Err
}
