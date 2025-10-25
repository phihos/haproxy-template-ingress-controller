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

package renderer

import (
	"log/slog"

	"haproxy-template-ic/pkg/k8s/types"
)

// StoreWrapper wraps a types.Store to provide template-friendly methods
// that don't return errors (errors are logged instead).
//
// This allows templates to call methods like List() and Get() directly
// without having to handle Go's multi-return values, which Gonja templates
// may not support cleanly.
//
// The wrapper implements lazy-cached unwrapping:
//   - List() results are unwrapped once on first call and cached for the reconciliation
//   - Get() results are unwrapped on-demand (typically small result sets)
type StoreWrapper struct {
	store        types.Store
	resourceType string
	logger       *slog.Logger

	// Lazy cache for List() results
	cachedList []interface{}
	listCached bool
}

// List returns all resources in the store.
//
// This method is intended for template iteration:
//
//	{% for ingress in resources.ingresses.List() %}
//	  {{ ingress.metadata.name }}
//	{% endfor %}
//
// Resources are unwrapped from unstructured.Unstructured to maps on first call
// and cached for subsequent calls within the same reconciliation cycle.
//
// If an error occurs, it's logged and an empty slice is returned.
func (w *StoreWrapper) List() []interface{} {
	// Return cached result if already unwrapped
	if w.listCached {
		w.logger.Debug("returning cached list",
			"resource_type", w.resourceType,
			"count", len(w.cachedList))
		return w.cachedList
	}

	// First call - fetch from store
	items, err := w.store.List()
	if err != nil {
		w.logger.Warn("failed to list resources from store",
			"resource_type", w.resourceType,
			"error", err)
		return []interface{}{}
	}

	w.logger.Info("unwrapping and caching list",
		"resource_type", w.resourceType,
		"count", len(items))

	// Unwrap unstructured resources to maps for template access
	unwrapped := make([]interface{}, len(items))
	for i, item := range items {
		unwrapped[i] = unwrapUnstructured(item)
	}

	// Cache for subsequent calls
	w.cachedList = unwrapped
	w.listCached = true

	return unwrapped
}

// Fetch performs O(1) indexed lookup using the provided keys.
//
// This method enables efficient lookups in templates and supports non-unique index keys
// by returning all resources matching the provided keys:
//
//	{% for endpoint_slice in resources.endpoints.Fetch(service_name) %}
//	  {{ endpoint_slice.metadata.name }}
//	{% endfor %}
//
// The keys must match the index configuration for the resource type.
// For example, if EndpointSlices are indexed by service name:
//
//	index_by: ["metadata.labels['kubernetes.io/service-name']"]
//
// Then you can look them up with:
//
//	resources.endpoints.Fetch("my-service")
//
// This will return ALL EndpointSlices for that service (typically multiple).
//
// If an error occurs, it's logged and an empty slice is returned.
func (w *StoreWrapper) Fetch(keys ...string) []interface{} {
	items, err := w.store.Get(keys...)
	if err != nil {
		w.logger.Warn("failed to fetch indexed resources from store",
			"resource_type", w.resourceType,
			"keys", keys,
			"error", err)
		return []interface{}{}
	}

	w.logger.Info("store fetch called",
		"resource_type", w.resourceType,
		"keys", keys,
		"found_count", len(items))

	// Unwrap unstructured resources to maps for template access
	unwrapped := make([]interface{}, len(items))
	for i, item := range items {
		unwrapped[i] = unwrapUnstructured(item)
	}

	return unwrapped
}

// GetSingle performs O(1) indexed lookup and expects exactly one matching resource.
//
// This method is useful when you know the index keys uniquely identify a resource:
//
//	{% set ingress = resources.ingresses.GetSingle("default", "my-ingress") %}
//	{% if ingress %}
//	  {{ ingress.metadata.name }}
//	{% endif %}
//
// Returns:
//   - nil if no resources match (this is NOT an error - allows templates to check existence)
//   - The single matching resource if exactly one matches
//   - nil + logs error if multiple resources match (ambiguous lookup)
//
// If an error occurs during the store operation, it's logged and nil is returned.
func (w *StoreWrapper) GetSingle(keys ...string) interface{} {
	items, err := w.store.Get(keys...)
	if err != nil {
		w.logger.Warn("failed to get single resource from store",
			"resource_type", w.resourceType,
			"keys", keys,
			"error", err)
		return nil
	}

	w.logger.Info("store GetSingle called",
		"resource_type", w.resourceType,
		"keys", keys,
		"found_count", len(items))

	if len(items) == 0 {
		// No resources found - this is valid, not an error
		return nil
	}

	if len(items) > 1 {
		// Ambiguous lookup - multiple resources match
		w.logger.Error("GetSingle found multiple resources (ambiguous lookup)",
			"resource_type", w.resourceType,
			"keys", keys,
			"count", len(items))
		return nil
	}

	// Exactly one resource found
	return unwrapUnstructured(items[0])
}

// unwrapUnstructured extracts the underlying data map from unstructured.Unstructured.
//
// Templates need to access resource fields like ingress.spec.rules, but Kubernetes
// resources are stored as unstructured.Unstructured objects. This function converts
// them to plain maps so templates can access fields naturally.
func unwrapUnstructured(resource interface{}) interface{} {
	// Type assert to interface with UnstructuredContent method
	type unstructuredInterface interface {
		UnstructuredContent() map[string]interface{}
	}

	if u, ok := resource.(unstructuredInterface); ok {
		return u.UnstructuredContent()
	}

	// Not an unstructured object, return as-is
	return resource
}
