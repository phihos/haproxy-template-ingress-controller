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
	"context"
	"log/slog"
	"os"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"haproxy-template-ic/pkg/controller/events"
	"haproxy-template-ic/pkg/core/config"
	busevents "haproxy-template-ic/pkg/events"
	"haproxy-template-ic/pkg/k8s/types"
)

// mockStore implements types.Store for testing.
type mockStore struct {
	items []interface{}
}

func (m *mockStore) Add(resource interface{}, keys []string) error {
	m.items = append(m.items, resource)
	return nil
}

func (m *mockStore) Update(resource interface{}, keys []string) error {
	return nil
}

func (m *mockStore) Delete(keys ...string) error {
	return nil
}

func (m *mockStore) List() ([]interface{}, error) {
	return m.items, nil
}

func (m *mockStore) Get(keys ...string) ([]interface{}, error) {
	return nil, nil
}

func (m *mockStore) Clear() error {
	m.items = nil
	return nil
}

// TestNew_Success tests successful renderer creation with valid configuration.
func TestNew_Success(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	cfg := &config.Config{
		HAProxyConfig: config.HAProxyConfig{
			Template: "global\n    daemon\n",
		},
		Maps: map[string]config.MapFile{
			"domain.map": {Template: "example.com backend1\n"},
		},
	}

	stores := map[string]types.Store{
		"ingresses": &mockStore{},
	}

	renderer, err := New(bus, cfg, stores, logger)

	require.NoError(t, err)
	assert.NotNil(t, renderer)
	assert.NotNil(t, renderer.engine)
	assert.Equal(t, cfg, renderer.config)
	assert.Equal(t, stores, renderer.stores)
}

// TestNew_InvalidTemplate tests renderer creation with invalid template syntax.
func TestNew_InvalidTemplate(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	cfg := &config.Config{
		HAProxyConfig: config.HAProxyConfig{
			Template: "global\n{{ unclosed tag\n",
		},
	}

	stores := map[string]types.Store{
		"ingresses": &mockStore{},
	}

	renderer, err := New(bus, cfg, stores, logger)

	assert.Error(t, err)
	assert.Nil(t, renderer)
	assert.Contains(t, err.Error(), "failed to create template engine")
}

// TestRenderer_SuccessfulRendering tests successful template rendering.
func TestRenderer_SuccessfulRendering(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	cfg := &config.Config{
		HAProxyConfig: config.HAProxyConfig{
			Template: `global
    daemon

defaults
    mode http

{% for ingress in resources.ingresses.List() %}
# Ingress: {{ ingress.metadata.name }}
{% endfor %}
`,
		},
	}

	// Create mock store with sample ingress
	ingressStore := &mockStore{
		items: []interface{}{
			map[string]interface{}{
				"metadata": map[string]interface{}{
					"name":      "test-ingress",
					"namespace": "default",
				},
			},
		},
	}

	stores := map[string]types.Store{
		"ingresses": ingressStore,
	}

	renderer, err := New(bus, cfg, stores, logger)
	require.NoError(t, err)

	// Subscribe to events
	eventChan := bus.Subscribe(50)
	bus.Start()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Start renderer
	go renderer.Start(ctx)

	// Give renderer time to start
	time.Sleep(50 * time.Millisecond)

	// Trigger reconciliation
	bus.Publish(events.NewReconciliationTriggeredEvent("test"))

	// Wait for rendered event
	timeout := time.After(1 * time.Second)
	var renderedEvent *events.TemplateRenderedEvent

	for {
		select {
		case event := <-eventChan:
			if e, ok := event.(*events.TemplateRenderedEvent); ok {
				renderedEvent = e
				goto Done
			}
		case <-timeout:
			t.Fatal("Timeout waiting for TemplateRenderedEvent")
		}
	}

Done:
	require.NotNil(t, renderedEvent)
	assert.Contains(t, renderedEvent.HAProxyConfig, "global")
	assert.Contains(t, renderedEvent.HAProxyConfig, "# Ingress: test-ingress")
	assert.Greater(t, renderedEvent.ConfigBytes, 0)
	assert.GreaterOrEqual(t, renderedEvent.DurationMs, int64(0))
}

