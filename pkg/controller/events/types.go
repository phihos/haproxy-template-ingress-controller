package events

import (
	"fmt"
	"time"

	"haproxy-template-ic/pkg/k8s/types"
)

// This file contains all event type definitions for the haproxy-template-ic controller.
//
// # Event Immutability Contract
//
// Events in this system are intended to be immutable after creation. They represent
// historical facts about what happened in the system and should not be modified after
// being published to the EventBus.
//
// To support this immutability contract:
//
//  1. All event types use pointer receivers for their Event interface methods.
//     This avoids copying large structs (200+ bytes) and follows Go best practices.
//
//  2. All event fields are exported to support JSON serialization and idiomatic Go access.
//     This follows industry standards (Kubernetes, NATS) rather than enforcing immutability
//     through unexported fields and getters.
//
//  3. Constructors perform defensive copying of slices and maps to prevent mutations
//     from affecting the published event. Publishers cannot modify events after creation.
//
//  4. Consumers MUST NOT modify event fields. This immutability contract is enforced through:
//     - A custom static analyzer (tools/linters/eventimmutability) that detects parameter mutations
//     - Code review for cases not caught by the analyzer
//     - Team discipline and documentation
//
// This approach balances performance, Go idioms, and practical immutability for an
// internal project where all consumers are controlled.
//
// Events are organized into categories:
// - Lifecycle Events: System startup and shutdown
// - Configuration Events: ConfigMap/Secret changes and validation
// - Resource Events: Kubernetes resource indexing and synchronization
// - Reconciliation Events: Template rendering and deployment cycles
// - Template Events: Template rendering operations
// - Validation Events: Configuration validation (syntax and semantics)
// - Deployment Events: HAProxy configuration deployment
// - Storage Events: Auxiliary file synchronization
// - HAProxy Pod Events: HAProxy pod discovery

// -----------------------------------------------------------------------------
// Event Type Constants
// -----------------------------------------------------------------------------

const (
	// Lifecycle event types.
	EventTypeControllerStarted  = "controller.started"
	EventTypeControllerShutdown = "controller.shutdown"

	// Configuration event types.
	EventTypeConfigParsed             = "config.parsed"
	EventTypeConfigValidationRequest  = "config.validation.request"
	EventTypeConfigValidationResponse = "config.validation.response"
	EventTypeConfigValidated          = "config.validated"
	EventTypeConfigInvalid            = "config.invalid"
	EventTypeConfigResourceChanged    = "config.resource.changed"

	// Resource event types.
	EventTypeResourceIndexUpdated = "resource.index.updated"
	EventTypeResourceSyncComplete = "resource.sync.complete"
	EventTypeIndexSynchronized    = "index.synchronized"

	// Reconciliation event types.
	EventTypeReconciliationTriggered = "reconciliation.triggered"
	EventTypeReconciliationStarted   = "reconciliation.started"
	EventTypeReconciliationCompleted = "reconciliation.completed"
	EventTypeReconciliationFailed    = "reconciliation.failed"

	// Template event types.
	EventTypeTemplateRendered     = "template.rendered"
	EventTypeTemplateRenderFailed = "template.render.failed"

	// Validation event types (HAProxy dataplane API validation).
	EventTypeValidationStarted   = "validation.started"
	EventTypeValidationCompleted = "validation.completed"
	EventTypeValidationFailed    = "validation.failed"

	// Deployment event types.
	EventTypeDeploymentStarted        = "deployment.started"
	EventTypeInstanceDeployed         = "instance.deployed"
	EventTypeInstanceDeploymentFailed = "instance.deployment.failed"
	EventTypeDeploymentCompleted      = "deployment.completed"

	// Storage event types.
	EventTypeStorageSyncStarted   = "storage.sync.started"
	EventTypeStorageSyncCompleted = "storage.sync.completed"
	EventTypeStorageSyncFailed    = "storage.sync.failed"

	// HAProxy pod event types.
	EventTypeHAProxyPodsDiscovered = "haproxy.pods.discovered"
	EventTypeHAProxyPodAdded       = "haproxy.pod.added"
	EventTypeHAProxyPodRemoved     = "haproxy.pod.removed"

	// Credentials event types.
	EventTypeSecretResourceChanged = "secret.resource.changed"
	EventTypeCredentialsUpdated    = "credentials.updated"
	EventTypeCredentialsInvalid    = "credentials.invalid"
)

// -----------------------------------------------------------------------------
// Lifecycle Events
// -----------------------------------------------------------------------------

// ControllerStartedEvent is published when the controller has completed startup
// and all components are ready to process events.
type ControllerStartedEvent struct {
	ConfigVersion string
	SecretVersion string
	timestamp     time.Time
}

