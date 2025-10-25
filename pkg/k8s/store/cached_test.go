package store

import (
	"testing"
	"time"

	"haproxy-template-ic/pkg/k8s/indexer"

	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/client-go/dynamic/fake"
)

// createTestIndexer creates a minimal indexer for testing.
func createTestIndexer() *indexer.Indexer {
	return &indexer.Indexer{}
}

// createTestResource creates a test resource with metadata.
func createTestResource(namespace, name string) *unstructured.Unstructured {
	return &unstructured.Unstructured{
		Object: map[string]interface{}{
			"apiVersion": "v1",
			"kind":       "ConfigMap",
			"metadata": map[string]interface{}{
				"namespace": namespace,
				"name":      name,
			},
			"data": map[string]interface{}{
				"key": "value",
			},
		},
	}
}

// TestNewCachedStore verifies store creation.
func TestNewCachedStore(t *testing.T) {
	scheme := runtime.NewScheme()
	client := fake.NewSimpleDynamicClient(scheme)
	indexer := createTestIndexer()

	gvr := schema.GroupVersionResource{
		Group:    "",
		Version:  "v1",
		Resource: "configmaps",
	}

	cfg := &CachedStoreConfig{
		NumKeys:   2,
		CacheTTL:  5 * time.Minute,
		Client:    client,
		GVR:       gvr,
		Namespace: "",
		Indexer:   indexer,
	}

	store, err := NewCachedStore(cfg)
	if err != nil {
		t.Fatalf("NewCachedStore failed: %v", err)
	}

	if store == nil {
		t.Fatal("NewCachedStore returned nil")
	}

	if store.Size() != 0 {
		t.Errorf("expected size 0, got %d", store.Size())
	}
}

