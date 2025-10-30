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

// Package renderer implements the Renderer component that renders HAProxy
// configuration and auxiliary files from templates.
//
// The Renderer is a Stage 5 component that subscribes to reconciliation
// trigger events, builds rendering context from resource stores, and publishes
// rendered output events for the next phase (validation/deployment).
package renderer

import (
	"context"
	"fmt"
	"log/slog"
	"sync"
	"time"

	"haproxy-template-ic/pkg/controller/events"
	"haproxy-template-ic/pkg/core/config"
	"haproxy-template-ic/pkg/dataplane"
	"haproxy-template-ic/pkg/dataplane/auxiliaryfiles"
	busevents "haproxy-template-ic/pkg/events"
	"haproxy-template-ic/pkg/k8s/types"
	"haproxy-template-ic/pkg/templating"
)

const (
	// EventBufferSize is the size of the event subscription buffer.
	EventBufferSize = 50
)

// Component implements the renderer component.
//
// It subscribes to ReconciliationTriggeredEvent and BecameLeaderEvent, renders all templates
// using the template engine and resource stores, and publishes the results
// via TemplateRenderedEvent or TemplateRenderFailedEvent.
//
// The component caches the last rendered output to support state replay during
// leadership transitions (when new leader-only components start subscribing).
type Component struct {
	eventBus *busevents.EventBus
	engine   *templating.TemplateEngine
	config   *config.Config
	stores   map[string]types.Store
	logger   *slog.Logger

	// State protected by mutex (for leadership transition replay)
	mu                   sync.RWMutex
	lastHAProxyConfig    string
	lastAuxiliaryFiles   *dataplane.AuxiliaryFiles
	lastAuxFileCount     int
	lastRenderDurationMs int64
	hasRenderedConfig    bool
}

// New creates a new Renderer component.
//
// The component pre-compiles all templates during initialization for optimal
// runtime performance.
//
// Parameters:
//   - eventBus: The EventBus for subscribing to events and publishing results
//   - config: Controller configuration containing templates
//   - stores: Map of resource type names to their stores (e.g., "ingresses" -> Store)
//   - logger: Structured logger for component logging
//
// Returns:
//   - A new Component instance ready to be started
//   - Error if template compilation fails
func New(
	eventBus *busevents.EventBus,
	config *config.Config,
	stores map[string]types.Store,
	logger *slog.Logger,
) (*Component, error) {
	// Log stores received during initialization
	logger.Info("creating renderer component",
		"store_count", len(stores))
	for resourceTypeName := range stores {
		logger.Info("renderer received store",
			"resource_type", resourceTypeName)
	}

	// Extract all templates from config
	templates := extractTemplates(config)

	// Create path resolver for get_path filter
	pathResolver := &templating.PathResolver{
		MapsDir:    config.Dataplane.MapsDir,
		SSLDir:     config.Dataplane.SSLCertsDir,
		GeneralDir: config.Dataplane.GeneralStorageDir,
	}

	// Register custom filters
	filters := map[string]templating.FilterFunc{
		"get_path":   pathResolver.GetPath,
		"glob_match": templating.GlobMatch,
		"b64decode":  templating.B64Decode,
	}

	// Register custom global functions
	functions := map[string]templating.GlobalFunc{
		"fail": failFunction,
	}

	// Pre-compile all templates with custom filters and functions
	engine, err := templating.New(templating.EngineTypeGonja, templates, filters, functions)
	if err != nil {
		return nil, fmt.Errorf("failed to create template engine: %w", err)
	}

	return &Component{
		eventBus: eventBus,
		engine:   engine,
		config:   config,
		stores:   stores,
		logger:   logger,
	}, nil
}

