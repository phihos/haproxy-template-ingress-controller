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

package discovery

import (
	"context"
	"log/slog"
	"os"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"

	"haproxy-template-ic/pkg/controller/events"
	coreconfig "haproxy-template-ic/pkg/core/config"
	"haproxy-template-ic/pkg/dataplane"
	busevents "haproxy-template-ic/pkg/events"
	"haproxy-template-ic/pkg/k8s/store"
	"haproxy-template-ic/pkg/k8s/types"
)

func TestComponent_ConfigValidatedEvent(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelDebug}))
	component := New(bus, logger)

	// Set pod store and credentials
	podStore := createTestPodStore(t, []string{"10.0.0.1", "10.0.0.2"})
	component.SetPodStore(podStore)

	credentials := &coreconfig.Credentials{
		DataplaneUsername: "admin",
		DataplanePassword: "secret",
	}

	// Subscribe to events
	eventChan := bus.Subscribe(10)
	bus.Start()

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// Start component
	go func() {
		_ = component.Start(ctx)
	}()

	// Publish CredentialsUpdatedEvent first (need credentials)
	bus.Publish(events.NewCredentialsUpdatedEvent(credentials, "v1"))

	// Wait briefly for credentials to be processed
	time.Sleep(50 * time.Millisecond)

	// Publish ConfigValidatedEvent
	config := &coreconfig.Config{
		Dataplane: coreconfig.DataplaneConfig{
			Port: 5555,
		},
	}
	bus.Publish(events.NewConfigValidatedEvent(config, "v1", "v1"))

	// Wait for HAProxyPodsDiscoveredEvent
	select {
	case event := <-eventChan:
		if discovered, ok := event.(*events.HAProxyPodsDiscoveredEvent); ok {
			assert.Equal(t, 2, discovered.Count)
			assert.Len(t, discovered.Endpoints, 2)

			// Verify endpoints
			endpoints := convertToDataplaneEndpoints(discovered.Endpoints)
			assert.Contains(t, endpoints, dataplane.Endpoint{
				URL:      "http://10.0.0.1:5555",
				Username: "admin",
				Password: "secret",
			})
			assert.Contains(t, endpoints, dataplane.Endpoint{
				URL:      "http://10.0.0.2:5555",
				Username: "admin",
				Password: "secret",
			})
		}
	case <-ctx.Done():
		t.Fatal("timeout waiting for HAProxyPodsDiscoveredEvent")
	}
}

func TestComponent_CredentialsUpdatedEvent(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelDebug}))
	component := New(bus, logger)

	// Set pod store and config
	podStore := createTestPodStore(t, []string{"10.0.0.1"})
	component.SetPodStore(podStore)

	// Subscribe to events
	eventChan := bus.Subscribe(10)
	bus.Start()

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// Start component
	go func() {
		_ = component.Start(ctx)
	}()

	// Publish ConfigValidatedEvent first (need dataplane port)
	config := &coreconfig.Config{
		Dataplane: coreconfig.DataplaneConfig{
			Port: 5555,
		},
	}
	bus.Publish(events.NewConfigValidatedEvent(config, "v1", "v1"))

	// Wait briefly for config to be processed
	time.Sleep(50 * time.Millisecond)

	// Publish CredentialsUpdatedEvent
	credentials := &coreconfig.Credentials{
		DataplaneUsername: "admin",
		DataplanePassword: "newsecret",
	}
	bus.Publish(events.NewCredentialsUpdatedEvent(credentials, "v2"))

	// Wait for HAProxyPodsDiscoveredEvent
	select {
	case event := <-eventChan:
		if discovered, ok := event.(*events.HAProxyPodsDiscoveredEvent); ok {
			assert.Equal(t, 1, discovered.Count)

			// Verify credentials
			endpoints := convertToDataplaneEndpoints(discovered.Endpoints)
			assert.Equal(t, "newsecret", endpoints[0].Password)
		}
	case <-ctx.Done():
		t.Fatal("timeout waiting for HAProxyPodsDiscoveredEvent")
	}
}

