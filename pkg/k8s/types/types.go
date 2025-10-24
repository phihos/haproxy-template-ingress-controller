// Package types defines core interfaces and types for the k8s package.
//
// This package provides the foundational types used across all k8s subpackages,
// including:
// - Store interface for resource indexing
// - Watcher configuration structures
// - Callback types for change notifications
// - Statistics and status types
package types

import (
	"context"
	"time"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime/schema"
)

// Store defines the interface for storing and retrieving indexed Kubernetes resources.
//
// Implementations must be thread-safe for concurrent access.
// Resources are indexed by one or more keys extracted using JSONPath expressions.
type Store interface {
	// Get retrieves all resources matching the provided index keys.
	// Keys are evaluated in order as specified in the index configuration.
	//
	// Returns:
	//   - A slice of matching resources
	//   - An error if the operation fails
	//
	// Example:
	//   // For index_by: ["metadata.namespace", "metadata.name"]
	//   resources, err := store.Get("default", "my-ingress")
	Get(keys ...string) ([]interface{}, error)

	// List returns all resources in the store.
	//
	// Returns:
	//   - A slice of all stored resources
	//   - An error if the operation fails
	List() ([]interface{}, error)

	// Add inserts a new resource into the store with the provided index keys.
	//
	// Parameters:
	//   - resource: The Kubernetes resource to store
	//   - keys: Index keys extracted from the resource
	//
	// Returns an error if the operation fails.
	Add(resource interface{}, keys []string) error

	// Update modifies an existing resource in the store.
	// If the resource doesn't exist, it will be added.
	//
	// Parameters:
	//   - resource: The updated Kubernetes resource
	//   - keys: Index keys extracted from the resource
	//
	// Returns an error if the operation fails.
	Update(resource interface{}, keys []string) error

	// Delete removes a resource from the store using its index keys.
	//
	// Parameters:
	//   - keys: Index keys identifying the resource to delete
	//
	// Returns an error if the operation fails.
	Delete(keys ...string) error

	// Clear removes all resources from the store.
	Clear() error
}

// StoreType defines the type of store implementation to use.
type StoreType int

const (
	// StoreTypeMemory stores complete resources in memory.
	// This is the default and provides fastest access but higher memory usage.
	StoreTypeMemory StoreType = iota

	// StoreTypeCached stores only index keys in memory and fetches resources
	// from the Kubernetes API on access. Responses are cached with a TTL.
	// This reduces memory usage at the cost of API latency on cache misses.
	StoreTypeCached
)

// String returns the string representation of the store type.
func (s StoreType) String() string {
	switch s {
	case StoreTypeMemory:
		return "memory"
	case StoreTypeCached:
		return "cached"
	default:
		return "unknown"
	}
}

// ChangeStats tracks aggregated statistics about resource changes since the last callback.
type ChangeStats struct {
	// Created is the number of resources added to the store.
	Created int

	// Modified is the number of resources updated in the store.
	Modified int

	// Deleted is the number of resources removed from the store.
	Deleted int

	// IsInitialSync is true when this callback is fired during initial synchronization.
	// During initial sync, Created count includes pre-existing resources being bulk-loaded.
	// After sync completes, IsInitialSync is false for all subsequent real-time changes.
	IsInitialSync bool
}

// Total returns the total number of changes.
func (c ChangeStats) Total() int {
	return c.Created + c.Modified + c.Deleted
}

// IsEmpty returns true if no changes occurred.
func (c ChangeStats) IsEmpty() bool {
	return c.Total() == 0
}

// OnChangeCallback is invoked when resources in the store change.
//
// The callback receives:
//   - store: The updated Store instance
//   - stats: Aggregated statistics about what changed
//
// Callbacks are debounced according to the WatcherConfig.DebounceInterval setting.
type OnChangeCallback func(store Store, stats ChangeStats)

// OnSyncCompleteCallback is invoked once after initial synchronization completes.
//
// This provides a clear signal that the store is fully populated with pre-existing
// resources and the watcher is ready for real-time change tracking.
//
// The callback receives:
//   - store: The fully synchronized Store instance
//   - initialCount: The number of pre-existing resources loaded during initial sync
type OnSyncCompleteCallback func(store Store, initialCount int)

