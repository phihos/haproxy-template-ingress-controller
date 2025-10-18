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

// buildRenderingContext extracts all resources from stores and builds the template context.
//
// The context structure is:
//
//	{
//	  "resources": {
//	    "ingresses": [...],  // All resources of type "ingresses"
//	    "services": [...],   // All resources of type "services"
//	    "secrets": [...],    // All resources of type "secrets"
//	    // ... other watched resources
//	  }
//	}
//
// Templates can access resources like: {{ resources.ingresses }}.
func (c *Component) buildRenderingContext() map[string]interface{} {
	// Create resources map
	resources := make(map[string]interface{})

	// Extract all resources from each store
	for resourceTypeName, store := range c.stores {
		resourceList, err := store.List()
		if err != nil {
			c.logger.Warn("failed to list resources from store",
				"resource_type", resourceTypeName,
				"error", err)
			// Continue with empty list for this resource type
			resources[resourceTypeName] = []interface{}{}
			continue
		}

		resources[resourceTypeName] = resourceList
	}

	// Build final context with resources under "resources" key
	context := map[string]interface{}{
		"resources": resources,
	}

	return context
}