// NewControllerStartedEvent creates a new ControllerStartedEvent.
func NewControllerStartedEvent(configVersion, secretVersion string) *ControllerStartedEvent {
	return &ControllerStartedEvent{
		ConfigVersion: configVersion,
		SecretVersion: secretVersion,
		timestamp:     time.Now(),
	}
}

func (e *ControllerStartedEvent) EventType() string    { return EventTypeControllerStarted }
func (e *ControllerStartedEvent) Timestamp() time.Time { return e.timestamp }

// ControllerShutdownEvent is published when the controller is shutting down gracefully.
type ControllerShutdownEvent struct {
	Reason    string
	timestamp time.Time
}

// NewControllerShutdownEvent creates a new ControllerShutdownEvent.
func NewControllerShutdownEvent(reason string) *ControllerShutdownEvent {
	return &ControllerShutdownEvent{
		Reason:    reason,
		timestamp: time.Now(),
	}
}

func (e *ControllerShutdownEvent) EventType() string    { return EventTypeControllerShutdown }
func (e *ControllerShutdownEvent) Timestamp() time.Time { return e.timestamp }

// -----------------------------------------------------------------------------
// Configuration Events
// -----------------------------------------------------------------------------

// ConfigParsedEvent is published when the configuration ConfigMap/Secret has been
// successfully parsed into a Config structure.
//
// This event does not mean the config is valid - only that it could be parsed.
// Validation occurs in a subsequent step.
type ConfigParsedEvent struct {
	// Config contains the parsed configuration.
	// Type: interface{} to avoid circular dependencies.
	// Consumers should type-assert to their expected config type.
	Config interface{}

	// Version is the resourceVersion of the ConfigMap.
	Version string

	// SecretVersion is the resourceVersion of the credentials Secret.
	SecretVersion string

	timestamp time.Time
}

// NewConfigParsedEvent creates a new ConfigParsedEvent.
func NewConfigParsedEvent(config interface{}, version, secretVersion string) *ConfigParsedEvent {
	return &ConfigParsedEvent{
		Config:        config,
		Version:       version,
		SecretVersion: secretVersion,
		timestamp:     time.Now(),
	}
}

func (e *ConfigParsedEvent) EventType() string    { return EventTypeConfigParsed }
func (e *ConfigParsedEvent) Timestamp() time.Time { return e.timestamp }

// ConfigValidationRequest is published to request validation of a parsed config.
//
// This is a Request event used in the scatter-gather pattern. Multiple validators
// (basic, template, jsonpath) will respond with ConfigValidationResponse events.
type ConfigValidationRequest struct {
	reqID string

	// Config contains the configuration to validate.
	Config interface{}

	// Version is the resourceVersion being validated.
	Version string

	timestamp time.Time
}

// NewConfigValidationRequest creates a new ConfigValidationRequest.
func NewConfigValidationRequest(config interface{}, version string) *ConfigValidationRequest {
	return &ConfigValidationRequest{
		reqID:     fmt.Sprintf("config-validation-%s-%d", version, time.Now().UnixNano()),
		Config:    config,
		Version:   version,
		timestamp: time.Now(),
	}
}

func (e *ConfigValidationRequest) EventType() string    { return EventTypeConfigValidationRequest }
func (e *ConfigValidationRequest) Timestamp() time.Time { return e.timestamp }
func (e *ConfigValidationRequest) RequestID() string    { return e.reqID }

// ConfigValidationResponse is sent by validators in response to ConfigValidationRequest.
//
// This is a Response event used in the scatter-gather pattern. The ValidationCoordinator
// collects all responses and determines if the config is valid overall.
type ConfigValidationResponse struct {
	reqID     string
	responder string

	// ValidatorName identifies which validator produced this response (basic, template, jsonpath).
	ValidatorName string

	// Valid is true if this validator found no errors.
	Valid bool

	// Errors contains validation error messages, empty if Valid is true.
	Errors []string

	timestamp time.Time
}

// NewConfigValidationResponse creates a new ConfigValidationResponse.
// Performs defensive copy of the errors slice.
func NewConfigValidationResponse(requestID, validatorName string, valid bool, errors []string) *ConfigValidationResponse {
	// Defensive copy of errors slice
	var errorsCopy []string
	if len(errors) > 0 {
		errorsCopy = make([]string, len(errors))
		copy(errorsCopy, errors)
	}

	return &ConfigValidationResponse{
		reqID:         requestID,
		responder:     validatorName,
		ValidatorName: validatorName,
		Valid:         valid,
		Errors:        errorsCopy,
		timestamp:     time.Now(),
	}
}

func (e *ConfigValidationResponse) EventType() string    { return EventTypeConfigValidationResponse }
func (e *ConfigValidationResponse) Timestamp() time.Time { return e.timestamp }
func (e *ConfigValidationResponse) RequestID() string    { return e.reqID }
func (e *ConfigValidationResponse) Responder() string    { return e.responder }