// TestRenderer_WithAuxiliaryFiles tests rendering with maps, files, and SSL certificates.
func TestRenderer_WithAuxiliaryFiles(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	cfg := &config.Config{
		HAProxyConfig: config.HAProxyConfig{
			Template: "global\n    daemon\n",
		},
		Maps: map[string]config.MapFile{
			"domains.map": {
				Template: "{% for ingress in resources.ingresses.List() %}{{ ingress.metadata.name }}.example.com backend1\n{% endfor %}",
			},
		},
		Files: map[string]config.GeneralFile{
			"error-500.http": {
				Template: "HTTP/1.0 500 Internal Server Error\nContent-Type: text/html\n\n<h1>Error 500</h1>\n",
			},
		},
		SSLCertificates: map[string]config.SSLCertificate{
			"example.pem": {
				Template: "-----BEGIN CERTIFICATE-----\ntest-cert-data\n-----END CERTIFICATE-----\n",
			},
		},
	}

	ingressStore := &mockStore{
		items: []interface{}{
			map[string]interface{}{
				"metadata": map[string]interface{}{
					"name": "test-ingress",
				},
			},
		},
	}

	stores := map[string]types.Store{
		"ingresses": ingressStore,
	}

	renderer, err := New(bus, cfg, stores, logger)
	require.NoError(t, err)

	eventChan := bus.Subscribe(50)
	bus.Start()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go renderer.Start(ctx)
	time.Sleep(50 * time.Millisecond)

	bus.Publish(events.NewReconciliationTriggeredEvent("test"))

	timeout := time.After(1 * time.Second)
	var renderedEvent *events.TemplateRenderedEvent

	for {
		select {
		case event := <-eventChan:
			if e, ok := event.(*events.TemplateRenderedEvent); ok {
				renderedEvent = e
				goto Done
			}
		case <-timeout:
			t.Fatal("Timeout waiting for TemplateRenderedEvent")
		}
	}

Done:
	require.NotNil(t, renderedEvent)
	assert.Equal(t, 3, renderedEvent.AuxiliaryFileCount, "Should have 1 map + 1 file + 1 SSL cert")

	// Verify auxiliary files are populated
	assert.NotNil(t, renderedEvent.AuxiliaryFiles)
}

// TestRenderer_RenderFailure tests handling of template rendering failures.
func TestRenderer_RenderFailure(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	cfg := &config.Config{
		HAProxyConfig: config.HAProxyConfig{
			Template: "global\n    daemon\n",
		},
		Maps: map[string]config.MapFile{
			"broken.map": {
				// Template references non-existent function
				Template: "{{ undefined_function() }}",
			},
		},
	}

	stores := map[string]types.Store{
		"ingresses": &mockStore{},
	}

	renderer, err := New(bus, cfg, stores, logger)
	require.NoError(t, err)

	eventChan := bus.Subscribe(50)
	bus.Start()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go renderer.Start(ctx)
	time.Sleep(50 * time.Millisecond)

	bus.Publish(events.NewReconciliationTriggeredEvent("test"))

	timeout := time.After(1 * time.Second)
	var failureEvent *events.TemplateRenderFailedEvent

	for {
		select {
		case event := <-eventChan:
			if e, ok := event.(*events.TemplateRenderFailedEvent); ok {
				failureEvent = e
				goto Done
			}
		case <-timeout:
			t.Fatal("Timeout waiting for TemplateRenderFailedEvent")
		}
	}

Done:
	require.NotNil(t, failureEvent)
	assert.Equal(t, "broken.map", failureEvent.TemplateName)
	assert.NotEmpty(t, failureEvent.Error)
}

