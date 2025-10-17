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

// Package executor implements the Executor component that orchestrates
// reconciliation cycles by coordinating pure components.
//
// The Executor is a key component in Stage 5 of the controller startup sequence.
// It subscribes to reconciliation trigger events, orchestrates pure components
// (Renderer, Validator, Deployer), and publishes events at each stage for
// observability and coordination.
package executor

import (
	"context"
	"log/slog"
	"time"

	"haproxy-template-ic/pkg/controller/events"
	busevents "haproxy-template-ic/pkg/events"
)

const (
	// EventBufferSize is the size of the event subscription buffer.
	EventBufferSize = 50
)

// Executor implements the reconciliation orchestrator component.
//
// It subscribes to ReconciliationTriggeredEvent and orchestrates the
// reconciliation workflow:
//  1. Render templates with current resource state
//  2. Validate generated configuration
//  3. Deploy validated configuration to HAProxy instances
//
// The component publishes events at each stage for observability:
//   - ReconciliationStartedEvent: Reconciliation cycle begins
//   - TemplateRenderedEvent: Template rendering completes
//   - ValidationCompletedEvent: Validation succeeds
//   - DeploymentCompletedEvent: Deployment succeeds
//   - ReconciliationCompletedEvent: Full cycle completes
//   - ReconciliationFailedEvent: Any stage fails
type Executor struct {
	eventBus *busevents.EventBus
	logger   *slog.Logger
}

// New creates a new Executor component.
//
// Parameters:
//   - eventBus: The EventBus for subscribing to events and publishing results
//   - logger: Structured logger for component logging
//
// Returns:
//   - A new Executor instance ready to be started
func New(eventBus *busevents.EventBus, logger *slog.Logger) *Executor {
	return &Executor{
		eventBus: eventBus,
		logger:   logger,
	}
}

// Start begins the executor's event loop.
//
// This method blocks until the context is cancelled or an error occurs.
// It subscribes to the EventBus and processes events:
//   - ReconciliationTriggeredEvent: Starts orchestration of reconciliation cycle
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
func (e *Executor) Start(ctx context.Context) error {
	e.logger.Info("Executor starting")

	eventChan := e.eventBus.Subscribe(EventBufferSize)

	for {
		select {
		case event := <-eventChan:
			e.handleEvent(event)

		case <-ctx.Done():
			e.logger.Info("Executor shutting down", "reason", ctx.Err())
			return nil
		}
	}
}

// handleEvent processes events from the EventBus.
func (e *Executor) handleEvent(event busevents.Event) {
	if ev, ok := event.(*events.ReconciliationTriggeredEvent); ok {
		e.handleReconciliationTriggered(ev)
	}
}

// handleReconciliationTriggered orchestrates a reconciliation cycle.
//
// This is the main entry point for the reconciliation workflow. It coordinates
// the following phases:
//  1. Template rendering
//  2. Configuration validation
//  3. Deployment to HAProxy instances
//
// Events are published at each phase for observability and coordination.
func (e *Executor) handleReconciliationTriggered(event *events.ReconciliationTriggeredEvent) {
	startTime := time.Now()

	e.logger.Info("Reconciliation triggered", "reason", event.Reason)

	// Publish reconciliation started event
	e.eventBus.Publish(events.NewReconciliationStartedEvent(event.Reason))

	// TODO: Implement orchestration phases:
	//   1. Render templates (call Renderer pure component)
	//   2. Validate configuration (call Validator pure component)
	//   3. Deploy to HAProxy instances (call Deployer pure component)
	//
	// For now, this is a minimal stub that establishes the event flow.
	e.logger.Debug("Orchestration not yet implemented - skipping render/validate/deploy phases")

	// Publish reconciliation completed event
	durationMs := time.Since(startTime).Milliseconds()
	e.eventBus.Publish(events.NewReconciliationCompletedEvent(durationMs))

	e.logger.Info("Reconciliation completed",
		"duration_ms", durationMs)
}