// TestNewCachedStore_Errors verifies error handling in store creation.
func TestNewCachedStore_Errors(t *testing.T) {
	scheme := runtime.NewScheme()
	client := fake.NewSimpleDynamicClient(scheme)
	indexer := createTestIndexer()
	gvr := schema.GroupVersionResource{Group: "", Version: "v1", Resource: "configmaps"}

	tests := []struct {
		name    string
		cfg     *CachedStoreConfig
		wantErr bool
	}{
		{
			name: "missing numKeys",
			cfg: &CachedStoreConfig{
				NumKeys:  0,
				Client:   client,
				GVR:      gvr,
				Indexer:  indexer,
				CacheTTL: 5 * time.Minute,
			},
			wantErr: true,
		},
		{
			name: "missing client",
			cfg: &CachedStoreConfig{
				NumKeys:  2,
				Client:   nil,
				GVR:      gvr,
				Indexer:  indexer,
				CacheTTL: 5 * time.Minute,
			},
			wantErr: true,
		},
		{
			name: "missing indexer",
			cfg: &CachedStoreConfig{
				NumKeys:  2,
				Client:   client,
				GVR:      gvr,
				Indexer:  nil,
				CacheTTL: 5 * time.Minute,
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := NewCachedStore(tt.cfg)
			if (err != nil) != tt.wantErr {
				t.Errorf("NewCachedStore() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

// TestCachedStore_AddAndGet verifies adding and retrieving resources.
func TestCachedStore_AddAndGet(t *testing.T) {
	scheme := runtime.NewScheme()
	resource := createTestResource("default", "test-cm")

	client := fake.NewSimpleDynamicClient(scheme, resource)
	indexer := createTestIndexer()

	gvr := schema.GroupVersionResource{
		Group:    "",
		Version:  "v1",
		Resource: "configmaps",
	}

	cfg := &CachedStoreConfig{
		NumKeys:   2,
		CacheTTL:  5 * time.Minute,
		Client:    client,
		GVR:       gvr,
		Namespace: "",
		Indexer:   indexer,
	}

	store, err := NewCachedStore(cfg)
	if err != nil {
		t.Fatalf("NewCachedStore failed: %v", err)
	}

	// Add resource
	err = store.Add(resource, []string{"default", "test-cm"})
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}

	// Verify size
	if store.Size() != 1 {
		t.Errorf("expected size 1, got %d", store.Size())
	}

	// Get resource (should hit cache)
	results, err := store.Get("default", "test-cm")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}

	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}

	retrieved := results[0].(*unstructured.Unstructured)
	if retrieved.GetName() != "test-cm" {
		t.Errorf("expected name 'test-cm', got %q", retrieved.GetName())
	}
}

// TestCachedStore_NonUniqueKeys verifies multiple resources with same index keys.
func TestCachedStore_NonUniqueKeys(t *testing.T) {
	scheme := runtime.NewScheme()

	// Create multiple resources with the same service label
	resources := []*unstructured.Unstructured{
		createTestResource("default", "nginx-slice-1"),
		createTestResource("default", "nginx-slice-2"),
		createTestResource("default", "nginx-slice-3"),
	}

	client := fake.NewSimpleDynamicClient(scheme, resources[0], resources[1], resources[2])
	indexer := createTestIndexer()

	gvr := schema.GroupVersionResource{
		Group:    "",
		Version:  "v1",
		Resource: "configmaps",
	}

	cfg := &CachedStoreConfig{
		NumKeys:   1, // Index by service name only
		CacheTTL:  5 * time.Minute,
		Client:    client,
		GVR:       gvr,
		Namespace: "",
		Indexer:   indexer,
	}

	store, err := NewCachedStore(cfg)
	if err != nil {
		t.Fatalf("NewCachedStore failed: %v", err)
	}

	// Add all resources with the same index key
	for _, res := range resources {
		if err := store.Add(res, []string{"nginx"}); err != nil {
			t.Fatalf("Add failed: %v", err)
		}
	}

	// Verify all 3 resources are tracked
	if store.Size() != 3 {
		t.Errorf("expected size 3, got %d", store.Size())
	}

	// Get should return all resources with the same index key
	results, err := store.Get("nginx")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}

	if len(results) != 3 {
		t.Fatalf("expected 3 results, got %d", len(results))
	}

	// Verify we got all three resources
	names := make(map[string]bool)
	for _, res := range results {
		r := res.(*unstructured.Unstructured)
		names[r.GetName()] = true
	}

	expectedNames := []string{"nginx-slice-1", "nginx-slice-2", "nginx-slice-3"}
	for _, expectedName := range expectedNames {
		if !names[expectedName] {
			t.Errorf("expected to find resource %q in results", expectedName)
		}
	}
}

// TestCachedStore_UpdateWithNonUniqueKeys verifies updating specific resource.
func TestCachedStore_UpdateWithNonUniqueKeys(t *testing.T) {
	scheme := runtime.NewScheme()

	slice1 := createTestResource("default", "nginx-slice-1")
	slice1.Object["version"] = "v1"

	slice2 := createTestResource("default", "nginx-slice-2")
	slice2.Object["version"] = "v1"

	client := fake.NewSimpleDynamicClient(scheme, slice1, slice2)
	indexer := createTestIndexer()

	gvr := schema.GroupVersionResource{
		Group:    "",
		Version:  "v1",
		Resource: "configmaps",
	}

	cfg := &CachedStoreConfig{
		NumKeys:   1,
		CacheTTL:  5 * time.Minute,
		Client:    client,
		GVR:       gvr,
		Namespace: "",
		Indexer:   indexer,
	}

	store, err := NewCachedStore(cfg)
	if err != nil {
		t.Fatalf("NewCachedStore failed: %v", err)
	}

	// Add both resources
	if err := store.Add(slice1, []string{"nginx"}); err != nil {
		t.Fatalf("Add slice1 failed: %v", err)
	}
	if err := store.Add(slice2, []string{"nginx"}); err != nil {
		t.Fatalf("Add slice2 failed: %v", err)
	}

	// Update slice1 specifically
	updatedSlice1 := createTestResource("default", "nginx-slice-1")
	updatedSlice1.Object["version"] = "v2"

	if err := store.Update(updatedSlice1, []string{"nginx"}); err != nil {
		t.Fatalf("Update failed: %v", err)
	}

	// Verify both resources still tracked
	if store.Size() != 2 {
		t.Errorf("expected size 2 after update, got %d", store.Size())
	}

	// Get all resources
	results, err := store.Get("nginx")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}

	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}

	// Find slice1 and verify it was updated (cache should have v2)
	var foundSlice1 *unstructured.Unstructured
	for _, res := range results {
		r := res.(*unstructured.Unstructured)
		if r.GetName() == "nginx-slice-1" {
			foundSlice1 = r
			break
		}
	}

	if foundSlice1 == nil {
		t.Fatal("slice1 not found after update")
	}

	if foundSlice1.Object["version"] != "v2" {
		t.Errorf("slice1 version: expected 'v2', got %v", foundSlice1.Object["version"])
	}
}