// Start begins the renderer's event loop.
//
// This method blocks until the context is cancelled or an error occurs.
// It subscribes to the EventBus and processes events:
//   - ReconciliationTriggeredEvent: Starts template rendering
//
// The component runs until the context is cancelled, at which point it
// performs cleanup and returns.
//
// Parameters:
//   - ctx: Context for cancellation and lifecycle management
//
// Returns:
//   - nil when context is cancelled (graceful shutdown)
//   - Error only in exceptional circumstances
func (c *Component) Start(ctx context.Context) error {
	c.logger.Info("Renderer starting")

	eventChan := c.eventBus.Subscribe(EventBufferSize)

	for {
		select {
		case event := <-eventChan:
			c.handleEvent(event)

		case <-ctx.Done():
			c.logger.Info("Renderer shutting down", "reason", ctx.Err())
			return nil
		}
	}
}

// handleEvent processes events from the EventBus.
func (c *Component) handleEvent(event busevents.Event) {
	switch ev := event.(type) {
	case *events.ReconciliationTriggeredEvent:
		c.handleReconciliationTriggered(ev)

	case *events.BecameLeaderEvent:
		c.handleBecameLeader(ev)
	}
}

// handleReconciliationTriggered renders all templates when reconciliation is triggered.
func (c *Component) handleReconciliationTriggered(event *events.ReconciliationTriggeredEvent) {
	startTime := time.Now()

	c.logger.Info("Template rendering triggered", "reason", event.Reason)

	// Build rendering context from all resource stores
	c.logger.Info("building rendering context")
	context := c.buildRenderingContext()

	// Render main HAProxy configuration
	c.logger.Info("rendering main template")
	haproxyConfig, err := c.engine.Render("haproxy.cfg", context)
	if err != nil {
		c.publishRenderFailure("haproxy.cfg", err)
		return
	}

	// Render all auxiliary files
	auxiliaryFiles, err := c.renderAuxiliaryFiles(context)
	if err != nil {
		// Error already published by renderAuxiliaryFiles
		return
	}

	// Calculate metrics
	durationMs := time.Since(startTime).Milliseconds()
	auxFileCount := len(auxiliaryFiles.MapFiles) +
		len(auxiliaryFiles.GeneralFiles) +
		len(auxiliaryFiles.SSLCertificates)

	c.logger.Info("Template rendering completed",
		"config_bytes", len(haproxyConfig),
		"auxiliary_files", auxFileCount,
		"duration_ms", durationMs)

	// Cache rendered output for leadership transition replay
	c.mu.Lock()
	c.lastHAProxyConfig = haproxyConfig
	c.lastAuxiliaryFiles = auxiliaryFiles
	c.lastAuxFileCount = auxFileCount
	c.lastRenderDurationMs = durationMs
	c.hasRenderedConfig = true
	c.mu.Unlock()

	// Publish success event with rendered content
	c.eventBus.Publish(events.NewTemplateRenderedEvent(
		haproxyConfig,
		auxiliaryFiles,
		auxFileCount,
		durationMs,
	))
}

// handleBecameLeader handles BecameLeaderEvent by re-publishing the last rendered config.
//
// This ensures DeploymentScheduler (which starts subscribing only after becoming leader)
// receives the current rendered state, even if rendering occurred before leadership was acquired.
//
// This prevents the "late subscriber problem" where leader-only components miss events
// that were published before they started subscribing.
func (c *Component) handleBecameLeader(_ *events.BecameLeaderEvent) {
	c.mu.RLock()
	hasState := c.hasRenderedConfig
	haproxyConfig := c.lastHAProxyConfig
	auxiliaryFiles := c.lastAuxiliaryFiles
	auxFileCount := c.lastAuxFileCount
	durationMs := c.lastRenderDurationMs
	c.mu.RUnlock()

	if !hasState {
		c.logger.Debug("became leader but no rendered config available yet, skipping state replay")
		return
	}

	c.logger.Info("became leader, re-publishing last rendered config for DeploymentScheduler",
		"config_bytes", len(haproxyConfig),
		"auxiliary_files", auxFileCount)

	// Re-publish the last rendered event to ensure new leader-only components receive it
	c.eventBus.Publish(events.NewTemplateRenderedEvent(
		haproxyConfig,
		auxiliaryFiles,
		auxFileCount,
		durationMs,
	))
}

