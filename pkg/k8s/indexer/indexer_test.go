package indexer

import (
	"testing"
)

// TestNew verifies indexer creation.
func TestNew(t *testing.T) {
	tests := []struct {
		name      string
		config    Config
		expectErr bool
	}{
		{
			name: "valid config",
			config: Config{
				IndexBy:      []string{"metadata.namespace", "metadata.name"},
				IgnoreFields: []string{"metadata.managedFields"},
			},
			expectErr: false,
		},
		{
			name: "empty IndexBy",
			config: Config{
				IndexBy:      []string{},
				IgnoreFields: []string{},
			},
			expectErr: true,
		},
		{
			name: "invalid JSONPath",
			config: Config{
				IndexBy: []string{"metadata.[namespace"},
			},
			expectErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := New(tt.config)
			if tt.expectErr && err == nil {
				t.Error("expected error but got nil")
			}
			if !tt.expectErr && err != nil {
				t.Errorf("unexpected error: %v", err)
			}
		})
	}
}

// TestExtractKeys verifies key extraction from resources.
func TestExtractKeys(t *testing.T) {
	indexer, err := New(Config{
		IndexBy: []string{"metadata.namespace", "metadata.name"},
	})
	if err != nil {
		t.Fatalf("failed to create indexer: %v", err)
	}

	resource := map[string]interface{}{
		"metadata": map[string]interface{}{
			"namespace": "default",
			"name":      "test-resource",
		},
	}

	keys, err := indexer.ExtractKeys(resource)
	if err != nil {
		t.Fatalf("ExtractKeys failed: %v", err)
	}

	if len(keys) != 2 {
		t.Fatalf("expected 2 keys, got %d", len(keys))
	}

	if keys[0] != "default" {
		t.Errorf("expected namespace='default', got %q", keys[0])
	}

	if keys[1] != "test-resource" {
		t.Errorf("expected name='test-resource', got %q", keys[1])
	}
}

// TestFilterFields verifies field filtering.
func TestFilterFields(t *testing.T) {
	indexer, err := New(Config{
		IndexBy:      []string{"metadata.name"},
		IgnoreFields: []string{"metadata.managedFields", "status"},
	})
	if err != nil {
		t.Fatalf("failed to create indexer: %v", err)
	}

	resource := map[string]interface{}{
		"metadata": map[string]interface{}{
			"name":          "test-resource",
			"managedFields": []interface{}{map[string]interface{}{"manager": "kubectl"}},
		},
		"spec": map[string]interface{}{
			"replicas": 3,
		},
		"status": map[string]interface{}{
			"ready": true,
		},
	}

	err = indexer.FilterFields(resource)
	if err != nil {
		t.Fatalf("FilterFields failed: %v", err)
	}

	// Verify managedFields was removed
	metadata := resource["metadata"].(map[string]interface{})
	if _, ok := metadata["managedFields"]; ok {
		t.Error("managedFields should have been removed")
	}

	// Verify status was removed
	if _, ok := resource["status"]; ok {
		t.Error("status should have been removed")
	}

	// Verify spec was preserved
	if _, ok := resource["spec"]; !ok {
		t.Error("spec should have been preserved")
	}
}

// TestProcess verifies combined filtering and key extraction.
func TestProcess(t *testing.T) {
	indexer, err := New(Config{
		IndexBy:      []string{"metadata.namespace", "metadata.name"},
		IgnoreFields: []string{"metadata.managedFields"},
	})
	if err != nil {
		t.Fatalf("failed to create indexer: %v", err)
	}

	resource := map[string]interface{}{
		"metadata": map[string]interface{}{
			"namespace":     "kube-system",
			"name":          "coredns",
			"managedFields": []interface{}{},
		},
	}

	keys, err := indexer.Process(resource)
	if err != nil {
		t.Fatalf("Process failed: %v", err)
	}

	// Verify keys were extracted correctly
	if len(keys) != 2 || keys[0] != "kube-system" || keys[1] != "coredns" {
		t.Errorf("unexpected keys: %v", keys)
	}

	// Verify managedFields was removed
	metadata := resource["metadata"].(map[string]interface{})
	if _, ok := metadata["managedFields"]; ok {
		t.Error("managedFields should have been removed")
	}
}