func TestComponent_ResourceIndexUpdatedEvent(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelDebug}))
	component := New(bus, logger)

	// Set pod store, config, and credentials
	podStore := createTestPodStore(t, []string{"10.0.0.1"})
	component.SetPodStore(podStore)

	credentials := &coreconfig.Credentials{
		DataplaneUsername: "admin",
		DataplanePassword: "secret",
	}

	// Subscribe to events
	eventChan := bus.Subscribe(10)
	bus.Start()

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// Start component
	go func() {
		_ = component.Start(ctx)
	}()

	// Publish prerequisite events
	config := &coreconfig.Config{
		Dataplane: coreconfig.DataplaneConfig{
			Port: 5555,
		},
	}
	bus.Publish(events.NewConfigValidatedEvent(config, "v1", "v1"))
	bus.Publish(events.NewCredentialsUpdatedEvent(credentials, "v1"))

	// Wait briefly for prerequisites to be processed
	time.Sleep(50 * time.Millisecond)

	// Publish ResourceIndexUpdatedEvent for haproxy-pods (real-time change, not initial sync)
	changeStats := types.ChangeStats{
		Created:       1,
		Modified:      0,
		Deleted:       0,
		IsInitialSync: false, // Real-time change
	}
	bus.Publish(events.NewResourceIndexUpdatedEvent("haproxy-pods", changeStats))

	// Wait for HAProxyPodsDiscoveredEvent
	select {
	case event := <-eventChan:
		if discovered, ok := event.(*events.HAProxyPodsDiscoveredEvent); ok {
			assert.Equal(t, 1, discovered.Count)
		}
	case <-ctx.Done():
		t.Fatal("timeout waiting for HAProxyPodsDiscoveredEvent")
	}
}

func TestComponent_ResourceIndexUpdatedEvent_InitialSync_Skipped(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelDebug}))
	component := New(bus, logger)

	// Set pod store, config, and credentials
	podStore := createTestPodStore(t, []string{"10.0.0.1"})
	component.SetPodStore(podStore)

	credentials := &coreconfig.Credentials{
		DataplaneUsername: "admin",
		DataplanePassword: "secret",
	}

	// Subscribe to events
	eventChan := bus.Subscribe(10)
	bus.Start()

	ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
	defer cancel()

	// Start component
	go func() {
		_ = component.Start(ctx)
	}()

	// Publish prerequisite events
	config := &coreconfig.Config{
		Dataplane: coreconfig.DataplaneConfig{
			Port: 5555,
		},
	}
	bus.Publish(events.NewConfigValidatedEvent(config, "v1", "v1"))
	bus.Publish(events.NewCredentialsUpdatedEvent(credentials, "v1"))

	// Wait briefly for prerequisites to be processed
	time.Sleep(50 * time.Millisecond)

	// Publish ResourceIndexUpdatedEvent with IsInitialSync=true
	changeStats := types.ChangeStats{
		Created:       1,
		Modified:      0,
		Deleted:       0,
		IsInitialSync: true, // Initial sync - should be skipped
	}
	bus.Publish(events.NewResourceIndexUpdatedEvent("haproxy-pods", changeStats))

	// Should NOT receive HAProxyPodsDiscoveredEvent
	select {
	case event := <-eventChan:
		if _, ok := event.(*events.HAProxyPodsDiscoveredEvent); ok {
			t.Fatal("unexpected HAProxyPodsDiscoveredEvent during initial sync")
		}
	case <-ctx.Done():
		// Expected - no event should be published
	}
}

func TestComponent_ResourceIndexUpdatedEvent_WrongResourceType_Ignored(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelDebug}))
	component := New(bus, logger)

	// Set pod store, config, and credentials
	podStore := createTestPodStore(t, []string{"10.0.0.1"})
	component.SetPodStore(podStore)

	credentials := &coreconfig.Credentials{
		DataplaneUsername: "admin",
		DataplanePassword: "secret",
	}

	// Subscribe to events
	eventChan := bus.Subscribe(10)
	bus.Start()

	ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
	defer cancel()

	// Start component
	go func() {
		_ = component.Start(ctx)
	}()

	// Publish prerequisite events
	config := &coreconfig.Config{
		Dataplane: coreconfig.DataplaneConfig{
			Port: 5555,
		},
	}
	bus.Publish(events.NewConfigValidatedEvent(config, "v1", "v1"))
	bus.Publish(events.NewCredentialsUpdatedEvent(credentials, "v1"))

	// Wait briefly for prerequisites to be processed
	time.Sleep(50 * time.Millisecond)

	// Publish ResourceIndexUpdatedEvent for different resource type
	changeStats := types.ChangeStats{
		Created:       1,
		Modified:      0,
		Deleted:       0,
		IsInitialSync: false,
	}
	bus.Publish(events.NewResourceIndexUpdatedEvent("ingresses", changeStats)) // Different resource

	// Should NOT receive HAProxyPodsDiscoveredEvent
	select {
	case event := <-eventChan:
		if _, ok := event.(*events.HAProxyPodsDiscoveredEvent); ok {
			t.Fatal("unexpected HAProxyPodsDiscoveredEvent for non-haproxy-pods resource")
		}
	case <-ctx.Done():
		// Expected - no event should be published
	}
}