// TestRenderer_EmptyStores tests rendering with empty resource stores.
func TestRenderer_EmptyStores(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	cfg := &config.Config{
		HAProxyConfig: config.HAProxyConfig{
			Template: `global
    daemon

{% if resources.ingresses.List()|length == 0 %}
# No ingresses configured
{% endif %}
`,
		},
	}

	stores := map[string]types.Store{
		"ingresses": &mockStore{items: []interface{}{}}, // Empty store
	}

	renderer, err := New(bus, cfg, stores, logger)
	require.NoError(t, err)

	eventChan := bus.Subscribe(50)
	bus.Start()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go renderer.Start(ctx)
	time.Sleep(50 * time.Millisecond)

	bus.Publish(events.NewReconciliationTriggeredEvent("test"))

	timeout := time.After(1 * time.Second)
	var renderedEvent *events.TemplateRenderedEvent

	for {
		select {
		case event := <-eventChan:
			if e, ok := event.(*events.TemplateRenderedEvent); ok {
				renderedEvent = e
				goto Done
			}
		case <-timeout:
			t.Fatal("Timeout waiting for TemplateRenderedEvent")
		}
	}

Done:
	require.NotNil(t, renderedEvent)
	assert.Contains(t, renderedEvent.HAProxyConfig, "# No ingresses configured")
}

// TestRenderer_MultipleStores tests rendering with multiple resource types.
func TestRenderer_MultipleStores(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	cfg := &config.Config{
		HAProxyConfig: config.HAProxyConfig{
			Template: `global
    daemon

# Ingresses: {{ resources.ingresses.List()|length }}
# Services: {{ resources.services.List()|length }}
# Pods: {{ resources.pods.List()|length }}
`,
		},
	}

	stores := map[string]types.Store{
		"ingresses": &mockStore{
			items: []interface{}{
				map[string]interface{}{"kind": "Ingress"},
				map[string]interface{}{"kind": "Ingress"},
			},
		},
		"services": &mockStore{
			items: []interface{}{
				map[string]interface{}{"kind": "Service"},
			},
		},
		"pods": &mockStore{
			items: []interface{}{
				map[string]interface{}{"kind": "Pod"},
				map[string]interface{}{"kind": "Pod"},
				map[string]interface{}{"kind": "Pod"},
			},
		},
	}

	renderer, err := New(bus, cfg, stores, logger)
	require.NoError(t, err)

	eventChan := bus.Subscribe(50)
	bus.Start()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go renderer.Start(ctx)
	time.Sleep(50 * time.Millisecond)

	bus.Publish(events.NewReconciliationTriggeredEvent("test"))

	timeout := time.After(1 * time.Second)
	var renderedEvent *events.TemplateRenderedEvent

	for {
		select {
		case event := <-eventChan:
			if e, ok := event.(*events.TemplateRenderedEvent); ok {
				renderedEvent = e
				goto Done
			}
		case <-timeout:
			t.Fatal("Timeout waiting for TemplateRenderedEvent")
		}
	}

Done:
	require.NotNil(t, renderedEvent)
	assert.Contains(t, renderedEvent.HAProxyConfig, "# Ingresses: 2")
	assert.Contains(t, renderedEvent.HAProxyConfig, "# Services: 1")
	assert.Contains(t, renderedEvent.HAProxyConfig, "# Pods: 3")
}

// TestRenderer_ContextCancellation tests graceful shutdown on context cancellation.
func TestRenderer_ContextCancellation(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	cfg := &config.Config{
		HAProxyConfig: config.HAProxyConfig{
			Template: "global\n    daemon\n",
		},
	}

	stores := map[string]types.Store{
		"ingresses": &mockStore{},
	}

	renderer, err := New(bus, cfg, stores, logger)
	require.NoError(t, err)

	bus.Start()

	ctx, cancel := context.WithCancel(context.Background())

	// Start renderer
	done := make(chan error, 1)
	go func() {
		done <- renderer.Start(ctx)
	}()

	// Cancel context
	time.Sleep(50 * time.Millisecond)
	cancel()

	// Should return quickly
	timeout := time.After(1 * time.Second)
	select {
	case err := <-done:
		assert.NoError(t, err, "Start should return nil on context cancellation")
	case <-timeout:
		t.Fatal("Renderer did not shut down within timeout")
	}
}

