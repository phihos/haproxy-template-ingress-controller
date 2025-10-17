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

// Package controller provides the main controller orchestration for the HAProxy template ingress controller.
//
// The controller follows an event-driven architecture with a reinitialization loop:
// 1. Fetch and validate initial configuration
// 2. Create EventBus and components
// 3. Start components and watchers
// 4. Wait for configuration changes
// 5. Reinitialize on valid config changes
package controller

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"golang.org/x/sync/errgroup"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"

	"haproxy-template-ic/pkg/controller/commentator"
	"haproxy-template-ic/pkg/controller/configchange"
	"haproxy-template-ic/pkg/controller/configloader"
	"haproxy-template-ic/pkg/controller/credentialsloader"
	"haproxy-template-ic/pkg/controller/events"
	"haproxy-template-ic/pkg/controller/indextracker"
	"haproxy-template-ic/pkg/controller/resourcewatcher"
	"haproxy-template-ic/pkg/controller/validator"
	coreconfig "haproxy-template-ic/pkg/core/config"
	busevents "haproxy-template-ic/pkg/events"
	"haproxy-template-ic/pkg/k8s/client"
	"haproxy-template-ic/pkg/k8s/types"
	"haproxy-template-ic/pkg/k8s/watcher"
)

const (
	// RetryDelay is the duration to wait before retrying after an iteration failure.
	RetryDelay = 5 * time.Second
)

// Run is the main entry point for the controller.
//
// It performs initial configuration fetching and validation, then enters a reinitialization
// loop where it responds to configuration changes by restarting with the new configuration.
//
// The controller uses an event-driven architecture:
//   - EventBus coordinates all components
//   - SingleWatchers monitor ConfigMap and Secret
//   - Components react to events and publish results
//   - ConfigChangeHandler detects validated config changes and signals reinitialization
//
// Parameters:
//   - ctx: Context for cancellation (SIGTERM, SIGINT, etc.)
//   - k8sClient: Kubernetes client for API access
//   - configMapName: Name of the ConfigMap containing the controller configuration
//   - secretName: Name of the Secret containing HAProxy Dataplane API credentials
//
// Returns:
//   - Error if the controller cannot start or encounters a fatal error
//   - nil if the context is cancelled (graceful shutdown)
func Run(ctx context.Context, k8sClient *client.Client, configMapName, secretName string) error {
	logger := slog.Default()

	logger.Info("HAProxy Template Ingress Controller starting",
		"configmap", configMapName,
		"secret", secretName,
		"namespace", k8sClient.Namespace())

	// Main reinitialization loop
	for {
		select {
		case <-ctx.Done():
			logger.Info("Controller shutting down", "reason", ctx.Err())
			return nil
		default:
			// Run one iteration
			err := runIteration(ctx, k8sClient, configMapName, secretName, logger)
			if err != nil {
				// Check if error is context cancellation (graceful shutdown)
				if ctx.Err() != nil {
					logger.Info("Controller shutting down during iteration", "reason", ctx.Err())
					return nil //nolint:nilerr // Graceful shutdown is not an error
				}

				// Log error and retry after delay
				logger.Error("Controller iteration failed, retrying",
					"error", err,
					"retry_delay", RetryDelay)
				time.Sleep(RetryDelay)
			}
			// If err == nil, config change occurred and we reinitialize immediately
		}
	}
}

