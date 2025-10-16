package store

import (
	"testing"
)

// TestNewMemoryStore verifies store creation.
func TestNewMemoryStore(t *testing.T) {
	store := NewMemoryStore(2)
	if store == nil {
		t.Fatal("NewMemoryStore returned nil")
	}

	if store.Size() != 0 {
		t.Errorf("expected size 0, got %d", store.Size())
	}
}

// TestMemoryStore_AddAndGet verifies adding and retrieving resources.
func TestMemoryStore_AddAndGet(t *testing.T) {
	store := NewMemoryStore(2)

	resource := map[string]string{
		"name": "test-resource",
		"data": "test-data",
	}

	// Add resource
	err := store.Add(resource, []string{"default", "test-resource"})
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}

	// Verify size
	if store.Size() != 1 {
		t.Errorf("expected size 1, got %d", store.Size())
	}

	// Get resource with exact match
	results, err := store.Get("default", "test-resource")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}

	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}

	retrieved := results[0].(map[string]string)
	if retrieved["name"] != "test-resource" {
		t.Errorf("unexpected resource: %v", retrieved)
	}
}

// TestMemoryStore_PartialMatch verifies partial key matching.
func TestMemoryStore_PartialMatch(t *testing.T) {
	store := NewMemoryStore(2)

	// Add multiple resources in same namespace
	resources := []struct {
		keys []string
		name string
	}{
		{[]string{"default", "resource-1"}, "resource-1"},
		{[]string{"default", "resource-2"}, "resource-2"},
		{[]string{"kube-system", "resource-3"}, "resource-3"},
	}

	for _, r := range resources {
		resource := map[string]string{"name": r.name}
		if err := store.Add(resource, r.keys); err != nil {
			t.Fatalf("Add failed: %v", err)
		}
	}

	// Get all resources in "default" namespace
	results, err := store.Get("default")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}

	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}
}

// TestMemoryStore_Update verifies resource updates.
func TestMemoryStore_Update(t *testing.T) {
	store := NewMemoryStore(2)

	resource := map[string]string{"version": "v1"}
	keys := []string{"default", "test"}

	// Add resource
	if err := store.Add(resource, keys); err != nil {
		t.Fatalf("Add failed: %v", err)
	}

	// Update resource
	updatedResource := map[string]string{"version": "v2"}
	if err := store.Update(updatedResource, keys); err != nil {
		t.Fatalf("Update failed: %v", err)
	}

	// Verify update
	results, err := store.Get(keys...)
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}

	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}

	retrieved := results[0].(map[string]string)
	if retrieved["version"] != "v2" {
		t.Errorf("expected version='v2', got %q", retrieved["version"])
	}
}

// TestMemoryStore_Delete verifies resource deletion.
func TestMemoryStore_Delete(t *testing.T) {
	store := NewMemoryStore(2)

	resource := map[string]string{"name": "test"}
	keys := []string{"default", "test"}

	// Add resource
	if err := store.Add(resource, keys); err != nil {
		t.Fatalf("Add failed: %v", err)
	}

	// Verify exists
	if store.Size() != 1 {
		t.Errorf("expected size 1, got %d", store.Size())
	}

	// Delete resource
	if err := store.Delete(keys...); err != nil {
		t.Fatalf("Delete failed: %v", err)
	}

	// Verify deleted
	if store.Size() != 0 {
		t.Errorf("expected size 0, got %d", store.Size())
	}

	// Verify not found
	results, err := store.Get(keys...)
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}

	if len(results) != 0 {
		t.Errorf("expected 0 results after delete, got %d", len(results))
	}
}

// TestMemoryStore_List verifies listing all resources.
func TestMemoryStore_List(t *testing.T) {
	store := NewMemoryStore(2)

	// Add multiple resources
	for i := 0; i < 5; i++ {
		resource := map[string]int{"index": i}
		keys := []string{"default", string(rune('a' + i))}
		if err := store.Add(resource, keys); err != nil {
			t.Fatalf("Add failed: %v", err)
		}
	}

	// List all
	results, err := store.List()
	if err != nil {
		t.Fatalf("List failed: %v", err)
	}

	if len(results) != 5 {
		t.Errorf("expected 5 results, got %d", len(results))
	}
}

// TestMemoryStore_Clear verifies clearing the store.
func TestMemoryStore_Clear(t *testing.T) {
	store := NewMemoryStore(2)

	// Add resources
	for i := 0; i < 3; i++ {
		resource := map[string]int{"index": i}
		keys := []string{"default", string(rune('a' + i))}
		if err := store.Add(resource, keys); err != nil {
			t.Fatalf("Add failed: %v", err)
		}
	}

	// Verify size
	if store.Size() != 3 {
		t.Errorf("expected size 3, got %d", store.Size())
	}

	// Clear
	if err := store.Clear(); err != nil {
		t.Fatalf("Clear failed: %v", err)
	}

	// Verify empty
	if store.Size() != 0 {
		t.Errorf("expected size 0 after clear, got %d", store.Size())
	}
}

// TestMemoryStore_WrongKeyCount verifies error on wrong key count.
func TestMemoryStore_WrongKeyCount(t *testing.T) {
	store := NewMemoryStore(2)

	resource := map[string]string{"name": "test"}

	// Try to add with wrong number of keys
	err := store.Add(resource, []string{"only-one-key"})
	if err == nil {
		t.Error("expected error for wrong key count")
	}

	// Try to delete with wrong number of keys
	err = store.Delete("only-one-key")
	if err == nil {
		t.Error("expected error for wrong key count")
	}
}