// ConfigValidatedEvent is published when all validators have confirmed the config is valid.
//
// After receiving this event, the controller proceeds to start resource watchers
// with the validated configuration.
type ConfigValidatedEvent struct {
	Config        interface{}
	Version       string
	SecretVersion string
	timestamp     time.Time
}

// NewConfigValidatedEvent creates a new ConfigValidatedEvent.
func NewConfigValidatedEvent(config interface{}, version, secretVersion string) *ConfigValidatedEvent {
	return &ConfigValidatedEvent{
		Config:        config,
		Version:       version,
		SecretVersion: secretVersion,
		timestamp:     time.Now(),
	}
}

func (e *ConfigValidatedEvent) EventType() string    { return EventTypeConfigValidated }
func (e *ConfigValidatedEvent) Timestamp() time.Time { return e.timestamp }

// ConfigInvalidEvent is published when config validation fails.
//
// The controller will continue running with the previous valid config and wait
// for the next ConfigMap update.
type ConfigInvalidEvent struct {
	Version string

	// ValidationErrors maps validator names to their error messages.
	ValidationErrors map[string][]string

	timestamp time.Time
}

// NewConfigInvalidEvent creates a new ConfigInvalidEvent.
// Performs defensive copy of the validation errors map and its slice values.
func NewConfigInvalidEvent(version string, validationErrors map[string][]string) *ConfigInvalidEvent {
	// Defensive copy of map with slice values
	errorsCopy := make(map[string][]string, len(validationErrors))
	for k, v := range validationErrors {
		if len(v) > 0 {
			vCopy := make([]string, len(v))
			copy(vCopy, v)
			errorsCopy[k] = vCopy
		} else {
			errorsCopy[k] = nil
		}
	}

	return &ConfigInvalidEvent{
		Version:          version,
		ValidationErrors: errorsCopy,
		timestamp:        time.Now(),
	}
}

func (e *ConfigInvalidEvent) EventType() string    { return EventTypeConfigInvalid }
func (e *ConfigInvalidEvent) Timestamp() time.Time { return e.timestamp }

// -----------------------------------------------------------------------------
// Resource Events
// -----------------------------------------------------------------------------

// ResourceIndexUpdatedEvent is published when a watched Kubernetes resource
// has been added, updated, or deleted in the local index.
type ResourceIndexUpdatedEvent struct {
	// ResourceTypeName identifies the resource type from config (e.g., "ingresses", "services").
	ResourceTypeName string

	// ChangeStats provides detailed change statistics including Created, Modified, Deleted counts
	// and whether this event occurred during initial sync.
	ChangeStats types.ChangeStats

	timestamp time.Time
}

// NewResourceIndexUpdatedEvent creates a new ResourceIndexUpdatedEvent.
// Performs a value copy of ChangeStats (it's a small struct with no pointers).
func NewResourceIndexUpdatedEvent(resourceTypeName string, changeStats types.ChangeStats) *ResourceIndexUpdatedEvent {
	return &ResourceIndexUpdatedEvent{
		ResourceTypeName: resourceTypeName,
		ChangeStats:      changeStats,
		timestamp:        time.Now(),
	}
}

func (e *ResourceIndexUpdatedEvent) EventType() string    { return EventTypeResourceIndexUpdated }
func (e *ResourceIndexUpdatedEvent) Timestamp() time.Time { return e.timestamp }

// ResourceSyncCompleteEvent is published when a resource watcher has completed
// its initial sync with the Kubernetes API.
type ResourceSyncCompleteEvent struct {
	// ResourceTypeName identifies the resource type from config (e.g., "ingresses").
	ResourceTypeName string

	// InitialCount is the number of resources loaded during initial sync.
	InitialCount int

	timestamp time.Time
}

// NewResourceSyncCompleteEvent creates a new ResourceSyncCompleteEvent.
func NewResourceSyncCompleteEvent(resourceTypeName string, initialCount int) *ResourceSyncCompleteEvent {
	return &ResourceSyncCompleteEvent{
		ResourceTypeName: resourceTypeName,
		InitialCount:     initialCount,
		timestamp:        time.Now(),
	}
}

func (e *ResourceSyncCompleteEvent) EventType() string    { return EventTypeResourceSyncComplete }
func (e *ResourceSyncCompleteEvent) Timestamp() time.Time { return e.timestamp }

// IndexSynchronizedEvent is published when all resource watchers have completed
// their initial sync and the system has a complete view of all resources.
//
// This is a critical milestone - the controller waits for this event before
// starting reconciliation to ensure it has complete data.
type IndexSynchronizedEvent struct {
	// ResourceCounts maps resource types to their counts.
	ResourceCounts map[string]int
	timestamp      time.Time
}

