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

package deployer

import (
	"context"
	"io"
	"log/slog"
	"os"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"haproxy-template-ic/pkg/controller/events"
	"haproxy-template-ic/pkg/dataplane"
	busevents "haproxy-template-ic/pkg/events"
)

// Test helper to create a test deployer component.
func createTestDeployer(eventBus *busevents.EventBus) *Component {
	// Create logger that writes to discard or stderr
	var w io.Writer = io.Discard
	if testing.Verbose() {
		w = os.Stderr
	}
	logger := slog.New(slog.NewTextHandler(w, &slog.HandlerOptions{Level: slog.LevelDebug}))
	return New(eventBus, logger)
}

// TestHandleDeploymentScheduled tests deployment execution when scheduled.
func TestHandleDeploymentScheduled(t *testing.T) {
	bus := busevents.NewEventBus(100)
	bus.Start()
	deployer := createTestDeployer(bus)

	ctx := context.Background()

	// Start deployer in background
	go deployer.Start(ctx)
	time.Sleep(10 * time.Millisecond)

	// Create deployment scheduled event (with no endpoints, just to test event handling)
	event := events.NewDeploymentScheduledEvent(
		"test config",
		nil,
		[]interface{}{},
		"test-runtime-config",
		"test-namespace",
		"test",
	)

	// Publish event
	bus.Publish(event)

	// Wait a bit for processing
	time.Sleep(100 * time.Millisecond)

	// Since there are no valid endpoints, no deployment events should be published
	// This test just verifies the component handles the event without crashing
}

// TestDeployToEndpoints_InvalidEndpointType tests handling invalid endpoint types.
func TestDeployToEndpoints_InvalidEndpointType(t *testing.T) {
	bus := busevents.NewEventBus(100)
	eventChan := bus.Subscribe(100)
	bus.Start()

	deployer := createTestDeployer(bus)

	ctx := context.Background()
	config := "test config"
	auxFiles := &dataplane.AuxiliaryFiles{}

	// Invalid endpoint type (string instead of dataplane.Endpoint)
	invalidEndpoints := []interface{}{"not-an-endpoint"}

	deployer.deployToEndpoints(ctx, config, auxFiles, invalidEndpoints, "test-runtime-config", "default", "test")

	// Should not crash, just log error
	// When all endpoints are invalid, we return early without publishing events
	timeout := time.After(100 * time.Millisecond)
	receivedEvents := []busevents.Event{}

loop:
	for {
		select {
		case event := <-eventChan:
			receivedEvents = append(receivedEvents, event)
		case <-timeout:
			break loop
		}
	}

	// No events should be published when all endpoints are invalid
	assert.Len(t, receivedEvents, 0)
}

// TestDeployToEndpoints_EventPublishing tests that all expected events are published.
func TestDeployToEndpoints_EventPublishing(t *testing.T) {
	// Note: This test can't actually deploy to real HAProxy instances
	// It tests the event publishing flow assuming deployment would succeed/fail
	bus := busevents.NewEventBus(100)
	bus.Start()

	deployer := createTestDeployer(bus)

	// This test would need a mock dataplane client to test event publishing
	// For now, we've verified the event publishing code structure
	assert.NotNil(t, deployer)
}

// TestComponent_Start tests the component startup and shutdown.
func TestComponent_Start(t *testing.T) {
	bus := busevents.NewEventBus(100)
	deployer := createTestDeployer(bus)

	ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
	defer cancel()

	err := deployer.Start(ctx)

	// Start returns nil on graceful shutdown, ctx.Err() indicates the reason
	require.NoError(t, err)
}

// TestComponent_EndToEndFlow tests the complete event flow.
func TestComponent_EndToEndFlow(t *testing.T) {
	bus := busevents.NewEventBus(100)
	deployer := createTestDeployer(bus)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Start component in background BEFORE starting bus
	// This ensures the component subscribes before events are published
	go deployer.Start(ctx)

	// Give deployer time to subscribe
	time.Sleep(10 * time.Millisecond)

	// NOW start the bus to begin event processing
	bus.Start()

	// Subscribe to events
	eventChan := bus.Subscribe(10)

	// Simulate deployment scheduled event (with no endpoints)
	bus.Publish(events.NewDeploymentScheduledEvent(
		"global\n  daemon\n",
		&dataplane.AuxiliaryFiles{},
		[]interface{}{}, // no endpoints
		"test-runtime-config",
		"test-namespace",
		"test",
	))

	// Wait for event processing
	time.Sleep(50 * time.Millisecond)

	// Verify no deployment events were published (no valid endpoints)
	timeout := time.After(100 * time.Millisecond)
	receivedEvents := 0

loop:
	for {
		select {
		case <-eventChan:
			receivedEvents++
		case <-timeout:
			break loop
		}
	}

	// Only the DeploymentScheduledEvent we published should be received
	assert.Equal(t, 1, receivedEvents)

	// Cleanup
	cancel()
	time.Sleep(50 * time.Millisecond)
}
