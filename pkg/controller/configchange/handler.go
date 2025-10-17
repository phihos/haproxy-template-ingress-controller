package configchange

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"haproxy-template-ic/pkg/controller/events"
	coreconfig "haproxy-template-ic/pkg/core/config"
	busevents "haproxy-template-ic/pkg/events"
)

// ConfigChangeHandler coordinates configuration validation and detects config changes.
//
// This component has two main responsibilities:
//
//  1. Validation Coordination: Subscribes to ConfigParsedEvent, sends ConfigValidationRequest,
//     collects responses from validators using scatter-gather pattern, and publishes
//     ConfigValidatedEvent or ConfigInvalidEvent.
//
//  2. Change Detection: Subscribes to ConfigValidatedEvent and signals the controller to
//     reinitialize via the configChangeCh channel.
//
// Architecture:
// This component bridges the gap between configuration parsing and validation, and between
// validation and controller reinitialization. It uses the scatter-gather pattern from the
// event bus for coordinating validation across multiple validators.
type ConfigChangeHandler struct {
	bus            *busevents.EventBus
	logger         *slog.Logger
	configChangeCh chan<- *coreconfig.Config
	validators     []string
	stopCh         chan struct{}
}

// NewConfigChangeHandler creates a new ConfigChangeHandler.
//
// Parameters:
//   - bus: The EventBus to subscribe to and publish on
//   - logger: Structured logger for diagnostics
//   - configChangeCh: Channel to signal controller reinitialization with validated config
//   - validators: List of expected validator names (e.g., ["basic", "template", "jsonpath"])
//
// Returns:
//   - *ConfigChangeHandler ready to start
func NewConfigChangeHandler(
	bus *busevents.EventBus,
	logger *slog.Logger,
	configChangeCh chan<- *coreconfig.Config,
	validators []string,
) *ConfigChangeHandler {
	return &ConfigChangeHandler{
		bus:            bus,
		logger:         logger,
		configChangeCh: configChangeCh,
		validators:     validators,
		stopCh:         make(chan struct{}),
	}
}

// Start begins processing events from the EventBus.
//
// This method blocks until Stop() is called or the context is canceled.
// It should typically be run in a goroutine.
//
// Example:
//
//	go handler.Start(ctx)
func (h *ConfigChangeHandler) Start(ctx context.Context) {
	eventCh := h.bus.Subscribe(50)

	h.logger.Info("ConfigChangeHandler started", "validators", h.validators)

	for {
		select {
		case <-ctx.Done():
			h.logger.Info("ConfigChangeHandler stopped", "reason", ctx.Err())
			return
		case <-h.stopCh:
			h.logger.Info("ConfigChangeHandler stopped")
			return
		case event := <-eventCh:
			switch e := event.(type) {
			case *events.ConfigParsedEvent:
				h.handleConfigParsed(ctx, e)
			case *events.ConfigValidatedEvent:
				h.handleConfigValidated(e)
			}
		}
	}
}

// Stop gracefully stops the component.
func (h *ConfigChangeHandler) Stop() {
	close(h.stopCh)
}

// handleConfigParsed coordinates validation for a parsed config using scatter-gather pattern.
func (h *ConfigChangeHandler) handleConfigParsed(ctx context.Context, event *events.ConfigParsedEvent) {
	// If no validators are configured, skip validation and immediately publish validated event
	if len(h.validators) == 0 {
		h.logger.Debug("No validators configured, skipping validation", "version", event.Version)
		h.bus.Publish(events.NewConfigValidatedEvent(
			event.Config,
			event.Version,
			event.SecretVersion,
		))
		return
	}

	h.logger.Info("Coordinating config validation", "version", event.Version)

	// Create validation request
	req := events.NewConfigValidationRequest(event.Config, event.Version)

	// Send request and wait for responses using scatter-gather
	// Timeout is set to 10 seconds based on expected validation performance:
	// - Small configs (10 templates, 5 JSONPaths): ~50-100ms
	// - Medium configs (100 templates, 20 JSONPaths): ~200-500ms
	// - Large configs (1000 templates, 100 JSONPaths): ~2-5 seconds
	// The 10s timeout provides adequate headroom even for very large configs
	// or systems under high CPU pressure. If validation consistently approaches
	// this timeout, consider investigating performance bottlenecks.
	result, err := h.bus.Request(ctx, req, busevents.RequestOptions{
		Timeout:            10 * time.Second,
		ExpectedResponders: h.validators,
	})

	if err != nil {
		h.logger.Error("Config validation request failed",
			"error", err,
			"version", event.Version)
		// Publish invalid event
		h.bus.Publish(events.NewConfigInvalidEvent(event.Version, map[string][]string{
			"coordinator": {err.Error()},
		}))
		return
	}

	// Collect validation errors
	validationErrors := make(map[string][]string)
	allValid := true

	for _, resp := range result.Responses {
		validationResp, ok := resp.(*events.ConfigValidationResponse)
		if !ok {
			h.logger.Warn("Received non-ConfigValidationResponse",
				"type", fmt.Sprintf("%T", resp))
			continue
		}

		if !validationResp.Valid {
			allValid = false
			validationErrors[validationResp.ValidatorName] = validationResp.Errors
		}
	}

	// Check for missing responders
	if len(result.Errors) > 0 {
		allValid = false
		validationErrors["coordinator"] = result.Errors
	}

	if allValid {
		h.logger.Info("Config validation succeeded", "version", event.Version)
		// Publish validated event
		h.bus.Publish(events.NewConfigValidatedEvent(
			event.Config,
			event.Version,
			event.SecretVersion,
		))
	} else {
		h.logger.Warn("Config validation failed",
			"version", event.Version,
			"error_count", len(validationErrors))
		// Publish invalid event
		h.bus.Publish(events.NewConfigInvalidEvent(event.Version, validationErrors))
	}
}

// handleConfigValidated signals controller reinitialization when config is validated.
func (h *ConfigChangeHandler) handleConfigValidated(event *events.ConfigValidatedEvent) {
	h.logger.Info("Config validated, signaling controller reinitialization",
		"version", event.Version)

	// Extract the config
	cfg, ok := event.Config.(*coreconfig.Config)
	if !ok {
		h.logger.Error("ConfigValidatedEvent contains invalid config type",
			"expected", "*coreconfig.Config",
			"got", fmt.Sprintf("%T", event.Config))
		return
	}

	// Signal controller to reinitialize
	// Use non-blocking send to avoid deadlock if channel is full
	select {
	case h.configChangeCh <- cfg:
		h.logger.Debug("Reinitialization signal sent")
	default:
		h.logger.Warn("Failed to send reinitialization signal: channel full")
	}
}
