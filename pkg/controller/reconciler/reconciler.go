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

// Package reconciler implements the Reconciler component that debounces resource
// changes and triggers reconciliation events.
//
// The Reconciler is a key component in Stage 5 of the controller startup sequence.
// It subscribes to resource change events, applies debouncing to batch rapid changes,
// and publishes reconciliation trigger events when the system reaches a quiet state.
package reconciler

import (
	"context"
	"log/slog"
	"time"

	"haproxy-template-ic/pkg/controller/events"
	busevents "haproxy-template-ic/pkg/events"
)

const (
	// DefaultDebounceInterval is the default time to wait after the last resource
	// change before triggering reconciliation.
	DefaultDebounceInterval = 500 * time.Millisecond

	// EventBufferSize is the size of the event subscription buffer.
	EventBufferSize = 100
)

// Reconciler implements the reconciliation debouncer component.
//
// It subscribes to resource change events and configuration change events,
// applies debouncing logic to prevent excessive reconciliations, and triggers
// reconciliation when appropriate.
//
// Debouncing behavior:
//   - Resource changes: Wait for quiet period (debounce interval) before triggering
//   - Config changes: Trigger immediately (no debouncing)
//
// The component publishes ReconciliationTriggeredEvent to signal the Executor
// to begin a reconciliation cycle.
type Reconciler struct {
	eventBus          *busevents.EventBus
	logger            *slog.Logger
	debounceInterval  time.Duration
	debounceTimer     *time.Timer
	pendingTrigger    bool
	lastTriggerReason string
}

// Config configures the Reconciler component.
type Config struct {
	// DebounceInterval is the time to wait after the last resource change
	// before triggering reconciliation. If not set, DefaultDebounceInterval is used.
	DebounceInterval time.Duration
}

// New creates a new Reconciler component.
//
// Parameters:
//   - eventBus: The EventBus for subscribing to events and publishing triggers
//   - logger: Structured logger for component logging
//   - config: Optional configuration (nil for defaults)
//
// Returns:
//   - A new Reconciler instance ready to be started
func New(eventBus *busevents.EventBus, logger *slog.Logger, config *Config) *Reconciler {
	debounceInterval := DefaultDebounceInterval
	if config != nil && config.DebounceInterval > 0 {
		debounceInterval = config.DebounceInterval
	}

	return &Reconciler{
		eventBus:         eventBus,
		logger:           logger,
		debounceInterval: debounceInterval,
		// Timer is created on first use to avoid firing immediately
		debounceTimer:     nil,
		pendingTrigger:    false,
		lastTriggerReason: "",
	}
}

// Start begins the reconciler's event loop.
//
// This method blocks until the context is cancelled or an error occurs.
// It subscribes to the EventBus and processes events:
//   - ResourceIndexUpdatedEvent: Starts/resets debounce timer
//   - ConfigValidatedEvent: Triggers immediate reconciliation
//   - Debounce timer expiration: Publishes ReconciliationTriggeredEvent
//
// The component runs until the context is cancelled, at which point it
// performs cleanup and returns.
//
// Parameters:
//   - ctx: Context for cancellation and lifecycle management
//
// Returns:
//   - nil when context is cancelled (graceful shutdown)
//   - Error only in exceptional circumstances
func (r *Reconciler) Start(ctx context.Context) error {
	r.logger.Info("Reconciler starting",
		"debounce_interval", r.debounceInterval)

	eventChan := r.eventBus.Subscribe(EventBufferSize)

	for {
		select {
		case event := <-eventChan:
			r.handleEvent(event)

		case <-r.getDebounceTimerChan():
			// Debounce timer expired - trigger reconciliation
			r.triggerReconciliation("debounce_timer")

		case <-ctx.Done():
			r.logger.Info("Reconciler shutting down", "reason", ctx.Err())
			r.cleanup()
			return nil
		}
	}
}