// OnResourceChangeCallback is invoked when a single watched resource changes.
//
// This callback is used by SingleWatcher for watching a specific named resource.
// The callback receives the updated resource directly, allowing immediate processing.
//
// Unlike OnChangeCallback (used for bulk watchers), this callback:
//   - Receives the actual resource object, not a Store
//   - Is invoked immediately without debouncing
//   - Returns an error if processing fails
//
// The callback receives:
//   - obj: The Kubernetes resource that changed (runtime.Object)
//
// Returns an error if resource processing fails.
type OnResourceChangeCallback func(obj interface{}) error

// WatcherConfig configures a Kubernetes resource watcher.
type WatcherConfig struct {
	// GroupVersionResource identifies the Kubernetes resource type to watch.
	//
	// Example for Ingress:
	//   GVR: schema.GroupVersionResource{
	//       Group:    "networking.k8s.io",
	//       Version:  "v1",
	//       Resource: "ingresses",
	//   }
	GVR schema.GroupVersionResource

	// Namespace restricts watching to a specific namespace.
	// If empty, watches all namespaces.
	//
	// Example:
	//   Namespace: "default"  // Watch only resources in default namespace
	//   Namespace: ""         // Watch resources in all namespaces
	Namespace string

	// NamespacedWatch, when true, restricts watching to the controller's own namespace.
	// This is determined automatically from the service account token.
	//
	// This is useful for watching HAProxy pods that must be in the same namespace
	// as the controller.
	//
	// Takes precedence over Namespace if both are set.
	NamespacedWatch bool

	// LabelSelector filters resources by label selector.
	// Uses Kubernetes label selector syntax.
	//
	// Example:
	//   LabelSelector: metav1.LabelSelector{
	//       MatchLabels: map[string]string{
	//           "app": "haproxy",
	//           "component": "loadbalancer",
	//       },
	//   }
	LabelSelector *metav1.LabelSelector

	// IndexBy specifies JSONPath expressions for extracting index keys from resources.
	//
	// Resources are indexed by the values of these expressions in order.
	// For O(1) lookup, use expressions that uniquely identify resources.
	//
	// Examples:
	//   // Index by namespace and name (standard iteration)
	//   IndexBy: []string{"metadata.namespace", "metadata.name"}
	//
	//   // Index by service name from label (O(1) service-to-endpoints lookup)
	//   IndexBy: []string{"metadata.labels['kubernetes.io/service-name']"}
	IndexBy []string

	// IgnoreFields specifies JSONPath expressions for fields to remove from resources
	// before storing them.
	//
	// This reduces memory usage by removing unnecessary fields.
	//
	// Examples:
	//   IgnoreFields: []string{
	//       "metadata.managedFields",  // Remove managed fields (verbose)
	//       "metadata.annotations",    // Remove annotations if not needed
	//   }
	IgnoreFields []string

	// StoreType determines the storage implementation to use.
	// See StoreType constants for available options.
	//
	// Default: StoreTypeMemory
	StoreType StoreType

	// CacheTTL sets the cache duration for StoreTypeCached.
	// Ignored for other store types.
	//
	// Cache entries are invalidated on resource updates. The TTL is reset
	// on every Get() access, implementing LRU-like behavior based on access time.
	// This ensures frequently accessed resources remain cached even if the original
	// TTL would have expired.
	//
	// Default: 2.2x drift prevention interval (allows one rendering cycle to fail
	// while still keeping resources cached)
	CacheTTL time.Duration

	// DebounceInterval sets the minimum time between OnChange callback invocations.
	//
	// Rapid resource changes within this interval are batched into a single callback
	// with aggregated statistics.
	//
	// Default: 500ms
	DebounceInterval time.Duration

	// OnChange is called when resources in the store change.
	// This callback is debounced according to DebounceInterval.
	//
	// The callback receives the updated Store and aggregated ChangeStats.
	// The ChangeStats.IsInitialSync field indicates if changes are from initial sync or real-time.
	OnChange OnChangeCallback

	// OnSyncComplete is called once after initial synchronization completes.
	// This provides a clear signal that the store is fully populated with pre-existing resources.
	//
	// The callback receives the store and the count of resources loaded during initial sync.
	// This is called after the informer's HasSynced() returns true.
	//
	// Optional: If not provided, no sync complete notification is sent.
	OnSyncComplete OnSyncCompleteCallback

	// CallOnChangeDuringSync determines if OnChange is called during initial synchronization.
	//
	// If false (default), OnChange is suppressed until sync completes, and only OnSyncComplete
	// is called with the final state. This avoids overwhelming the callback with bulk load events.
	//
	// If true, OnChange is called for every change during initial sync with IsInitialSync=true,
	// allowing incremental processing of pre-existing resources.
	//
	// Default: false
	CallOnChangeDuringSync bool

	// Context is used for cancellation of the watcher.
	// If nil, context.Background() is used.
	Context context.Context
}