// TestCachedStore_DeleteWithNonUniqueKeys verifies Delete removes all matching resources.
func TestCachedStore_DeleteWithNonUniqueKeys(t *testing.T) {
	scheme := runtime.NewScheme()

	slice1 := createTestResource("default", "nginx-slice-1")
	slice2 := createTestResource("default", "nginx-slice-2")

	client := fake.NewSimpleDynamicClient(scheme, slice1, slice2)
	indexer := createTestIndexer()

	gvr := schema.GroupVersionResource{
		Group:    "",
		Version:  "v1",
		Resource: "configmaps",
	}

	cfg := &CachedStoreConfig{
		NumKeys:   1,
		CacheTTL:  5 * time.Minute,
		Client:    client,
		GVR:       gvr,
		Namespace: "",
		Indexer:   indexer,
	}

	store, err := NewCachedStore(cfg)
	if err != nil {
		t.Fatalf("NewCachedStore failed: %v", err)
	}

	// Add resources
	if err := store.Add(slice1, []string{"nginx"}); err != nil {
		t.Fatalf("Add slice1 failed: %v", err)
	}
	if err := store.Add(slice2, []string{"nginx"}); err != nil {
		t.Fatalf("Add slice2 failed: %v", err)
	}

	// Verify both exist
	if store.Size() != 2 {
		t.Errorf("expected size 2 before delete, got %d", store.Size())
	}

	// Delete all resources with this index key
	if err := store.Delete("nginx"); err != nil {
		t.Fatalf("Delete failed: %v", err)
	}

	// Verify ALL resources were deleted
	if store.Size() != 0 {
		t.Errorf("expected size 0 after delete, got %d", store.Size())
	}

	// Verify cache was cleared
	if store.CacheSize() != 0 {
		t.Errorf("expected cache size 0 after delete, got %d", store.CacheSize())
	}

	results, err := store.Get("nginx")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}

	if len(results) != 0 {
		t.Errorf("expected 0 results after delete, got %d", len(results))
	}
}

// TestCachedStore_List verifies listing all resources.
func TestCachedStore_List(t *testing.T) {
	scheme := runtime.NewScheme()

	// Create resources for two different services
	resources := []*unstructured.Unstructured{
		createTestResource("default", "nginx-slice-1"),
		createTestResource("default", "nginx-slice-2"),
		createTestResource("default", "apache-slice-1"),
	}

	client := fake.NewSimpleDynamicClient(scheme, resources[0], resources[1], resources[2])
	indexer := createTestIndexer()

	gvr := schema.GroupVersionResource{
		Group:    "",
		Version:  "v1",
		Resource: "configmaps",
	}

	cfg := &CachedStoreConfig{
		NumKeys:   1,
		CacheTTL:  5 * time.Minute,
		Client:    client,
		GVR:       gvr,
		Namespace: "",
		Indexer:   indexer,
	}

	store, err := NewCachedStore(cfg)
	if err != nil {
		t.Fatalf("NewCachedStore failed: %v", err)
	}

	// Add resources with different index keys
	if err := store.Add(resources[0], []string{"nginx"}); err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	if err := store.Add(resources[1], []string{"nginx"}); err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	if err := store.Add(resources[2], []string{"apache"}); err != nil {
		t.Fatalf("Add failed: %v", err)
	}

	// List should return all resources
	results, err := store.List()
	if err != nil {
		t.Fatalf("List failed: %v", err)
	}

	if len(results) != 3 {
		t.Fatalf("expected 3 results, got %d", len(results))
	}

	// Verify all resource names are present
	names := make(map[string]bool)
	for _, res := range results {
		r := res.(*unstructured.Unstructured)
		names[r.GetName()] = true
	}

	expectedNames := []string{"nginx-slice-1", "nginx-slice-2", "apache-slice-1"}
	for _, expectedName := range expectedNames {
		if !names[expectedName] {
			t.Errorf("expected to find resource %q in List results", expectedName)
		}
	}
}

