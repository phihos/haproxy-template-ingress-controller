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
	// SchedulerEventBufferSize is the size of the event subscription buffer for the scheduler.
	SchedulerEventBufferSize = 50
)

// scheduledDeployment represents a deployment that was triggered while another
// deployment was in progress. Only the latest scheduled deployment is kept (latest wins).
type scheduledDeployment struct {
	config    string
	auxFiles  interface{}
	endpoints []interface{}
	reason    string
}

// DeploymentScheduler implements deployment scheduling with rate limiting.
//
// It subscribes to events that trigger deployments, maintains the state of
// rendered and validated configurations, and enforces minimum deployment intervals.
//
// Event subscriptions:
//   - TemplateRenderedEvent: Track rendered config and auxiliary files
//   - ValidationCompletedEvent: Cache validated config and schedule deployment
//   - HAProxyPodsDiscoveredEvent: Update endpoints and schedule deployment
//   - DriftPreventionTriggeredEvent: Schedule drift prevention deployment
//
// The component publishes DeploymentScheduledEvent when a deployment should execute.
type DeploymentScheduler struct {
	eventBus              *busevents.EventBus
	eventChan             <-chan busevents.Event // Event subscription channel (subscribed in constructor)
	logger                *slog.Logger
	minDeploymentInterval time.Duration
	ctx                   context.Context // Main event loop context for scheduling

	// State protected by mutex
	mu                  sync.RWMutex
	lastRenderedConfig  string        // Last rendered HAProxy config (before validation)
	lastAuxiliaryFiles  interface{}   // Last rendered auxiliary files
	lastValidatedConfig string        // Last validated HAProxy config
	lastValidatedAux    interface{}   // Last validated auxiliary files
	currentEndpoints    []interface{} // Current HAProxy pod endpoints
	hasValidConfig      bool          // Whether we have a validated config to deploy

	// Deployment scheduling and rate limiting
	schedulerMutex        sync.Mutex
	deploymentInProgress  bool
	pendingDeployment     *scheduledDeployment
	lastDeploymentEndTime time.Time // When the last deployment completed
}

// NewDeploymentScheduler creates a new DeploymentScheduler component.
//
// Parameters:
//   - eventBus: The EventBus for subscribing to events and publishing scheduled deployments
//   - logger: Structured logger for component logging
//   - minDeploymentInterval: Minimum time between consecutive deployments (rate limiting)
//
// Returns:
//   - A new DeploymentScheduler instance ready to be started
func NewDeploymentScheduler(eventBus *busevents.EventBus, logger *slog.Logger, minDeploymentInterval time.Duration) *DeploymentScheduler {
	return &DeploymentScheduler{
		eventBus:              eventBus,
		eventChan:             eventBus.Subscribe(SchedulerEventBufferSize),
		logger:                logger.With("component", "deployment-scheduler"),
		minDeploymentInterval: minDeploymentInterval,
	}
}

// Start begins the deployment scheduler's event loop.
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
func (s *DeploymentScheduler) Start(ctx context.Context) error {
	s.ctx = ctx // Save context for scheduling operations

	s.logger.Info("DeploymentScheduler starting",
		"min_deployment_interval_ms", s.minDeploymentInterval.Milliseconds())

	for {
		select {
		case event := <-s.eventChan:
			s.handleEvent(ctx, event)

		case <-ctx.Done():
			s.logger.Info("DeploymentScheduler shutting down", "reason", ctx.Err())
			return nil
		}
	}
}

// handleEvent processes events from the EventBus.
func (s *DeploymentScheduler) handleEvent(ctx context.Context, event busevents.Event) {
	switch e := event.(type) {
	case *events.TemplateRenderedEvent:
		s.handleTemplateRendered(e)

	case *events.ValidationCompletedEvent:
		s.handleValidationCompleted(ctx, e)

	case *events.HAProxyPodsDiscoveredEvent:
		s.handlePodsDiscovered(ctx, e)

	case *events.DriftPreventionTriggeredEvent:
		s.handleDriftPreventionTriggered(ctx, e)

	case *events.DeploymentCompletedEvent:
		s.handleDeploymentCompleted(e)

	case *events.LostLeadershipEvent:
		s.handleLostLeadership(e)
	}
}

// handleTemplateRendered handles template rendering completion.
//
// This caches the rendered configuration and auxiliary files for later deployment
// after validation completes.
func (s *DeploymentScheduler) handleTemplateRendered(event *events.TemplateRenderedEvent) {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.lastRenderedConfig = event.HAProxyConfig
	s.lastAuxiliaryFiles = event.AuxiliaryFiles

	s.logger.Debug("cached rendered config for deployment after validation",
		"config_bytes", event.ConfigBytes,
		"aux_files", event.AuxiliaryFileCount)
}

