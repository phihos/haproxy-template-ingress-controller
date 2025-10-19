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

// Package discovery provides the Discovery event adapter component.
//
// This package wraps the pure Discovery component (pkg/dataplane/discovery)
// with event-driven coordination. It subscribes to configuration, credentials,
// and pod change events, and publishes discovered HAProxy endpoints.
package discovery

import (
	"context"
	"fmt"
	"log/slog"
	"sync"

	"haproxy-template-ic/pkg/controller/events"
	coreconfig "haproxy-template-ic/pkg/core/config"
	busevents "haproxy-template-ic/pkg/events"
	"haproxy-template-ic/pkg/k8s/types"
)

const (
	// EventBufferSize is the buffer size for event subscriptions.
	EventBufferSize = 100
)

// Component is the Discovery event adapter.
//
// This component:
//   - Subscribes to ConfigValidatedEvent, CredentialsUpdatedEvent, and ResourceIndexUpdatedEvent
//   - Maintains current state (dataplanePort, credentials, podStore)
//   - Calls Discovery.DiscoverEndpoints() when relevant events occur
//   - Publishes HAProxyPodsDiscoveredEvent with discovered endpoints
//
// Event Flow:
//  1. ConfigValidatedEvent → Update dataplanePort → Trigger discovery
//  2. CredentialsUpdatedEvent → Update credentials → Trigger discovery
//  3. ResourceIndexUpdatedEvent (haproxy-pods) → Trigger discovery
//  4. Discovery completes → Publish HAProxyPodsDiscoveredEvent
type Component struct {
	discovery *Discovery
	eventBus  *busevents.EventBus
	logger    *slog.Logger

	// State protected by mutex
	mu               sync.RWMutex
	dataplanePort    int
	credentials      *coreconfig.Credentials
	podStore         types.Store
	hasCredentials   bool
	hasDataplanePort bool
}

// New creates a new Discovery event adapter component.
//
// Parameters:
//   - eventBus: The event bus for subscribing to and publishing events
//   - logger: Structured logger for observability
//
// Returns a configured Component ready to be started.
func New(eventBus *busevents.EventBus, logger *slog.Logger) *Component {
	return &Component{
		eventBus: eventBus,
		logger:   logger.With("component", "discovery"),
	}
}

// Start begins the Discovery component's event processing loop.
//
// This method:
//   - Subscribes to relevant events
//   - Maintains state from config and credential updates
//   - Triggers discovery when HAProxy pods change
//   - Publishes discovered endpoints
//   - Runs until context is cancelled
//
// Returns an error if the event loop fails.
func (c *Component) Start(ctx context.Context) error {
	c.logger.Info("starting discovery component")

	// Subscribe to events
	eventChan := c.eventBus.Subscribe(EventBufferSize)

	for {
		select {
		case event := <-eventChan:
			c.handleEvent(event)

		case <-ctx.Done():
			c.logger.Info("discovery component stopping")
			return ctx.Err()
		}
	}
}

// handleEvent processes incoming events and triggers discovery as needed.
func (c *Component) handleEvent(event interface{}) {
	switch e := event.(type) {
	case *events.ConfigValidatedEvent:
		c.handleConfigValidated(e)

	case *events.CredentialsUpdatedEvent:
		c.handleCredentialsUpdated(e)

	case *events.ResourceIndexUpdatedEvent:
		c.handleResourceIndexUpdated(e)

	case *events.ResourceSyncCompleteEvent:
		c.handleResourceSyncComplete(e)
	}
}

// handleConfigValidated processes ConfigValidatedEvent.
//
// Updates dataplanePort from config and triggers discovery if credentials are available.
func (c *Component) handleConfigValidated(event *events.ConfigValidatedEvent) {
	// Type-assert config
	config, ok := event.Config.(*coreconfig.Config)
	if !ok {
		c.logger.Error("invalid config type in ConfigValidatedEvent",
			"expected", "*coreconfig.Config",
			"actual", fmt.Sprintf("%T", event.Config))
		return
	}

	c.mu.Lock()
	oldPort := c.dataplanePort
	c.dataplanePort = config.Dataplane.Port
	c.hasDataplanePort = true

	// Recreate discovery instance with new port
	c.discovery = &Discovery{
		dataplanePort: c.dataplanePort,
	}

	// Check if we have all requirements for discovery
	podStore := c.podStore
	credentials := c.credentials
	hasCredentials := c.hasCredentials
	c.mu.Unlock()

	c.logger.Debug("config validated, updated dataplane port",
		"old_port", oldPort,
		"new_port", c.dataplanePort)

	// Trigger discovery if we have everything
	if hasCredentials && podStore != nil {
		c.triggerDiscovery(podStore, *credentials)
	}
}

