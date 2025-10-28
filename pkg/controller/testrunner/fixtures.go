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

	for resourceType, resources := range fixtures {
		r.logger.Debug("Creating fixture store",
			"resource_type", resourceType,
			"count", len(resources))

		// Find watched resource config for this resource type
		watchedResource, exists := r.config.WatchedResources[resourceType]
		if !exists {
			return nil, fmt.Errorf("resource type %q not found in watched resources", resourceType)
		}

		// Create indexer for this resource type
		idx, err := indexer.New(indexer.Config{
			IndexBy:      watchedResource.IndexBy,
			IgnoreFields: r.config.WatchedResourcesIgnoreFields,
		})
		if err != nil {
			return nil, fmt.Errorf("failed to create indexer for %s: %w", resourceType, err)
		}

		// Create store with indexing configuration from watched resource
		// Use number of index fields for numKeys parameter
		numKeys := len(watchedResource.IndexBy)
		if numKeys < 1 {
			numKeys = 1
		}
		storeInstance := store.NewMemoryStore(numKeys)

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

		stores[resourceType] = storeInstance
	}

	return stores, nil
}
