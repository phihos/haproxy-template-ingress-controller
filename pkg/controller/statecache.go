// Copyright 2025 Philipp Hossner.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at.
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software.
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and.
// limitations under the License.

package controller

import (
	"context"
	"fmt"
	"sync"
	"time"

	"haproxy-template-ic/pkg/controller/debug"
	"haproxy-template-ic/pkg/controller/events"
	"haproxy-template-ic/pkg/controller/resourcewatcher"
	coreconfig "haproxy-template-ic/pkg/core/config"
	"haproxy-template-ic/pkg/dataplane"
	busevents "haproxy-template-ic/pkg/events"
)

// StateCache caches controller state by subscribing to events.
//
// This component implements the debug.StateProvider interface and provides
// thread-safe access to the controller's internal state for debug purposes.
//
// It subscribes to key events and updates its cached state accordingly:.
//   - ConfigValidatedEvent → updates config cache
//   - CredentialsUpdatedEvent → updates credentials cache
//   - RenderCompletedEvent → updates rendered config cache
//   - DeploymentCompletedEvent → updates auxiliary files cache (future)
type StateCache struct {
	bus             *busevents.EventBus
	resourceWatcher *resourcewatcher.ResourceWatcherComponent
	eventChan       <-chan busevents.Event // Event channel from Subscribe()

	// Cached state (thread-safe)
	mu                   sync.RWMutex
	currentConfig        *coreconfig.Config
	currentConfigVersion string
	currentCreds         *coreconfig.Credentials
	currentCredsVersion  string
	lastRendered         string
	lastRenderedTime     time.Time
	lastAuxFiles         *dataplane.AuxiliaryFiles
	lastAuxFilesTime     time.Time

	// Webhook state
	webhookServerRunning bool
	webhookServerPort    int
	webhookServerPath    string
	webhookStartTime     time.Time
	webhookCertExpiry    time.Time
	webhookLastRotation  time.Time
	webhookStatsTotal    int64
	webhookStatsAllowed  int64
	webhookStatsDenied   int64
	webhookStatsErrors   int64
}

// NewStateCache creates a new state cache component.
func NewStateCache(bus *busevents.EventBus, resourceWatcher *resourcewatcher.ResourceWatcherComponent) *StateCache {
	return &StateCache{
		bus:             bus,
		resourceWatcher: resourceWatcher,
	}
}

// Subscribe registers this StateCache with the EventBus.
//
// This must be called BEFORE bus.Start() to ensure the StateCache
// receives all events, including buffered startup events.
//
// Call this synchronously before starting the event bus:
//
//	stateCache := NewStateCache(bus, resourceWatcher)
//	stateCache.Subscribe()
//	bus.Start()
//	go stateCache.Run(ctx)
func (sc *StateCache) Subscribe() {
	sc.eventChan = sc.bus.Subscribe(100)
}

// Run begins processing events and updating cached state.
//
// This should be called AFTER Subscribe() and bus.Start().
// Run in a goroutine:
//
//	go stateCache.Run(ctx)
func (sc *StateCache) Run(ctx context.Context) error {
	if sc.eventChan == nil {
		panic("StateCache.Subscribe() must be called before Run()")
	}

	for {
		select {
		case event := <-sc.eventChan:
			sc.handleEvent(event)

		case <-ctx.Done():
			return nil
		}
	}
}

// Start is a convenience method that calls Subscribe() and Run() together.
//
// Deprecated: Use Subscribe() + Run() for proper initialization ordering.
// This method exists for backward compatibility but should not be used in new code.
func (sc *StateCache) Start(ctx context.Context) error {
	sc.Subscribe()
	return sc.Run(ctx)
}

