package events

import (
	"fmt"
	"time"
)

// This file contains all event type definitions for the haproxy-template-ic controller.
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

func (e ControllerStartedEvent) EventType() string { return EventTypeControllerStarted }

// ControllerShutdownEvent is published when the controller is shutting down gracefully.
type ControllerShutdownEvent struct {
	Reason    string
	timestamp time.Time
}

func (e ControllerShutdownEvent) EventType() string { return EventTypeControllerShutdown }

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

func (e ConfigParsedEvent) EventType() string { return EventTypeConfigParsed }

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

func NewConfigValidationRequest(config interface{}, version string) ConfigValidationRequest {
	return ConfigValidationRequest{
		reqID:     fmt.Sprintf("config-validation-%s-%d", version, time.Now().UnixNano()),
		Config:    config,
		Version:   version,
		timestamp: time.Now(),
	}
}

func (e ConfigValidationRequest) EventType() string { return EventTypeConfigValidationRequest }
func (e ConfigValidationRequest) RequestID() string { return e.reqID }

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

func NewConfigValidationResponse(requestID, validatorName string, valid bool, errors []string) ConfigValidationResponse {
	return ConfigValidationResponse{
		reqID:         requestID,
		responder:     validatorName,
		ValidatorName: validatorName,
		Valid:         valid,
		Errors:        errors,
		timestamp:     time.Now(),
	}
}

func (e ConfigValidationResponse) EventType() string { return EventTypeConfigValidationResponse }
func (e ConfigValidationResponse) RequestID() string { return e.reqID }
func (e ConfigValidationResponse) Responder() string { return e.responder }

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

func (e ConfigValidatedEvent) EventType() string { return EventTypeConfigValidated }

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

func (e ConfigInvalidEvent) EventType() string { return EventTypeConfigInvalid }

// -----------------------------------------------------------------------------
// Resource Events
// -----------------------------------------------------------------------------

// ResourceIndexUpdatedEvent is published when a watched Kubernetes resource
// has been added, updated, or deleted in the local index.
type ResourceIndexUpdatedEvent struct {
	// ResourceType identifies the resource (e.g., "ingresses", "services").
	ResourceType string

	// Count is the current total number of indexed resources of this type.
	Count int

	// ChangeType describes the operation: "added", "updated", "deleted".
	ChangeType string

	timestamp time.Time
}

func (e ResourceIndexUpdatedEvent) EventType() string { return EventTypeResourceIndexUpdated }

// ResourceSyncCompleteEvent is published when a resource watcher has completed
// its initial sync with the Kubernetes API.
type ResourceSyncCompleteEvent struct {
	ResourceType string
	InitialCount int
	timestamp    time.Time
}

func (e ResourceSyncCompleteEvent) EventType() string { return EventTypeResourceSyncComplete }

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

func (e IndexSynchronizedEvent) EventType() string { return EventTypeIndexSynchronized }

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

func (e ReconciliationTriggeredEvent) EventType() string { return EventTypeReconciliationTriggered }

// ReconciliationStartedEvent is published when the Executor begins a reconciliation cycle.
type ReconciliationStartedEvent struct {
	// Trigger describes what triggered this reconciliation.
	Trigger   string
	timestamp time.Time
}

func (e ReconciliationStartedEvent) EventType() string { return EventTypeReconciliationStarted }

// ReconciliationCompletedEvent is published when a reconciliation cycle completes successfully.
type ReconciliationCompletedEvent struct {
	DurationMs int64
	timestamp  time.Time
}

func (e ReconciliationCompletedEvent) EventType() string { return EventTypeReconciliationCompleted }

// ReconciliationFailedEvent is published when a reconciliation cycle fails.
type ReconciliationFailedEvent struct {
	Error     string
	Phase     string // Which phase failed: "render", "validate", "deploy"
	timestamp time.Time
}

func (e ReconciliationFailedEvent) EventType() string { return EventTypeReconciliationFailed }

// -----------------------------------------------------------------------------
// Template Events
// -----------------------------------------------------------------------------

// TemplateRenderedEvent is published when template rendering completes successfully.
type TemplateRenderedEvent struct {
	// ConfigBytes is the size of the rendered haproxy.cfg.
	ConfigBytes int

	// AuxiliaryFileCount is the number of auxiliary files rendered (maps, certs, error pages).
	AuxiliaryFileCount int

	DurationMs int64
	timestamp  time.Time
}

func (e TemplateRenderedEvent) EventType() string { return EventTypeTemplateRendered }

// TemplateRenderFailedEvent is published when template rendering fails.
type TemplateRenderFailedEvent struct {
	Error      string
	StackTrace string
	timestamp  time.Time
}

func (e TemplateRenderFailedEvent) EventType() string { return EventTypeTemplateRenderFailed }

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

func (e ValidationStartedEvent) EventType() string { return EventTypeValidationStarted }