// handleEvent processes events from the EventBus.
func (r *Reconciler) handleEvent(event busevents.Event) {
	switch e := event.(type) {
	case *events.ResourceIndexUpdatedEvent:
		r.handleResourceChange(e)

	case *events.ConfigValidatedEvent:
		r.handleConfigChange(e)
	}
}

// handleResourceChange processes resource index update events.
//
// Resource changes are debounced to batch rapid successive changes.
// The debounce timer is reset on each change, and reconciliation is
// only triggered after a quiet period.
func (r *Reconciler) handleResourceChange(event *events.ResourceIndexUpdatedEvent) {
	// Skip initial sync events - we don't want to trigger reconciliation
	// until the initial sync is complete
	if event.ChangeStats.IsInitialSync {
		r.logger.Debug("Skipping initial sync event",
			"resource_type", event.ResourceTypeName,
			"created", event.ChangeStats.Created,
			"modified", event.ChangeStats.Modified,
			"deleted", event.ChangeStats.Deleted)
		return
	}

	r.logger.Debug("Resource change detected, resetting debounce timer",
		"resource_type", event.ResourceTypeName,
		"created", event.ChangeStats.Created,
		"modified", event.ChangeStats.Modified,
		"deleted", event.ChangeStats.Deleted,
		"debounce_interval", r.debounceInterval)

	r.pendingTrigger = true
	r.lastTriggerReason = "resource_change"
	r.resetDebounceTimer()
}

// handleConfigChange processes configuration validation events.
//
// Config changes trigger immediate reconciliation without debouncing,
// as configuration updates are infrequent and require prompt action.
func (r *Reconciler) handleConfigChange(event *events.ConfigValidatedEvent) {
	r.logger.Info("Configuration change detected, triggering immediate reconciliation",
		"config_version", event.Version,
		"secret_version", event.SecretVersion)

	r.stopDebounceTimer()
	r.pendingTrigger = false
	r.triggerReconciliation("config_change")
}

// resetDebounceTimer resets the debounce timer to the configured interval.
func (r *Reconciler) resetDebounceTimer() {
	if r.debounceTimer == nil {
		// Create timer on first use
		r.debounceTimer = time.NewTimer(r.debounceInterval)
	} else {
		// Stop and drain existing timer before resetting
		if !r.debounceTimer.Stop() {
			// Timer already fired, drain the channel
			select {
			case <-r.debounceTimer.C:
			default:
			}
		}
		r.debounceTimer.Reset(r.debounceInterval)
	}
}

// stopDebounceTimer stops the debounce timer if it's running.
func (r *Reconciler) stopDebounceTimer() {
	if r.debounceTimer != nil {
		if !r.debounceTimer.Stop() {
			// Timer already fired, drain the channel
			select {
			case <-r.debounceTimer.C:
			default:
			}
		}
	}
	r.pendingTrigger = false
}

// getDebounceTimerChan returns the debounce timer's channel or a nil channel
// if the timer hasn't been created yet.
//
// This allows the select statement to work correctly - a nil channel blocks forever,
// which is the desired behavior when there's no active debounce timer.
func (r *Reconciler) getDebounceTimerChan() <-chan time.Time {
	if r.debounceTimer == nil {
		return nil
	}
	return r.debounceTimer.C
}

// triggerReconciliation publishes a ReconciliationTriggeredEvent.
func (r *Reconciler) triggerReconciliation(reason string) {
	r.logger.Info("Triggering reconciliation", "reason", reason)

	r.eventBus.Publish(events.NewReconciliationTriggeredEvent(reason))
	r.pendingTrigger = false
}

// cleanup performs cleanup when the component is shutting down.
func (r *Reconciler) cleanup() {
	r.stopDebounceTimer()

	// If there was a pending trigger when we shut down, log it
	if r.pendingTrigger {
		r.logger.Debug("Reconciler shutting down with pending trigger",
			"last_reason", r.lastTriggerReason)
	}
}