func TestComponent_ResourceSyncCompleteEvent(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelDebug}))
	component := New(bus, logger)

	// Set pod store, config, and credentials
	podStore := createTestPodStore(t, []string{"10.0.0.1"})
	component.SetPodStore(podStore)

	credentials := &coreconfig.Credentials{
		DataplaneUsername: "admin",
		DataplanePassword: "secret",
	}

	// Subscribe to events
	eventChan := bus.Subscribe(10)
	bus.Start()

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// Start component
	go func() {
		_ = component.Start(ctx)
	}()

	// Publish prerequisite events
	config := &coreconfig.Config{
		Dataplane: coreconfig.DataplaneConfig{
			Port: 5555,
		},
	}
	bus.Publish(events.NewConfigValidatedEvent(config, "v1", "v1"))
	bus.Publish(events.NewCredentialsUpdatedEvent(credentials, "v1"))

	// Wait briefly for prerequisites to be processed
	time.Sleep(50 * time.Millisecond)

	// Publish ResourceSyncCompleteEvent for haproxy-pods
	bus.Publish(events.NewResourceSyncCompleteEvent("haproxy-pods", 1))

	// Wait for HAProxyPodsDiscoveredEvent
	select {
	case event := <-eventChan:
		if discovered, ok := event.(*events.HAProxyPodsDiscoveredEvent); ok {
			assert.Equal(t, 1, discovered.Count)
		}
	case <-ctx.Done():
		t.Fatal("timeout waiting for HAProxyPodsDiscoveredEvent")
	}
}

func TestComponent_ResourceSyncCompleteEvent_WrongResourceType_Ignored(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelDebug}))
	component := New(bus, logger)

	// Set pod store, config, and credentials
	podStore := createTestPodStore(t, []string{"10.0.0.1"})
	component.SetPodStore(podStore)

	credentials := &coreconfig.Credentials{
		DataplaneUsername: "admin",
		DataplanePassword: "secret",
	}

	// Subscribe to events
	eventChan := bus.Subscribe(10)
	bus.Start()

	ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
	defer cancel()

	// Start component
	go func() {
		_ = component.Start(ctx)
	}()

	// Publish prerequisite events
	config := &coreconfig.Config{
		Dataplane: coreconfig.DataplaneConfig{
			Port: 5555,
		},
	}
	bus.Publish(events.NewConfigValidatedEvent(config, "v1", "v1"))
	bus.Publish(events.NewCredentialsUpdatedEvent(credentials, "v1"))

	// Wait briefly for prerequisites to be processed
	time.Sleep(50 * time.Millisecond)

	// Publish ResourceSyncCompleteEvent for different resource type
	bus.Publish(events.NewResourceSyncCompleteEvent("ingresses", 0))

	// Should NOT receive HAProxyPodsDiscoveredEvent
	select {
	case event := <-eventChan:
		if _, ok := event.(*events.HAProxyPodsDiscoveredEvent); ok {
			t.Fatal("unexpected HAProxyPodsDiscoveredEvent for non-haproxy-pods resource")
		}
	case <-ctx.Done():
		// Expected - no event should be published
	}
}