// TestCachedStore_CacheTTL verifies cache expiration.
func TestCachedStore_CacheTTL(t *testing.T) {
	scheme := runtime.NewScheme()
	resource := createTestResource("default", "test-cm")

	client := fake.NewSimpleDynamicClient(scheme, resource)
	indexer := createTestIndexer()

	gvr := schema.GroupVersionResource{
		Group:    "",
		Version:  "v1",
		Resource: "configmaps",
	}

	cfg := &CachedStoreConfig{
		NumKeys:   2,
		CacheTTL:  100 * time.Millisecond, // Very short TTL for testing
		Client:    client,
		GVR:       gvr,
		Namespace: "",
		Indexer:   indexer,
	}

	store, err := NewCachedStore(cfg)
	if err != nil {
		t.Fatalf("NewCachedStore failed: %v", err)
	}

	// Add resource (caches it)
	if err := store.Add(resource, []string{"default", "test-cm"}); err != nil {
		t.Fatalf("Add failed: %v", err)
	}

	// Verify cached
	if store.CacheSize() != 1 {
		t.Errorf("expected cache size 1, got %d", store.CacheSize())
	}

	// Wait for TTL expiration
	time.Sleep(150 * time.Millisecond)

	// Evict expired entries
	evicted := store.EvictExpired()
	if evicted != 1 {
		t.Errorf("expected 1 evicted entry, got %d", evicted)
	}

	if store.CacheSize() != 0 {
		t.Errorf("expected cache size 0 after eviction, got %d", store.CacheSize())
	}
}

// TestCachedStore_Clear verifies clearing the store.
func TestCachedStore_Clear(t *testing.T) {
	scheme := runtime.NewScheme()

	resources := []*unstructured.Unstructured{
		createTestResource("default", "cm-1"),
		createTestResource("default", "cm-2"),
	}

	client := fake.NewSimpleDynamicClient(scheme, resources[0], resources[1])
	indexer := createTestIndexer()

	gvr := schema.GroupVersionResource{
		Group:    "",
		Version:  "v1",
		Resource: "configmaps",
	}

	cfg := &CachedStoreConfig{
		NumKeys:   2,
		CacheTTL:  5 * time.Minute,
		Client:    client,
		GVR:       gvr,
		Namespace: "",
		Indexer:   indexer,
	}

	store, err := NewCachedStore(cfg)
	if err != nil {
		t.Fatalf("NewCachedStore failed: %v", err)
	}

	// Add resources
	for _, res := range resources {
		if err := store.Add(res, []string{"default", res.GetName()}); err != nil {
			t.Fatalf("Add failed: %v", err)
		}
	}

	// Verify size
	if store.Size() != 2 {
		t.Errorf("expected size 2, got %d", store.Size())
	}

	// Clear
	if err := store.Clear(); err != nil {
		t.Fatalf("Clear failed: %v", err)
	}

	// Verify empty
	if store.Size() != 0 {
		t.Errorf("expected size 0 after clear, got %d", store.Size())
	}

	if store.CacheSize() != 0 {
		t.Errorf("expected cache size 0 after clear, got %d", store.CacheSize())
	}
}

// TestCachedStore_PartialMatch verifies partial key matching.
func TestCachedStore_PartialMatch(t *testing.T) {
	scheme := runtime.NewScheme()

	// Create resources in different namespaces
	resources := []*unstructured.Unstructured{
		createTestResource("default", "cm-1"),
		createTestResource("default", "cm-2"),
		createTestResource("kube-system", "cm-3"),
	}

	client := fake.NewSimpleDynamicClient(scheme, resources[0], resources[1], resources[2])
	indexer := createTestIndexer()

	gvr := schema.GroupVersionResource{
		Group:    "",
		Version:  "v1",
		Resource: "configmaps",
	}

	cfg := &CachedStoreConfig{
		NumKeys:   2,
		CacheTTL:  5 * time.Minute,
		Client:    client,
		GVR:       gvr,
		Namespace: "",
		Indexer:   indexer,
	}

	store, err := NewCachedStore(cfg)
	if err != nil {
		t.Fatalf("NewCachedStore failed: %v", err)
	}

	// Add resources
	for _, res := range resources {
		if err := store.Add(res, []string{res.GetNamespace(), res.GetName()}); err != nil {
			t.Fatalf("Add failed: %v", err)
		}
	}

	// Get all resources in "default" namespace (partial match)
	results, err := store.Get("default")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}

	if len(results) != 2 {
		t.Fatalf("expected 2 results for 'default' namespace, got %d", len(results))
	}

	// Verify both are from default namespace
	for _, res := range results {
		r := res.(*unstructured.Unstructured)
		if r.GetNamespace() != "default" {
			t.Errorf("expected namespace 'default', got %q", r.GetNamespace())
		}
	}
}

