package resourcewatcher

import (
	"context"
	"log/slog"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"k8s.io/apimachinery/pkg/runtime/schema"

	coreconfig "haproxy-template-ic/pkg/core/config"
	busevents "haproxy-template-ic/pkg/events"
	"haproxy-template-ic/pkg/k8s/client"
)

func TestToGVR(t *testing.T) {
	tests := []struct {
		name    string
		wr      coreconfig.WatchedResource
		want    schema.GroupVersionResource
		wantErr bool
	}{
		{
			name: "core resource",
			wr: coreconfig.WatchedResource{
				APIVersion: "v1",
				Resources:  "services",
			},
			want: schema.GroupVersionResource{
				Group:    "",
				Version:  "v1",
				Resource: "services",
			},
		},
		{
			name: "networking resource",
			wr: coreconfig.WatchedResource{
				APIVersion: "networking.k8s.io/v1",
				Resources:  "ingresses",
			},
			want: schema.GroupVersionResource{
				Group:    "networking.k8s.io",
				Version:  "v1",
				Resource: "ingresses",
			},
		},
		{
			name: "discovery resource",
			wr: coreconfig.WatchedResource{
				APIVersion: "discovery.k8s.io/v1",
				Resources:  "endpointslices",
			},
			want: schema.GroupVersionResource{
				Group:    "discovery.k8s.io",
				Version:  "v1",
				Resource: "endpointslices",
			},
		},
		{
			name: "missing api_version",
			wr: coreconfig.WatchedResource{
				Resources: "ingresses",
			},
			wantErr: true,
		},
		{
			name: "missing kind",
			wr: coreconfig.WatchedResource{
				APIVersion: "v1",
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := toGVR(&tt.wr)

			if tt.wantErr {
				require.Error(t, err)
				return
			}

			require.NoError(t, err)
			assert.Equal(t, tt.want, got)
		})
	}
}

func TestParseAPIVersion(t *testing.T) {
	tests := []struct {
		name        string
		apiVersion  string
		wantGroup   string
		wantVersion string
	}{
		{
			name:        "core resource",
			apiVersion:  "v1",
			wantGroup:   "",
			wantVersion: "v1",
		},
		{
			name:        "namespaced resource",
			apiVersion:  "networking.k8s.io/v1",
			wantGroup:   "networking.k8s.io",
			wantVersion: "v1",
		},
		{
			name:        "custom resource",
			apiVersion:  "example.com/v1alpha1",
			wantGroup:   "example.com",
			wantVersion: "v1alpha1",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			group, version := parseAPIVersion(tt.apiVersion)
			assert.Equal(t, tt.wantGroup, group)
			assert.Equal(t, tt.wantVersion, version)
		})
	}
}

func TestMergeIgnoreFields(t *testing.T) {
	tests := []struct {
		name        string
		global      []string
		perResource []string
		want        []string
	}{
		{
			name:        "only global",
			global:      []string{"metadata.managedFields", "metadata.annotations"},
			perResource: nil,
			want:        []string{"metadata.managedFields", "metadata.annotations"},
		},
		{
			name:        "only per-resource",
			global:      nil,
			perResource: []string{"spec.template"},
			want:        []string{"spec.template"},
		},
		{
			name:        "merge without duplicates",
			global:      []string{"metadata.managedFields"},
			perResource: []string{"spec.template"},
			want:        []string{"metadata.managedFields", "spec.template"},
		},
		{
			name:        "deduplicate",
			global:      []string{"metadata.managedFields", "metadata.annotations"},
			perResource: []string{"metadata.managedFields", "spec.template"},
			want:        []string{"metadata.managedFields", "metadata.annotations", "spec.template"},
		},
		{
			name:        "both empty",
			global:      []string{},
			perResource: []string{},
			want:        []string{},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := mergeIgnoreFields(tt.global, tt.perResource)
			assert.Equal(t, tt.want, got)
		})
	}
}