// NewIndexSynchronizedEvent creates a new IndexSynchronizedEvent.
// Performs defensive copy of the resource counts map.
func NewIndexSynchronizedEvent(resourceCounts map[string]int) *IndexSynchronizedEvent {
	// Defensive copy of map
	countsCopy := make(map[string]int, len(resourceCounts))
	for k, v := range resourceCounts {
		countsCopy[k] = v
	}

	return &IndexSynchronizedEvent{
		ResourceCounts: countsCopy,
		timestamp:      time.Now(),
	}
}

func (e *IndexSynchronizedEvent) EventType() string    { return EventTypeIndexSynchronized }
func (e *IndexSynchronizedEvent) Timestamp() time.Time { return e.timestamp }

// -----------------------------------------------------------------------------
// Reconciliation Events
// -----------------------------------------------------------------------------

// ReconciliationTriggeredEvent is published when a reconciliation cycle should start.
//
// This event is typically published by the Reconciler after the debounce timer
// expires, or immediately for config changes.
type ReconciliationTriggeredEvent struct {
	// Reason describes why reconciliation was triggered.
	// Examples: "debounce_timer", "config_change", "manual_trigger"
	Reason    string
	timestamp time.Time
}

// NewReconciliationTriggeredEvent creates a new ReconciliationTriggeredEvent.
func NewReconciliationTriggeredEvent(reason string) *ReconciliationTriggeredEvent {
	return &ReconciliationTriggeredEvent{
		Reason:    reason,
		timestamp: time.Now(),
	}
}

func (e *ReconciliationTriggeredEvent) EventType() string    { return EventTypeReconciliationTriggered }
func (e *ReconciliationTriggeredEvent) Timestamp() time.Time { return e.timestamp }

// ReconciliationStartedEvent is published when the Executor begins a reconciliation cycle.
type ReconciliationStartedEvent struct {
	// Trigger describes what triggered this reconciliation.
	Trigger   string
	timestamp time.Time
}

// NewReconciliationStartedEvent creates a new ReconciliationStartedEvent.
func NewReconciliationStartedEvent(trigger string) *ReconciliationStartedEvent {
	return &ReconciliationStartedEvent{
		Trigger:   trigger,
		timestamp: time.Now(),
	}
}

func (e *ReconciliationStartedEvent) EventType() string    { return EventTypeReconciliationStarted }
func (e *ReconciliationStartedEvent) Timestamp() time.Time { return e.timestamp }

// ReconciliationCompletedEvent is published when a reconciliation cycle completes successfully.
type ReconciliationCompletedEvent struct {
	DurationMs int64
	timestamp  time.Time
}

// NewReconciliationCompletedEvent creates a new ReconciliationCompletedEvent.
func NewReconciliationCompletedEvent(durationMs int64) *ReconciliationCompletedEvent {
	return &ReconciliationCompletedEvent{
		DurationMs: durationMs,
		timestamp:  time.Now(),
	}
}

func (e *ReconciliationCompletedEvent) EventType() string    { return EventTypeReconciliationCompleted }
func (e *ReconciliationCompletedEvent) Timestamp() time.Time { return e.timestamp }

// ReconciliationFailedEvent is published when a reconciliation cycle fails.
type ReconciliationFailedEvent struct {
	Error     string
	Phase     string // Which phase failed: "render", "validate", "deploy"
	timestamp time.Time
}

// NewReconciliationFailedEvent creates a new ReconciliationFailedEvent.
func NewReconciliationFailedEvent(err, phase string) *ReconciliationFailedEvent {
	return &ReconciliationFailedEvent{
		Error:     err,
		Phase:     phase,
		timestamp: time.Now(),
	}
}

func (e *ReconciliationFailedEvent) EventType() string    { return EventTypeReconciliationFailed }
func (e *ReconciliationFailedEvent) Timestamp() time.Time { return e.timestamp }

// -----------------------------------------------------------------------------
// Template Events
// -----------------------------------------------------------------------------

// TemplateRenderedEvent is published when template rendering completes successfully.
//
// This event carries the rendered HAProxy configuration and all auxiliary files
// for the next phase (validation/deployment).
type TemplateRenderedEvent struct {
	// HAProxyConfig is the rendered main HAProxy configuration.
	HAProxyConfig string

	// AuxiliaryFiles contains all rendered auxiliary files (maps, certificates, general files).
	// Type: interface{} to avoid circular dependencies with pkg/dataplane.
	// Consumers should type-assert to *dataplane.AuxiliaryFiles.
	AuxiliaryFiles interface{}

	// Metrics for observability
	ConfigBytes        int   // Size of HAProxyConfig
	AuxiliaryFileCount int   // Number of auxiliary files
	DurationMs         int64 // Rendering duration

	timestamp time.Time
}

