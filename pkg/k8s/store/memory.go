package store

import (
	"fmt"
	"sync"

	"haproxy-template-ic/pkg/k8s/types"
)

// MemoryStore stores complete Kubernetes resources in memory using nested maps.
//
// This provides O(1) lookup performance at the cost of higher memory usage.
// Resources are stored with their full specification after field filtering.
//
// Thread-safe for concurrent access.
type MemoryStore struct {
	mu       sync.RWMutex
	data     map[string]interface{} // Flat map: composite key -> resource
	numKeys  int                    // Number of index keys
	allItems []interface{}          // Cache of all items for List()
	dirty    bool                   // True if allItems needs rebuilding
}

// NewMemoryStore creates a new memory-backed store.
//
// Parameters:
//   - numKeys: Number of index keys (must match indexer configuration)
func NewMemoryStore(numKeys int) *MemoryStore {
	if numKeys < 1 {
		numKeys = 1
	}

	return &MemoryStore{
		data:     make(map[string]interface{}),
		numKeys:  numKeys,
		allItems: make([]interface{}, 0),
		dirty:    false,
	}
}

// Get retrieves all resources matching the provided index keys.
func (s *MemoryStore) Get(keys ...string) ([]interface{}, error) {
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

	// Exact match: return single item
	if len(keys) == s.numKeys {
		keyStr := makeKeyString(keys)
		if item, ok := s.data[keyStr]; ok {
			return []interface{}{item}, nil
		}
		return []interface{}{}, nil
	}

	// Partial match: return all matching items
	prefix := makeKeyString(keys) + "/"
	var results []interface{}

	for key, item := range s.data {
		// Check if key starts with prefix
		if len(key) >= len(prefix) && key[:len(prefix)] == prefix {
			results = append(results, item)
		}
	}

	return results, nil
}

// List returns all resources in the store.
func (s *MemoryStore) List() ([]interface{}, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	// Return cached list if not dirty
	if !s.dirty && s.allItems != nil {
		return s.allItems, nil
	}

	// Rebuild cache
	s.mu.RUnlock()
	s.mu.Lock()
	defer func() {
		s.mu.Unlock()
		s.mu.RLock()
	}()

	// Double-check after acquiring write lock
	if !s.dirty && s.allItems != nil {
		return s.allItems, nil
	}

	items := make([]interface{}, 0, len(s.data))
	for _, item := range s.data {
		items = append(items, item)
	}

	s.allItems = items
	s.dirty = false

	return items, nil
}

// Add inserts a new resource into the store.
func (s *MemoryStore) Add(resource interface{}, keys []string) error {
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
	s.data[keyStr] = resource
	s.dirty = true

	return nil
}

// Update modifies an existing resource or adds it if it doesn't exist.
func (s *MemoryStore) Update(resource interface{}, keys []string) error {
	// Update is identical to Add for memory store
	return s.Add(resource, keys)
}

// Delete removes a resource from the store.
func (s *MemoryStore) Delete(keys ...string) error {
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
	if _, ok := s.data[keyStr]; ok {
		delete(s.data, keyStr)
		s.dirty = true
	}

	return nil
}

// Clear removes all resources from the store.
func (s *MemoryStore) Clear() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.data = make(map[string]interface{})
	s.allItems = make([]interface{}, 0)
	s.dirty = false

	return nil
}

// Size returns the number of resources in the store.
func (s *MemoryStore) Size() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return len(s.data)
}

// Ensure MemoryStore implements types.Store interface.
var _ types.Store = (*MemoryStore)(nil)