// handleEvent processes events and updates cached state.
func (sc *StateCache) handleEvent(event interface{}) {
	switch e := event.(type) {
	case *events.ConfigValidatedEvent:
		// Type assert from interface{} to *coreconfig.Config
		if cfg, ok := e.Config.(*coreconfig.Config); ok {
			sc.mu.Lock()
			sc.currentConfig = cfg
			sc.currentConfigVersion = e.Version
			sc.mu.Unlock()
		} else {
			// Log when type assertion fails for debugging
			fmt.Printf("DEBUG: StateCache: ConfigValidatedEvent config type assertion failed, got %T\n", e.Config)
		}

	case *events.CredentialsUpdatedEvent:
		// Type assert from interface{} to *coreconfig.Credentials
		if creds, ok := e.Credentials.(*coreconfig.Credentials); ok {
			sc.mu.Lock()
			sc.currentCreds = creds
			sc.currentCredsVersion = e.SecretVersion
			sc.mu.Unlock()
		} else {
			// Log when type assertion fails for debugging
			fmt.Printf("DEBUG: StateCache: CredentialsUpdatedEvent credentials type assertion failed, got %T\n", e.Credentials)
		}

	case *events.TemplateRenderedEvent:
		sc.mu.Lock()
		sc.lastRendered = e.HAProxyConfig
		sc.lastRenderedTime = time.Now()

		// Type assert auxiliary files from interface{}
		if auxFiles, ok := e.AuxiliaryFiles.(*dataplane.AuxiliaryFiles); ok {
			sc.lastAuxFiles = auxFiles
			sc.lastAuxFilesTime = time.Now()
		} else if e.AuxiliaryFiles != nil {
			// Log when type assertion fails for debugging (only if not nil)
			fmt.Printf("DEBUG: StateCache: TemplateRenderedEvent auxiliary files type assertion failed, got %T\n", e.AuxiliaryFiles)
		}
		sc.mu.Unlock()

	// Webhook events
	case *events.WebhookServerStartedEvent:
		sc.mu.Lock()
		sc.webhookServerRunning = true
		sc.webhookServerPort = e.Port
		sc.webhookServerPath = e.Path
		sc.webhookStartTime = time.Now()
		sc.mu.Unlock()

	case *events.WebhookServerStoppedEvent:
		sc.mu.Lock()
		sc.webhookServerRunning = false
		sc.mu.Unlock()

	case *events.WebhookCertificatesGeneratedEvent:
		sc.mu.Lock()
		sc.webhookCertExpiry = e.ValidUntil
		sc.mu.Unlock()

	case *events.WebhookCertificatesRotatedEvent:
		sc.mu.Lock()
		sc.webhookCertExpiry = e.NewValidUntil
		sc.webhookLastRotation = time.Now()
		sc.mu.Unlock()

	case *events.WebhookValidationRequestEvent:
		sc.mu.Lock()
		sc.webhookStatsTotal++
		sc.mu.Unlock()

	case *events.WebhookValidationAllowedEvent:
		sc.mu.Lock()
		sc.webhookStatsAllowed++
		sc.mu.Unlock()

	case *events.WebhookValidationDeniedEvent:
		sc.mu.Lock()
		sc.webhookStatsDenied++
		sc.mu.Unlock()

	case *events.WebhookValidationErrorEvent:
		sc.mu.Lock()
		sc.webhookStatsErrors++
		sc.mu.Unlock()
	}
}

// GetConfig implements debug.StateProvider.
func (sc *StateCache) GetConfig() (*coreconfig.Config, string, error) {
	sc.mu.RLock()
	defer sc.mu.RUnlock()

	if sc.currentConfig == nil {
		return nil, "", fmt.Errorf("config not loaded yet")
	}

	return sc.currentConfig, sc.currentConfigVersion, nil
}

// GetCredentials implements debug.StateProvider.
func (sc *StateCache) GetCredentials() (*coreconfig.Credentials, string, error) {
	sc.mu.RLock()
	defer sc.mu.RUnlock()

	if sc.currentCreds == nil {
		return nil, "", fmt.Errorf("credentials not loaded yet")
	}

	return sc.currentCreds, sc.currentCredsVersion, nil
}