// fetchAndValidateInitialConfig fetches, parses, and validates the initial ConfigMap and Secret.
//
// Returns the validated configuration and credentials, or an error if any step fails.
func fetchAndValidateInitialConfig(
	ctx context.Context,
	k8sClient *client.Client,
	configMapName string,
	secretName string,
	configMapGVR schema.GroupVersionResource,
	secretGVR schema.GroupVersionResource,
	logger *slog.Logger,
) (*coreconfig.Config, *coreconfig.Credentials, error) {
	logger.Info("Fetching initial configuration and credentials")

	var configMapResource *unstructured.Unstructured
	var secretResource *unstructured.Unstructured

	g, gCtx := errgroup.WithContext(ctx)

	// Fetch ConfigMap
	g.Go(func() error {
		var err error
		configMapResource, err = k8sClient.GetResource(gCtx, configMapGVR, configMapName)
		if err != nil {
			return fmt.Errorf("failed to fetch ConfigMap %q: %w", configMapName, err)
		}
		return nil
	})

	// Fetch Secret
	g.Go(func() error {
		var err error
		secretResource, err = k8sClient.GetResource(gCtx, secretGVR, secretName)
		if err != nil {
			return fmt.Errorf("failed to fetch Secret %q: %w", secretName, err)
		}
		return nil
	})

	// Wait for both fetches to complete
	if err := g.Wait(); err != nil {
		return nil, nil, err
	}

	// Parse initial configuration
	logger.Info("Parsing initial configuration")

	cfg, err := parseConfigMap(configMapResource)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to parse initial ConfigMap: %w", err)
	}

	creds, err := parseSecret(secretResource)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to parse initial Secret: %w", err)
	}

	// Validate initial configuration
	logger.Info("Validating initial configuration")

	if err := coreconfig.ValidateStructure(cfg); err != nil {
		return nil, nil, fmt.Errorf("initial configuration validation failed: %w", err)
	}

	if err := coreconfig.ValidateCredentials(creds); err != nil {
		return nil, nil, fmt.Errorf("initial credentials validation failed: %w", err)
	}

	logger.Info("Initial configuration validated successfully",
		"config_version", configMapResource.GetResourceVersion(),
		"secret_version", secretResource.GetResourceVersion())

	return cfg, creds, nil
}

// setupComponents creates and starts all event-driven components.
//
// Returns the EventBus, iteration context, cancel function, and config change channel.
func setupComponents(
	ctx context.Context,
	logger *slog.Logger,
) (*busevents.EventBus, context.Context, context.CancelFunc, chan *coreconfig.Config) {
	// Create EventBus with buffer for pre-start events
	bus := busevents.NewEventBus(100)

	// Create components
	eventCommentator := commentator.NewEventCommentator(bus, logger, 1000)
	configLoaderComponent := configloader.NewConfigLoaderComponent(bus, logger)
	credentialsLoaderComponent := credentialsloader.NewCredentialsLoaderComponent(bus, logger)

	// Create validators
	basicValidator := validator.NewBasicValidator(bus, logger)
	templateValidator := validator.NewTemplateValidator(bus, logger)
	jsonpathValidator := validator.NewJSONPathValidator(bus, logger)

	// Create config change channel for reinitialization signaling
	configChangeCh := make(chan *coreconfig.Config, 1)

	// Register validators for scatter-gather validation
	validators := validator.AllValidatorNames()

	configChangeHandlerComponent := configchange.NewConfigChangeHandler(
		bus,
		logger,
		configChangeCh,
		validators,
	)

	// Start components in goroutines with iteration-specific context
	iterCtx, cancel := context.WithCancel(ctx)

	go eventCommentator.Start(iterCtx)
	go configLoaderComponent.Start(iterCtx)
	go credentialsLoaderComponent.Start(iterCtx)
	go basicValidator.Start(iterCtx)
	go templateValidator.Start(iterCtx)
	go jsonpathValidator.Start(iterCtx)
	go configChangeHandlerComponent.Start(iterCtx)

	logger.Debug("All components started")

	return bus, iterCtx, cancel, configChangeCh
}