// ValidationCompletedEvent is published when configuration validation succeeds.
type ValidationCompletedEvent struct {
	Endpoints  []interface{}
	Warnings   []string // Non-fatal warnings
	DurationMs int64
	timestamp  time.Time
}

func (e ValidationCompletedEvent) EventType() string { return EventTypeValidationCompleted }

// ValidationFailedEvent is published when configuration validation fails.
type ValidationFailedEvent struct {
	Endpoints  []interface{}
	Errors     []string // Validation errors
	DurationMs int64
	timestamp  time.Time
}

func (e ValidationFailedEvent) EventType() string { return EventTypeValidationFailed }

// -----------------------------------------------------------------------------
// Deployment Events
// -----------------------------------------------------------------------------

// DeploymentStartedEvent is published when deployment to HAProxy instances begins.
type DeploymentStartedEvent struct {
	Endpoints []interface{}
	timestamp time.Time
}

func (e DeploymentStartedEvent) EventType() string { return EventTypeDeploymentStarted }

// InstanceDeployedEvent is published when deployment to a single HAProxy instance succeeds.
type InstanceDeployedEvent struct {
	Endpoint       interface{} // The HAProxy endpoint that was deployed to
	DurationMs     int64
	ReloadRequired bool // Whether this deployment required an HAProxy reload
	timestamp      time.Time
}

func (e InstanceDeployedEvent) EventType() string { return EventTypeInstanceDeployed }

// InstanceDeploymentFailedEvent is published when deployment to a single HAProxy instance fails.
type InstanceDeploymentFailedEvent struct {
	Endpoint  interface{}
	Error     string
	Retryable bool // Whether this failure is retryable
	timestamp time.Time
}

func (e InstanceDeploymentFailedEvent) EventType() string { return EventTypeInstanceDeploymentFailed }

// DeploymentCompletedEvent is published when deployment to all HAProxy instances completes.
type DeploymentCompletedEvent struct {
	Total      int // Total number of instances
	Succeeded  int // Number of successful deployments
	Failed     int // Number of failed deployments
	DurationMs int64
	timestamp  time.Time
}

func (e DeploymentCompletedEvent) EventType() string { return EventTypeDeploymentCompleted }

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

func (e StorageSyncStartedEvent) EventType() string { return EventTypeStorageSyncStarted }

// StorageSyncCompletedEvent is published when auxiliary file synchronization completes.
type StorageSyncCompletedEvent struct {
	Phase string

	// Stats contains sync statistics.
	// Type: interface{} to avoid circular dependencies.
	Stats interface{}

	DurationMs int64
	timestamp  time.Time
}

func (e StorageSyncCompletedEvent) EventType() string { return EventTypeStorageSyncCompleted }

// StorageSyncFailedEvent is published when auxiliary file synchronization fails.
type StorageSyncFailedEvent struct {
	Phase     string
	Error     string
	timestamp time.Time
}

func (e StorageSyncFailedEvent) EventType() string { return EventTypeStorageSyncFailed }

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

func (e HAProxyPodsDiscoveredEvent) EventType() string { return EventTypeHAProxyPodsDiscovered }

// HAProxyPodAddedEvent is published when a new HAProxy pod is discovered.
type HAProxyPodAddedEvent struct {
	Endpoint  interface{}
	timestamp time.Time
}

func (e HAProxyPodAddedEvent) EventType() string { return EventTypeHAProxyPodAdded }

// HAProxyPodRemovedEvent is published when an HAProxy pod is removed.
type HAProxyPodRemovedEvent struct {
	Endpoint  interface{}
	timestamp time.Time
}

func (e HAProxyPodRemovedEvent) EventType() string { return EventTypeHAProxyPodRemoved }

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

func (e ConfigResourceChangedEvent) EventType() string { return EventTypeConfigResourceChanged }

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

func (e SecretResourceChangedEvent) EventType() string { return EventTypeSecretResourceChanged }

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

func (e CredentialsUpdatedEvent) EventType() string { return EventTypeCredentialsUpdated }

// CredentialsInvalidEvent is published when credential loading or validation fails.
//
// The controller will continue running with the previous valid credentials and wait
// for the next Secret update.
type CredentialsInvalidEvent struct {
	SecretVersion string
	Error         string

	timestamp time.Time
}

func (e CredentialsInvalidEvent) EventType() string { return EventTypeCredentialsInvalid }

// -----------------------------------------------------------------------------
// Constructor Functions
// -----------------------------------------------------------------------------

// NewConfigResourceChangedEvent creates a new ConfigResourceChangedEvent.
func NewConfigResourceChangedEvent(resource interface{}) ConfigResourceChangedEvent {
	return ConfigResourceChangedEvent{
		Resource:  resource,
		timestamp: time.Now(),
	}
}

// NewSecretResourceChangedEvent creates a new SecretResourceChangedEvent.
func NewSecretResourceChangedEvent(resource interface{}) SecretResourceChangedEvent {
	return SecretResourceChangedEvent{
		Resource:  resource,
		timestamp: time.Now(),
	}
}

