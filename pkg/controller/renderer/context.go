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

// buildRenderingContext wraps stores for template access and builds the template context.
//
// The context structure is:
//
//	{
//	  "resources": {
//	    "ingresses": StoreWrapper,  // Provides List() and Get() methods
//	    "services": StoreWrapper,   // Provides List() and Get() methods
//	    "secrets": StoreWrapper,    // Provides List() and Get() methods
//	    // ... other watched resources
//	  }
//	}
//
// Templates can access resources with List() for iteration:
//
//	{% for ingress in resources.ingresses.List() %}
//	  {{ ingress.metadata.name }}
//	{% endfor %}
//
// Or with Get() for O(1) indexed lookups:
//
//	{% for endpoint_slice in resources.endpoints.Get(service_name) %}
//	  {{ endpoint_slice.metadata.name }}
//	{% endfor %}
func (c *Component) buildRenderingContext() map[string]interface{} {
	// Create resources map with wrapped stores
	resources := make(map[string]interface{})

	// Wrap each store to provide template-friendly methods
	for resourceTypeName, store := range c.stores {
		c.logger.Info("wrapping store for rendering context",
			"resource_type", resourceTypeName)
		resources[resourceTypeName] = &StoreWrapper{
			store:        store,
			resourceType: resourceTypeName,
			logger:       c.logger,
		}
	}

	c.logger.Info("rendering context built",
		"resource_count", len(resources))

	// Build final context with resources under "resources" key
	context := map[string]interface{}{
		"resources": resources,
	}

	return context
}