// setupResourceWatchers creates and starts resource watchers and index tracker, then waits for sync.
//
// Returns an error if watcher creation or synchronization fails.
func setupResourceWatchers(
	iterCtx context.Context,
	cfg *coreconfig.Config,
	k8sClient *client.Client,
	bus *busevents.EventBus,
	logger *slog.Logger,
	cancel context.CancelFunc,
) error {
	// Extract resource type names for IndexSynchronizationTracker
	resourceNames := make([]string, 0, len(cfg.WatchedResources))
	for name := range cfg.WatchedResources {
		resourceNames = append(resourceNames, name)
	}

	// Create ResourceWatcherComponent
	resourceWatcher, err := resourcewatcher.New(cfg, k8sClient, bus, logger)
	if err != nil {
		return fmt.Errorf("failed to create resource watcher: %w", err)
	}

	// Create IndexSynchronizationTracker
	indexTracker := indextracker.New(bus, logger, resourceNames)

	// Start resource watcher and index tracker
	go func() {
		if err := resourceWatcher.Start(iterCtx); err != nil {
			logger.Error("resource watcher failed", "error", err)
			cancel()
		}
	}()

	go func() {
		if err := indexTracker.Start(iterCtx); err != nil {
			logger.Error("index tracker failed", "error", err)
			cancel()
		}
	}()

	// Wait for all resource indices to sync
	logger.Debug("Waiting for resource indices to sync")
	if err := resourceWatcher.WaitForAllSync(iterCtx); err != nil {
		return fmt.Errorf("resource watcher sync failed: %w", err)
	}
	logger.Info("All resource indices synced successfully")

	return nil
}

// setupConfigWatchers creates and starts ConfigMap and Secret watchers, then waits for sync.
//
// Returns an error if watcher creation or synchronization fails.
func setupConfigWatchers(
	iterCtx context.Context,
	k8sClient *client.Client,
	configMapName string,
	secretName string,
	configMapGVR schema.GroupVersionResource,
	secretGVR schema.GroupVersionResource,
	bus *busevents.EventBus,
	logger *slog.Logger,
	cancel context.CancelFunc,
) error {
	// Create watchers for ConfigMap and Secret
	configMapWatcher, err := watcher.NewSingle(&types.SingleWatcherConfig{
		GVR:       configMapGVR,
		Namespace: k8sClient.Namespace(),
		Name:      configMapName,
		OnChange: func(obj interface{}) error {
			bus.Publish(events.NewConfigResourceChangedEvent(obj))
			return nil
		},
	}, k8sClient)
	if err != nil {
		return fmt.Errorf("failed to create ConfigMap watcher: %w", err)
	}

	secretWatcher, err := watcher.NewSingle(&types.SingleWatcherConfig{
		GVR:       secretGVR,
		Namespace: k8sClient.Namespace(),
		Name:      secretName,
		OnChange: func(obj interface{}) error {
			bus.Publish(events.NewSecretResourceChangedEvent(obj))
			return nil
		},
	}, k8sClient)
	if err != nil {
		return fmt.Errorf("failed to create Secret watcher: %w", err)
	}

	// Start watchers in goroutines
	go func() {
		if err := configMapWatcher.Start(iterCtx); err != nil {
			logger.Error("ConfigMap watcher failed", "error", err)
			cancel()
		}
	}()

	go func() {
		if err := secretWatcher.Start(iterCtx); err != nil {
			logger.Error("Secret watcher failed", "error", err)
			cancel()
		}
	}()

	logger.Debug("Watchers started, waiting for initial sync")

	// Wait for watchers to complete initial sync in parallel
	watcherGroup, watcherCtx := errgroup.WithContext(iterCtx)

	watcherGroup.Go(func() error {
		if err := configMapWatcher.WaitForSync(watcherCtx); err != nil {
			return fmt.Errorf("ConfigMap watcher sync failed: %w", err)
		}
		return nil
	})

	watcherGroup.Go(func() error {
		if err := secretWatcher.WaitForSync(watcherCtx); err != nil {
			return fmt.Errorf("Secret watcher sync failed: %w", err)
		}
		return nil
	})

	// Wait for both watchers to sync
	if err := watcherGroup.Wait(); err != nil {
		return err
	}

	logger.Info("Watchers synced successfully")

	return nil
}

