package commentator

import (
	"context"
	"fmt"
	"log/slog"
	"strings"
	"time"

	"haproxy-template-ic/pkg/controller/events"
	"haproxy-template-ic/pkg/controller/validator"
	busevents "haproxy-template-ic/pkg/events"
)

const (
	// maxErrorPreviewLength is the maximum length for error message previews
	// in validation failure summaries. Longer errors are truncated.
	maxErrorPreviewLength = 80
)

// - Decouples logging from business logic.
type EventCommentator struct {
	bus        *busevents.EventBus
	logger     *slog.Logger
	ringBuffer *RingBuffer
	stopCh     chan struct{}
}

// NewEventCommentator creates a new Event Commentator.
//
// Parameters:
//   - bus: The EventBus to subscribe to
//   - logger: The structured logger to use
//   - bufferSize: Ring buffer capacity (recommended: 1000)
//
// Returns:
//   - *EventCommentator ready to start
func NewEventCommentator(bus *busevents.EventBus, logger *slog.Logger, bufferSize int) *EventCommentator {
	return &EventCommentator{
		bus:        bus,
		logger:     logger,
		ringBuffer: NewRingBuffer(bufferSize),
		stopCh:     make(chan struct{}),
	}
}

// Start begins processing events from the EventBus.
//
// This method blocks until Stop() is called or the context is canceled.
// It should typically be run in a goroutine.
//
// Example:
//
//	go commentator.Start(ctx)
func (ec *EventCommentator) Start(ctx context.Context) {
	// Subscribe to all events with generous buffer
	eventCh := ec.bus.Subscribe(200)

	ec.logger.Info("Event commentator started", "buffer_capacity", ec.ringBuffer.Capacity())

	for {
		select {
		case <-ctx.Done():
			ec.logger.Info("Event commentator stopped", "reason", ctx.Err())
			return
		case <-ec.stopCh:
			ec.logger.Info("Event commentator stopped")
			return
		case event := <-eventCh:
			ec.processEvent(event)
		}
	}
}

// Stop gracefully stops the commentator.
func (ec *EventCommentator) Stop() {
	close(ec.stopCh)
}

// processEvent handles a single event: adds to buffer and logs with domain insights.
func (ec *EventCommentator) processEvent(event busevents.Event) {
	// Add to ring buffer first (for correlation)
	ec.ringBuffer.Add(event)

	// Generate domain-aware log message with correlation
	ec.logWithInsight(event)
}

// logWithInsight produces a domain-aware log message for the event.
//
// This is where the "commentator" intelligence lives - applying domain knowledge
// and correlating recent events to provide contextual insights.
func (ec *EventCommentator) logWithInsight(event busevents.Event) {
	eventType := event.EventType()

	// Determine log level based on event type
	level := ec.determineLogLevel(eventType)

	// Generate contextual message and structured attributes
	message, attrs := ec.generateInsight(event)

	// Log with appropriate level
	ec.logger.Log(context.Background(), level, message, attrs...)
}

// determineLogLevel maps event types to appropriate log levels.
func (ec *EventCommentator) determineLogLevel(eventType string) slog.Level {
	switch eventType {
	// Error level - failures
	case events.EventTypeReconciliationFailed,
		events.EventTypeTemplateRenderFailed,
		events.EventTypeValidationFailed,
		events.EventTypeInstanceDeploymentFailed,
		events.EventTypeStorageSyncFailed:
		return slog.LevelError

	// Warn level - invalid states
	case events.EventTypeConfigInvalid,
		events.EventTypeCredentialsInvalid:
		return slog.LevelWarn

	// Info level - lifecycle and completion events
	case events.EventTypeControllerStarted,
		events.EventTypeControllerShutdown,
		events.EventTypeConfigValidated,
		events.EventTypeIndexSynchronized,
		events.EventTypeReconciliationCompleted,
		events.EventTypeValidationCompleted,
		events.EventTypeDeploymentCompleted:
		return slog.LevelInfo

	// Debug level - everything else (detailed operational events)
	default:
		return slog.LevelDebug
	}
}