// SetDefaults applies default values to unset configuration fields.
func (c *WatcherConfig) SetDefaults() {
	if c.CacheTTL == 0 {
		// Default TTL: 2.2x the default drift prevention interval (60s)
		// This results in ~132s, allowing one rendering cycle to fail
		// while still keeping resources cached
		c.CacheTTL = 2*time.Minute + 10*time.Second
	}
	if c.DebounceInterval == 0 {
		c.DebounceInterval = 500 * time.Millisecond
	}
	if c.Context == nil {
		c.Context = context.Background()
	}
}

// Validate checks if the configuration is valid.
// Returns an error if any required field is missing or invalid.
func (c *WatcherConfig) Validate() error {
	if c.GVR.Resource == "" {
		return &ConfigError{Field: "GVR.Resource", Message: "resource is required"}
	}
	if len(c.IndexBy) == 0 {
		return &ConfigError{Field: "IndexBy", Message: "at least one index key is required"}
	}
	if c.OnChange == nil {
		return &ConfigError{Field: "OnChange", Message: "callback is required"}
	}
	return nil
}

// ConfigError represents a configuration validation error.
type ConfigError struct {
	Field   string
	Message string
}

func (e *ConfigError) Error() string {
	return "config error in " + e.Field + ": " + e.Message
}

// SingleWatcherConfig configures a watcher for a single named Kubernetes resource.
//
// Unlike WatcherConfig (which watches collections of resources), SingleWatcherConfig
// watches one specific resource identified by namespace and name.
//
// This is ideal for watching:
//   - Configuration stored in a specific ConfigMap
//   - Credentials stored in a specific Secret
//   - Any other single resource that the controller depends on
type SingleWatcherConfig struct {
	// GroupVersionResource identifies the Kubernetes resource type to watch.
	//
	// Example for ConfigMap:
	//   GVR: schema.GroupVersionResource{
	//       Group:    "",
	//       Version:  "v1",
	//       Resource: "configmaps",
	//   }
	GVR schema.GroupVersionResource

	// Namespace is the namespace containing the resource.
	// This is required for SingleWatcher (unlike bulk watchers which can watch all namespaces).
	//
	// Example:
	//   Namespace: "kube-system"
	Namespace string

	// Name is the name of the specific resource to watch.
	// This is required and identifies the single resource to monitor.
	//
	// Example:
	//   Name: "haproxy-config"
	Name string

	// OnChange is called when the watched resource changes (add, update, delete).
	// This callback is invoked immediately without debouncing.
	//
	// The callback receives the resource object directly and returns an error if processing fails.
	OnChange OnResourceChangeCallback

	// Context is used for cancellation of the watcher.
	// If nil, context.Background() is used.
	Context context.Context
}

// SetDefaults applies default values to unset configuration fields.
func (c *SingleWatcherConfig) SetDefaults() {
	if c.Context == nil {
		c.Context = context.Background()
	}
}

// Validate checks if the configuration is valid.
// Returns an error if any required field is missing or invalid.
func (c *SingleWatcherConfig) Validate() error {
	if c.GVR.Resource == "" {
		return &ConfigError{Field: "GVR.Resource", Message: "resource is required"}
	}
	if c.Namespace == "" {
		return &ConfigError{Field: "Namespace", Message: "namespace is required"}
	}
	if c.Name == "" {
		return &ConfigError{Field: "Name", Message: "resource name is required"}
	}
	if c.OnChange == nil {
		return &ConfigError{Field: "OnChange", Message: "callback is required"}
	}
	return nil
}
