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

package reconciler

import (
	"context"
	"log/slog"
	"os"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"haproxy-template-ic/pkg/controller/events"
	busevents "haproxy-template-ic/pkg/events"
	"haproxy-template-ic/pkg/k8s/types"
)

// TestReconciler_DebounceResourceChanges tests that resource changes are properly debounced.
func TestReconciler_DebounceResourceChanges(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	// Use short debounce interval for faster tests
	config := &Config{
		DebounceInterval: 100 * time.Millisecond,
	}

	reconciler := New(bus, logger, config)

	// Subscribe to reconciliation triggered events
	eventChan := bus.Subscribe(50)
	bus.Start()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Start reconciler in background
	go reconciler.Start(ctx)

	// Give the reconciler time to start listening
	time.Sleep(50 * time.Millisecond)

	// Publish a resource change event (not initial sync)
	bus.Publish(events.NewResourceIndexUpdatedEvent("ingresses", types.ChangeStats{
		Created:       1,
		Modified:      0,
		Deleted:       0,
		IsInitialSync: false,
	}))

	// Wait for debounce timer to expire and reconciliation to trigger
	timeout := time.After(500 * time.Millisecond)
	var receivedEvent *events.ReconciliationTriggeredEvent

	for {
		select {
		case event := <-eventChan:
			if e, ok := event.(*events.ReconciliationTriggeredEvent); ok {
				receivedEvent = e
				goto Done
			}
		case <-timeout:
			t.Fatal("Timeout waiting for ReconciliationTriggeredEvent")
		}
	}

Done:
	require.NotNil(t, receivedEvent, "Should receive ReconciliationTriggeredEvent")
	assert.Equal(t, "debounce_timer", receivedEvent.Reason)
}

// TestReconciler_MultipleChangesResetDebounce tests that multiple changes reset the debounce timer.
func TestReconciler_MultipleChangesResetDebounce(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	config := &Config{
		DebounceInterval: 200 * time.Millisecond,
	}

	reconciler := New(bus, logger, config)

	eventChan := bus.Subscribe(50)
	bus.Start()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go reconciler.Start(ctx)

	// Give the reconciler time to start listening
	time.Sleep(50 * time.Millisecond)

	// Start timing from here to measure total delay
	startTime := time.Now()

	// Publish first change
	bus.Publish(events.NewResourceIndexUpdatedEvent("ingresses", types.ChangeStats{
		Created:       1,
		IsInitialSync: false,
	}))

	// Wait 100ms (half of debounce interval)
	time.Sleep(100 * time.Millisecond)

	// Publish second change - this should reset the timer
	bus.Publish(events.NewResourceIndexUpdatedEvent("services", types.ChangeStats{
		Modified:      1,
		IsInitialSync: false,
	}))

	// Now wait for debounce to complete (200ms from second event)
	// Total time: 100ms + 200ms = 300ms
	timeout := time.After(400 * time.Millisecond)
	var receivedEvent *events.ReconciliationTriggeredEvent

	for {
		select {
		case event := <-eventChan:
			if e, ok := event.(*events.ReconciliationTriggeredEvent); ok {
				receivedEvent = e
				goto Done
			}
		case <-timeout:
			t.Fatal("Timeout waiting for ReconciliationTriggeredEvent")
		}
	}

Done:
	elapsed := time.Since(startTime)

	require.NotNil(t, receivedEvent)
	assert.Equal(t, "debounce_timer", receivedEvent.Reason)

	// Should take at least 250ms (100ms wait + 200ms debounce, with some tolerance)
	assert.Greater(t, elapsed, 250*time.Millisecond,
		"Reconciliation should be delayed by the full debounce interval after the second change")
}

// TestReconciler_ConfigChangeImmediateTrigger tests that config changes trigger immediately.
func TestReconciler_ConfigChangeImmediateTrigger(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	config := &Config{
		DebounceInterval: 500 * time.Millisecond, // Long interval
	}

	reconciler := New(bus, logger, config)

	eventChan := bus.Subscribe(50)
	bus.Start()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go reconciler.Start(ctx)

	// Give the reconciler time to start listening
	time.Sleep(50 * time.Millisecond)

	// Publish config change event
	bus.Publish(events.NewConfigValidatedEvent(nil, "v1", "s1"))

	// Should trigger immediately (within 100ms, not after 500ms debounce)
	timeout := time.After(200 * time.Millisecond)
	var receivedEvent *events.ReconciliationTriggeredEvent

	for {
		select {
		case event := <-eventChan:
			if e, ok := event.(*events.ReconciliationTriggeredEvent); ok {
				receivedEvent = e
				goto Done
			}
		case <-timeout:
			t.Fatal("Timeout waiting for ReconciliationTriggeredEvent")
		}
	}

Done:
	require.NotNil(t, receivedEvent)
	assert.Equal(t, "config_change", receivedEvent.Reason)
}

// TestReconciler_SkipInitialSyncEvents tests that initial sync events don't trigger reconciliation.
func TestReconciler_SkipInitialSyncEvents(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	config := &Config{
		DebounceInterval: 100 * time.Millisecond,
	}

	reconciler := New(bus, logger, config)

	eventChan := bus.Subscribe(50)
	bus.Start()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go reconciler.Start(ctx)

	// Publish initial sync events
	bus.Publish(events.NewResourceIndexUpdatedEvent("ingresses", types.ChangeStats{
		Created:       10,
		IsInitialSync: true,
	}))

	bus.Publish(events.NewResourceIndexUpdatedEvent("services", types.ChangeStats{
		Created:       5,
		IsInitialSync: true,
	}))

	// Wait longer than debounce interval
	time.Sleep(300 * time.Millisecond)

	// Should NOT receive any reconciliation triggered events
	select {
	case event := <-eventChan:
		if _, ok := event.(*events.ReconciliationTriggeredEvent); ok {
			t.Fatal("Should not trigger reconciliation for initial sync events")
		}
	default:
		// Expected - no events
	}
}