// handleValidationCompleted handles successful configuration validation.
//
// This caches the validated configuration and schedules deployment to current endpoints.
// This is called during full reconciliation cycles (config or resource changes).
func (s *DeploymentScheduler) handleValidationCompleted(ctx context.Context, event *events.ValidationCompletedEvent) {
	s.logger.Info("validation completed, preparing deployment",
		"warnings", len(event.Warnings),
		"duration_ms", event.DurationMs)

	// Log warnings if any
	for _, warning := range event.Warnings {
		s.logger.Warn("validation warning", "warning", warning)
	}

	// Get current state and cache validated config BEFORE scheduling
	// This prevents race where pod discovery reads stale config
	s.mu.Lock()
	config := s.lastRenderedConfig
	auxFiles := s.lastAuxiliaryFiles
	endpoints := s.currentEndpoints
	// Cache validated config immediately to prevent race condition
	s.lastValidatedConfig = config
	s.lastValidatedAux = auxFiles
	s.hasValidConfig = true
	s.mu.Unlock()

	if config == "" {
		s.logger.Error("no rendered config available for deployment")
		return
	}

	if len(endpoints) == 0 {
		s.logger.Debug("no endpoints available yet, config cached for later deployment")
		return
	}

	// Schedule deployment to current endpoints (or queue if deployment in progress)
	s.scheduleOrQueue(ctx, config, auxFiles, endpoints, "config_validation")
}

// handlePodsDiscovered handles HAProxy pod discovery/changes.
//
// This schedules deployment of the last validated configuration to the new set of endpoints.
// This is called when HAProxy pods are added/removed/updated without config changes.
func (s *DeploymentScheduler) handlePodsDiscovered(ctx context.Context, event *events.HAProxyPodsDiscoveredEvent) {
	s.mu.Lock()
	s.currentEndpoints = event.Endpoints
	endpointCount := len(event.Endpoints)
	config := s.lastValidatedConfig
	auxFiles := s.lastValidatedAux
	hasValidConfig := s.hasValidConfig
	s.mu.Unlock()

	s.logger.Info("HAProxy pods discovered",
		"count", endpointCount)

	if !hasValidConfig {
		s.logger.Debug("no validated config available yet, skipping deployment")
		return
	}

	if endpointCount == 0 {
		s.logger.Debug("no endpoints available, skipping deployment")
		return
	}

	// Schedule deployment of last validated config to new endpoints (or queue if in progress)
	s.scheduleOrQueue(ctx, config, auxFiles, event.Endpoints, "pod_discovery")
}

// handleDriftPreventionTriggered handles drift prevention trigger events.
//
// This schedules deployment of the last validated configuration to current endpoints
// to prevent configuration drift caused by external factors.
func (s *DeploymentScheduler) handleDriftPreventionTriggered(ctx context.Context, event *events.DriftPreventionTriggeredEvent) {
	s.mu.RLock()
	config := s.lastValidatedConfig
	auxFiles := s.lastValidatedAux
	endpoints := s.currentEndpoints
	hasValidConfig := s.hasValidConfig
	s.mu.RUnlock()

	s.logger.Info("drift prevention triggered",
		"time_since_last_deployment", event.TimeSinceLastDeployment)

	if !hasValidConfig {
		s.logger.Debug("no validated config available, skipping drift prevention deployment")
		return
	}

	if len(endpoints) == 0 {
		s.logger.Debug("no endpoints available, skipping drift prevention deployment")
		return
	}

	// Schedule drift prevention deployment (or queue if in progress)
	s.scheduleOrQueue(ctx, config, auxFiles, endpoints, "drift_prevention")
}

// handleDeploymentCompleted handles deployment completion events.
//
// This marks the deployment as complete, updates the deployment end time,
// and processes any pending deployment via scheduleOrQueue.
func (s *DeploymentScheduler) handleDeploymentCompleted(_ *events.DeploymentCompletedEvent) {
	s.schedulerMutex.Lock()

	// Mark deployment as complete
	s.deploymentInProgress = false
	s.lastDeploymentEndTime = time.Now()

	// Check if there's a pending deployment to process
	pending := s.pendingDeployment
	if pending != nil {
		s.pendingDeployment = nil
		s.schedulerMutex.Unlock()

		s.logger.Info("deployment completed, processing queued deployment",
			"pending_reason", pending.reason,
			"pending_endpoint_count", len(pending.endpoints))

		// Use scheduleOrQueue for proper mutex management and goroutine control
		// This ensures only one scheduling goroutine runs at a time
		s.scheduleOrQueue(s.ctx, pending.config, pending.auxFiles, pending.endpoints, pending.reason)
		return
	}

	s.schedulerMutex.Unlock()
}

// scheduleOrQueue either queues a deployment if one is in progress, or schedules it immediately.
//
// This prevents concurrent deployments which can cause version conflicts.
// Uses a "latest wins" pattern where pending deployments overwrite each other.
func (s *DeploymentScheduler) scheduleOrQueue(
	ctx context.Context,
	config string,
	auxFiles interface{},
	endpoints []interface{},
	reason string,
) {
	s.schedulerMutex.Lock()

	if s.deploymentInProgress {
		// Deployment already in progress - overwrite pending (latest wins)
		s.pendingDeployment = &scheduledDeployment{
			config:    config,
			auxFiles:  auxFiles,
			endpoints: endpoints,
			reason:    reason,
		}
		s.schedulerMutex.Unlock()
		s.logger.Info("deployment in progress, queued for later",
			"reason", reason,
			"endpoint_count", len(endpoints))
		return
	}

	// Mark as in-progress and unlock before scheduling
	s.deploymentInProgress = true
	s.schedulerMutex.Unlock()

	// Schedule deployment asynchronously to avoid blocking event loop
	// This allows new events to be received and queued while we handle rate limiting
	go s.scheduleWithRateLimitUnlocked(ctx, config, auxFiles, endpoints, reason)
}