// generateInsight creates a contextual message and structured attributes for the event.
//
// This applies domain knowledge and uses the ring buffer for event correlation.
//
//nolint:gocyclo,revive // Large switch statement handling many event types - refactoring would reduce readability
func (ec *EventCommentator) generateInsight(event busevents.Event) (insight string, args []any) {
	eventType := event.EventType()
	attrs := []any{
		"event_type", eventType,
		"timestamp", event.Timestamp(),
	}

	switch e := event.(type) {
	// Lifecycle Events
	case *events.ControllerStartedEvent:
		return fmt.Sprintf("Controller started successfully with config %s", e.ConfigVersion),
			append(attrs, "config_version", e.ConfigVersion, "secret_version", e.SecretVersion)

	case *events.ControllerShutdownEvent:
		return fmt.Sprintf("Controller shutting down: %s", e.Reason),
			append(attrs, "reason", e.Reason)

	// Configuration Events
	case *events.ConfigParsedEvent:
		return fmt.Sprintf("Configuration parsed successfully (version %s)", e.Version),
			append(attrs, "version", e.Version, "secret_version", e.SecretVersion)

	case *events.ConfigValidationRequest:
		// Get validator count from validator package constants
		validatorCount := len(validator.AllValidatorNames())
		return fmt.Sprintf("Configuration validation started (version %s, expecting %d validators)",
				e.Version, validatorCount),
			append(attrs, "version", e.Version, "validator_count", validatorCount)

	case *events.ConfigValidationResponse:
		// Show real-time validator results with performance metrics
		statusSymbol := "✓"
		statusText := "OK"
		if !e.Valid {
			statusSymbol = "✗"
			statusText = "FAILED"
		}

		// Build metrics message based on validator type
		var metricsMsg string
		if e.Valid {
			// For successful validation, show positive metrics
			switch e.ValidatorName {
			case "basic":
				metricsMsg = ""
			case "template":
				// Template validator logs template_count
				metricsMsg = ""
			case "jsonpath":
				// JSONPath validator logs expression_count
				metricsMsg = ""
			}
		} else {
			// For failures, show error count
			metricsMsg = fmt.Sprintf(", %d errors", len(e.Errors))
		}

		return fmt.Sprintf("Validator '%s': %s %s%s",
				e.ValidatorName, statusSymbol, statusText, metricsMsg),
			append(attrs, "validator", e.ValidatorName, "valid", e.Valid, "error_count", len(e.Errors))

	case *events.ConfigValidatedEvent:
		// Correlate: how long did validation take?
		validationRequests := ec.ringBuffer.FindByTypeInWindow(events.EventTypeConfigValidationRequest, 30*time.Second)
		var correlationMsg string
		if len(validationRequests) > 0 {
			duration := event.Timestamp().Sub(validationRequests[0].Timestamp())
			correlationMsg = fmt.Sprintf(" (validation completed in %v)", duration.Round(time.Millisecond))
		}
		return fmt.Sprintf("Configuration validated successfully%s", correlationMsg),
			append(attrs, "version", e.Version, "secret_version", e.SecretVersion)

	case *events.ConfigInvalidEvent:
		// Build detailed breakdown per validator
		errorCount := 0
		var validatorBreakdown []string
		for validatorName, errs := range e.ValidationErrors {
			errorCount += len(errs)
			if len(errs) > 0 {
				// Show first error as example
				firstError := errs[0]
				if len(firstError) > maxErrorPreviewLength {
					firstError = firstError[:maxErrorPreviewLength-3] + "..."
				}
				validatorBreakdown = append(validatorBreakdown,
					fmt.Sprintf("%s: %d errors (e.g., %q)", validatorName, len(errs), firstError))
			}
		}

		detailMsg := ""
		if len(validatorBreakdown) > 0 {
			detailMsg = fmt.Sprintf(": %s", strings.Join(validatorBreakdown, "; "))
		}

		return fmt.Sprintf("Configuration validation failed with %d errors across %d validators%s",
				errorCount, len(e.ValidationErrors), detailMsg),
			append(attrs, "version", e.Version, "validator_count", len(e.ValidationErrors), "error_count", errorCount)

	// Resource Events
	case *events.ResourceIndexUpdatedEvent:
		// Don't log during initial sync to reduce noise
		if e.ChangeStats.IsInitialSync {
			return fmt.Sprintf("Resource index loading: %s (created=%d, modified=%d, deleted=%d)",
					e.ResourceTypeName, e.ChangeStats.Created, e.ChangeStats.Modified, e.ChangeStats.Deleted),
				append(attrs,
					"resource_type", e.ResourceTypeName,
					"created", e.ChangeStats.Created,
					"modified", e.ChangeStats.Modified,
					"deleted", e.ChangeStats.Deleted,
					"initial_sync", true)
		}
		return fmt.Sprintf("Resource index updated: %s (created=%d, modified=%d, deleted=%d)",
				e.ResourceTypeName, e.ChangeStats.Created, e.ChangeStats.Modified, e.ChangeStats.Deleted),
			append(attrs,
				"resource_type", e.ResourceTypeName,
				"created", e.ChangeStats.Created,
				"modified", e.ChangeStats.Modified,
				"deleted", e.ChangeStats.Deleted,
				"initial_sync", false)

	case *events.ResourceSyncCompleteEvent:
		return fmt.Sprintf("Initial sync complete for %s (%d resources)",
				e.ResourceTypeName, e.InitialCount),
			append(attrs, "resource_type", e.ResourceTypeName, "initial_count", e.InitialCount)

	case *events.IndexSynchronizedEvent:
		totalResources := 0
		for _, count := range e.ResourceCounts {
			totalResources += count
		}
		return fmt.Sprintf("All resource indexes synchronized (%d resources across %d types)",
				totalResources, len(e.ResourceCounts)),
			append(attrs, "resource_types", len(e.ResourceCounts), "total_resources", totalResources)

	// Reconciliation Events
	case *events.ReconciliationTriggeredEvent:
		// Correlate: when was the last reconciliation?
		recentReconciliations := ec.ringBuffer.FindByTypeInWindow(events.EventTypeReconciliationCompleted, 5*time.Minute)
		var correlationMsg string
		if len(recentReconciliations) > 0 {
			timeSince := event.Timestamp().Sub(recentReconciliations[0].Timestamp())
			correlationMsg = fmt.Sprintf(" (previous reconciliation was %v ago)", timeSince.Round(time.Second))
		}
		return fmt.Sprintf("Reconciliation triggered: %s%s", e.Reason, correlationMsg),
			append(attrs, "reason", e.Reason)

	case *events.ReconciliationStartedEvent:
		return fmt.Sprintf("Reconciliation started: %s", e.Trigger),
			append(attrs, "trigger", e.Trigger)

	case *events.ReconciliationCompletedEvent:
		// Correlate: find the ReconciliationStartedEvent
		startEvents := ec.ringBuffer.FindByTypeInWindow(events.EventTypeReconciliationStarted, 1*time.Minute)
		var phaseInfo string
		if len(startEvents) > 0 {
			totalDuration := event.Timestamp().Sub(startEvents[0].Timestamp())
			phaseInfo = fmt.Sprintf(" (total cycle: %v, reconciliation: %dms)",
				totalDuration.Round(time.Millisecond), e.DurationMs)
		} else {
			phaseInfo = fmt.Sprintf(" (%dms)", e.DurationMs)
		}
		return fmt.Sprintf("Reconciliation completed successfully%s", phaseInfo),
			append(attrs, "duration_ms", e.DurationMs)

	case *events.ReconciliationFailedEvent:
		return fmt.Sprintf("Reconciliation failed in %s phase: %s", e.Phase, e.Error),
			append(attrs, "phase", e.Phase, "error", e.Error)

	// Template Events
	case *events.TemplateRenderedEvent:
		sizeKB := float64(e.ConfigBytes) / 1024.0
		return fmt.Sprintf("Template rendered: %.1f KB config + %d auxiliary files in %dms",
				sizeKB, e.AuxiliaryFileCount, e.DurationMs),
			append(attrs, "config_bytes", e.ConfigBytes, "aux_files", e.AuxiliaryFileCount, "duration_ms", e.DurationMs)

	case *events.TemplateRenderFailedEvent:
		// Error is already formatted by renderer component, just pass it through
		return fmt.Sprintf("Template rendering failed:\n%s", e.Error),
			append(attrs, "template", e.TemplateName)

	// Validation Events
	case *events.ValidationStartedEvent:
		return "Configuration validation started",
			attrs

	case *events.ValidationCompletedEvent:
		warningInfo := ""
		if len(e.Warnings) > 0 {
			warningInfo = fmt.Sprintf(" with %d warnings", len(e.Warnings))
		}
		return fmt.Sprintf("Configuration validation succeeded%s (%dms)", warningInfo, e.DurationMs),
			append(attrs, "warnings", len(e.Warnings), "duration_ms", e.DurationMs)

	case *events.ValidationFailedEvent:
		return fmt.Sprintf("Configuration validation failed with %d errors (%dms)",
				len(e.Errors), e.DurationMs),
			append(attrs, "error_count", len(e.Errors), "duration_ms", e.DurationMs)

	// Deployment Events
	case *events.DeploymentStartedEvent:
		return fmt.Sprintf("Deployment started to %d HAProxy instances", len(e.Endpoints)),
			append(attrs, "instance_count", len(e.Endpoints))

	case *events.InstanceDeployedEvent:
		reloadInfo := ""
		if e.ReloadRequired {
			reloadInfo = " (reload triggered)"
		}
		return fmt.Sprintf("Instance deployed successfully in %dms%s", e.DurationMs, reloadInfo),
			append(attrs, "duration_ms", e.DurationMs, "reload_required", e.ReloadRequired)

	case *events.InstanceDeploymentFailedEvent:
		retryableInfo := ""
		if e.Retryable {
			retryableInfo = " (retryable)"
		}
		return fmt.Sprintf("Instance deployment failed%s: %s", retryableInfo, e.Error),
			append(attrs, "error", e.Error, "retryable", e.Retryable)

	case *events.DeploymentCompletedEvent:
		successRate := float64(e.Succeeded) / float64(e.Total) * 100
		return fmt.Sprintf("Deployment completed: %d/%d instances succeeded (%.0f%%) in %dms",
				e.Succeeded, e.Total, successRate, e.DurationMs),
			append(attrs, "total", e.Total, "succeeded", e.Succeeded, "failed", e.Failed, "duration_ms", e.DurationMs)

	// Storage Events
	case *events.StorageSyncStartedEvent:
		return fmt.Sprintf("Auxiliary file sync started: %s phase to %d instances", e.Phase, len(e.Endpoints)),
			append(attrs, "phase", e.Phase, "instance_count", len(e.Endpoints))

	case *events.StorageSyncCompletedEvent:
		return fmt.Sprintf("Auxiliary file sync completed: %s phase (%dms)", e.Phase, e.DurationMs),
			append(attrs, "phase", e.Phase, "duration_ms", e.DurationMs)

	case *events.StorageSyncFailedEvent:
		return fmt.Sprintf("Auxiliary file sync failed: %s phase: %s", e.Phase, e.Error),
			append(attrs, "phase", e.Phase, "error", e.Error)

	// HAProxy Pod Events
	case *events.HAProxyPodsDiscoveredEvent:
		// Correlate: was this a change?
		recentDiscoveries := ec.ringBuffer.FindByTypeInWindow(events.EventTypeHAProxyPodsDiscovered, 30*time.Second)
		var changeInfo string
		if len(recentDiscoveries) > 1 {
			// Compare with previous discovery
			changeInfo = " (pods changed)"
		}
		return fmt.Sprintf("HAProxy pods discovered: %d instances%s", e.Count, changeInfo),
			append(attrs, "count", e.Count)

	case *events.HAProxyPodAddedEvent:
		return "HAProxy pod added to cluster",
			attrs

	case *events.HAProxyPodRemovedEvent:
		return "HAProxy pod removed from cluster",
			attrs

	default:
		// Fallback for unknown event types
		return fmt.Sprintf("Event: %s", eventType), attrs
	}
}