// runIteration runs a single controller iteration.
//
// This function orchestrates the initialization sequence:
//  1. Fetches and validates initial ConfigMap and Secret
//  2. Creates and starts all event-driven components
//  3. Creates and starts resource watchers, waits for sync
//  4. Creates and starts ConfigMap/Secret watchers, waits for sync
//  5. Starts the EventBus (releases buffered events)
//  6. Waits for config change signal or context cancellation
//
// Returns:
//   - Error if initialization fails (causes retry)
//   - nil if context is cancelled or config change occurs (normal exit)
func runIteration(
	ctx context.Context,
	k8sClient *client.Client,
	configMapName string,
	secretName string,
	logger *slog.Logger,
) error {
	logger.Info("Starting controller iteration")

	// Define GVRs for ConfigMap and Secret
	configMapGVR := schema.GroupVersionResource{
		Group:    "",
		Version:  "v1",
		Resource: "configmaps",
	}

	secretGVR := schema.GroupVersionResource{
		Group:    "",
		Version:  "v1",
		Resource: "secrets",
	}

	// 1. Fetch and validate initial configuration
	cfg, _, err := fetchAndValidateInitialConfig(
		ctx, k8sClient, configMapName, secretName,
		configMapGVR, secretGVR, logger,
	)
	if err != nil {
		return err
	}

	// 2. Setup components
	bus, iterCtx, cancel, configChangeCh := setupComponents(ctx, logger)
	defer cancel()

	// 3. Setup resource watchers
	if err := setupResourceWatchers(iterCtx, cfg, k8sClient, bus, logger, cancel); err != nil {
		return err
	}

	// 4. Setup config watchers
	if err := setupConfigWatchers(
		iterCtx, k8sClient, configMapName, secretName,
		configMapGVR, secretGVR, bus, logger, cancel,
	); err != nil {
		return err
	}

	// 5. Start the EventBus (releases buffered events and begins normal operation)
	bus.Start()

	logger.Info("Controller iteration initialized successfully - entering event loop")

	// 6. Wait for config change signal or context cancellation
	select {
	case <-iterCtx.Done():
		logger.Info("Controller iteration cancelled", "reason", iterCtx.Err())
		return nil

	case newConfig := <-configChangeCh:
		logger.Info("Configuration change detected, triggering reinitialization",
			"new_config_version", fmt.Sprintf("%p", newConfig))

		// Cancel iteration context to stop all components and watchers
		cancel()

		// Brief pause to allow cleanup
		time.Sleep(500 * time.Millisecond)

		logger.Info("Reinitialization triggered - starting new iteration")
		return nil
	}
}

// parseConfigMap extracts and parses configuration from a ConfigMap resource.
func parseConfigMap(resource *unstructured.Unstructured) (*coreconfig.Config, error) {
	// Extract ConfigMap data field
	data, found, err := unstructured.NestedStringMap(resource.Object, "data")
	if err != nil {
		return nil, fmt.Errorf("failed to extract data field: %w", err)
	}
	if !found {
		return nil, fmt.Errorf("ConfigMap has no data field")
	}

	// Extract "config" key containing YAML
	configYAML, ok := data["config"]
	if !ok {
		return nil, fmt.Errorf("ConfigMap data missing 'config' key")
	}

	// Parse YAML
	cfg, err := coreconfig.ParseConfig(configYAML)
	if err != nil {
		return nil, fmt.Errorf("failed to parse config YAML: %w", err)
	}

	return cfg, nil
}

// parseSecret extracts and parses credentials from a Secret resource.
func parseSecret(resource *unstructured.Unstructured) (*coreconfig.Credentials, error) {
	// Extract Secret data field
	dataRaw, found, err := unstructured.NestedMap(resource.Object, "data")
	if err != nil {
		return nil, fmt.Errorf("failed to extract data field: %w", err)
	}
	if !found {
		return nil, fmt.Errorf("Secret has no data field")
	}

	// Convert map[string]interface{} to map[string][]byte
	data := make(map[string][]byte)
	for key, value := range dataRaw {
		if strValue, ok := value.(string); ok {
			data[key] = []byte(strValue)
		} else {
			return nil, fmt.Errorf("Secret data key %q has invalid type: %T", key, value)
		}
	}

	// Load credentials
	creds, err := coreconfig.LoadCredentials(data)
	if err != nil {
		return nil, fmt.Errorf("failed to load credentials: %w", err)
	}

	return creds, nil
}