func TestNew_NilParameters(t *testing.T) {
	cfg := &coreconfig.Config{}
	bus := busevents.NewEventBus(10)
	logger := slog.Default()

	// Create a mock k8s client (nil is okay for these tests since we're testing nil validation)
	// We use a placeholder that's non-nil but won't be used
	dummyClient := &client.Client{}

	tests := []struct {
		name      string
		cfg       *coreconfig.Config
		k8sClient *client.Client
		bus       *busevents.EventBus
		logger    *slog.Logger
		wantErr   string
	}{
		{
			name:      "nil config",
			cfg:       nil,
			k8sClient: dummyClient,
			bus:       bus,
			logger:    logger,
			wantErr:   "config is nil",
		},
		{
			name:      "nil k8s client",
			cfg:       cfg,
			k8sClient: nil,
			bus:       bus,
			logger:    logger,
			wantErr:   "k8s client is nil",
		},
		{
			name:      "nil event bus",
			cfg:       cfg,
			k8sClient: dummyClient,
			bus:       nil,
			logger:    logger,
			wantErr:   "event bus is nil",
		},
		{
			name:      "nil logger",
			cfg:       cfg,
			k8sClient: dummyClient,
			bus:       bus,
			logger:    nil,
			wantErr:   "logger is nil",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := New(tt.cfg, tt.k8sClient, tt.bus, tt.logger)
			require.Error(t, err)
			assert.Contains(t, err.Error(), tt.wantErr)
		})
	}
}

func TestNew_EmptyConfig(t *testing.T) {
	t.Skip("Requires Kubernetes cluster - run as integration test")

	cfg := &coreconfig.Config{
		WatchedResources: map[string]coreconfig.WatchedResource{},
	}
	k8sClient, err := client.New(client.Config{})
	require.NoError(t, err)
	bus := busevents.NewEventBus(10)
	logger := slog.Default()

	rwc, err := New(cfg, k8sClient, bus, logger)
	require.NoError(t, err)
	require.NotNil(t, rwc)

	// Should have no watchers for empty config
	assert.Empty(t, rwc.watchers)
	assert.Empty(t, rwc.stores)
}

func TestNew_InvalidResource(t *testing.T) {
	t.Skip("Requires Kubernetes cluster - run as integration test")

	cfg := &coreconfig.Config{
		WatchedResources: map[string]coreconfig.WatchedResource{
			"invalid": {
				// Missing APIVersion and Kind
				IndexBy: []string{"metadata.namespace"},
			},
		},
	}
	k8sClient, err := client.New(client.Config{})
	require.NoError(t, err)
	bus := busevents.NewEventBus(10)
	logger := slog.Default()

	_, err = New(cfg, k8sClient, bus, logger)
	require.Error(t, err)
	assert.Contains(t, err.Error(), "invalid resource")
}

func TestGetStore(t *testing.T) {
	t.Skip("Requires Kubernetes cluster - run as integration test")

	cfg := &coreconfig.Config{
		WatchedResources: map[string]coreconfig.WatchedResource{
			"services": {
				APIVersion: "v1",
				Resources:  "services",
				IndexBy:    []string{"metadata.namespace"},
			},
		},
	}
	k8sClient, err := client.New(client.Config{})
	require.NoError(t, err)
	bus := busevents.NewEventBus(10)
	logger := slog.Default()

	rwc, err := New(cfg, k8sClient, bus, logger)
	require.NoError(t, err)

	// Existing resource type
	store := rwc.GetStore("services")
	assert.NotNil(t, store)

	// Non-existent resource type
	store = rwc.GetStore("ingresses")
	assert.Nil(t, store)
}