// NewTemplateRenderedEvent creates a new TemplateRenderedEvent.
// Performs defensive copy of the haproxyConfig string.
func NewTemplateRenderedEvent(haproxyConfig string, auxiliaryFiles interface{}, auxFileCount int, durationMs int64) *TemplateRenderedEvent {
	// Calculate config size
	configBytes := len(haproxyConfig)

	return &TemplateRenderedEvent{
		HAProxyConfig:      haproxyConfig,
		AuxiliaryFiles:     auxiliaryFiles,
		ConfigBytes:        configBytes,
		AuxiliaryFileCount: auxFileCount,
		DurationMs:         durationMs,
		timestamp:          time.Now(),
	}
}

func (e *TemplateRenderedEvent) EventType() string    { return EventTypeTemplateRendered }
func (e *TemplateRenderedEvent) Timestamp() time.Time { return e.timestamp }

// TemplateRenderFailedEvent is published when template rendering fails.
type TemplateRenderFailedEvent struct {
	// TemplateName is the name of the template that failed to render.
	TemplateName string

	// Error is the error message.
	Error string

	// StackTrace provides additional debugging context.
	StackTrace string

	timestamp time.Time
}

// NewTemplateRenderFailedEvent creates a new TemplateRenderFailedEvent.
func NewTemplateRenderFailedEvent(templateName, err, stackTrace string) *TemplateRenderFailedEvent {
	return &TemplateRenderFailedEvent{
		TemplateName: templateName,
		Error:        err,
		StackTrace:   stackTrace,
		timestamp:    time.Now(),
	}
}

func (e *TemplateRenderFailedEvent) EventType() string    { return EventTypeTemplateRenderFailed }
func (e *TemplateRenderFailedEvent) Timestamp() time.Time { return e.timestamp }

// -----------------------------------------------------------------------------
// Validation Events
// -----------------------------------------------------------------------------

// ValidationStartedEvent is published when configuration validation begins.
type ValidationStartedEvent struct {
	// Endpoints is the list of HAProxy instances that will be validated against.
	// Type: []interface{} to avoid circular dependencies.
	Endpoints []interface{}
	timestamp time.Time
}

// NewValidationStartedEvent creates a new ValidationStartedEvent.
// Performs defensive copy of the endpoints slice.
func NewValidationStartedEvent(endpoints []interface{}) *ValidationStartedEvent {
	// Defensive copy of slice
	var endpointsCopy []interface{}
	if len(endpoints) > 0 {
		endpointsCopy = make([]interface{}, len(endpoints))
		copy(endpointsCopy, endpoints)
	}

	return &ValidationStartedEvent{
		Endpoints: endpointsCopy,
		timestamp: time.Now(),
	}
}

func (e *ValidationStartedEvent) EventType() string    { return EventTypeValidationStarted }
func (e *ValidationStartedEvent) Timestamp() time.Time { return e.timestamp }

// ValidationCompletedEvent is published when configuration validation succeeds.
type ValidationCompletedEvent struct {
	Endpoints  []interface{}
	Warnings   []string // Non-fatal warnings
	DurationMs int64
	timestamp  time.Time
}

// NewValidationCompletedEvent creates a new ValidationCompletedEvent.
// Performs defensive copy of the endpoints and warnings slices.
func NewValidationCompletedEvent(endpoints []interface{}, warnings []string, durationMs int64) *ValidationCompletedEvent {
	// Defensive copy of endpoints slice
	var endpointsCopy []interface{}
	if len(endpoints) > 0 {
		endpointsCopy = make([]interface{}, len(endpoints))
		copy(endpointsCopy, endpoints)
	}

	// Defensive copy of warnings slice
	var warningsCopy []string
	if len(warnings) > 0 {
		warningsCopy = make([]string, len(warnings))
		copy(warningsCopy, warnings)
	}

	return &ValidationCompletedEvent{
		Endpoints:  endpointsCopy,
		Warnings:   warningsCopy,
		DurationMs: durationMs,
		timestamp:  time.Now(),
	}
}

func (e *ValidationCompletedEvent) EventType() string    { return EventTypeValidationCompleted }
func (e *ValidationCompletedEvent) Timestamp() time.Time { return e.timestamp }

// ValidationFailedEvent is published when configuration validation fails.
type ValidationFailedEvent struct {
	Endpoints  []interface{}
	Errors     []string // Validation errors
	DurationMs int64
	timestamp  time.Time
}

