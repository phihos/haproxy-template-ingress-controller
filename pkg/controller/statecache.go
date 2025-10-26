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

	// Initialization state (guarded by initOnce)
	initOnce  sync.Once
	eventChan <-chan busevents.Event
}

// Compile-time check that StateCache implements debug.StateProvider interface.
var _ debug.StateProvider = (*StateCache)(nil)

// NewStateCache creates a new state cache component.
//
// The StateCache subscribes to the EventBus when Start() is called and must be started
// BEFORE bus.Start() to ensure it receives all buffered startup events.
//
// Usage:
//
//	stateCache := NewStateCache(bus, resourceWatcher)
//	stateCache.Start(ctx)  // Subscribe immediately, process events in background
//	bus.Start()            // Release buffered events
func NewStateCache(bus *busevents.EventBus, resourceWatcher *resourcewatcher.ResourceWatcherComponent) *StateCache {
	return &StateCache{
		bus:             bus,
		resourceWatcher: resourceWatcher,
	}
}

// Start subscribes to the EventBus and begins processing events.
//
// This method:
// 1. Subscribes to the EventBus (exactly once, thread-safe)
// 2. Starts the event processing loop
//
// IMPORTANT: Call this BEFORE bus.Start() to ensure the StateCache receives all
// buffered startup events. The subscription happens immediately when this method
// is called, before the event loop starts.
//
// This method blocks until the context is cancelled.
func (sc *StateCache) Start(ctx context.Context) error {
	// Subscribe to EventBus exactly once (thread-safe)
	sc.initOnce.Do(func() {
		sc.eventChan = sc.bus.Subscribe(100)
	})

	// Event processing loop
	for {
		select {
		case event := <-sc.eventChan:
			sc.handleEvent(event)

		case <-ctx.Done():
			return nil
		}
	}
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
