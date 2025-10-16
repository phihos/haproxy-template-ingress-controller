package store

import (
	"context"
	"fmt"
	"sync"
	"time"

	"haproxy-template-ic/pkg/k8s/indexer"
	"haproxy-template-ic/pkg/k8s/types"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/client-go/dynamic"
)

// cacheEntry holds a cached resource with its expiration time.
type cacheEntry struct {
	resource  interface{}
	expiresAt time.Time
}

// CachedStore stores only index keys in memory and fetches resources from
// the Kubernetes API on access. Fetched resources are cached with a TTL.
//
// This reduces memory usage for large resources (e.g., Secrets) at the cost
// of API latency on cache misses.
//
// Thread-safe for concurrent access.
type CachedStore struct {
	mu        sync.RWMutex
	keys      map[string][]string         // Composite key -> index keys
	cache     map[string]*cacheEntry      // Composite key -> cached resource
	numKeys   int                         // Number of index keys
	cacheTTL  time.Duration               // Cache entry TTL
	client    dynamic.Interface           // Kubernetes dynamic client
	gvr       schema.GroupVersionResource // Resource type to fetch
	namespace string                      // Namespace for fetching (empty = all)
	indexer   *indexer.Indexer            // Indexer for processing fetched resources
}

// CachedStoreConfig configures a CachedStore.
type CachedStoreConfig struct {
	// NumKeys is the number of index keys (must match indexer configuration)
	NumKeys int

	// CacheTTL is the cache entry time-to-live
	CacheTTL time.Duration

	// Client is the Kubernetes dynamic client for fetching resources
	Client dynamic.Interface

	// GVR identifies the resource type to fetch
	GVR schema.GroupVersionResource

	// Namespace restricts fetching to a specific namespace (empty = all namespaces)
	Namespace string

	// Indexer processes fetched resources (field filtering)
	Indexer *indexer.Indexer
}

// NewCachedStore creates a new API-backed store with caching.
func NewCachedStore(cfg CachedStoreConfig) (*CachedStore, error) {
	if cfg.NumKeys < 1 {
		return nil, fmt.Errorf("numKeys must be at least 1")
	}
	if cfg.Client == nil {
		return nil, fmt.Errorf("client is required")
	}
	if cfg.Indexer == nil {
		return nil, fmt.Errorf("indexer is required")
	}
	if cfg.CacheTTL == 0 {
		cfg.CacheTTL = 2*time.Minute + 10*time.Second
	}

	return &CachedStore{
		keys:      make(map[string][]string),
		cache:     make(map[string]*cacheEntry),
		numKeys:   cfg.NumKeys,
		cacheTTL:  cfg.CacheTTL,
		client:    cfg.Client,
		gvr:       cfg.GVR,
		namespace: cfg.Namespace,
		indexer:   cfg.Indexer,
	}, nil
}

// Get retrieves all resources matching the provided index keys.
func (s *CachedStore) Get(keys ...string) ([]interface{}, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	if len(keys) == 0 {
		return nil, &StoreError{
			Operation: "get",
			Keys:      keys,
			Err:       fmt.Errorf("at least one key required"),
		}
	}

	if len(keys) > s.numKeys {
		return nil, &StoreError{
			Operation: "get",
			Keys:      keys,
			Err:       fmt.Errorf("too many keys: got %d, expected %d", len(keys), s.numKeys),
		}
	}

	// Find matching keys
	var matchingKeys [][]string

	if len(keys) == s.numKeys {
		// Exact match
		keyStr := makeKeyString(keys)
		if indexKeys, ok := s.keys[keyStr]; ok {
			matchingKeys = append(matchingKeys, indexKeys)
		}
	} else {
		// Partial match
		prefix := makeKeyString(keys) + "/"
		for keyStr, indexKeys := range s.keys {
			if len(keyStr) >= len(prefix) && keyStr[:len(prefix)] == prefix {
				matchingKeys = append(matchingKeys, indexKeys)
			}
		}
	}

	// Fetch resources
	results := make([]interface{}, 0, len(matchingKeys))
	for _, indexKeys := range matchingKeys {
		resource, err := s.fetchResource(indexKeys)
		if err != nil {
			// Skip resources that can't be fetched (may be deleted)
			continue
		}
		results = append(results, resource)
	}

	return results, nil
}