// NewValidationFailedEvent creates a new ValidationFailedEvent.
// Performs defensive copy of the endpoints and errors slices.
func NewValidationFailedEvent(endpoints []interface{}, errors []string, durationMs int64) *ValidationFailedEvent {
	// Defensive copy of endpoints slice
	var endpointsCopy []interface{}
	if len(endpoints) > 0 {
		endpointsCopy = make([]interface{}, len(endpoints))
		copy(endpointsCopy, endpoints)
	}

	// Defensive copy of errors slice
	var errorsCopy []string
	if len(errors) > 0 {
		errorsCopy = make([]string, len(errors))
		copy(errorsCopy, errors)
	}

	return &ValidationFailedEvent{
		Endpoints:  endpointsCopy,
		Errors:     errorsCopy,
		DurationMs: durationMs,
		timestamp:  time.Now(),
	}
}

func (e *ValidationFailedEvent) EventType() string    { return EventTypeValidationFailed }
func (e *ValidationFailedEvent) Timestamp() time.Time { return e.timestamp }

// -----------------------------------------------------------------------------
// Deployment Events
// -----------------------------------------------------------------------------

// DeploymentStartedEvent is published when deployment to HAProxy instances begins.
type DeploymentStartedEvent struct {
	Endpoints []interface{}
	timestamp time.Time
}

// NewDeploymentStartedEvent creates a new DeploymentStartedEvent.
// Performs defensive copy of the endpoints slice.
func NewDeploymentStartedEvent(endpoints []interface{}) *DeploymentStartedEvent {
	// Defensive copy of slice
	var endpointsCopy []interface{}
	if len(endpoints) > 0 {
		endpointsCopy = make([]interface{}, len(endpoints))
		copy(endpointsCopy, endpoints)
	}

	return &DeploymentStartedEvent{
		Endpoints: endpointsCopy,
		timestamp: time.Now(),
	}
}

func (e *DeploymentStartedEvent) EventType() string    { return EventTypeDeploymentStarted }
func (e *DeploymentStartedEvent) Timestamp() time.Time { return e.timestamp }

// InstanceDeployedEvent is published when deployment to a single HAProxy instance succeeds.
type InstanceDeployedEvent struct {
	Endpoint       interface{} // The HAProxy endpoint that was deployed to
	DurationMs     int64
	ReloadRequired bool // Whether this deployment required an HAProxy reload
	timestamp      time.Time
}

// NewInstanceDeployedEvent creates a new InstanceDeployedEvent.
func NewInstanceDeployedEvent(endpoint interface{}, durationMs int64, reloadRequired bool) *InstanceDeployedEvent {
	return &InstanceDeployedEvent{
		Endpoint:       endpoint,
		DurationMs:     durationMs,
		ReloadRequired: reloadRequired,
		timestamp:      time.Now(),
	}
}

func (e *InstanceDeployedEvent) EventType() string    { return EventTypeInstanceDeployed }
func (e *InstanceDeployedEvent) Timestamp() time.Time { return e.timestamp }

// InstanceDeploymentFailedEvent is published when deployment to a single HAProxy instance fails.
type InstanceDeploymentFailedEvent struct {
	Endpoint  interface{}
	Error     string
	Retryable bool // Whether this failure is retryable
	timestamp time.Time
}

// NewInstanceDeploymentFailedEvent creates a new InstanceDeploymentFailedEvent.
func NewInstanceDeploymentFailedEvent(endpoint interface{}, err string, retryable bool) *InstanceDeploymentFailedEvent {
	return &InstanceDeploymentFailedEvent{
		Endpoint:  endpoint,
		Error:     err,
		Retryable: retryable,
		timestamp: time.Now(),
	}
}

func (e *InstanceDeploymentFailedEvent) EventType() string    { return EventTypeInstanceDeploymentFailed }
func (e *InstanceDeploymentFailedEvent) Timestamp() time.Time { return e.timestamp }

// DeploymentCompletedEvent is published when deployment to all HAProxy instances completes.
type DeploymentCompletedEvent struct {
	Total      int // Total number of instances
	Succeeded  int // Number of successful deployments
	Failed     int // Number of failed deployments
	DurationMs int64
	timestamp  time.Time
}

// NewDeploymentCompletedEvent creates a new DeploymentCompletedEvent.
func NewDeploymentCompletedEvent(total, succeeded, failed int, durationMs int64) *DeploymentCompletedEvent {
	return &DeploymentCompletedEvent{
		Total:      total,
		Succeeded:  succeeded,
		Failed:     failed,
		DurationMs: durationMs,
		timestamp:  time.Now(),
	}
}

func (e *DeploymentCompletedEvent) EventType() string    { return EventTypeDeploymentCompleted }
func (e *DeploymentCompletedEvent) Timestamp() time.Time { return e.timestamp }

// -----------------------------------------------------------------------------
// Storage Events (Auxiliary Files)
// -----------------------------------------------------------------------------

