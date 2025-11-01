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

// Package deployer implements deployment scheduling and execution components.
package deployer

import (
	"context"
	"log/slog"
	"sync"
	"time"

	"haproxy-template-ic/pkg/controller/events"
	busevents "haproxy-template-ic/pkg/events"
)

const (
	// DriftMonitorEventBufferSize is the size of the event subscription buffer for the drift monitor.
	DriftMonitorEventBufferSize = 50
)

// DriftPreventionMonitor monitors deployment activity and triggers periodic
// deployments to prevent configuration drift caused by external factors.
//
// When no deployment has occurred within the configured interval, it publishes
// a DriftPreventionTriggeredEvent to trigger a deployment. This helps detect
// and correct configuration drift caused by other Dataplane API clients or
// manual changes.
//
// Event subscriptions:
//   - DeploymentCompletedEvent: Reset drift prevention timer
//
// The component publishes DriftPreventionTriggeredEvent when drift prevention
// is needed.
type DriftPreventionMonitor struct {
	eventBus                *busevents.EventBus
	eventChan               <-chan busevents.Event // Event subscription channel (subscribed in constructor)
	logger                  *slog.Logger
	driftPreventionInterval time.Duration

	// Timer management protected by mutex
	mu                 sync.Mutex
	driftTimer         *time.Timer
	driftTimerChan     <-chan time.Time
	lastDeploymentTime time.Time
	timerActive        bool
}

// NewDriftPreventionMonitor creates a new DriftPreventionMonitor component.
//
// Parameters:
//   - eventBus: The EventBus for subscribing to events and publishing triggers
//   - logger: Structured logger for component logging
//   - driftPreventionInterval: Interval after which to trigger drift prevention deployment
//
// Returns:
//   - A new DriftPreventionMonitor instance ready to be started
func NewDriftPreventionMonitor(eventBus *busevents.EventBus, logger *slog.Logger, driftPreventionInterval time.Duration) *DriftPreventionMonitor {
	return &DriftPreventionMonitor{
		eventBus:                eventBus,
		eventChan:               eventBus.Subscribe(DriftMonitorEventBufferSize),
		logger:                  logger.With("component", "drift-prevention-monitor"),
		driftPreventionInterval: driftPreventionInterval,
	}
}

// Start begins the drift prevention monitor's event loop.
//
// This method blocks until the context is cancelled or an error occurs.
// It processes events from the subscription channel established in the constructor.
//
// Parameters:
//   - ctx: Context for cancellation and lifecycle management
//
// Returns:
//   - nil when context is cancelled (graceful shutdown)
//   - Error only in exceptional circumstances
func (m *DriftPreventionMonitor) Start(ctx context.Context) error {
	m.logger.Info("DriftPreventionMonitor starting",
		"drift_prevention_interval_ms", m.driftPreventionInterval.Milliseconds())

	// Start initial drift prevention timer
	m.resetDriftTimer()

	for {
		select {
		case event := <-m.eventChan:
			m.handleEvent(event)

		case <-m.getDriftTimerChan():
			m.handleDriftTimerExpired()

		case <-ctx.Done():
			m.logger.Info("DriftPreventionMonitor shutting down", "reason", ctx.Err())
			m.stopDriftTimer()
			return nil
		}
	}
}

// handleEvent processes events from the EventBus.
func (m *DriftPreventionMonitor) handleEvent(event busevents.Event) {
	switch e := event.(type) {
	case *events.DeploymentCompletedEvent:
		m.handleDeploymentCompleted()

	case *events.LostLeadershipEvent:
		m.handleLostLeadership(e)
	}
}

// handleDeploymentCompleted handles deployment completion events.
//
// This resets the drift prevention timer since a deployment has occurred.
func (m *DriftPreventionMonitor) handleDeploymentCompleted() {
	m.logger.Debug("deployment completed, resetting drift prevention timer")
	m.resetDriftTimer()
}

// handleDriftTimerExpired handles drift timer expiration.
//
// This publishes a DriftPreventionTriggeredEvent to trigger a deployment.
func (m *DriftPreventionMonitor) handleDriftTimerExpired() {
	m.mu.Lock()
	timeSinceLastDeployment := time.Since(m.lastDeploymentTime)
	m.mu.Unlock()

	m.logger.Info("drift prevention timer expired, triggering deployment",
		"time_since_last_deployment", timeSinceLastDeployment)

	// Publish drift prevention trigger event
	m.eventBus.Publish(events.NewDriftPreventionTriggeredEvent(timeSinceLastDeployment))

	// Reset timer for next interval
	// Note: The deployment will complete and trigger handleDeploymentCompleted
	// which will also reset the timer, but we reset here to ensure the timer
	// keeps running even if the deployment fails
	m.resetDriftTimer()
}

// resetDriftTimer resets the drift prevention timer.
//
// This should be called whenever a deployment completes or when the timer expires.
func (m *DriftPreventionMonitor) resetDriftTimer() {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.lastDeploymentTime = time.Now()

	// Stop existing timer if any
	if m.driftTimer != nil {
		m.driftTimer.Stop()
	}

	// Create new timer
	m.driftTimer = time.NewTimer(m.driftPreventionInterval)
	m.driftTimerChan = m.driftTimer.C
	m.timerActive = true

	m.logger.Debug("drift prevention timer reset",
		"next_trigger_in_ms", m.driftPreventionInterval.Milliseconds())
}

// stopDriftTimer stops the drift prevention timer.
//
// This should be called during shutdown.
func (m *DriftPreventionMonitor) stopDriftTimer() {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.driftTimer != nil {
		m.driftTimer.Stop()
		m.timerActive = false
	}
}

// getDriftTimerChan returns the drift timer channel for select statements.
//
// Returns a closed channel if no timer is active to prevent blocking.
func (m *DriftPreventionMonitor) getDriftTimerChan() <-chan time.Time {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.timerActive && m.driftTimerChan != nil {
		return m.driftTimerChan
	}

	// Return closed channel to prevent blocking
	closed := make(chan time.Time)
	close(closed)
	return closed
}

// handleLostLeadership handles LostLeadershipEvent by stopping the drift prevention timer.
//
// When a replica loses leadership, leader-only components (including this monitor)
// are stopped via context cancellation. However, we defensively stop the timer and
// clear state to prevent potential issues during shutdown.
//
// This ensures:
//   - The drift timer is properly stopped (no leaked goroutines)
//   - lastDeploymentTime is cleared (fresh start if leadership is reacquired)
func (m *DriftPreventionMonitor) handleLostLeadership(_ *events.LostLeadershipEvent) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.timerActive {
		m.logger.Info("lost leadership, stopping drift prevention timer")
	}

	// Stop drift timer
	if m.driftTimer != nil {
		m.driftTimer.Stop()
		m.timerActive = false
	}

	// Clear last deployment time (fresh start if leadership is reacquired)
	m.lastDeploymentTime = time.Time{}
}
