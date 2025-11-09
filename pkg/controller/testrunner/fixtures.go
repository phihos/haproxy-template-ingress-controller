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

package testrunner

import (
	"fmt"

	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"

	"haproxy-template-ic/pkg/controller/resourcestore"
	"haproxy-template-ic/pkg/k8s/indexer"
	"haproxy-template-ic/pkg/k8s/store"
	"haproxy-template-ic/pkg/k8s/types"
)

// createStoresFromFixtures creates resource stores from test fixtures.
//
// This converts the test fixtures (map of resource type → list of resources)
// into resource stores that can be used for template rendering.
//
// Implementation:
//   - Phase 1: Create empty stores for ALL watched resources
//   - Phase 2: Populate stores with fixture data where provided
//
// This ensures templates can safely call .List() on any watched resource type,
// even if that resource type is not present in test fixtures.
//
// Parameters:
//   - fixtures: Map of resource type names to lists of Kubernetes resources
//
// Returns:
//   - Map of resource type names to resource stores
//   - error if fixture processing fails
//
//nolint:revive // Complexity acceptable for fixture processing with indexing and type inference
func (r *Runner) createStoresFromFixtures(fixtures map[string][]interface{}) (map[string]types.Store, error) {
	stores := make(map[string]types.Store)

	// PHASE 1: Create empty stores for ALL watched resources
	// This ensures templates can safely reference any watched resource type
	for resourceType, watchedResource := range r.config.WatchedResources {
		r.logger.Debug("Creating empty store for watched resource",
			"resource_type", resourceType)

		// Use number of index fields for numKeys parameter
		numKeys := len(watchedResource.IndexBy)
		if numKeys < 1 {
			numKeys = 1
		}
		stores[resourceType] = store.NewMemoryStore(numKeys)
	}

	// Create store for haproxy-pods (special controller metadata, not a watched resource)
	r.logger.Debug("Creating empty store for haproxy-pods (controller metadata)")
	stores["haproxy-pods"] = store.NewMemoryStore(2) // namespace + name keys

	// PHASE 2: Populate stores with fixture data
	for resourceType, resources := range fixtures {
		r.logger.Debug("Populating fixture store",
			"resource_type", resourceType,
			"count", len(resources))

		// Handle haproxy-pods specially (controller metadata, not a watched resource)
		if resourceType == "haproxy-pods" {
			storeInstance := stores["haproxy-pods"]

			for i, resourceObj := range resources {
				resourceMap, ok := resourceObj.(map[string]interface{})
				if !ok {
					return nil, fmt.Errorf("haproxy-pods fixture at index %d is not a map", i)
				}

				resource := &unstructured.Unstructured{Object: resourceMap}

				// Ensure TypeMeta for haproxy-pods (Pod resources)
				if resource.GetAPIVersion() == "" {
					resource.SetAPIVersion("v1")
				}
				if resource.GetKind() == "" {
					resource.SetKind("Pod")
				}

				r.logger.Debug("Adding haproxy-pods fixture to store",
					"index", i,
					"name", resource.GetName(),
					"namespace", resource.GetNamespace())

				// Use namespace + name as keys (matches discovery component indexing)
				keys := []string{resource.GetNamespace(), resource.GetName()}

				if err := storeInstance.Add(resource, keys); err != nil {
					return nil, fmt.Errorf("failed to add haproxy-pods fixture: %w", err)
				}
			}
			continue // Skip normal watched resource processing
		}

		// Verify resource type is in watched resources
		watchedResource, exists := r.config.WatchedResources[resourceType]
		if !exists {
			return nil, fmt.Errorf("resource type %q in fixtures not found in watched resources", resourceType)
		}

		// Create indexer for this resource type
		idx, err := indexer.New(indexer.Config{
			IndexBy:      watchedResource.IndexBy,
			IgnoreFields: r.config.WatchedResourcesIgnoreFields,
		})
		if err != nil {
			return nil, fmt.Errorf("failed to create indexer for %s: %w", resourceType, err)
		}

		// Get the existing empty store created in Phase 1
		storeInstance := stores[resourceType]

		// Add all fixture resources to the store
		for i, resourceObj := range resources {
			// Convert interface{} to unstructured.Unstructured
			// The interface{} is expected to be a map[string]interface{}
			resourceMap, ok := resourceObj.(map[string]interface{})
			if !ok {
				return nil, fmt.Errorf("fixture resource at index %d in %s is not a map", i, resourceType)
			}

			resource := &unstructured.Unstructured{Object: resourceMap}

			// Ensure resource has TypeMeta (some fixtures might omit it)
			if resource.GetAPIVersion() == "" {
				resource.SetAPIVersion(watchedResource.APIVersion)
			}
			if resource.GetKind() == "" {
				// Extract kind from resource name (e.g., "ingresses" → "Ingress")
				// This is a heuristic; proper kind resolution would use RESTMapper
				kind := resourcestore.SingularizeResourceType(watchedResource.Resources)
				resource.SetKind(kind)
			}

			r.logger.Debug("Adding fixture resource to store",
				"resource_type", resourceType,
				"index", i,
				"name", resource.GetName(),
				"namespace", resource.GetNamespace())

			// Extract index keys using indexer
			keys, err := idx.ExtractKeys(resource)
			if err != nil {
				return nil, fmt.Errorf("failed to extract index keys from fixture resource: %w", err)
			}

			if err := storeInstance.Add(resource, keys); err != nil {
				return nil, fmt.Errorf("failed to add fixture resource to %s store: %w", resourceType, err)
			}
		}
	}

	return stores, nil
}