func TestComponent_MissingPrerequisites(t *testing.T) {
	tests := []struct {
		name           string
		hasConfig      bool
		hasCredentials bool
		hasPodStore    bool
		shouldDiscover bool
	}{
		{
			name:           "all prerequisites present",
			hasConfig:      true,
			hasCredentials: true,
			hasPodStore:    true,
			shouldDiscover: true,
		},
		{
			name:           "missing config",
			hasConfig:      false,
			hasCredentials: true,
			hasPodStore:    true,
			shouldDiscover: false,
		},
		{
			name:           "missing credentials",
			hasConfig:      true,
			hasCredentials: false,
			hasPodStore:    true,
			shouldDiscover: false,
		},
		{
			name:           "missing pod store",
			hasConfig:      true,
			hasCredentials: true,
			hasPodStore:    false,
			shouldDiscover: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			testMissingPrerequisite(t, tt.hasConfig, tt.hasCredentials, tt.hasPodStore, tt.shouldDiscover)
		})
	}
}

// testMissingPrerequisite is a helper that tests discovery with missing prerequisites.
func testMissingPrerequisite(t *testing.T, hasConfig, hasCredentials, hasPodStore, shouldDiscover bool) {
	t.Helper()

	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelDebug}))
	component := New(bus, logger)

	// Set prerequisites based on test case
	if hasPodStore {
		podStore := createTestPodStore(t, []string{"10.0.0.1"})
		component.SetPodStore(podStore)
	}

	// Subscribe to events
	eventChan := bus.Subscribe(10)
	bus.Start()

	ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
	defer cancel()

	// Start component
	go func() {
		_ = component.Start(ctx)
	}()

	// Publish prerequisite events
	if hasConfig {
		config := &coreconfig.Config{
			Dataplane: coreconfig.DataplaneConfig{
				Port: 5555,
			},
		}
		bus.Publish(events.NewConfigValidatedEvent(config, "v1", "v1"))
	}

	if hasCredentials {
		credentials := &coreconfig.Credentials{
			DataplaneUsername: "admin",
			DataplanePassword: "secret",
		}
		bus.Publish(events.NewCredentialsUpdatedEvent(credentials, "v1"))
	}

	// Wait briefly for prerequisites to be processed
	time.Sleep(50 * time.Millisecond)

	// Publish ResourceIndexUpdatedEvent
	changeStats := types.ChangeStats{
		Created:       1,
		Modified:      0,
		Deleted:       0,
		IsInitialSync: false,
	}
	bus.Publish(events.NewResourceIndexUpdatedEvent("haproxy-pods", changeStats))

	// Check if discovery occurred
	checkDiscoveryOccurred(t, eventChan, ctx, shouldDiscover)
}

// checkDiscoveryOccurred verifies if discovery occurred as expected.
func checkDiscoveryOccurred(t *testing.T, eventChan <-chan busevents.Event, ctx context.Context, shouldDiscover bool) {
	t.Helper()

	select {
	case event := <-eventChan:
		if _, ok := event.(*events.HAProxyPodsDiscoveredEvent); ok {
			if !shouldDiscover {
				t.Fatal("unexpected HAProxyPodsDiscoveredEvent when prerequisites missing")
			}
			// Expected discovery
		}
	case <-ctx.Done():
		if shouldDiscover {
			t.Fatal("expected HAProxyPodsDiscoveredEvent but none received")
		}
		// Expected - no discovery without prerequisites
	}
}

// -----------------------------------------------------------------------------
// Helper Functions
// -----------------------------------------------------------------------------

// createTestPodStore creates a test pod store with the specified pod IPs.
func createTestPodStore(t *testing.T, podIPs []string) types.Store {
	t.Helper()

	podStore := store.NewMemoryStore(2)

	for i, ip := range podIPs {
		pod := &unstructured.Unstructured{}
		pod.SetAPIVersion("v1")
		pod.SetKind("Pod")
		pod.SetName("haproxy-" + string(rune('0'+i)))
		pod.SetNamespace("default")

		// Set pod IP
		err := unstructured.SetNestedField(pod.Object, ip, "status", "podIP")
		require.NoError(t, err)

		keys := []string{pod.GetNamespace(), pod.GetName()}
		err = podStore.Add(pod, keys)
		require.NoError(t, err)
	}

	return podStore
}

// convertToDataplaneEndpoints converts []interface{} to []dataplane.Endpoint.
func convertToDataplaneEndpoints(endpoints []interface{}) []dataplane.Endpoint {
	result := make([]dataplane.Endpoint, 0, len(endpoints))
	for _, e := range endpoints {
		if ep, ok := e.(dataplane.Endpoint); ok {
			result = append(result, ep)
		}
	}
	return result
}