// StorageSyncStartedEvent is published when auxiliary file synchronization begins.
type StorageSyncStartedEvent struct {
	// Phase describes which sync phase: "pre-config", "config", "post-config"
	Phase     string
	Endpoints []interface{}
	timestamp time.Time
}

// NewStorageSyncStartedEvent creates a new StorageSyncStartedEvent.
// Performs defensive copy of the endpoints slice.
func NewStorageSyncStartedEvent(phase string, endpoints []interface{}) *StorageSyncStartedEvent {
	// Defensive copy of slice
	var endpointsCopy []interface{}
	if len(endpoints) > 0 {
		endpointsCopy = make([]interface{}, len(endpoints))
		copy(endpointsCopy, endpoints)
	}

	return &StorageSyncStartedEvent{
		Phase:     phase,
		Endpoints: endpointsCopy,
		timestamp: time.Now(),
	}
}

func (e *StorageSyncStartedEvent) EventType() string    { return EventTypeStorageSyncStarted }
func (e *StorageSyncStartedEvent) Timestamp() time.Time { return e.timestamp }

// StorageSyncCompletedEvent is published when auxiliary file synchronization completes.
type StorageSyncCompletedEvent struct {
	Phase string

	// Stats contains sync statistics.
	// Type: interface{} to avoid circular dependencies.
	Stats interface{}

	DurationMs int64
	timestamp  time.Time
}

// NewStorageSyncCompletedEvent creates a new StorageSyncCompletedEvent.
func NewStorageSyncCompletedEvent(phase string, stats interface{}, durationMs int64) *StorageSyncCompletedEvent {
	return &StorageSyncCompletedEvent{
		Phase:      phase,
		Stats:      stats,
		DurationMs: durationMs,
		timestamp:  time.Now(),
	}
}

func (e *StorageSyncCompletedEvent) EventType() string    { return EventTypeStorageSyncCompleted }
func (e *StorageSyncCompletedEvent) Timestamp() time.Time { return e.timestamp }

// StorageSyncFailedEvent is published when auxiliary file synchronization fails.
type StorageSyncFailedEvent struct {
	Phase     string
	Error     string
	timestamp time.Time
}

// NewStorageSyncFailedEvent creates a new StorageSyncFailedEvent.
func NewStorageSyncFailedEvent(phase, err string) *StorageSyncFailedEvent {
	return &StorageSyncFailedEvent{
		Phase:     phase,
		Error:     err,
		timestamp: time.Now(),
	}
}

func (e *StorageSyncFailedEvent) EventType() string    { return EventTypeStorageSyncFailed }
func (e *StorageSyncFailedEvent) Timestamp() time.Time { return e.timestamp }

// -----------------------------------------------------------------------------
// HAProxy Pod Events
// -----------------------------------------------------------------------------

// HAProxyPodsDiscoveredEvent is published when HAProxy pods are discovered or updated.
type HAProxyPodsDiscoveredEvent struct {
	// Endpoints is the list of discovered HAProxy Dataplane API endpoints.
	Endpoints []interface{}
	Count     int
	timestamp time.Time
}

// NewHAProxyPodsDiscoveredEvent creates a new HAProxyPodsDiscoveredEvent.
// Performs defensive copy of the endpoints slice.
func NewHAProxyPodsDiscoveredEvent(endpoints []interface{}, count int) *HAProxyPodsDiscoveredEvent {
	// Defensive copy of slice
	var endpointsCopy []interface{}
	if len(endpoints) > 0 {
		endpointsCopy = make([]interface{}, len(endpoints))
		copy(endpointsCopy, endpoints)
	}

	return &HAProxyPodsDiscoveredEvent{
		Endpoints: endpointsCopy,
		Count:     count,
		timestamp: time.Now(),
	}
}

func (e *HAProxyPodsDiscoveredEvent) EventType() string    { return EventTypeHAProxyPodsDiscovered }
func (e *HAProxyPodsDiscoveredEvent) Timestamp() time.Time { return e.timestamp }

// HAProxyPodAddedEvent is published when a new HAProxy pod is discovered.
type HAProxyPodAddedEvent struct {
	Endpoint  interface{}
	timestamp time.Time
}

// NewHAProxyPodAddedEvent creates a new HAProxyPodAddedEvent.
func NewHAProxyPodAddedEvent(endpoint interface{}) *HAProxyPodAddedEvent {
	return &HAProxyPodAddedEvent{
		Endpoint:  endpoint,
		timestamp: time.Now(),
	}
}

func (e *HAProxyPodAddedEvent) EventType() string    { return EventTypeHAProxyPodAdded }
func (e *HAProxyPodAddedEvent) Timestamp() time.Time { return e.timestamp }

