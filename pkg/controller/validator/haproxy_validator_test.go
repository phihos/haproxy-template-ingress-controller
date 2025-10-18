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

package validator

import (
	"context"
	"log/slog"
	"os"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"haproxy-template-ic/pkg/controller/events"
	"haproxy-template-ic/pkg/controller/renderer"
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

// TestRendererToValidator_SuccessFlow tests the successful flow from Renderer to Validator.
func TestRendererToValidator_SuccessFlow(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	// Create a minimal valid HAProxy config
	cfg := &config.Config{
		HAProxyConfig: config.HAProxyConfig{
			Template: `global
    daemon

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend http-in
    bind :80
    default_backend servers

backend servers
    server s1 127.0.0.1:8080
`,
		},
	}

	stores := map[string]types.Store{
		"ingresses": &mockStore{},
	}

	// Create renderer
	rendererComponent, err := renderer.New(bus, cfg, stores, logger)
	require.NoError(t, err)

	// Create validator
	validatorComponent := NewHAProxyValidator(bus, logger)

	// Subscribe to events
	eventChan := bus.Subscribe(50)
	bus.Start()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Start components
	go rendererComponent.Start(ctx)
	go validatorComponent.Start(ctx)

	time.Sleep(50 * time.Millisecond)

	// Trigger reconciliation
	bus.Publish(events.NewReconciliationTriggeredEvent("test"))

	// Wait for validation completed event
	timeout := time.After(2 * time.Second)
	var validationCompleted *events.ValidationCompletedEvent
	sawRendered := false

	for {
		select {
		case event := <-eventChan:
			switch e := event.(type) {
			case *events.TemplateRenderedEvent:
				sawRendered = true
				assert.Contains(t, e.HAProxyConfig, "global")
				assert.Contains(t, e.HAProxyConfig, "frontend http-in")
			case *events.ValidationCompletedEvent:
				validationCompleted = e
				goto Done
			case *events.ValidationFailedEvent:
				t.Fatalf("Validation failed unexpectedly: %v", e.Errors)
			}
		case <-timeout:
			t.Fatal("Timeout waiting for ValidationCompletedEvent")
		}
	}

Done:
	assert.True(t, sawRendered, "Should have received TemplateRenderedEvent")
	require.NotNil(t, validationCompleted)
	assert.GreaterOrEqual(t, validationCompleted.DurationMs, int64(0))
}

// TestRendererToValidator_ValidationFailure tests validation failure handling.
func TestRendererToValidator_ValidationFailure(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	// Create an invalid HAProxy config (semantic error)
	cfg := &config.Config{
		HAProxyConfig: config.HAProxyConfig{
			Template: `global
    daemon

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend http-in
    bind :80
    default_backend servers
    use_backend nonexistent if TRUE

backend servers
    server s1 127.0.0.1:8080
`,
		},
	}

	stores := map[string]types.Store{
		"ingresses": &mockStore{},
	}

	rendererComponent, err := renderer.New(bus, cfg, stores, logger)
	require.NoError(t, err)

	validatorComponent := NewHAProxyValidator(bus, logger)

	eventChan := bus.Subscribe(50)
	bus.Start()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go rendererComponent.Start(ctx)
	go validatorComponent.Start(ctx)

	time.Sleep(50 * time.Millisecond)

	bus.Publish(events.NewReconciliationTriggeredEvent("test"))

	// Wait for validation failed event
	timeout := time.After(2 * time.Second)
	var validationFailed *events.ValidationFailedEvent

	for {
		select {
		case event := <-eventChan:
			switch e := event.(type) {
			case *events.ValidationFailedEvent:
				validationFailed = e
				goto Done
			case *events.ValidationCompletedEvent:
				t.Fatal("Validation succeeded unexpectedly - config should be invalid")
			}
		case <-timeout:
			t.Fatal("Timeout waiting for ValidationFailedEvent")
		}
	}

Done:
	require.NotNil(t, validationFailed)
	assert.Greater(t, len(validationFailed.Errors), 0, "Should have validation errors")
	assert.GreaterOrEqual(t, validationFailed.DurationMs, int64(0))
}

// TestRendererToValidator_WithMapFiles tests validation with map files.
func TestRendererToValidator_WithMapFiles(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	cfg := &config.Config{
		HAProxyConfig: config.HAProxyConfig{
			Template: `global
    daemon

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend http-in
    bind :80
    http-request set-header X-Backend %[base,map(maps/hosts.map,default)]
    default_backend servers

backend servers
    server s1 127.0.0.1:8080
`,
		},
		Maps: map[string]config.MapFile{
			"maps/hosts.map": {
				Template: "example.com backend1\ntest.com backend2\n",
			},
		},
	}

	stores := map[string]types.Store{
		"ingresses": &mockStore{},
	}

	rendererComponent, err := renderer.New(bus, cfg, stores, logger)
	require.NoError(t, err)

	validatorComponent := NewHAProxyValidator(bus, logger)

	eventChan := bus.Subscribe(50)
	bus.Start()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go rendererComponent.Start(ctx)
	go validatorComponent.Start(ctx)

	time.Sleep(50 * time.Millisecond)

	bus.Publish(events.NewReconciliationTriggeredEvent("test"))

	// Wait for validation completed event
	timeout := time.After(2 * time.Second)
	var validationCompleted *events.ValidationCompletedEvent

	for {
		select {
		case event := <-eventChan:
			switch e := event.(type) {
			case *events.ValidationCompletedEvent:
				validationCompleted = e
				goto Done
			case *events.ValidationFailedEvent:
				t.Fatalf("Validation failed unexpectedly: %v", e.Errors)
			}
		case <-timeout:
			t.Fatal("Timeout waiting for ValidationCompletedEvent")
		}
	}

Done:
	require.NotNil(t, validationCompleted)
	assert.GreaterOrEqual(t, validationCompleted.DurationMs, int64(0))
}

// TestRendererToValidator_MultipleReconciliations tests multiple reconciliation cycles.
func TestRendererToValidator_MultipleReconciliations(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	cfg := &config.Config{
		HAProxyConfig: config.HAProxyConfig{
			Template: `global
    daemon

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend http-in
    bind :80
    default_backend servers

backend servers
    server s1 127.0.0.1:8080
`,
		},
	}

	stores := map[string]types.Store{
		"ingresses": &mockStore{},
	}

	rendererComponent, err := renderer.New(bus, cfg, stores, logger)
	require.NoError(t, err)

	validatorComponent := NewHAProxyValidator(bus, logger)

	eventChan := bus.Subscribe(50)
	bus.Start()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go rendererComponent.Start(ctx)
	go validatorComponent.Start(ctx)

	time.Sleep(50 * time.Millisecond)

	// Trigger first reconciliation
	bus.Publish(events.NewReconciliationTriggeredEvent("first"))

	// Wait for first validation
	timeout1 := time.After(2 * time.Second)
	receivedFirst := false

Loop1:
	for {
		select {
		case event := <-eventChan:
			if _, ok := event.(*events.ValidationCompletedEvent); ok {
				receivedFirst = true
				break Loop1
			}
		case <-timeout1:
			t.Fatal("Timeout waiting for first validation")
		}
	}

	assert.True(t, receivedFirst)

	// Trigger second reconciliation
	bus.Publish(events.NewReconciliationTriggeredEvent("second"))

	// Wait for second validation
	timeout2 := time.After(2 * time.Second)
	var secondValidation *events.ValidationCompletedEvent

Loop2:
	for {
		select {
		case event := <-eventChan:
			if e, ok := event.(*events.ValidationCompletedEvent); ok {
				secondValidation = e
				break Loop2
			}
		case <-timeout2:
			t.Fatal("Timeout waiting for second validation")
		}
	}

	require.NotNil(t, secondValidation)
}

// TestValidator_ContextCancellation tests graceful shutdown on context cancellation.
func TestValidator_ContextCancellation(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	validatorComponent := NewHAProxyValidator(bus, logger)

	bus.Start()

	ctx, cancel := context.WithCancel(context.Background())

	done := make(chan error, 1)
	go func() {
		done <- validatorComponent.Start(ctx)
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
		t.Fatal("Validator did not shut down within timeout")
	}
}
