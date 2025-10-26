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

// Package debug provides controller-specific debug variable implementations.
//
// This package integrates the generic pkg/introspection infrastructure with
// controller-specific state. It defines:
//   - StateProvider interface for accessing controller internal state
//   - Var implementations (ConfigVar, RenderedVar, etc.)
//   - Event buffer for tracking recent events
//   - Registration logic for publishing variables
//
// The controller implements StateProvider and provides thread-safe access
// to its internal state (config, rendered output, resources, etc.).
package debug

import (
	"time"

	"haproxy-template-ic/pkg/core/config"
	"haproxy-template-ic/pkg/dataplane"
)

// StateProvider provides access to controller internal state.
//
// This interface is implemented by the controller to expose its state
// to debug variables in a thread-safe manner. The controller caches
// state by subscribing to events (ConfigValidatedEvent, RenderCompletedEvent, etc.)
// and updates the cached values accordingly.
//
// All methods must be thread-safe as they may be called concurrently
// from HTTP request handlers.
type StateProvider interface {
	// GetConfig returns the current validated configuration and its version.
	//
	// Returns error if config is not yet loaded.
	//
	// Example return:
	//   config: &config.Config{...}
	//   version: "v123"
	//   error: nil
	GetConfig() (*config.Config, string, error)

	// GetCredentials returns the current credentials and their version.
	//
	// Returns error if credentials are not yet loaded.
	//
	// Example return:
	//   creds: &config.Credentials{...}
	//   version: "v456"
	//   error: nil
	GetCredentials() (*config.Credentials, string, error)

	// GetRenderedConfig returns the most recently rendered HAProxy configuration
	// and the timestamp when it was rendered.
	//
	// Returns error if no config has been rendered yet.
	//
	// Example return:
	//   rendered: "global\n  maxconn 2000\n..."
	//   timestamp: 2025-01-15 10:30:45
	//   error: nil
	GetRenderedConfig() (string, time.Time, error)

	// GetAuxiliaryFiles returns the most recently used auxiliary files
	// (SSL certificates, map files, general files) and the timestamp.
	//
	// Returns error if no auxiliary files have been cached yet.
	//
	// Example return:
	//   auxFiles: &dataplane.AuxiliaryFiles{SSLCertificates: [...], ...}
	//   timestamp: 2025-01-15 10:30:45
	//   error: nil
	GetAuxiliaryFiles() (*dataplane.AuxiliaryFiles, time.Time, error)

	// GetResourceCounts returns a map of resource type → count.
	//
	// The keys are resource names as defined in the controller configuration
	// (e.g., "ingresses", "services", "haproxy-pods").
	//
	// Example return:
	//   {
	//     "ingresses": 5,
	//     "services": 12,
	//     "haproxy-pods": 2
	//   }
	GetResourceCounts() (map[string]int, error)

	// GetResourcesByType returns all resources of a specific type.
	//
	// The resourceType parameter should match a key from GetResourceCounts().
	//
	// Returns error if the resource type is not found.
	//
	// Example:
	//   resources, err := provider.GetResourcesByType("ingresses")
	GetResourcesByType(resourceType string) ([]interface{}, error)
}

// ComponentStatus represents the status of a controller component.
//
// Used by GetComponentStatus() to provide insight into component health.
type ComponentStatus struct {
	// Running indicates if the component is currently active
	Running bool `json:"running"`

	// LastSeen is the timestamp of the last activity from this component
	LastSeen time.Time `json:"last_seen"`

	// ErrorRate is the percentage of errors (0.0 to 1.0)
	// Optional - may be 0 if not tracked
	ErrorRate float64 `json:"error_rate,omitempty"`

	// Details provides additional component-specific information
	// Optional - may be nil
	Details map[string]interface{} `json:"details,omitempty"`
}
