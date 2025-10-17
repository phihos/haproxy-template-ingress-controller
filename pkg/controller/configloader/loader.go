package configloader

import (
	"context"
	"fmt"
	"log/slog"

	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"

	"haproxy-template-ic/pkg/controller/events"
	"haproxy-template-ic/pkg/core/config"
	busevents "haproxy-template-ic/pkg/events"
)

// ConfigLoaderComponent subscribes to ConfigResourceChangedEvent and parses ConfigMap data.
//
// This component is responsible for:
// - Extracting YAML configuration from ConfigMap resources
// - Parsing YAML into config.Config structures
// - Publishing ConfigParsedEvent for successfully parsed configs
// - Logging errors for invalid YAML
//
// Architecture:
// This is a pure event-driven component with no knowledge of watchers or
// Kubernetes. It simply reacts to ConfigResourceChangedEvent and produces
// ConfigParsedEvent.
type ConfigLoaderComponent struct {
	bus    *busevents.EventBus
	logger *slog.Logger
	stopCh chan struct{}
}

// NewConfigLoaderComponent creates a new ConfigLoader component.
//
// Parameters:
//   - bus: The EventBus to subscribe to and publish on
//   - logger: Structured logger for diagnostics
//
// Returns:
//   - *ConfigLoaderComponent ready to start
func NewConfigLoaderComponent(bus *busevents.EventBus, logger *slog.Logger) *ConfigLoaderComponent {
	return &ConfigLoaderComponent{
		bus:    bus,
		logger: logger,
		stopCh: make(chan struct{}),
	}
}

// Start begins processing events from the EventBus.
//
// This method blocks until Stop() is called or the context is canceled.
// It should typically be run in a goroutine.
//
// Example:
//
//	go component.Start(ctx)
func (c *ConfigLoaderComponent) Start(ctx context.Context) {
	eventCh := c.bus.Subscribe(50)

	c.logger.Info("ConfigLoader component started")

	for {
		select {
		case <-ctx.Done():
			c.logger.Info("ConfigLoader component stopped", "reason", ctx.Err())
			return
		case <-c.stopCh:
			c.logger.Info("ConfigLoader component stopped")
			return
		case event := <-eventCh:
			if configEvent, ok := event.(*events.ConfigResourceChangedEvent); ok {
				c.processConfigChange(configEvent)
			}
		}
	}
}

// Stop gracefully stops the component.
func (c *ConfigLoaderComponent) Stop() {
	close(c.stopCh)
}

// processConfigChange handles a ConfigResourceChangedEvent by parsing the ConfigMap.
func (c *ConfigLoaderComponent) processConfigChange(event *events.ConfigResourceChangedEvent) {
	// Extract unstructured resource
	resource, ok := event.Resource.(*unstructured.Unstructured)
	if !ok {
		c.logger.Error("ConfigResourceChangedEvent contains invalid resource type",
			"expected", "*unstructured.Unstructured",
			"got", fmt.Sprintf("%T", event.Resource))
		return
	}

	// Get resourceVersion for tracking
	version := resource.GetResourceVersion()

	c.logger.Debug("Processing ConfigMap change", "version", version)

	// Extract ConfigMap data
	data, found, err := unstructured.NestedStringMap(resource.Object, "data")
	if err != nil {
		c.logger.Error("Failed to extract ConfigMap data field",
			"error", err,
			"version", version)
		return
	}
	if !found {
		c.logger.Error("ConfigMap has no data field", "version", version)
		return
	}

	// Extract the "config" key which contains the YAML
	configYAML, ok := data["config"]
	if !ok {
		c.logger.Error("ConfigMap data missing 'config' key", "version", version)
		return
	}

	// Parse the configuration
	cfg, err := config.ParseConfig(configYAML)
	if err != nil {
		c.logger.Error("Failed to parse configuration YAML",
			"error", err,
			"version", version)
		return
	}

	c.logger.Info("Configuration parsed successfully", "version", version)

	// Publish ConfigParsedEvent
	// Note: SecretVersion will be empty here - it gets populated later when
	// the ValidationCoordinator correlates with credentials
	parsedEvent := events.NewConfigParsedEvent(cfg, version, "")
	c.bus.Publish(parsedEvent)
}
