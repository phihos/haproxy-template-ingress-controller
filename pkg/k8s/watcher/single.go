// Package watcher provides Kubernetes resource watching with indexing,
// field filtering, and debounced callbacks.
package watcher

import (
	"context"
	"fmt"
	"log/slog"
	"sync"
	"sync/atomic"

	"haproxy-template-ic/pkg/k8s/client"
	"haproxy-template-ic/pkg/k8s/types"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/fields"
	"k8s.io/client-go/dynamic/dynamicinformer"
	"k8s.io/client-go/tools/cache"
)

// SingleWatcher watches a single named Kubernetes resource and invokes callbacks on changes.
//
// Unlike the bulk Watcher (which watches collections of resources with indexing and debouncing),
// SingleWatcher is optimized for watching one specific resource:
//   - No indexing or store (just the current resource)
//   - No debouncing (immediate callbacks)
//   - Simpler API (resource object in callback, not Store)
//
// Callback Behavior:
//   - During initial sync: All events (Add/Update/Delete) are suppressed (no callbacks)
//   - After sync completes: All events trigger callbacks immediately
//   - Use WaitForSync() to ensure initial state is loaded before relying on callbacks
//
// Thread Safety:
//   - Safe for concurrent use
//   - Callbacks may be invoked from multiple goroutines
//   - Users should ensure callbacks are thread-safe
//
// This is ideal for watching configuration or credentials in a specific ConfigMap or Secret.
type SingleWatcher struct {
	config    types.SingleWatcherConfig
	client    *client.Client
	informer  cache.SharedIndexInformer
	stopCh    chan struct{}
	synced    atomic.Bool   // True after initial sync completes
	syncCh    chan struct{} // Closed when sync completes
	stopOnce  sync.Once     // Ensures Stop() is idempotent
	startOnce sync.Once     // Ensures Start() is idempotent
	started   atomic.Bool   // True if Start() has been called
}

// NewSingle creates a new single-resource watcher with the provided configuration.
//
// Returns an error if:
//   - Configuration validation fails
//   - Client is nil
//   - Informer creation fails
//
// Example:
//
//	watcher, err := watcher.NewSingle(types.SingleWatcherConfig{
//	    GVR: schema.GroupVersionResource{
//	        Group:    "",
//	        Version:  "v1",
//	        Resource: "configmaps",
//	    },
//	    Namespace: "default",
//	    Name:      "haproxy-config",
//	    OnChange: func(obj interface{}) error {
//	        cm := obj.(*corev1.ConfigMap)
//	        // Process configuration
//	        return nil
//	    },
//	}, k8sClient)
func NewSingle(cfg types.SingleWatcherConfig, k8sClient *client.Client) (*SingleWatcher, error) {
	// Set defaults
	cfg.SetDefaults()

	// Validate configuration
	if err := cfg.Validate(); err != nil {
		return nil, err
	}

	if k8sClient == nil {
		return nil, fmt.Errorf("k8s client is nil")
	}

	w := &SingleWatcher{
		config: cfg,
		client: k8sClient,
		stopCh: make(chan struct{}),
		syncCh: make(chan struct{}),
		// synced defaults to false (atomic.Bool zero value)
	}

	// Create informer
	if err := w.createInformer(); err != nil {
		return nil, fmt.Errorf("failed to create informer: %w", err)
	}

	return w, nil
}

// createInformer creates a SharedIndexInformer for the single watched resource.
func (w *SingleWatcher) createInformer() error {
	// Get dynamic client
	dynamicClient := w.client.DynamicClient()
	if dynamicClient == nil {
		return fmt.Errorf("dynamic client is nil")
	}

	// Create informer factory with field selector for specific resource name
	informerFactory := dynamicinformer.NewFilteredDynamicSharedInformerFactory(
		dynamicClient,
		0, // No resync
		w.config.Namespace,
		func(options *metav1.ListOptions) {
			// Filter by resource name using field selector
			options.FieldSelector = fields.OneTermEqualSelector("metadata.name", w.config.Name).String()
		},
	)

	// Get informer for resource
	w.informer = informerFactory.ForResource(w.config.GVR).Informer()

	// Add event handlers
	_, err := w.informer.AddEventHandler(cache.ResourceEventHandlerFuncs{
		AddFunc:    w.handleAdd,
		UpdateFunc: w.handleUpdate,
		DeleteFunc: w.handleDelete,
	})
	if err != nil {
		return fmt.Errorf("failed to add event handler: %w", err)
	}

	return nil
}

// handleAdd handles resource addition events.
func (w *SingleWatcher) handleAdd(obj interface{}) {
	resource := w.convertToUnstructured(obj)
	if resource == nil {
		return
	}

	// Skip callback during initial sync - we don't want to trigger change events
	// for resources that already exist. Only invoke callback for real additions
	// that happen after sync completes.
	if !w.synced.Load() {
		// During initial sync, skip callback
		return
	}

	// Invoke callback immediately (no debouncing for single resource)
	if w.config.OnChange != nil {
		if err := w.config.OnChange(resource); err != nil {
			// Log error but don't propagate - callback failures shouldn't stop the watcher
			slog.Warn("Watcher callback failed on Add event",
				"error", err,
				"resource_name", resource.GetName(),
				"resource_namespace", resource.GetNamespace(),
				"resource_kind", resource.GetKind())
		}
	}
}

