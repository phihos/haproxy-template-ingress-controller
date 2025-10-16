package sections

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/codegen/dataplaneapi"
	"haproxy-template-ic/pkg/dataplane/client"
)

// PriorityCache defines priority for cache sections.
// Caches should be created early as they might be referenced by backends.
const PriorityCache = 15

// CreateCacheOperation represents creating a new cache section.
type CreateCacheOperation struct {
	Cache *models.Cache
}

// NewCreateCacheOperation creates a new cache section creation operation.
func NewCreateCacheOperation(cache *models.Cache) *CreateCacheOperation {
	return &CreateCacheOperation{
		Cache: cache,
	}
}

// Type implements Operation.Type.
func (op *CreateCacheOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateCacheOperation) Section() string {
	return "cache"
}

// Priority implements Operation.Priority.
func (op *CreateCacheOperation) Priority() int {
	return PriorityCache
}

// Execute creates the cache section via the Dataplane API.
func (op *CreateCacheOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Cache == nil {
		return fmt.Errorf("cache section is nil")
	}
	if op.Cache.Name == nil || *op.Cache.Name == "" {
		return fmt.Errorf("cache section name is empty")
	}

	apiClient := c.Client()

	// Convert models.Cache to dataplaneapi.Cache using JSON marshaling
	var apiCache dataplaneapi.Cache
	data, err := json.Marshal(op.Cache)
	if err != nil {
		return fmt.Errorf("failed to marshal cache section: %w", err)
	}
	if err := json.Unmarshal(data, &apiCache); err != nil {
		return fmt.Errorf("failed to unmarshal cache section: %w", err)
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.CreateCacheParams{}
	if transactionID != "" {
		params.TransactionId = &transactionID
	} else {
		v, err := c.GetVersion(ctx)
		if err != nil {
			return fmt.Errorf("failed to get version: %w", err)
		}
		version := int(v)
		params.Version = &version
	}

	// Call the CreateCache API
	resp, err := apiClient.CreateCache(ctx, params, apiCache)
	if err != nil {
		return fmt.Errorf("failed to create cache section '%s': %w", *op.Cache.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("cache section creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateCacheOperation) Describe() string {
	name := "unknown"
	if op.Cache.Name != nil && *op.Cache.Name != "" {
		name = *op.Cache.Name
	}
	return fmt.Sprintf("Create cache '%s'", name)
}

// DeleteCacheOperation represents deleting an existing cache section.
type DeleteCacheOperation struct {
	Cache *models.Cache
}

// NewDeleteCacheOperation creates a new cache section deletion operation.
func NewDeleteCacheOperation(cache *models.Cache) *DeleteCacheOperation {
	return &DeleteCacheOperation{
		Cache: cache,
	}
}

// Type implements Operation.Type.
func (op *DeleteCacheOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteCacheOperation) Section() string {
	return "cache"
}

// Priority implements Operation.Priority.
func (op *DeleteCacheOperation) Priority() int {
	return PriorityCache
}

// Execute deletes the cache section via the Dataplane API.
func (op *DeleteCacheOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Cache == nil {
		return fmt.Errorf("cache section is nil")
	}
	if op.Cache.Name == nil || *op.Cache.Name == "" {
		return fmt.Errorf("cache section name is empty")
	}

	apiClient := c.Client()

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.DeleteCacheParams{}
	if transactionID != "" {
		params.TransactionId = &transactionID
	} else {
		v, err := c.GetVersion(ctx)
		if err != nil {
			return fmt.Errorf("failed to get version: %w", err)
		}
		version := int(v)
		params.Version = &version
	}

	// Call the DeleteCache API
	resp, err := apiClient.DeleteCache(ctx, *op.Cache.Name, params)
	if err != nil {
		return fmt.Errorf("failed to delete cache section '%s': %w", *op.Cache.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("cache section deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteCacheOperation) Describe() string {
	name := "unknown"
	if op.Cache.Name != nil && *op.Cache.Name != "" {
		name = *op.Cache.Name
	}
	return fmt.Sprintf("Delete cache '%s'", name)
}

// UpdateCacheOperation represents updating an existing cache section.
type UpdateCacheOperation struct {
	Cache *models.Cache
}

// NewUpdateCacheOperation creates a new cache section update operation.
func NewUpdateCacheOperation(cache *models.Cache) *UpdateCacheOperation {
	return &UpdateCacheOperation{
		Cache: cache,
	}
}

// Type implements Operation.Type.
func (op *UpdateCacheOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateCacheOperation) Section() string {
	return "cache"
}

// Priority implements Operation.Priority.
func (op *UpdateCacheOperation) Priority() int {
	return PriorityCache
}

// Execute updates the cache section via the Dataplane API.
func (op *UpdateCacheOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Cache == nil {
		return fmt.Errorf("cache section is nil")
	}
	if op.Cache.Name == nil || *op.Cache.Name == "" {
		return fmt.Errorf("cache section name is empty")
	}

	apiClient := c.Client()

	// Convert models.Cache to dataplaneapi.Cache using JSON marshaling
	var apiCache dataplaneapi.Cache
	data, err := json.Marshal(op.Cache)
	if err != nil {
		return fmt.Errorf("failed to marshal cache section: %w", err)
	}
	if err := json.Unmarshal(data, &apiCache); err != nil {
		return fmt.Errorf("failed to unmarshal cache section: %w", err)
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.ReplaceCacheParams{}
	if transactionID != "" {
		params.TransactionId = &transactionID
	} else {
		v, err := c.GetVersion(ctx)
		if err != nil {
			return fmt.Errorf("failed to get version: %w", err)
		}
		version := int(v)
		params.Version = &version
	}

	// Call the ReplaceCache API
	resp, err := apiClient.ReplaceCache(ctx, *op.Cache.Name, params, apiCache)
	if err != nil {
		return fmt.Errorf("failed to update cache section '%s': %w", *op.Cache.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("cache section update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateCacheOperation) Describe() string {
	name := "unknown"
	if op.Cache.Name != nil && *op.Cache.Name != "" {
		name = *op.Cache.Name
	}
	return fmt.Sprintf("Update cache '%s'", name)
}
