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

// Package deployer implements the Deployer component that deploys validated
// HAProxy configurations to discovered HAProxy pod endpoints.
//
// The Deployer maintains state of the last validated configuration and handles
// two deployment scenarios:
//  1. Full reconciliation: Deploy newly validated config to current endpoints
//  2. Pod changes only: Re-deploy last validated config to new set of endpoints
package deployer

import (
	"context"
	"log/slog"
	"sync"

	"haproxy-template-ic/pkg/controller/events"
	busevents "haproxy-template-ic/pkg/events"
)

const (
	// EventBufferSize is the size of the event subscription buffer.
	EventBufferSize = 50
)

// Component implements the deployer component.
//
// It subscribes to validation completion and pod discovery events,
// maintains the last validated configuration, and deploys to HAProxy instances.
//
// Event subscriptions:
//   - ValidationCompletedEvent: Cache validated config and deploy to current endpoints
//   - HAProxyPodsDiscoveredEvent: Re-deploy cached config to new endpoints
//
// The component publishes deployment result events for observability.
type Component struct {
	eventBus *busevents.EventBus
	logger   *slog.Logger

	// State protected by mutex
	mu                  sync.RWMutex
	lastValidatedConfig string        //nolint:unused // Will be used when deployment is implemented
	lastAuxiliaryFiles  interface{}   //nolint:unused // Will be used when deployment is implemented
	currentEndpoints    []interface{} // Current HAProxy pod endpoints
	hasValidConfig      bool          // Whether we have a validated config to deploy
}

// New creates a new Deployer component.
//
// Parameters:
//   - eventBus: The EventBus for subscribing to events and publishing results
//   - logger: Structured logger for component logging
//
// Returns:
//   - A new Component instance ready to be started
func New(eventBus *busevents.EventBus, logger *slog.Logger) *Component {
	return &Component{
		eventBus: eventBus,
		logger:   logger.With("component", "deployer"),
	}
}

// Start begins the deployer's event loop.
//
// This method blocks until the context is cancelled or an error occurs.
// It subscribes to the EventBus and processes events:
//   - ValidationCompletedEvent: Cache config and deploy to current endpoints
//   - HAProxyPodsDiscoveredEvent: Re-deploy cached config to new endpoints
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
	c.logger.Info("Deployer starting")

	eventChan := c.eventBus.Subscribe(EventBufferSize)

	for {
		select {
		case event := <-eventChan:
			c.handleEvent(event)

		case <-ctx.Done():
			c.logger.Info("Deployer shutting down", "reason", ctx.Err())
			return nil
		}
	}
}

// handleEvent processes events from the EventBus.
func (c *Component) handleEvent(event busevents.Event) {
	switch e := event.(type) {
	case *events.ValidationCompletedEvent:
		c.handleValidationCompleted(e)

	case *events.HAProxyPodsDiscoveredEvent:
		c.handlePodsDiscovered(e)
	}
}

// handleValidationCompleted handles successful configuration validation.
//
// This caches the validated configuration and triggers deployment to current endpoints.
// This is called during full reconciliation cycles (config or resource changes).
func (c *Component) handleValidationCompleted(event *events.ValidationCompletedEvent) {
	c.logger.Info("Validation completed, caching config for deployment",
		"warnings", len(event.Warnings),
		"duration_ms", event.DurationMs)

	// Log warnings if any
	for _, warning := range event.Warnings {
		c.logger.Warn("Validation warning", "warning", warning)
	}

	// TODO: Extract validated config from preceding TemplateRenderedEvent
	// For now, this is a stub - we need to wire up config flow

	c.logger.Debug("Deployment phase not yet implemented")
}

// handlePodsDiscovered handles HAProxy pod discovery/changes.
//
// This re-deploys the last validated configuration to the new set of endpoints.
// This is called when HAProxy pods are added/removed/updated without config changes.
func (c *Component) handlePodsDiscovered(event *events.HAProxyPodsDiscoveredEvent) {
	c.mu.Lock()
	c.currentEndpoints = event.Endpoints
	endpointCount := len(event.Endpoints)
	hasValidConfig := c.hasValidConfig
	c.mu.Unlock()

	c.logger.Info("HAProxy pods discovered",
		"count", endpointCount)

	if !hasValidConfig {
		c.logger.Debug("No validated config available yet, skipping deployment")
		return
	}

	// TODO: Implement re-deployment to new endpoints
	//   1. Deploy lastValidatedConfig to currentEndpoints
	//   2. Publish DeploymentCompletedEvent or DeploymentFailedEvent
	c.logger.Debug("Re-deployment to new endpoints not yet implemented",
		"endpoint_count", endpointCount)
}