func TestGetAllStores(t *testing.T) {
	t.Skip("Requires Kubernetes cluster - run as integration test")

	cfg := &coreconfig.Config{
		WatchedResources: map[string]coreconfig.WatchedResource{
			"services": {
				APIVersion: "v1",
				Resources:  "services",
				IndexBy:    []string{"metadata.namespace"},
			},
			"pods": {
				APIVersion: "v1",
				Resources:  "pods",
				IndexBy:    []string{"metadata.namespace"},
			},
		},
	}
	k8sClient, err := client.New(client.Config{})
	require.NoError(t, err)
	bus := busevents.NewEventBus(10)
	logger := slog.Default()

	rwc, err := New(cfg, k8sClient, bus, logger)
	require.NoError(t, err)

	stores := rwc.GetAllStores()
	assert.Len(t, stores, 2)
	assert.NotNil(t, stores["services"])
	assert.NotNil(t, stores["pods"])

	// Verify it returns a copy (modifying return value doesn't affect internal state)
	stores["services"] = nil
	assert.NotNil(t, rwc.stores["services"])
}

func TestSyncTracking(t *testing.T) {
	t.Skip("Requires Kubernetes cluster - run as integration test")

	cfg := &coreconfig.Config{
		WatchedResources: map[string]coreconfig.WatchedResource{
			"services": {
				APIVersion: "v1",
				Resources:  "services",
				IndexBy:    []string{"metadata.namespace"},
			},
			"pods": {
				APIVersion: "v1",
				Resources:  "pods",
				IndexBy:    []string{"metadata.namespace"},
			},
		},
	}
	k8sClient, err := client.New(client.Config{})
	require.NoError(t, err)
	bus := busevents.NewEventBus(10)
	logger := slog.Default()

	rwc, err := New(cfg, k8sClient, bus, logger)
	require.NoError(t, err)

	// Initially nothing is synced
	assert.False(t, rwc.IsSynced("services"))
	assert.False(t, rwc.IsSynced("pods"))
	assert.False(t, rwc.AllSynced())

	// Simulate OnSyncComplete callback for services
	rwc.syncMu.Lock()
	rwc.synced["services"] = true
	rwc.syncMu.Unlock()

	assert.True(t, rwc.IsSynced("services"))
	assert.False(t, rwc.IsSynced("pods"))
	assert.False(t, rwc.AllSynced())

	// Simulate OnSyncComplete callback for pods
	rwc.syncMu.Lock()
	rwc.synced["pods"] = true
	rwc.syncMu.Unlock()

	assert.True(t, rwc.IsSynced("services"))
	assert.True(t, rwc.IsSynced("pods"))
	assert.True(t, rwc.AllSynced())
}

// TestEventPublishing verifies that the component publishes correct events.
// This is an integration test that requires a bit more setup.
func TestEventPublishing(t *testing.T) {
	t.Skip("Integration test - requires real k8s client or extensive mocking")

	// This test would verify:
	// 1. ResourceIndexUpdatedEvent is published on resource changes
	// 2. ResourceSyncCompleteEvent is published on initial sync
	// 3. Events contain correct resource type names and stats
}

// TestStart verifies that Start() begins watching and waits for context cancellation.
func TestStart(t *testing.T) {
	t.Skip("Requires Kubernetes cluster - run as integration test")

	cfg := &coreconfig.Config{
		WatchedResources: map[string]coreconfig.WatchedResource{
			"services": {
				APIVersion: "v1",
				Resources:  "services",
				IndexBy:    []string{"metadata.namespace"},
			},
		},
	}
	k8sClient, err := client.New(client.Config{})
	require.NoError(t, err)
	bus := busevents.NewEventBus(10)
	logger := slog.Default()

	rwc, err := New(cfg, k8sClient, bus, logger)
	require.NoError(t, err)

	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	// Start should not block
	done := make(chan error, 1)
	go func() {
		done <- rwc.Start(ctx)
	}()

	// Verify it completes when context is cancelled
	select {
	case err := <-done:
		require.NoError(t, err)
	case <-time.After(1 * time.Second):
		t.Fatal("Start() did not return after context cancellation")
	}
}