// renderAuxiliaryFiles renders all auxiliary files (maps, general files, SSL certificates).
func (c *Component) renderAuxiliaryFiles(context map[string]interface{}) (*dataplane.AuxiliaryFiles, error) {
	auxFiles := &dataplane.AuxiliaryFiles{}

	// Render map files
	for name := range c.config.Maps {
		rendered, err := c.engine.Render(name, context)
		if err != nil {
			c.publishRenderFailure(name, err)
			return nil, err
		}

		auxFiles.MapFiles = append(auxFiles.MapFiles, auxiliaryfiles.MapFile{
			Path:    name,
			Content: rendered,
		})
	}

	// Render general files
	for name := range c.config.Files {
		rendered, err := c.engine.Render(name, context)
		if err != nil {
			c.publishRenderFailure(name, err)
			return nil, err
		}

		auxFiles.GeneralFiles = append(auxFiles.GeneralFiles, auxiliaryfiles.GeneralFile{
			Filename: name,
			Content:  rendered,
		})
	}

	// Render SSL certificates
	for name := range c.config.SSLCertificates {
		rendered, err := c.engine.Render(name, context)
		if err != nil {
			c.publishRenderFailure(name, err)
			return nil, err
		}

		auxFiles.SSLCertificates = append(auxFiles.SSLCertificates, auxiliaryfiles.SSLCertificate{
			Path:    name,
			Content: rendered,
		})
	}

	return auxFiles, nil
}

// publishRenderFailure publishes a template render failure event.
func (c *Component) publishRenderFailure(templateName string, err error) {
	// Get template content for context in error message
	templateContent, _ := c.engine.GetRawTemplate(templateName)

	// Format error for human readability
	formattedError := templating.FormatRenderError(err, templateName, templateContent)

	// Log formatted error (multi-line for readability)
	c.logger.Error("Template rendering failed\n"+formattedError,
		"template", templateName,
		"error_raw", err.Error()) // Keep raw error for programmatic access

	// Publish event with formatted error
	c.eventBus.Publish(events.NewTemplateRenderFailedEvent(
		templateName,
		formattedError,
		"", // Stack trace could be added here if needed
	))
}

// extractTemplates converts config templates to map for engine initialization.
func extractTemplates(cfg *config.Config) map[string]string {
	templates := make(map[string]string)

	// Main HAProxy config
	templates["haproxy.cfg"] = cfg.HAProxyConfig.Template

	// Template snippets
	for name, snippet := range cfg.TemplateSnippets {
		templates[name] = snippet.Template
	}

	// Map files
	for name, mapDef := range cfg.Maps {
		templates[name] = mapDef.Template
	}

	// General files
	for name, fileDef := range cfg.Files {
		templates[name] = fileDef.Template
	}

	// SSL certificates
	for name, certDef := range cfg.SSLCertificates {
		templates[name] = certDef.Template
	}

	return templates
}

// failFunction is a global function that causes template rendering to fail with a custom error message.
// This is useful for template-level validation where we want to provide clear error messages
// when required resources are missing or invalid.
//
// Usage in templates:
//
//	{% if secret is none %}
//	  {{ fail("Secret 'namespace/name' referenced by annotation 'haproxy.org/auth-secret' does not exist") }}
//	{% endif %}
func failFunction(args ...interface{}) (interface{}, error) {
	// Validate arguments
	if len(args) != 1 {
		return nil, fmt.Errorf("fail() requires exactly one string argument, got %d arguments", len(args))
	}

	message, ok := args[0].(string)
	if !ok {
		return nil, fmt.Errorf("fail() argument must be a string, got %T", args[0])
	}

	// Return error with the custom message
	// This will cause template rendering to fail and propagate the error
	// through the validation webhook to the user
	return nil, fmt.Errorf("%s", message)
}
