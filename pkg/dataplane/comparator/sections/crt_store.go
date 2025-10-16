package sections

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/codegen/dataplaneapi"
	"haproxy-template-ic/pkg/dataplane/client"
)

// PriorityCrtStore defines priority for crt-store sections.
const PriorityCrtStore = 10

// CreateCrtStoreOperation represents creating a new crt-store section.
type CreateCrtStoreOperation struct {
	CrtStore *models.CrtStore
}

// NewCreateCrtStoreOperation creates a new crt-store section creation operation.
func NewCreateCrtStoreOperation(crtStore *models.CrtStore) *CreateCrtStoreOperation {
	return &CreateCrtStoreOperation{
		CrtStore: crtStore,
	}
}

// Type implements Operation.Type.
func (op *CreateCrtStoreOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateCrtStoreOperation) Section() string {
	return "crt-store"
}

// Priority implements Operation.Priority.
func (op *CreateCrtStoreOperation) Priority() int {
	return PriorityCrtStore
}

// Execute creates the crt-store section via the Dataplane API.
func (op *CreateCrtStoreOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.CrtStore == nil {
		return fmt.Errorf("crt-store section is nil")
	}
	if op.CrtStore.Name == "" {
		return fmt.Errorf("crt-store section name is empty")
	}

	apiClient := c.Client()

	// Convert models.CrtStore to dataplaneapi.CrtStore using JSON marshaling
	var apiCrtStore dataplaneapi.CrtStore
	data, err := json.Marshal(op.CrtStore)
	if err != nil {
		return fmt.Errorf("failed to marshal crt-store section: %w", err)
	}
	if err := json.Unmarshal(data, &apiCrtStore); err != nil {
		return fmt.Errorf("failed to unmarshal crt-store section: %w", err)
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.CreateCrtStoreParams{}
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

	// Call the CreateCrtStore API
	resp, err := apiClient.CreateCrtStore(ctx, params, apiCrtStore)
	if err != nil {
		return fmt.Errorf("failed to create crt-store section '%s': %w", op.CrtStore.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("crt-store section creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateCrtStoreOperation) Describe() string {
	name := "unknown"
	if op.CrtStore.Name != "" {
		name = op.CrtStore.Name
	}
	return fmt.Sprintf("Create crt-store '%s'", name)
}

// DeleteCrtStoreOperation represents deleting an existing crt-store section.
type DeleteCrtStoreOperation struct {
	CrtStore *models.CrtStore
}

// NewDeleteCrtStoreOperation creates a new crt-store section deletion operation.
func NewDeleteCrtStoreOperation(crtStore *models.CrtStore) *DeleteCrtStoreOperation {
	return &DeleteCrtStoreOperation{
		CrtStore: crtStore,
	}
}

// Type implements Operation.Type.
func (op *DeleteCrtStoreOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteCrtStoreOperation) Section() string {
	return "crt-store"
}

// Priority implements Operation.Priority.
func (op *DeleteCrtStoreOperation) Priority() int {
	return PriorityCrtStore
}

// Execute deletes the crt-store section via the Dataplane API.
func (op *DeleteCrtStoreOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.CrtStore == nil {
		return fmt.Errorf("crt-store section is nil")
	}
	if op.CrtStore.Name == "" {
		return fmt.Errorf("crt-store section name is empty")
	}

	apiClient := c.Client()

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.DeleteCrtStoreParams{}
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

	// Call the DeleteCrtStore API
	resp, err := apiClient.DeleteCrtStore(ctx, op.CrtStore.Name, params)
	if err != nil {
		return fmt.Errorf("failed to delete crt-store section '%s': %w", op.CrtStore.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("crt-store section deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteCrtStoreOperation) Describe() string {
	name := "unknown"
	if op.CrtStore.Name != "" {
		name = op.CrtStore.Name
	}
	return fmt.Sprintf("Delete crt-store '%s'", name)
}

// UpdateCrtStoreOperation represents updating an existing crt-store section.
type UpdateCrtStoreOperation struct {
	CrtStore *models.CrtStore
}

// NewUpdateCrtStoreOperation creates a new crt-store section update operation.
func NewUpdateCrtStoreOperation(crtStore *models.CrtStore) *UpdateCrtStoreOperation {
	return &UpdateCrtStoreOperation{
		CrtStore: crtStore,
	}
}

// Type implements Operation.Type.
func (op *UpdateCrtStoreOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateCrtStoreOperation) Section() string {
	return "crt-store"
}

// Priority implements Operation.Priority.
func (op *UpdateCrtStoreOperation) Priority() int {
	return PriorityCrtStore
}

// Execute updates the crt-store section via the Dataplane API.
func (op *UpdateCrtStoreOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.CrtStore == nil {
		return fmt.Errorf("crt-store section is nil")
	}
	if op.CrtStore.Name == "" {
		return fmt.Errorf("crt-store section name is empty")
	}

	apiClient := c.Client()

	// Convert models.CrtStore to dataplaneapi.CrtStore using JSON marshaling
	var apiCrtStore dataplaneapi.CrtStore
	data, err := json.Marshal(op.CrtStore)
	if err != nil {
		return fmt.Errorf("failed to marshal crt-store section: %w", err)
	}
	if err := json.Unmarshal(data, &apiCrtStore); err != nil {
		return fmt.Errorf("failed to unmarshal crt-store section: %w", err)
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.EditCrtStoreParams{}
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

	// Call the EditCrtStore API (note: uses Edit, not Replace)
	resp, err := apiClient.EditCrtStore(ctx, op.CrtStore.Name, params, apiCrtStore)
	if err != nil {
		return fmt.Errorf("failed to update crt-store section '%s': %w", op.CrtStore.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("crt-store section update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateCrtStoreOperation) Describe() string {
	name := "unknown"
	if op.CrtStore.Name != "" {
		name = op.CrtStore.Name
	}
	return fmt.Sprintf("Update crt-store '%s'", name)
}