// TestReconciler_ConfigCancelsDebounce tests that config changes cancel pending debounce.
func TestReconciler_ConfigCancelsDebounce(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	config := &Config{
		DebounceInterval: 300 * time.Millisecond,
	}

	reconciler := New(bus, logger, config)

	eventChan := bus.Subscribe(50)
	bus.Start()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go reconciler.Start(ctx)

	// Publish resource change (starts debounce timer)
	bus.Publish(events.NewResourceIndexUpdatedEvent("ingresses", types.ChangeStats{
		Created:       1,
		IsInitialSync: false,
	}))

	// Wait a bit but not long enough for debounce
	time.Sleep(100 * time.Millisecond)

	// Publish config change (should trigger immediately and cancel debounce)
	bus.Publish(events.NewConfigValidatedEvent(nil, "v2", "s2"))

	// Should receive config_change trigger quickly
	timeout := time.After(200 * time.Millisecond)
	var receivedEvents []*events.ReconciliationTriggeredEvent

Loop:
	for {
		select {
		case event := <-eventChan:
			if e, ok := event.(*events.ReconciliationTriggeredEvent); ok {
				receivedEvents = append(receivedEvents, e)
			}
		case <-timeout:
			break Loop
		}
	}

	// Should only receive one event (config_change), not the debounced resource_change
	require.Len(t, receivedEvents, 1, "Should only receive one reconciliation trigger")
	assert.Equal(t, "config_change", receivedEvents[0].Reason)
}

// TestReconciler_ContextCancellation tests graceful shutdown on context cancellation.
func TestReconciler_ContextCancellation(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	reconciler := New(bus, logger, nil)

	eventChan := bus.Subscribe(50)
	bus.Start()

	ctx, cancel := context.WithCancel(context.Background())

	// Start reconciler
	done := make(chan error, 1)
	go func() {
		done <- reconciler.Start(ctx)
	}()

	// Publish a resource change to start debounce
	bus.Publish(events.NewResourceIndexUpdatedEvent("ingresses", types.ChangeStats{
		Created:       1,
		IsInitialSync: false,
	}))

	// Cancel context before debounce expires
	time.Sleep(50 * time.Millisecond)
	cancel()

	// Should return quickly
	timeout := time.After(1 * time.Second)
	select {
	case err := <-done:
		assert.NoError(t, err, "Start should return nil on context cancellation")
	case <-timeout:
		t.Fatal("Reconciler did not shut down within timeout")
	}

	// Should not have triggered reconciliation
	select {
	case event := <-eventChan:
		if _, ok := event.(*events.ReconciliationTriggeredEvent); ok {
			t.Fatal("Should not trigger reconciliation after context cancellation")
		}
	default:
		// Expected - no reconciliation event
	}
}

// TestReconciler_CustomDebounceInterval tests using a custom debounce interval.
func TestReconciler_CustomDebounceInterval(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	customInterval := 150 * time.Millisecond
	config := &Config{
		DebounceInterval: customInterval,
	}

	reconciler := New(bus, logger, config)

	eventChan := bus.Subscribe(50)
	bus.Start()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go reconciler.Start(ctx)

	// Give the reconciler time to start listening
	time.Sleep(50 * time.Millisecond)

	startTime := time.Now()

	// Publish resource change
	bus.Publish(events.NewResourceIndexUpdatedEvent("ingresses", types.ChangeStats{
		Created:       1,
		IsInitialSync: false,
	}))

	// Wait for reconciliation
	timeout := time.After(500 * time.Millisecond)
	var receivedEvent *events.ReconciliationTriggeredEvent

	for {
		select {
		case event := <-eventChan:
			if e, ok := event.(*events.ReconciliationTriggeredEvent); ok {
				receivedEvent = e
				goto Done
			}
		case <-timeout:
			t.Fatal("Timeout waiting for ReconciliationTriggeredEvent")
		}
	}

Done:
	elapsed := time.Since(startTime)

	require.NotNil(t, receivedEvent)
	assert.Equal(t, "debounce_timer", receivedEvent.Reason)

	// Verify timing is approximately correct (with tolerance)
	assert.Greater(t, elapsed, customInterval-10*time.Millisecond,
		"Should wait at least the custom debounce interval")
	assert.Less(t, elapsed, customInterval+100*time.Millisecond,
		"Should not wait significantly longer than the custom debounce interval")
}

// TestReconciler_DefaultConfig tests using default configuration.
func TestReconciler_DefaultConfig(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	// Pass nil config to use defaults
	reconciler := New(bus, logger, nil)

	assert.Equal(t, DefaultDebounceInterval, reconciler.debounceInterval,
		"Should use default debounce interval when config is nil")
}

// TestReconciler_ZeroDebounceUsesDefault tests that zero debounce interval falls back to default.
func TestReconciler_ZeroDebounceUsesDefault(t *testing.T) {
	bus := busevents.NewEventBus(100)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	config := &Config{
		DebounceInterval: 0, // Invalid - should use default
	}

	reconciler := New(bus, logger, config)

	assert.Equal(t, DefaultDebounceInterval, reconciler.debounceInterval,
		"Should use default debounce interval when config value is zero")
}