// NewConfigParsedEvent creates a new ConfigParsedEvent.
func NewConfigParsedEvent(config interface{}, version, secretVersion string) ConfigParsedEvent {
	return ConfigParsedEvent{
		Config:        config,
		Version:       version,
		SecretVersion: secretVersion,
		timestamp:     time.Now(),
	}
}

// NewConfigValidatedEvent creates a new ConfigValidatedEvent.
func NewConfigValidatedEvent(config interface{}, version, secretVersion string) ConfigValidatedEvent {
	return ConfigValidatedEvent{
		Config:        config,
		Version:       version,
		SecretVersion: secretVersion,
		timestamp:     time.Now(),
	}
}

// NewConfigInvalidEvent creates a new ConfigInvalidEvent.
func NewConfigInvalidEvent(version string, validationErrors map[string][]string) ConfigInvalidEvent {
	return ConfigInvalidEvent{
		Version:          version,
		ValidationErrors: validationErrors,
		timestamp:        time.Now(),
	}
}

// NewCredentialsUpdatedEvent creates a new CredentialsUpdatedEvent.
func NewCredentialsUpdatedEvent(credentials interface{}, secretVersion string) CredentialsUpdatedEvent {
	return CredentialsUpdatedEvent{
		Credentials:   credentials,
		SecretVersion: secretVersion,
		timestamp:     time.Now(),
	}
}

// NewCredentialsInvalidEvent creates a new CredentialsInvalidEvent.
func NewCredentialsInvalidEvent(secretVersion, errMsg string) CredentialsInvalidEvent {
	return CredentialsInvalidEvent{
		SecretVersion: secretVersion,
		Error:         errMsg,
		timestamp:     time.Now(),
	}
}

// -----------------------------------------------------------------------------
// Timestamp Methods (Event Interface Implementation)
// -----------------------------------------------------------------------------

func (e ControllerStartedEvent) Timestamp() time.Time        { return e.timestamp }
func (e ControllerShutdownEvent) Timestamp() time.Time       { return e.timestamp }
func (e ConfigParsedEvent) Timestamp() time.Time             { return e.timestamp }
func (e ConfigValidationRequest) Timestamp() time.Time       { return e.timestamp }
func (e ConfigValidationResponse) Timestamp() time.Time      { return e.timestamp }
func (e ConfigValidatedEvent) Timestamp() time.Time          { return e.timestamp }
func (e ConfigInvalidEvent) Timestamp() time.Time            { return e.timestamp }
func (e ResourceIndexUpdatedEvent) Timestamp() time.Time     { return e.timestamp }
func (e ResourceSyncCompleteEvent) Timestamp() time.Time     { return e.timestamp }
func (e IndexSynchronizedEvent) Timestamp() time.Time        { return e.timestamp }
func (e ReconciliationTriggeredEvent) Timestamp() time.Time  { return e.timestamp }
func (e ReconciliationStartedEvent) Timestamp() time.Time    { return e.timestamp }
func (e ReconciliationCompletedEvent) Timestamp() time.Time  { return e.timestamp }
func (e ReconciliationFailedEvent) Timestamp() time.Time     { return e.timestamp }
func (e TemplateRenderedEvent) Timestamp() time.Time         { return e.timestamp }
func (e TemplateRenderFailedEvent) Timestamp() time.Time     { return e.timestamp }
func (e ValidationStartedEvent) Timestamp() time.Time        { return e.timestamp }
func (e ValidationCompletedEvent) Timestamp() time.Time      { return e.timestamp }
func (e ValidationFailedEvent) Timestamp() time.Time         { return e.timestamp }
func (e DeploymentStartedEvent) Timestamp() time.Time        { return e.timestamp }
func (e InstanceDeployedEvent) Timestamp() time.Time         { return e.timestamp }
func (e InstanceDeploymentFailedEvent) Timestamp() time.Time { return e.timestamp }
func (e DeploymentCompletedEvent) Timestamp() time.Time      { return e.timestamp }
func (e StorageSyncStartedEvent) Timestamp() time.Time       { return e.timestamp }
func (e StorageSyncCompletedEvent) Timestamp() time.Time     { return e.timestamp }
func (e StorageSyncFailedEvent) Timestamp() time.Time        { return e.timestamp }
func (e HAProxyPodsDiscoveredEvent) Timestamp() time.Time    { return e.timestamp }
func (e HAProxyPodAddedEvent) Timestamp() time.Time          { return e.timestamp }
func (e HAProxyPodRemovedEvent) Timestamp() time.Time        { return e.timestamp }
func (e ConfigResourceChangedEvent) Timestamp() time.Time    { return e.timestamp }
func (e SecretResourceChangedEvent) Timestamp() time.Time    { return e.timestamp }
func (e CredentialsUpdatedEvent) Timestamp() time.Time       { return e.timestamp }
func (e CredentialsInvalidEvent) Timestamp() time.Time       { return e.timestamp }