// scheduleWithRateLimitUnlocked schedules a deployment, enforcing rate limiting.
//
// This method should only be called from scheduleOrQueue() which manages the scheduler mutex.
// It enforces the minimum deployment interval and recursively processes pending deployments.
func (s *DeploymentScheduler) scheduleWithRateLimitUnlocked(
	ctx context.Context,
	config string,
	auxFiles interface{},
	endpoints []interface{},
	reason string,
) {
	// Get last deployment time for rate limiting
	s.schedulerMutex.Lock()
	lastDeploymentEnd := s.lastDeploymentEndTime
	s.schedulerMutex.Unlock()

	// Enforce minimum deployment interval (rate limiting)
	// Only enforce if we have a previous deployment time (not zero)
	if !lastDeploymentEnd.IsZero() && s.minDeploymentInterval > 0 {
		timeSinceLastDeployment := time.Since(lastDeploymentEnd)
		if timeSinceLastDeployment < s.minDeploymentInterval {
			sleepDuration := s.minDeploymentInterval - timeSinceLastDeployment
			s.logger.Info("enforcing minimum deployment interval",
				"sleep_duration_ms", sleepDuration.Milliseconds(),
				"min_interval_ms", s.minDeploymentInterval.Milliseconds(),
				"time_since_last_ms", timeSinceLastDeployment.Milliseconds())

			// Sleep with context awareness
			timer := time.NewTimer(sleepDuration)
			select {
			case <-timer.C:
				// Sleep completed
			case <-ctx.Done():
				timer.Stop()
				s.schedulerMutex.Lock()
				s.deploymentInProgress = false
				s.schedulerMutex.Unlock()
				s.logger.Info("deployment scheduling cancelled during rate limit sleep",
					"reason", reason)
				return
			}
		}
	}

	// Publish DeploymentScheduledEvent
	s.logger.Info("scheduling deployment",
		"reason", reason,
		"endpoint_count", len(endpoints),
		"config_bytes", len(config))

	s.eventBus.Publish(events.NewDeploymentScheduledEvent(config, auxFiles, endpoints, reason))

	// Note: We wait for DeploymentCompletedEvent to update lastDeploymentEndTime
	// This is handled in handleDeploymentCompleted()

	// Check for pending deployment and process it
	s.schedulerMutex.Lock()
	pending := s.pendingDeployment
	s.pendingDeployment = nil

	if pending == nil {
		// No pending work - wait for DeploymentCompletedEvent to mark as done
		// (deploymentInProgress stays true until handleDeploymentCompleted)
		s.schedulerMutex.Unlock()
		return
	}

	// Pending deployment exists - stay in scheduling mode
	// (deploymentInProgress stays true)
	s.schedulerMutex.Unlock()

	// Check context before processing pending
	select {
	case <-ctx.Done():
		s.schedulerMutex.Lock()
		s.deploymentInProgress = false // Shutdown case - safe to clear
		s.schedulerMutex.Unlock()
		s.logger.Info("deployment scheduling cancelled, discarding pending deployment",
			"reason", pending.reason)
		return
	default:
	}

	s.logger.Info("processing queued deployment",
		"reason", pending.reason,
		"endpoint_count", len(pending.endpoints))

	// Recursive: schedule pending (we're still marked as in-progress)
	s.scheduleWithRateLimitUnlocked(ctx, pending.config, pending.auxFiles,
		pending.endpoints, pending.reason)
}

// handleLostLeadership handles LostLeadershipEvent by clearing deployment state.
//
// When a replica loses leadership, leader-only components (including this scheduler)
// are stopped via context cancellation. However, we defensively clear state to prevent
// potential deadlocks if there's a race condition during shutdown.
//
// This prevents scenarios where:
//   - deploymentInProgress is stuck at true, blocking future deployments
//   - pendingDeployment contains stale deployments that shouldn't execute
func (s *DeploymentScheduler) handleLostLeadership(_ *events.LostLeadershipEvent) {
	s.schedulerMutex.Lock()
	defer s.schedulerMutex.Unlock()

	if s.deploymentInProgress || s.pendingDeployment != nil {
		s.logger.Info("lost leadership, clearing deployment state",
			"deployment_in_progress", s.deploymentInProgress,
			"has_pending", s.pendingDeployment != nil)
	}

	// Clear deployment state to prevent stale deployments
	s.deploymentInProgress = false
	s.pendingDeployment = nil

	// Note: lastDeploymentEndTime is NOT cleared - this historical data is safe to keep
	// and helps prevent rapid deployments if leadership is quickly reacquired
}
