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
//   - Subscribes to ConfigValidatedEvent, CredentialsUpdatedEvent, ResourceIndexUpdatedEvent, and BecameLeaderEvent
//   - Maintains current state (dataplanePort, credentials, podStore)
//   - Calls Discovery.DiscoverEndpoints() when relevant events occur
//   - Publishes HAProxyPodsDiscoveredEvent with discovered endpoints
//   - Publishes HAProxyPodTerminatedEvent when pods are removed
//
// Event Flow:
//  1. ConfigValidatedEvent → Update dataplanePort → Trigger discovery
//  2. CredentialsUpdatedEvent → Update credentials → Trigger discovery
//  3. ResourceIndexUpdatedEvent (haproxy-pods) → Trigger discovery
//  4. BecameLeaderEvent → Re-trigger discovery for new leader's DeploymentScheduler
//  5. Discovery completes → Compare with previous endpoints → Publish HAProxyPodTerminatedEvent for removed pods → Publish HAProxyPodsDiscoveredEvent
type Component struct {
	discovery *Discovery
	eventBus  *busevents.EventBus
	logger    *slog.Logger

	// State protected by mutex
	mu               sync.RWMutex
	dataplanePort    int
	credentials      *coreconfig.Credentials
	podStore         types.Store
	lastEndpoints    map[string]string // Map of PodName → PodNamespace for tracking removals
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
		eventBus:      eventBus,
		logger:        logger.With("component", "discovery"),
		lastEndpoints: make(map[string]string),
	}
}

// Start begins the Discovery component's event processing loop.
//
// This method:
//   - Subscribes to relevant events
//   - Checks for existing pods and triggers initial discovery if needed
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

	// Perform initial discovery check after subscribing
	// This ensures we discover pods even if ResourceSyncCompleteEvent was already published
	c.performInitialDiscovery()

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

	case *events.BecameLeaderEvent:
		c.handleBecameLeader(e)
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

// handleBecameLeader processes BecameLeaderEvent.
//
// Re-publishes HAProxy pod discovery when this replica becomes leader.
// This ensures the DeploymentScheduler (which only starts on the leader) receives
// current endpoint state even if pods were discovered before leadership was acquired.
func (c *Component) handleBecameLeader(_ *events.BecameLeaderEvent) {
	c.logger.Info("became leader, re-discovering HAProxy pods for deployment scheduler")

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
		c.logger.Warn("became leader but cannot discover pods yet, missing requirements",
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

// performInitialDiscovery checks if pods already exist and triggers discovery.
//
// This is called after subscribing to events to handle the case where
// ResourceSyncCompleteEvent was already published before we subscribed.
func (c *Component) performInitialDiscovery() {
	c.mu.RLock()
	podStore := c.podStore
	credentials := c.credentials
	hasCredentials := c.hasCredentials
	hasDataplanePort := c.hasDataplanePort
	c.mu.RUnlock()

	// Check if we have all requirements
	if !hasCredentials || !hasDataplanePort || podStore == nil {
		c.logger.Debug("skipping initial discovery, missing requirements",
			"has_credentials", hasCredentials,
			"has_dataplane_port", hasDataplanePort,
			"has_pod_store", podStore != nil)
		return
	}

	// Check if pods exist in store
	pods, err := podStore.List()
	if err != nil {
		c.logger.Error("failed to list pods during initial discovery", "error", err)
		return
	}

	if len(pods) == 0 {
		c.logger.Debug("no pods found during initial discovery check")
		return
	}

	c.logger.Info("found existing pods during initial discovery check",
		"count", len(pods))

	// Trigger discovery
	c.triggerDiscovery(podStore, *credentials)
}

// triggerDiscovery performs endpoint discovery and publishes the results.
//
// This method calls the pure Discovery component, detects removed pods,
// publishes HAProxyPodTerminatedEvent for removed pods, and publishes HAProxyPodsDiscoveredEvent.
func (c *Component) triggerDiscovery(podStore types.Store, credentials coreconfig.Credentials) {
	c.logger.Debug("triggering HAProxy pod discovery")

	// Call pure Discovery component with logger for debugging
	endpoints, err := c.discovery.DiscoverEndpointsWithLogger(podStore, credentials, c.logger)
	if err != nil {
		c.logger.Error("discovery failed", "error", err)
		return
	}

	// Log summary
	c.logger.Info("discovered HAProxy pods",
		"count", len(endpoints))

	// Log detailed endpoint list for debugging connection issues
	if c.logger != nil && len(endpoints) > 0 {
		for i, ep := range endpoints {
			c.logger.Debug("discovered endpoint",
				"index", i,
				"pod", ep.PodName,
				"url", ep.URL)
		}
	}

	// Build map of current endpoints for comparison
	currentEndpoints := make(map[string]string)
	for _, ep := range endpoints {
		currentEndpoints[ep.PodName] = ep.PodNamespace
	}

	// Detect removed pods and publish termination events
	c.mu.Lock()
	for podName, podNamespace := range c.lastEndpoints {
		if _, exists := currentEndpoints[podName]; !exists {
			// Pod was removed
			c.logger.Info("detected pod termination",
				"pod_name", podName,
				"pod_namespace", podNamespace)

			// Publish HAProxyPodTerminatedEvent (without holding lock)
			c.mu.Unlock()
			c.eventBus.Publish(events.NewHAProxyPodTerminatedEvent(podName, podNamespace))
			c.mu.Lock()
		}
	}

	// Update last endpoints cache
	c.lastEndpoints = currentEndpoints
	c.mu.Unlock()

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