// TestRenderer_MultipleReconciliations tests handling multiple reconciliation triggers.
func TestRenderer_MultipleReconciliations(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	cfg := &config.Config{
		HAProxyConfig: config.HAProxyConfig{
			Template: "global\n    daemon\n# Count: {{ resources.ingresses.List()|length }}\n",
		},
	}

	ingressStore := &mockStore{
		items: []interface{}{
			map[string]interface{}{"name": "ing1"},
		},
	}

	stores := map[string]types.Store{
		"ingresses": ingressStore,
	}

	renderer, err := New(bus, cfg, stores, logger)
	require.NoError(t, err)

	eventChan := bus.Subscribe(50)
	bus.Start()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go renderer.Start(ctx)
	time.Sleep(50 * time.Millisecond)

	// Trigger first reconciliation
	bus.Publish(events.NewReconciliationTriggeredEvent("first"))

	// Wait for first render
	timeout1 := time.After(500 * time.Millisecond)
	receivedFirst := false

Loop1:
	for {
		select {
		case event := <-eventChan:
			if _, ok := event.(*events.TemplateRenderedEvent); ok {
				receivedFirst = true
				break Loop1
			}
		case <-timeout1:
			t.Fatal("Timeout waiting for first render")
		}
	}

	assert.True(t, receivedFirst)

	// Add more ingresses to store
	ingressStore.items = append(ingressStore.items, map[string]interface{}{"name": "ing2"})

	// Trigger second reconciliation
	bus.Publish(events.NewReconciliationTriggeredEvent("second"))

	// Wait for second render
	timeout2 := time.After(500 * time.Millisecond)
	var secondEvent *events.TemplateRenderedEvent

Loop2:
	for {
		select {
		case event := <-eventChan:
			if e, ok := event.(*events.TemplateRenderedEvent); ok {
				secondEvent = e
				break Loop2
			}
		case <-timeout2:
			t.Fatal("Timeout waiting for second render")
		}
	}

	require.NotNil(t, secondEvent)
	assert.Contains(t, secondEvent.HAProxyConfig, "# Count: 2")
}

// TestBuildRenderingContext tests the context building logic.
func TestBuildRenderingContext(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	cfg := &config.Config{
		HAProxyConfig: config.HAProxyConfig{
			Template: "global\n    daemon\n",
		},
	}

	stores := map[string]types.Store{
		"ingresses": &mockStore{
			items: []interface{}{
				map[string]interface{}{"name": "ing1"},
				map[string]interface{}{"name": "ing2"},
			},
		},
		"services": &mockStore{
			items: []interface{}{
				map[string]interface{}{"name": "svc1"},
			},
		},
	}

	renderer, err := New(bus, cfg, stores, logger)
	require.NoError(t, err)

	// Build context
	ctx := renderer.buildRenderingContext()

	// Verify structure
	require.Contains(t, ctx, "resources")

	resources, ok := ctx["resources"].(map[string]interface{})
	require.True(t, ok, "resources should be a map")

	// Verify ingresses store wrapper
	ingressesWrapper, ok := resources["ingresses"].(*StoreWrapper)
	require.True(t, ok, "ingresses should be a StoreWrapper")
	assert.Equal(t, "ingresses", ingressesWrapper.resourceType)

	// Verify ingresses content via List()
	ingresses := ingressesWrapper.List()
	assert.Len(t, ingresses, 2)

	// Verify services store wrapper
	servicesWrapper, ok := resources["services"].(*StoreWrapper)
	require.True(t, ok, "services should be a StoreWrapper")
	assert.Equal(t, "services", servicesWrapper.resourceType)

	// Verify services content via List()
	services := servicesWrapper.List()
	assert.Len(t, services, 1)
}