// List returns all resources in the store.
func (s *CachedStore) List() ([]interface{}, error) {
	s.mu.RLock()
	allKeys := make([][]string, 0, len(s.keys))
	for _, indexKeys := range s.keys {
		allKeys = append(allKeys, indexKeys)
	}
	s.mu.RUnlock()

	// Fetch all resources
	results := make([]interface{}, 0, len(allKeys))
	for _, indexKeys := range allKeys {
		resource, err := s.fetchResource(indexKeys)
		if err != nil {
			// Skip resources that can't be fetched
			continue
		}
		results = append(results, resource)
	}

	return results, nil
}

// Add inserts a new resource into the store.
func (s *CachedStore) Add(resource interface{}, keys []string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if len(keys) != s.numKeys {
		return &StoreError{
			Operation: "add",
			Keys:      keys,
			Err:       fmt.Errorf("wrong number of keys: got %d, expected %d", len(keys), s.numKeys),
		}
	}

	keyStr := makeKeyString(keys)
	s.keys[keyStr] = keys

	// Cache the resource
	s.cache[keyStr] = &cacheEntry{
		resource:  resource,
		expiresAt: time.Now().Add(s.cacheTTL),
	}

	return nil
}

// Update modifies an existing resource or adds it if it doesn't exist.
func (s *CachedStore) Update(resource interface{}, keys []string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if len(keys) != s.numKeys {
		return &StoreError{
			Operation: "update",
			Keys:      keys,
			Err:       fmt.Errorf("wrong number of keys: got %d, expected %d", len(keys), s.numKeys),
		}
	}

	keyStr := makeKeyString(keys)
	s.keys[keyStr] = keys

	// Invalidate cache entry (will be refetched on next access)
	delete(s.cache, keyStr)

	return nil
}

// Delete removes a resource from the store.
func (s *CachedStore) Delete(keys ...string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if len(keys) != s.numKeys {
		return &StoreError{
			Operation: "delete",
			Keys:      keys,
			Err:       fmt.Errorf("wrong number of keys: got %d, expected %d", len(keys), s.numKeys),
		}
	}

	keyStr := makeKeyString(keys)
	delete(s.keys, keyStr)
	delete(s.cache, keyStr)

	return nil
}

// Clear removes all resources from the store.
func (s *CachedStore) Clear() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.keys = make(map[string][]string)
	s.cache = make(map[string]*cacheEntry)

	return nil
}

// fetchResource fetches a resource from cache or API.
func (s *CachedStore) fetchResource(keys []string) (interface{}, error) {
	keyStr := makeKeyString(keys)

	// Check cache first
	s.mu.RLock()
	entry, ok := s.cache[keyStr]
	s.mu.RUnlock()

	if ok && time.Now().Before(entry.expiresAt) {
		// Cache hit
		return entry.resource, nil
	}

	// Cache miss - fetch from API
	// Assumes keys are [namespace, name] or just [name] for cluster-scoped resources
	var resource *unstructured.Unstructured
	var err error

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if s.namespace != "" || len(keys) >= 2 {
		// Namespaced resource
		ns := s.namespace
		if ns == "" && len(keys) >= 2 {
			ns = keys[0]
		}
		name := keys[len(keys)-1]
		resource, err = s.client.Resource(s.gvr).Namespace(ns).Get(ctx, name, metav1.GetOptions{})
	} else {
		// Cluster-scoped resource
		name := keys[0]
		resource, err = s.client.Resource(s.gvr).Get(ctx, name, metav1.GetOptions{})
	}

	if err != nil {
		return nil, &StoreError{
			Operation: "fetch",
			Keys:      keys,
			Err:       err,
		}
	}

	// Process resource (field filtering)
	if err := s.indexer.FilterFields(resource); err != nil {
		return nil, &StoreError{
			Operation: "process",
			Keys:      keys,
			Err:       err,
		}
	}

	// Update cache
	s.mu.Lock()
	s.cache[keyStr] = &cacheEntry{
		resource:  resource,
		expiresAt: time.Now().Add(s.cacheTTL),
	}
	s.mu.Unlock()

	return resource, nil
}

// Size returns the number of tracked resources in the store.
func (s *CachedStore) Size() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return len(s.keys)
}

// CacheSize returns the number of cached resources.
func (s *CachedStore) CacheSize() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return len(s.cache)
}

// EvictExpired removes expired cache entries.
func (s *CachedStore) EvictExpired() int {
	s.mu.Lock()
	defer s.mu.Unlock()

	now := time.Now()
	evicted := 0

	for key, entry := range s.cache {
		if now.After(entry.expiresAt) {
			delete(s.cache, key)
			evicted++
		}
	}

	return evicted
}

// Ensure CachedStore implements types.Store interface.
var _ types.Store = (*CachedStore)(nil)