// handleUpdate handles resource update events.
func (w *SingleWatcher) handleUpdate(oldObj, newObj interface{}) {
	resource := w.convertToUnstructured(newObj)
	if resource == nil {
		return
	}

	// Skip callback during initial sync - we don't want to trigger change events
	// for resources that are updating during the sync process. Only invoke callback
	// for real updates that happen after sync completes.
	if !w.synced.Load() {
		// During initial sync, skip callback
		return
	}

	// Invoke callback immediately (no debouncing for single resource)
	if w.config.OnChange != nil {
		if err := w.config.OnChange(resource); err != nil {
			// Log error but don't propagate - callback failures shouldn't stop the watcher
			slog.Warn("Watcher callback failed on Update event",
				"error", err,
				"resource_name", resource.GetName(),
				"resource_namespace", resource.GetNamespace(),
				"resource_kind", resource.GetKind())
		}
	}
}

// handleDelete handles resource deletion events.
func (w *SingleWatcher) handleDelete(obj interface{}) {
	resource := w.convertToUnstructured(obj)
	if resource == nil {
		// Handle DeletedFinalStateUnknown
		if tombstone, ok := obj.(cache.DeletedFinalStateUnknown); ok {
			resource = w.convertToUnstructured(tombstone.Obj)
		}
		if resource == nil {
			return
		}
	}

	// Skip callback during initial sync for consistency (unlikely scenario but possible)
	// Only invoke callback for real deletions that happen after sync completes.
	if !w.synced.Load() {
		// During initial sync, skip callback
		return
	}

	// Invoke callback to signal deletion
	if w.config.OnChange != nil {
		if err := w.config.OnChange(resource); err != nil {
			// Log error but don't propagate - callback failures shouldn't stop the watcher
			slog.Warn("Watcher callback failed on Delete event",
				"error", err,
				"resource_name", resource.GetName(),
				"resource_namespace", resource.GetNamespace(),
				"resource_kind", resource.GetKind())
		}
	}
}

// convertToUnstructured converts a resource to *unstructured.Unstructured.
func (w *SingleWatcher) convertToUnstructured(obj interface{}) *unstructured.Unstructured {
	if u, ok := obj.(*unstructured.Unstructured); ok {
		return u
	}
	return nil
}

// Start begins watching the resource.
//
// This method blocks until the context is cancelled or an error occurs.
// Initial sync is performed before continuing.
//
// This method is idempotent - calling it multiple times is safe. The initialization
// logic (starting informer, syncing) only runs once, but each call will block until
// the context is cancelled.
func (w *SingleWatcher) Start(ctx context.Context) error {
	var startErr error

	// Ensure initialization only happens once
	w.startOnce.Do(func() {
		w.started.Store(true)

		// Start informer
		go w.informer.Run(w.stopCh)

		// Wait for cache sync
		if !cache.WaitForCacheSync(ctx.Done(), w.informer.HasSynced) {
			startErr = fmt.Errorf("failed to sync cache")
			return
		}

		// Mark sync as complete atomically
		w.synced.Store(true)
		close(w.syncCh)
	})

	// Return any error from initialization
	if startErr != nil {
		return startErr
	}

	// Wait for context cancellation
	<-ctx.Done()

	return w.Stop()
}

// Stop stops watching the resource.
//
// This method is idempotent and safe to call multiple times.
func (w *SingleWatcher) Stop() error {
	w.stopOnce.Do(func() {
		close(w.stopCh)
	})
	return nil
}

// WaitForSync blocks until initial synchronization is complete.
//
// This is useful when you need to wait for the watcher to have the current
// state of the resource before performing operations that depend on it.
//
// Returns an error if sync fails or context is cancelled.
//
// Example:
//
//	watcher, _ := watcher.NewSingle(cfg, client)
//	go watcher.Start(ctx)
//
//	err := watcher.WaitForSync(ctx)
//	if err != nil {
//	    log.Fatal(err)
//	}
//	log.Println("Watcher synced, resource is available")
func (w *SingleWatcher) WaitForSync(ctx context.Context) error {
	// Wait for sync channel to close or context to be cancelled
	select {
	case <-w.syncCh:
		return nil
	case <-ctx.Done():
		return fmt.Errorf("context cancelled while waiting for sync")
	}
}

// IsSynced returns true if initial synchronization has completed.
//
// This provides a non-blocking way to check if the watcher has synced.
func (w *SingleWatcher) IsSynced() bool {
	return w.synced.Load()
}

// IsStarted returns true if Start() has been called.
//
// This provides a non-blocking way to check if the watcher has been started.
func (w *SingleWatcher) IsStarted() bool {
	return w.started.Load()
}