// GetRenderedConfig implements debug.StateProvider.
func (sc *StateCache) GetRenderedConfig() (string, time.Time, error) {
	sc.mu.RLock()
	defer sc.mu.RUnlock()

	if sc.lastRendered == "" {
		return "", time.Time{}, fmt.Errorf("no config rendered yet")
	}

	return sc.lastRendered, sc.lastRenderedTime, nil
}

// GetAuxiliaryFiles implements debug.StateProvider.
func (sc *StateCache) GetAuxiliaryFiles() (*dataplane.AuxiliaryFiles, time.Time, error) {
	sc.mu.RLock()
	defer sc.mu.RUnlock()

	if sc.lastAuxFiles == nil {
		// Return empty but valid structure
		return &dataplane.AuxiliaryFiles{}, time.Time{}, nil
	}

	return sc.lastAuxFiles, sc.lastAuxFilesTime, nil
}

// GetResourceCounts implements debug.StateProvider.
func (sc *StateCache) GetResourceCounts() (map[string]int, error) {
	if sc.resourceWatcher == nil {
		return nil, fmt.Errorf("resource watcher not initialized")
	}

	stores := sc.resourceWatcher.GetAllStores()
	counts := make(map[string]int, len(stores))

	for name, store := range stores {
		items, err := store.List()
		if err != nil {
			return nil, fmt.Errorf("failed to list resources for %q: %w", name, err)
		}
		counts[name] = len(items)
	}

	return counts, nil
}

// GetResourcesByType implements debug.StateProvider.
func (sc *StateCache) GetResourcesByType(resourceType string) ([]interface{}, error) {
	if sc.resourceWatcher == nil {
		return nil, fmt.Errorf("resource watcher not initialized")
	}

	stores := sc.resourceWatcher.GetAllStores()
	store, ok := stores[resourceType]
	if !ok {
		return nil, fmt.Errorf("resource type %q not found", resourceType)
	}

	return store.List()
}

// GetWebhookServerInfo implements debug.StateProvider.
func (sc *StateCache) GetWebhookServerInfo() (*debug.WebhookServerInfo, error) {
	sc.mu.RLock()
	defer sc.mu.RUnlock()

	// Check if webhook was ever started
	if sc.webhookServerPort == 0 {
		return nil, fmt.Errorf("webhook not configured")
	}

	return &debug.WebhookServerInfo{
		Running:   sc.webhookServerRunning,
		Port:      sc.webhookServerPort,
		Path:      sc.webhookServerPath,
		StartTime: sc.webhookStartTime,
	}, nil
}

// GetWebhookCertificateInfo implements debug.StateProvider.
func (sc *StateCache) GetWebhookCertificateInfo() (*debug.WebhookCertInfo, error) {
	sc.mu.RLock()
	defer sc.mu.RUnlock()

	// Check if webhook certificates were generated
	if sc.webhookCertExpiry.IsZero() {
		return nil, fmt.Errorf("webhook certificates not generated yet")
	}

	daysRemaining := int(time.Until(sc.webhookCertExpiry).Hours() / 24)

	return &debug.WebhookCertInfo{
		ValidUntil:    sc.webhookCertExpiry,
		LastRotation:  sc.webhookLastRotation,
		DaysRemaining: daysRemaining,
	}, nil
}

// GetWebhookValidationStats implements debug.StateProvider.
func (sc *StateCache) GetWebhookValidationStats() (*debug.WebhookValidationStats, error) {
	sc.mu.RLock()
	defer sc.mu.RUnlock()

	// Check if webhook is configured (port set)
	if sc.webhookServerPort == 0 {
		return nil, fmt.Errorf("webhook not configured")
	}

	return &debug.WebhookValidationStats{
		TotalRequests: sc.webhookStatsTotal,
		Allowed:       sc.webhookStatsAllowed,
		Denied:        sc.webhookStatsDenied,
		Errors:        sc.webhookStatsErrors,
	}, nil
}
