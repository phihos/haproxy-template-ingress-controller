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
	"encoding/base64"
	"fmt"
	"log/slog"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"golang.org/x/sync/errgroup"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"

	"haproxy-template-ic/pkg/controller/commentator"
	"haproxy-template-ic/pkg/controller/configchange"
	"haproxy-template-ic/pkg/controller/configloader"
	"haproxy-template-ic/pkg/controller/credentialsloader"
	"haproxy-template-ic/pkg/controller/debug"
	"haproxy-template-ic/pkg/controller/deployer"
	"haproxy-template-ic/pkg/controller/discovery"
	"haproxy-template-ic/pkg/controller/events"
	"haproxy-template-ic/pkg/controller/executor"
	"haproxy-template-ic/pkg/controller/indextracker"
	"haproxy-template-ic/pkg/controller/metrics"
	"haproxy-template-ic/pkg/controller/reconciler"
	"haproxy-template-ic/pkg/controller/renderer"
	"haproxy-template-ic/pkg/controller/resourcewatcher"
	"haproxy-template-ic/pkg/controller/validator"
	coreconfig "haproxy-template-ic/pkg/core/config"
	"haproxy-template-ic/pkg/dataplane"
	busevents "haproxy-template-ic/pkg/events"
	"haproxy-template-ic/pkg/introspection"
	"haproxy-template-ic/pkg/k8s/client"
	"haproxy-template-ic/pkg/k8s/types"
	"haproxy-template-ic/pkg/k8s/watcher"
	pkgmetrics "haproxy-template-ic/pkg/metrics"
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
//   - debugPort: Port for debug HTTP server (0 to disable)
//
// Returns:
//   - Error if the controller cannot start or encounters a fatal error
//   - nil if the context is cancelled (graceful shutdown)
func Run(ctx context.Context, k8sClient *client.Client, configMapName, secretName string, debugPort int) error {
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
			err := runIteration(ctx, k8sClient, configMapName, secretName, debugPort, logger)
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

// componentSetup contains all resources created during component initialization.
type componentSetup struct {
	Bus              *busevents.EventBus
	MetricsComponent *metrics.Component
	MetricsRegistry  *prometheus.Registry
	IterCtx          context.Context
	Cancel           context.CancelFunc
	ConfigChangeCh   chan *coreconfig.Config
}

// setupComponents creates and starts all event-driven components.
func setupComponents(
	ctx context.Context,
	logger *slog.Logger,
) *componentSetup {
	// Create EventBus with buffer for pre-start events
	bus := busevents.NewEventBus(100)

	// Create Prometheus registry for this iteration (instance-based, not global)
	registry := prometheus.NewRegistry()

	// Create metrics collector
	domainMetrics := metrics.New(registry)
	metricsComponent := metrics.NewComponent(domainMetrics, bus)

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

	return &componentSetup{
		Bus:              bus,
		MetricsComponent: metricsComponent,
		MetricsRegistry:  registry,
		IterCtx:          iterCtx,
		Cancel:           cancel,
		ConfigChangeCh:   configChangeCh,
	}
}

// setupInfrastructureServers starts debug and metrics HTTP servers.
func setupInfrastructureServers(
	ctx context.Context,
	cfg *coreconfig.Config,
	debugPort int,
	setup *componentSetup,
	stateCache *StateCache,
	logger *slog.Logger,
) {
	logger.Info("Stage 6: Starting debug infrastructure")

	// Create instance-based introspection registry (lives/dies with this iteration)
	registry := introspection.NewRegistry()

	// Create event buffer for tracking recent events
	eventBuffer := debug.NewEventBuffer(1000, setup.Bus)
	go func() {
		if err := eventBuffer.Start(ctx); err != nil {
			logger.Error("event buffer failed", "error", err)
		}
	}()

	// Register debug variables with registry
	debug.RegisterVariables(registry, stateCache, eventBuffer)

	// Start debug HTTP server if port is configured
	if debugPort > 0 {
		debugServer := introspection.NewServer(fmt.Sprintf(":%d", debugPort), registry)
		go func() {
			if err := debugServer.Start(ctx); err != nil {
				logger.Error("debug server failed", "error", err, "port", debugPort)
			}
		}()
		logger.Info("Debug HTTP server started",
			"port", debugPort,
			"bind_address", fmt.Sprintf("0.0.0.0:%d", debugPort),
			"access_method", "kubectl port-forward",
			"endpoints", []string{"/debug/vars", "/debug/pprof"})
	} else {
		logger.Debug("Debug HTTP server disabled (port=0)")
	}

	// Start metrics HTTP server if port is configured
	metricsPort := cfg.Controller.MetricsPort
	if metricsPort > 0 {
		metricsServer := pkgmetrics.NewServer(fmt.Sprintf(":%d", metricsPort), setup.MetricsRegistry)
		go func() {
			if err := metricsServer.Start(ctx); err != nil {
				logger.Error("metrics server failed", "error", err, "port", metricsPort)
			}
		}()
		logger.Info("Metrics HTTP server started",
			"port", metricsPort,
			"bind_address", fmt.Sprintf("0.0.0.0:%d", metricsPort),
			"access_method", "kubectl port-forward",
			"endpoint", "/metrics")
	} else {
		logger.Debug("Metrics HTTP server disabled (port=0)")
	}
}

// setupResourceWatchers creates and starts resource watchers and index tracker, then waits for sync.
//
// Returns the ResourceWatcherComponent and an error if watcher creation or synchronization fails.
func setupResourceWatchers(
	iterCtx context.Context,
	cfg *coreconfig.Config,
	k8sClient *client.Client,
	bus *busevents.EventBus,
	logger *slog.Logger,
	cancel context.CancelFunc,
) (*resourcewatcher.ResourceWatcherComponent, error) {
	// Extract resource type names for IndexSynchronizationTracker
	// Include haproxy-pods which is auto-injected by ResourceWatcherComponent
	resourceNames := make([]string, 0, len(cfg.WatchedResources)+1)
	for name := range cfg.WatchedResources {
		resourceNames = append(resourceNames, name)
	}
	// Add haproxy-pods (auto-injected)
	resourceNames = append(resourceNames, "haproxy-pods")

	// Create ResourceWatcherComponent
	resourceWatcher, err := resourcewatcher.New(cfg, k8sClient, bus, logger)
	if err != nil {
		return nil, fmt.Errorf("failed to create resource watcher: %w", err)
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
		return nil, fmt.Errorf("resource watcher sync failed: %w", err)
	}
	logger.Info("All resource indices synced successfully")

	return resourceWatcher, nil
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

// reconciliationComponents holds all reconciliation-related components.
type reconciliationComponents struct {
	reconciler          *reconciler.Reconciler
	renderer            *renderer.Component
	haproxyValidator    *validator.HAProxyValidatorComponent
	executor            *executor.Executor
	discovery           *discovery.Component
	deployer            *deployer.Component
	deploymentScheduler *deployer.DeploymentScheduler
	driftMonitor        *deployer.DriftPreventionMonitor
}

// createReconciliationComponents creates all reconciliation components.
func createReconciliationComponents(
	cfg *coreconfig.Config,
	resourceWatcher *resourcewatcher.ResourceWatcherComponent,
	bus *busevents.EventBus,
	logger *slog.Logger,
) (*reconciliationComponents, error) {
	// Create Reconciler with default configuration
	reconcilerComponent := reconciler.New(bus, logger, nil)

	// Create Renderer with stores from ResourceWatcher
	stores := resourceWatcher.GetAllStores()
	rendererComponent, err := renderer.New(bus, cfg, stores, logger)
	if err != nil {
		return nil, fmt.Errorf("failed to create renderer: %w", err)
	}

	// Create HAProxy Validator
	validationPaths := dataplane.ValidationPaths{
		MapsDir:           cfg.Dataplane.MapsDir,
		SSLCertsDir:       cfg.Dataplane.SSLCertsDir,
		GeneralStorageDir: cfg.Dataplane.GeneralStorageDir,
		ConfigFile:        cfg.Dataplane.ConfigFile,
	}
	haproxyValidatorComponent := validator.NewHAProxyValidator(bus, logger, validationPaths)

	// Create Executor
	executorComponent := executor.New(bus, logger)

	// Create Deployer
	deployerComponent := deployer.New(bus, logger)

	// Create DeploymentScheduler with rate limiting
	minDeploymentInterval := cfg.Dataplane.GetMinDeploymentInterval()
	deploymentSchedulerComponent := deployer.NewDeploymentScheduler(bus, logger, minDeploymentInterval)

	// Create DriftPreventionMonitor
	driftPreventionInterval := cfg.Dataplane.GetDriftPreventionInterval()
	driftMonitorComponent := deployer.NewDriftPreventionMonitor(bus, logger, driftPreventionInterval)

	// Create Discovery component and set pod store
	discoveryComponent := discovery.New(bus, logger)
	podStore := resourceWatcher.GetStore("haproxy-pods")
	if podStore == nil {
		return nil, fmt.Errorf("haproxy-pods store not found (should be auto-injected)")
	}
	discoveryComponent.SetPodStore(podStore)

	return &reconciliationComponents{
		reconciler:          reconcilerComponent,
		renderer:            rendererComponent,
		haproxyValidator:    haproxyValidatorComponent,
		executor:            executorComponent,
		discovery:           discoveryComponent,
		deployer:            deployerComponent,
		deploymentScheduler: deploymentSchedulerComponent,
		driftMonitor:        driftMonitorComponent,
	}, nil
}

// startReconciliationComponents starts all reconciliation components in background goroutines.
func startReconciliationComponents(
	iterCtx context.Context,
	components *reconciliationComponents,
	logger *slog.Logger,
	cancel context.CancelFunc,
) {
	// Start reconciler in background
	go func() {
		if err := components.reconciler.Start(iterCtx); err != nil {
			logger.Error("reconciler failed", "error", err)
			cancel()
		}
	}()

	// Start renderer in background
	go func() {
		if err := components.renderer.Start(iterCtx); err != nil {
			logger.Error("renderer failed", "error", err)
			cancel()
		}
	}()

	// Start HAProxy validator in background
	go func() {
		if err := components.haproxyValidator.Start(iterCtx); err != nil {
			logger.Error("HAProxy validator failed", "error", err)
			cancel()
		}
	}()

	// Start executor in background
	go func() {
		if err := components.executor.Start(iterCtx); err != nil {
			logger.Error("executor failed", "error", err)
			cancel()
		}
	}()

	// Start discovery in background
	go func() {
		if err := components.discovery.Start(iterCtx); err != nil {
			logger.Error("discovery failed", "error", err)
			cancel()
		}
	}()

	// Start deployer in background
	go func() {
		if err := components.deployer.Start(iterCtx); err != nil {
			logger.Error("deployer failed", "error", err)
			cancel()
		}
	}()

	// Start deployment scheduler in background
	go func() {
		if err := components.deploymentScheduler.Start(iterCtx); err != nil {
			logger.Error("deployment scheduler failed", "error", err)
			cancel()
		}
	}()

	// Start drift prevention monitor in background
	go func() {
		if err := components.driftMonitor.Start(iterCtx); err != nil {
			logger.Error("drift prevention monitor failed", "error", err)
			cancel()
		}
	}()

	logger.Info("Reconciliation components started",
		"components", "Reconciler, Renderer, HAProxyValidator, Executor, Discovery, Deployer, DeploymentScheduler, DriftMonitor")
}

// setupReconciliation creates and starts the reconciliation components (Stage 5).
//
// The Reconciler debounces resource changes and triggers reconciliation events.
// The Renderer subscribes to reconciliation events and renders HAProxy configuration.
// The HAProxyValidator validates rendered configurations using syntax and semantic checks.
// The Executor subscribes to reconciliation events and orchestrates pure components
// (Renderer, Validator, Deployer) to perform the reconciliation workflow.
//
// All components are started after initial resource synchronization to ensure we
// have a complete view of the cluster state before beginning reconciliation cycles.
func setupReconciliation(
	iterCtx context.Context,
	cfg *coreconfig.Config,
	creds *coreconfig.Credentials,
	resourceWatcher *resourcewatcher.ResourceWatcherComponent,
	bus *busevents.EventBus,
	logger *slog.Logger,
	cancel context.CancelFunc,
) error {
	// Create all components
	components, err := createReconciliationComponents(cfg, resourceWatcher, bus, logger)
	if err != nil {
		return err
	}

	// Start all components in background
	startReconciliationComponents(iterCtx, components, logger, cancel)

	// Give components a brief moment to subscribe to the EventBus
	// before publishing initial state events
	time.Sleep(100 * time.Millisecond)

	// Publish initial config and credentials events
	// This ensures reconciliation components (especially Discovery) receive the initial state
	// even though they started after the initial ConfigMap/Secret watcher events
	bus.Publish(events.NewConfigValidatedEvent(cfg, "initial", "initial"))
	logger.Debug("Published initial ConfigValidatedEvent for reconciliation components")

	bus.Publish(events.NewCredentialsUpdatedEvent(creds, "initial"))
	logger.Debug("Published initial CredentialsUpdatedEvent for reconciliation components")

	// Trigger initial reconciliation to bootstrap the pipeline
	// This ensures at least one reconciliation cycle runs even with 0 resources
	bus.Publish(events.NewReconciliationTriggeredEvent("initial_sync_complete"))
	logger.Debug("Published initial reconciliation trigger")

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
//  6. Starts reconciliation components (Stage 5)
//  7. Starts debug infrastructure (StateCache, EventBuffer, debug server if enabled)
//  8. Waits for config change signal or context cancellation
//
// Returns:
//   - Error if initialization fails (causes retry)
//   - nil if context is cancelled or config change occurs (normal exit)
func runIteration(
	ctx context.Context,
	k8sClient *client.Client,
	configMapName string,
	secretName string,
	debugPort int,
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
	cfg, creds, err := fetchAndValidateInitialConfig(
		ctx, k8sClient, configMapName, secretName,
		configMapGVR, secretGVR, logger,
	)
	if err != nil {
		return err
	}

	// 2. Setup components
	setup := setupComponents(ctx, logger)
	defer setup.Cancel()

	// 3. Setup resource watchers
	resourceWatcher, err := setupResourceWatchers(setup.IterCtx, cfg, k8sClient, setup.Bus, logger, setup.Cancel)
	if err != nil {
		return err
	}

	// 4. Setup config watchers
	if err := setupConfigWatchers(
		setup.IterCtx, k8sClient, configMapName, secretName,
		configMapGVR, secretGVR, setup.Bus, logger, setup.Cancel,
	); err != nil {
		return err
	}

	// 5. Initialize StateCache and metrics component, subscribe BEFORE bus.Start()
	// This ensures they receive all events, including buffered startup events
	stateCache := NewStateCache(setup.Bus, resourceWatcher)
	stateCache.Subscribe() // Synchronous - registers subscription immediately

	// Subscribe metrics component (synchronous - must be before bus.Start())
	setup.MetricsComponent.Start()

	// 5.5. Start the EventBus (releases buffered events and begins normal operation)
	setup.Bus.Start()

	// 5.6. Start StateCache and metrics component event loops in background
	go func() {
		if err := stateCache.Run(setup.IterCtx); err != nil {
			logger.Error("state cache failed", "error", err)
			// Non-fatal error - don't cancel iteration
		}
	}()

	go func() {
		if err := setup.MetricsComponent.Run(setup.IterCtx); err != nil {
			logger.Error("metrics component failed", "error", err)
			// Non-fatal error - don't cancel iteration
		}
	}()

	// 6. Start reconciliation components (Stage 5)
	logger.Info("Stage 5: Starting reconciliation components")
	if err := setupReconciliation(setup.IterCtx, cfg, creds, resourceWatcher, setup.Bus, logger, setup.Cancel); err != nil {
		return err
	}

	// 7. Setup debug and metrics infrastructure
	setupInfrastructureServers(setup.IterCtx, cfg, debugPort, setup, stateCache, logger)

	logger.Info("Controller iteration initialized successfully - entering event loop")

	// 8. Wait for config change signal or context cancellation
	select {
	case <-setup.IterCtx.Done():
		logger.Info("Controller iteration cancelled", "reason", setup.IterCtx.Err())
		return nil

	case newConfig := <-setup.ConfigChangeCh:
		logger.Info("Configuration change detected, triggering reinitialization",
			"new_config_version", fmt.Sprintf("%p", newConfig))

		// Cancel iteration context to stop all components and watchers
		setup.Cancel()

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

	// Parse YAML and apply defaults
	cfg, err := coreconfig.LoadConfig(configYAML)
	if err != nil {
		return nil, fmt.Errorf("failed to load config YAML: %w", err)
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
	// Kubernetes Secrets are base64-encoded, so we need to decode them
	data := make(map[string][]byte)
	for key, value := range dataRaw {
		if strValue, ok := value.(string); ok {
			// Decode base64-encoded value
			decoded, err := base64.StdEncoding.DecodeString(strValue)
			if err != nil {
				return nil, fmt.Errorf("failed to decode base64 for key %q: %w", key, err)
			}
			data[key] = decoded
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
