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
	"sort"

	"haproxy-template-ic/pkg/core/config"
)

// buildRenderingContext wraps stores for template access and builds the template context.
//
// The context structure is:
//
//	{
//	  "resources": {
//	    "ingresses": StoreWrapper,  // Provides List(), Fetch(), and GetSingle() methods
//	    "services": StoreWrapper,
//	    "secrets": StoreWrapper,
//	    // ... other watched resources
//	  },
//	  "template_snippets": ["snippet1", "snippet2", ...]  // Sorted by priority
//	}
//
// Templates can access resources:
//
//	{% for ingress in resources.ingresses.List() %}
//	  {{ ingress.metadata.name }}
//	{% endfor %}
//
// And iterate over matching template snippets:
//
//	{%- set matching = template_snippets | glob_match("backend-annotation-*") %}
//	{%- for snippet_name in matching %}
//	  {% include snippet_name %}
//	{%- endfor %}
func (c *Component) buildRenderingContext() map[string]interface{} {
	// Create resources map with wrapped stores
	resources := make(map[string]interface{})

	// Wrap each store to provide template-friendly methods
	for resourceTypeName, store := range c.stores {
		c.logger.Info("wrapping store for rendering context",
			"resource_type", resourceTypeName)
		resources[resourceTypeName] = &StoreWrapper{
			Store:        store,
			ResourceType: resourceTypeName,
			Logger:       c.logger,
		}
	}

	// Sort template snippets by priority for template access
	snippetNames := sortSnippetsByPriority(c.config.TemplateSnippets)

	c.logger.Info("rendering context built",
		"resource_count", len(resources),
		"snippet_count", len(snippetNames))

	// Build final context
	context := map[string]interface{}{
		"resources":         resources,
		"template_snippets": snippetNames,
	}

	return context
}

// sortSnippetsByPriority sorts template snippet names by priority, then alphabetically.
// Returns a slice of snippet names in the sorted order.
//
// Snippets without an explicit priority default to 500.
// Lower priority values are sorted first.
func sortSnippetsByPriority(snippets map[string]config.TemplateSnippet) []string {
	type snippetWithPriority struct {
		name     string
		priority int
	}

	// Build list with priorities
	list := make([]snippetWithPriority, 0, len(snippets))
	for name, snippet := range snippets {
		priority := snippet.Priority
		if priority == 0 {
			priority = 500 // Default priority
		}
		list = append(list, snippetWithPriority{name, priority})
	}

	// Sort by priority (ascending), then by name (alphabetically)
	sort.Slice(list, func(i, j int) bool {
		if list[i].priority != list[j].priority {
			return list[i].priority < list[j].priority
		}
		return list[i].name < list[j].name
	})

	// Extract sorted names
	names := make([]string, len(list))
	for i, item := range list {
		names[i] = item.name
	}

	return names
}