// handleCredentialsUpdated processes CredentialsUpdatedEvent.
//
// Updates credentials and triggers discovery if config and pod store are available.
func (c *Component) handleCredentialsUpdated(event *events.CredentialsUpdatedEvent) {
	// Type-assert credentials
	credentials, ok := event.Credentials.(*coreconfig.Credentials)
	if !ok {
		c.logger.Error("invalid credentials type in CredentialsUpdatedEvent",
			"expected", "*coreconfig.Credentials",
			"actual", fmt.Sprintf("%T", event.Credentials))
		return
	}

	c.mu.Lock()
	c.credentials = credentials
	c.hasCredentials = true

	// Check if we have all requirements for discovery
	podStore := c.podStore
	hasDataplanePort := c.hasDataplanePort
	c.mu.Unlock()

	c.logger.Debug("credentials updated",
		"secret_version", event.SecretVersion)

	// Trigger discovery if we have everything
	if hasDataplanePort && podStore != nil {
		c.triggerDiscovery(podStore, *credentials)
	}
}

// handleResourceIndexUpdated processes ResourceIndexUpdatedEvent.
//
// Triggers discovery when HAProxy pods change (ignores initial sync).
func (c *Component) handleResourceIndexUpdated(event *events.ResourceIndexUpdatedEvent) {
	// Only handle haproxy-pods resource type
	if event.ResourceTypeName != "haproxy-pods" {
		return
	}

	// Skip initial sync events (wait for ResourceSyncCompleteEvent)
	if event.ChangeStats.IsInitialSync {
		c.logger.Debug("skipping initial sync event for haproxy-pods")
		return
	}

	c.logger.Debug("haproxy pods changed",
		"created", event.ChangeStats.Created,
		"modified", event.ChangeStats.Modified,
		"deleted", event.ChangeStats.Deleted)

	// Get current state
	c.mu.RLock()
	podStore := c.podStore
	credentials := c.credentials
	hasCredentials := c.hasCredentials
	hasDataplanePort := c.hasDataplanePort
	c.mu.RUnlock()

	// Trigger discovery if we have everything
	if hasCredentials && hasDataplanePort && podStore != nil {
		c.triggerDiscovery(podStore, *credentials)
	} else {
		c.logger.Debug("skipping discovery, missing requirements",
			"has_credentials", hasCredentials,
			"has_dataplane_port", hasDataplanePort,
			"has_pod_store", podStore != nil)
	}
}

// handleResourceSyncComplete processes ResourceSyncCompleteEvent.
//
// Triggers discovery after initial sync completes for HAProxy pods.
func (c *Component) handleResourceSyncComplete(event *events.ResourceSyncCompleteEvent) {
	// Only handle haproxy-pods resource type
	if event.ResourceTypeName != "haproxy-pods" {
		return
	}

	c.logger.Debug("haproxy pods initial sync complete")

	// Get current state
	c.mu.RLock()
	podStore := c.podStore
	credentials := c.credentials
	hasCredentials := c.hasCredentials
	hasDataplanePort := c.hasDataplanePort
	c.mu.RUnlock()

	// Trigger discovery if we have everything
	if hasCredentials && hasDataplanePort && podStore != nil {
		c.triggerDiscovery(podStore, *credentials)
	} else {
		c.logger.Debug("skipping discovery after sync, missing requirements",
			"has_credentials", hasCredentials,
			"has_dataplane_port", hasDataplanePort,
			"has_pod_store", podStore != nil)
	}
}

// SetPodStore sets the pod store reference.
//
// This is called by the controller after creating the haproxy-pods resource watcher.
// It allows the Discovery component to access pod resources for endpoint discovery.
//
// Thread-safe.
func (c *Component) SetPodStore(store types.Store) {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.podStore = store

	c.logger.Debug("pod store set")
}

// triggerDiscovery performs endpoint discovery and publishes the results.
//
// This method calls the pure Discovery component and publishes HAProxyPodsDiscoveredEvent.
func (c *Component) triggerDiscovery(podStore types.Store, credentials coreconfig.Credentials) {
	c.logger.Debug("triggering HAProxy pod discovery")

	// Call pure Discovery component
	endpoints, err := c.discovery.DiscoverEndpoints(podStore, credentials)
	if err != nil {
		c.logger.Error("discovery failed", "error", err)
		return
	}

	c.logger.Info("discovered HAProxy pods",
		"count", len(endpoints),
		"endpoints", endpoints)

	// Convert endpoints to []interface{} for event
	endpointsInterface := make([]interface{}, len(endpoints))
	for i, ep := range endpoints {
		endpointsInterface[i] = ep
	}

	// Publish HAProxyPodsDiscoveredEvent
	c.eventBus.Publish(events.NewHAProxyPodsDiscoveredEvent(
		endpointsInterface,
		len(endpoints),
	))
}
