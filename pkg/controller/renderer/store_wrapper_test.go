package renderer

import (
	"log/slog"
	"os"
	"testing"

	"haproxy-template-ic/pkg/k8s/store"

	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

// createTestResource creates a test Kubernetes resource.
func createTestResource(namespace, name string, data map[string]interface{}) *unstructured.Unstructured {
	obj := &unstructured.Unstructured{
		Object: map[string]interface{}{
			"apiVersion": "v1",
			"kind":       "ConfigMap",
			"metadata": map[string]interface{}{
				"namespace": namespace,
				"name":      name,
			},
		},
	}

	// Add additional data fields
	for k, v := range data {
		obj.Object[k] = v
	}

	return obj
}

// TestStoreWrapper_List verifies List method with caching.
func TestStoreWrapper_List(t *testing.T) {
	memStore := store.NewMemoryStore(2)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	wrapper := &StoreWrapper{
		store:        memStore,
		resourceType: "test-resource",
		logger:       logger,
	}

	// Add test resources
	resources := []*unstructured.Unstructured{
		createTestResource("default", "res-1", nil),
		createTestResource("default", "res-2", nil),
		createTestResource("kube-system", "res-3", nil),
	}

	for _, res := range resources {
		if err := memStore.Add(res, []string{res.GetNamespace(), res.GetName()}); err != nil {
			t.Fatalf("Add failed: %v", err)
		}
	}

	// First call to List - should unwrap and cache
	results := wrapper.List()
	if len(results) != 3 {
		t.Fatalf("expected 3 results, got %d", len(results))
	}

	// Verify results are unwrapped maps
	for _, res := range results {
		m, ok := res.(map[string]interface{})
		if !ok {
			t.Errorf("expected map[string]interface{}, got %T", res)
			continue
		}

		// Verify we can access fields
		metadata, ok := m["metadata"].(map[string]interface{})
		if !ok {
			t.Error("expected metadata to be accessible")
		}

		if _, ok := metadata["name"]; !ok {
			t.Error("expected name field in metadata")
		}
	}

	// Second call to List - should return cached result
	cachedResults := wrapper.List()
	if len(cachedResults) != 3 {
		t.Fatalf("expected 3 cached results, got %d", len(cachedResults))
	}

	// Verify it's the same slice reference (cached)
	if &results[0] != &cachedResults[0] {
		t.Error("expected List to return cached slice")
	}
}

// TestStoreWrapper_Fetch verifies Fetch method with non-unique keys.
func TestStoreWrapper_Fetch(t *testing.T) {
	memStore := store.NewMemoryStore(1) // Index by single key
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	wrapper := &StoreWrapper{
		store:        memStore,
		resourceType: "endpoint-slice",
		logger:       logger,
	}

	// Add multiple resources with the same index key (service name)
	resources := []*unstructured.Unstructured{
		createTestResource("default", "nginx-slice-1", map[string]interface{}{
			"endpoints": []string{"10.0.0.1:80"},
		}),
		createTestResource("default", "nginx-slice-2", map[string]interface{}{
			"endpoints": []string{"10.0.0.2:80"},
		}),
		createTestResource("default", "nginx-slice-3", map[string]interface{}{
			"endpoints": []string{"10.0.0.3:80"},
		}),
	}

	for _, res := range resources {
		if err := memStore.Add(res, []string{"nginx"}); err != nil {
			t.Fatalf("Add failed: %v", err)
		}
	}

	// Fetch all EndpointSlices for the "nginx" service
	results := wrapper.Fetch("nginx")
	if len(results) != 3 {
		t.Fatalf("expected 3 results, got %d", len(results))
	}

	// Verify all results are unwrapped
	names := make(map[string]bool)
	for _, res := range results {
		m, ok := res.(map[string]interface{})
		if !ok {
			t.Errorf("expected map[string]interface{}, got %T", res)
			continue
		}

		metadata := m["metadata"].(map[string]interface{})
		name := metadata["name"].(string)
		names[name] = true
	}

	expectedNames := []string{"nginx-slice-1", "nginx-slice-2", "nginx-slice-3"}
	for _, expectedName := range expectedNames {
		if !names[expectedName] {
			t.Errorf("expected to find resource %q in Fetch results", expectedName)
		}
	}
}

// TestStoreWrapper_Fetch_Empty verifies Fetch returns empty slice when no matches.
func TestStoreWrapper_Fetch_Empty(t *testing.T) {
	memStore := store.NewMemoryStore(1)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	wrapper := &StoreWrapper{
		store:        memStore,
		resourceType: "test-resource",
		logger:       logger,
	}

	// Fetch with no matching resources
	results := wrapper.Fetch("nonexistent")
	if len(results) != 0 {
		t.Errorf("expected empty slice, got %d results", len(results))
	}
}

// TestStoreWrapper_GetSingle verifies GetSingle returns single resource.
func TestStoreWrapper_GetSingle(t *testing.T) {
	memStore := store.NewMemoryStore(2)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	wrapper := &StoreWrapper{
		store:        memStore,
		resourceType: "ingress",
		logger:       logger,
	}

	// Add single resource
	resource := createTestResource("default", "my-ingress", map[string]interface{}{
		"spec": map[string]interface{}{
			"rules": []interface{}{},
		},
	})

	if err := memStore.Add(resource, []string{"default", "my-ingress"}); err != nil {
		t.Fatalf("Add failed: %v", err)
	}

	// GetSingle should return the resource
	result := wrapper.GetSingle("default", "my-ingress")
	if result == nil {
		t.Fatal("expected result, got nil")
	}

	// Verify result is unwrapped
	m, ok := result.(map[string]interface{})
	if !ok {
		t.Fatalf("expected map[string]interface{}, got %T", result)
	}

	metadata := m["metadata"].(map[string]interface{})
	name := metadata["name"].(string)
	if name != "my-ingress" {
		t.Errorf("expected name 'my-ingress', got %q", name)
	}
}

// TestStoreWrapper_GetSingle_Empty verifies GetSingle returns nil when no matches.
func TestStoreWrapper_GetSingle_Empty(t *testing.T) {
	memStore := store.NewMemoryStore(2)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	wrapper := &StoreWrapper{
		store:        memStore,
		resourceType: "ingress",
		logger:       logger,
	}

	// GetSingle with no matching resources
	result := wrapper.GetSingle("default", "nonexistent")
	if result != nil {
		t.Errorf("expected nil, got %v", result)
	}
}

// TestStoreWrapper_GetSingle_MultipleResources verifies GetSingle returns nil
// and logs error when multiple resources match.
func TestStoreWrapper_GetSingle_MultipleResources(t *testing.T) {
	memStore := store.NewMemoryStore(1) // Index by single key
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	wrapper := &StoreWrapper{
		store:        memStore,
		resourceType: "endpoint-slice",
		logger:       logger,
	}

	// Add multiple resources with the same index key
	resources := []*unstructured.Unstructured{
		createTestResource("default", "nginx-slice-1", nil),
		createTestResource("default", "nginx-slice-2", nil),
	}

	for _, res := range resources {
		if err := memStore.Add(res, []string{"nginx"}); err != nil {
			t.Fatalf("Add failed: %v", err)
		}
	}

	// GetSingle should return nil when multiple resources match (ambiguous)
	result := wrapper.GetSingle("nginx")
	if result != nil {
		t.Errorf("expected nil for ambiguous lookup, got %v", result)
	}
}

// TestStoreWrapper_List_WithErrors verifies List handles store errors gracefully.
func TestStoreWrapper_List_WithErrors(t *testing.T) {
	// Create a mock store that returns an error
	mockStore := &mockStoreWithError{returnError: true}
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	wrapper := &StoreWrapper{
		store:        mockStore,
		resourceType: "test-resource",
		logger:       logger,
	}

	// List should return empty slice on error
	results := wrapper.List()
	if len(results) != 0 {
		t.Errorf("expected empty slice on error, got %d results", len(results))
	}
}

// TestStoreWrapper_Fetch_WithErrors verifies Fetch handles store errors gracefully.
func TestStoreWrapper_Fetch_WithErrors(t *testing.T) {
	mockStore := &mockStoreWithError{returnError: true}
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	wrapper := &StoreWrapper{
		store:        mockStore,
		resourceType: "test-resource",
		logger:       logger,
	}

	// Fetch should return empty slice on error
	results := wrapper.Fetch("test")
	if len(results) != 0 {
		t.Errorf("expected empty slice on error, got %d results", len(results))
	}
}

// TestStoreWrapper_GetSingle_WithErrors verifies GetSingle handles store errors gracefully.
func TestStoreWrapper_GetSingle_WithErrors(t *testing.T) {
	mockStore := &mockStoreWithError{returnError: true}
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	wrapper := &StoreWrapper{
		store:        mockStore,
		resourceType: "test-resource",
		logger:       logger,
	}

	// GetSingle should return nil on error
	result := wrapper.GetSingle("test")
	if result != nil {
		t.Errorf("expected nil on error, got %v", result)
	}
}

// TestStoreWrapper_List_Caching verifies List caching behavior.
func TestStoreWrapper_List_Caching(t *testing.T) {
	memStore := store.NewMemoryStore(2)
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelError}))

	wrapper := &StoreWrapper{
		store:        memStore,
		resourceType: "test-resource",
		logger:       logger,
	}

	// Add resource
	resource := createTestResource("default", "res-1", nil)
	if err := memStore.Add(resource, []string{"default", "res-1"}); err != nil {
		t.Fatalf("Add failed: %v", err)
	}

	// First List call - caches result
	results1 := wrapper.List()
	if len(results1) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results1))
	}

	// Add another resource to the store
	resource2 := createTestResource("default", "res-2", nil)
	if err := memStore.Add(resource2, []string{"default", "res-2"}); err != nil {
		t.Fatalf("Add failed: %v", err)
	}

	// Second List call - should still return cached result (1 resource)
	results2 := wrapper.List()
	if len(results2) != 1 {
		t.Errorf("expected cached result with 1 resource, got %d", len(results2))
	}

	// Verify it's the same cached slice
	if &results1[0] != &results2[0] {
		t.Error("expected List to return the same cached slice")
	}
}

// mockStoreWithError is a mock store that can return errors for testing.
type mockStoreWithError struct {
	returnError bool
}

func (m *mockStoreWithError) Get(keys ...string) ([]interface{}, error) {
	if m.returnError {
		return nil, &store.StoreError{
			Operation: "get",
			Keys:      keys,
			Err:       nil,
		}
	}
	return []interface{}{}, nil
}

func (m *mockStoreWithError) List() ([]interface{}, error) {
	if m.returnError {
		return nil, &store.StoreError{
			Operation: "list",
			Err:       nil,
		}
	}
	return []interface{}{}, nil
}

func (m *mockStoreWithError) Add(resource interface{}, keys []string) error {
	return nil
}

func (m *mockStoreWithError) Update(resource interface{}, keys []string) error {
	return nil
}

func (m *mockStoreWithError) Delete(keys ...string) error {
	return nil
}

func (m *mockStoreWithError) Clear() error {
	return nil
}

func (m *mockStoreWithError) Size() int {
	return 0
}