// HAProxyPodRemovedEvent is published when an HAProxy pod is removed.
type HAProxyPodRemovedEvent struct {
	Endpoint  interface{}
	timestamp time.Time
}

// NewHAProxyPodRemovedEvent creates a new HAProxyPodRemovedEvent.
func NewHAProxyPodRemovedEvent(endpoint interface{}) *HAProxyPodRemovedEvent {
	return &HAProxyPodRemovedEvent{
		Endpoint:  endpoint,
		timestamp: time.Now(),
	}
}

func (e *HAProxyPodRemovedEvent) EventType() string    { return EventTypeHAProxyPodRemoved }
func (e *HAProxyPodRemovedEvent) Timestamp() time.Time { return e.timestamp }

// -----------------------------------------------------------------------------
// Configuration Resource Events
// -----------------------------------------------------------------------------

// ConfigResourceChangedEvent is published when the ConfigMap resource is added, updated, or deleted.
//
// This is a low-level event published directly by the SingleWatcher callback in the controller package.
// The ConfigLoaderComponent subscribes to this event and handles parsing.
type ConfigResourceChangedEvent struct {
	// Resource contains the raw ConfigMap resource.
	// Type: interface{} to avoid circular dependencies.
	// Consumers should type-assert to *unstructured.Unstructured or *corev1.ConfigMap.
	Resource interface{}

	timestamp time.Time
}

// NewConfigResourceChangedEvent creates a new ConfigResourceChangedEvent.
func NewConfigResourceChangedEvent(resource interface{}) *ConfigResourceChangedEvent {
	return &ConfigResourceChangedEvent{
		Resource:  resource,
		timestamp: time.Now(),
	}
}

func (e *ConfigResourceChangedEvent) EventType() string    { return EventTypeConfigResourceChanged }
func (e *ConfigResourceChangedEvent) Timestamp() time.Time { return e.timestamp }

// SecretResourceChangedEvent is published when the Secret resource is added, updated, or deleted.
//
// This is a low-level event published directly by the SingleWatcher callback in the controller package.
// The CredentialsLoaderComponent subscribes to this event and handles parsing.
type SecretResourceChangedEvent struct {
	// Resource contains the raw Secret resource.
	// Type: interface{} to avoid circular dependencies.
	// Consumers should type-assert to *unstructured.Unstructured or *corev1.Secret.
	Resource interface{}

	timestamp time.Time
}

// NewSecretResourceChangedEvent creates a new SecretResourceChangedEvent.
func NewSecretResourceChangedEvent(resource interface{}) *SecretResourceChangedEvent {
	return &SecretResourceChangedEvent{
		Resource:  resource,
		timestamp: time.Now(),
	}
}

func (e *SecretResourceChangedEvent) EventType() string    { return EventTypeSecretResourceChanged }
func (e *SecretResourceChangedEvent) Timestamp() time.Time { return e.timestamp }

// -----------------------------------------------------------------------------
// Credentials Events
// -----------------------------------------------------------------------------

// CredentialsUpdatedEvent is published when credentials have been successfully
// loaded and validated from the Secret.
type CredentialsUpdatedEvent struct {
	// Credentials contains the validated credentials.
	// Type: interface{} to avoid circular dependencies.
	// Consumers should type-assert to their expected credentials type.
	Credentials interface{}

	// SecretVersion is the resourceVersion of the Secret.
	SecretVersion string

	timestamp time.Time
}

// NewCredentialsUpdatedEvent creates a new CredentialsUpdatedEvent.
func NewCredentialsUpdatedEvent(credentials interface{}, secretVersion string) *CredentialsUpdatedEvent {
	return &CredentialsUpdatedEvent{
		Credentials:   credentials,
		SecretVersion: secretVersion,
		timestamp:     time.Now(),
	}
}

func (e *CredentialsUpdatedEvent) EventType() string    { return EventTypeCredentialsUpdated }
func (e *CredentialsUpdatedEvent) Timestamp() time.Time { return e.timestamp }

// CredentialsInvalidEvent is published when credential loading or validation fails.
//
// The controller will continue running with the previous valid credentials and wait
// for the next Secret update.
type CredentialsInvalidEvent struct {
	SecretVersion string
	Error         string

	timestamp time.Time
}

// NewCredentialsInvalidEvent creates a new CredentialsInvalidEvent.
func NewCredentialsInvalidEvent(secretVersion, errMsg string) *CredentialsInvalidEvent {
	return &CredentialsInvalidEvent{
		SecretVersion: secretVersion,
		Error:         errMsg,
		timestamp:     time.Now(),
	}
}

func (e *CredentialsInvalidEvent) EventType() string    { return EventTypeCredentialsInvalid }
func (e *CredentialsInvalidEvent) Timestamp() time.Time { return e.timestamp }