// TestCachedStore_TTLReset verifies that TTL is reset on cache hits.
func TestCachedStore_TTLReset(t *testing.T) {
	scheme := runtime.NewScheme()
	resource := createTestResource("default", "test-cm")

	client := fake.NewSimpleDynamicClient(scheme, resource)
	indexer := createTestIndexer()

	gvr := schema.GroupVersionResource{
		Group:    "",
		Version:  "v1",
		Resource: "configmaps",
	}

	// Short TTL for testing
	cacheTTL := 200 * time.Millisecond

	cfg := &CachedStoreConfig{
		NumKeys:   2,
		CacheTTL:  cacheTTL,
		Client:    client,
		GVR:       gvr,
		Namespace: "",
		Indexer:   indexer,
	}

	store, err := NewCachedStore(cfg)
	if err != nil {
		t.Fatalf("NewCachedStore failed: %v", err)
	}

	// Add resource to cache
	if err := store.Add(resource, []string{"default", "test-cm"}); err != nil {
		t.Fatalf("Add failed: %v", err)
	}

	// Record initial expiration time
	store.mu.RLock()
	initialExpiry := store.cache["default/test-cm"].expiresAt
	store.mu.RUnlock()

	// Wait a bit
	time.Sleep(50 * time.Millisecond)

	// Access resource (should reset TTL)
	results, err := store.Get("default", "test-cm")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}

	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}

	// Check that expiration time was extended
	store.mu.RLock()
	newExpiry := store.cache["default/test-cm"].expiresAt
	store.mu.RUnlock()

	if !newExpiry.After(initialExpiry) {
		t.Errorf("expiration time was not extended: initial=%v, new=%v", initialExpiry, newExpiry)
	}

	// The new expiry should be approximately cacheTTL from now
	expectedExpiry := time.Now().Add(cacheTTL)
	diff := newExpiry.Sub(expectedExpiry).Abs()
	if diff > 100*time.Millisecond {
		t.Errorf("new expiry time is not approximately cacheTTL from now: diff=%v", diff)
	}

	// Now wait for the original TTL to pass (without accessing)
	// The entry should still be cached because we reset the TTL
	time.Sleep(cacheTTL)

	// Entry should still be in cache (not expired yet)
	store.mu.RLock()
	_, ok := store.cache["default/test-cm"]
	store.mu.RUnlock()

	if !ok {
		t.Error("entry was evicted even though TTL was reset")
	}

	// Now wait for the new TTL to expire
	time.Sleep(cacheTTL + 50*time.Millisecond)

	// Evict expired entries
	evicted := store.EvictExpired()

	// Should have evicted the resource
	if evicted != 1 {
		t.Errorf("expected 1 evicted entry, got %d", evicted)
	}
}

// TestCachedStore_CacheMissLogging verifies that cache misses trigger API fetches and logging.
// This test verifies the logging infrastructure is working, but doesn't
// actually check the log output (that would require a test logger).
func TestCachedStore_CacheMissLogging(t *testing.T) {
	scheme := runtime.NewScheme()
	resource := createTestResource("default", "test-cm")

	client := fake.NewSimpleDynamicClient(scheme, resource)

	// Create a properly initialized indexer
	idx, err := indexer.New(indexer.Config{
		IndexBy:      []string{"metadata.namespace", "metadata.name"},
		IgnoreFields: []string{},
	})
	if err != nil {
		t.Fatalf("failed to create indexer: %v", err)
	}

	gvr := schema.GroupVersionResource{
		Group:    "",
		Version:  "v1",
		Resource: "configmaps",
	}

	cfg := &CachedStoreConfig{
		NumKeys:   2,
		CacheTTL:  5 * time.Minute,
		Client:    client,
		GVR:       gvr,
		Namespace: "",
		Indexer:   idx,
		// Logger is optional, will use slog.Default()
	}

	store, err := NewCachedStore(cfg)
	if err != nil {
		t.Fatalf("NewCachedStore failed: %v", err)
	}

	// Add resource reference (but not in cache)
	if err := store.Add(resource, []string{"default", "test-cm"}); err != nil {
		t.Fatalf("Add failed: %v", err)
	}

	// Clear cache to force API fetch
	store.cache = make(map[string]*cacheEntry)

	// Get resource (should fetch from API and log)
	results, err := store.Get("default", "test-cm")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}

	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}

	// Resource should now be cached
	if store.CacheSize() != 1 {
		t.Errorf("expected cache size 1 after fetch, got %d", store.CacheSize())
	}
}
