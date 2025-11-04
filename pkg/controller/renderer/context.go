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
//	  "controller": {
//	    "haproxy_pods": StoreWrapper,  // HAProxy controller pods for pod-maxconn calculations
//	  },
//	  "template_snippets": ["snippet1", "snippet2", ...]  // Sorted by priority
//	  "config": Config,  // Controller configuration (e.g., config.debug.headers.enabled)
//	}
//
// Templates can access resources:
//
//	{% for ingress in resources.ingresses.List() %}
//	  {{ ingress.metadata.name }}
//	{% endfor %}
//
// Templates can access controller metadata:
//
//	{%- set pod_count = controller.haproxy_pods.List() | length %}
//	{%- if pod_count > 0 %}
//	  {# Distribute load across {{ pod_count }} HAProxy replicas #}
//	{%- endif %}
//
// Iterate over matching template snippets:
//
//	{%- set matching = template_snippets | glob_match("backend-annotation-*") %}
//	{%- for snippet_name in matching %}
//	  {% include snippet_name %}
//	{%- endfor %}
//
// And access controller configuration:
//
//	{%- if config.debug.headers.enabled | default(false) %}
//	  http-response set-header X-Debug-Info %[var(txn.backend_name)]
//	{%- endif %}
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

	// Create controller namespace with HAProxy pods store
	controller := make(map[string]interface{})
	if c.haproxyPodStore != nil {
		c.logger.Info("wrapping HAProxy pods store for rendering context")
		controller["haproxy_pods"] = &StoreWrapper{
			Store:        c.haproxyPodStore,
			ResourceType: "haproxy-pods",
			Logger:       c.logger,
		}
	} else {
		c.logger.Warn("HAProxy pods store is nil, controller.haproxy_pods will not be available")
	}

	// Sort template snippets by priority for template access
	snippetNames := sortSnippetsByPriority(c.config.TemplateSnippets)

	c.logger.Info("rendering context built",
		"resource_count", len(resources),
		"controller_fields", len(controller),
		"snippet_count", len(snippetNames))

	// Build final context
	context := map[string]interface{}{
		"resources":         resources,
		"controller":        controller,
		"template_snippets": snippetNames,
	}

	// Merge extraContext variables into top-level context
	MergeExtraContextInto(context, c.config)

	if c.config.TemplatingSettings.ExtraContext != nil {
		c.logger.Info("added extra context variables to template context",
			"variable_count", len(c.config.TemplatingSettings.ExtraContext))
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

// MergeExtraContextInto merges the extraContext variables from the config into the provided template context.
//
// This allows templates to access custom variables directly (e.g., {{ debug.enabled }})
// instead of wrapping them in a "config" object.
//
// If extraContext is nil or empty, the context is left unchanged.
func MergeExtraContextInto(context map[string]interface{}, cfg *config.Config) {
	if cfg.TemplatingSettings.ExtraContext != nil {
		for key, value := range cfg.TemplatingSettings.ExtraContext {
			context[key] = value
		}
	}
}
