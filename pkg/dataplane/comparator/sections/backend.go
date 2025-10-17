// Package sections contains section-specific comparison logic and operations
// for HAProxy configuration elements.
package sections

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/codegen/dataplaneapi"
	"haproxy-template-ic/pkg/dataplane/client"
)

// OperationType represents the type of configuration operation.
type OperationType int

const (
	OperationCreate OperationType = iota
	OperationUpdate
	OperationDelete
)

// Higher priority = executed first for Deletes.
const (
	PriorityGlobal   = 10
	PriorityDefaults = 20
	PriorityFrontend = 30
	PriorityBackend  = 30
	PriorityBind     = 40
	PriorityServer   = 40
	PriorityACL      = 50
	PriorityRule     = 60
)

const (
	sectionBackend = "backend"
)

// CreateBackendOperation represents creating a new backend.
type CreateBackendOperation struct {
	Backend *models.Backend
}

// NewCreateBackendOperation creates a new backend creation operation.
func NewCreateBackendOperation(backend *models.Backend) *CreateBackendOperation {
	return &CreateBackendOperation{
		Backend: backend,
	}
}

// Type implements Operation.Type.
func (op *CreateBackendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateBackendOperation) Section() string {
	return sectionBackend
}

// Priority implements Operation.Priority.
func (op *CreateBackendOperation) Priority() int {
	return PriorityBackend
}

// Execute creates the backend via the Dataplane API.
func (op *CreateBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Backend == nil {
		return fmt.Errorf("backend is nil")
	}
	if op.Backend.Name == "" {
		return fmt.Errorf("backend name is empty")
	}

	apiClient := c.Client()

	// Convert models.Backend to dataplaneapi.Backend using JSON marshaling
	// This is necessary because they are incompatible types
	var apiBackend dataplaneapi.Backend
	data, err := json.Marshal(op.Backend)
	if err != nil {
		return fmt.Errorf("failed to marshal backend: %w", err)
	}
	if err := json.Unmarshal(data, &apiBackend); err != nil {
		return fmt.Errorf("failed to unmarshal backend: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateBackendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateBackend API
	resp, err := apiClient.CreateBackend(ctx, params, apiBackend)
	if err != nil {
		return fmt.Errorf("failed to create backend '%s': %w", op.Backend.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("backend creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateBackendOperation) Describe() string {
	name := unknownFallback
	if op.Backend.Name != "" {
		name = op.Backend.Name
	}
	return fmt.Sprintf("Create backend '%s'", name)
}

// DeleteBackendOperation represents deleting an existing backend.
type DeleteBackendOperation struct {
	Backend *models.Backend
}

// NewDeleteBackendOperation creates a new backend deletion operation.
func NewDeleteBackendOperation(backend *models.Backend) *DeleteBackendOperation {
	return &DeleteBackendOperation{
		Backend: backend,
	}
}

// Type implements Operation.Type.
func (op *DeleteBackendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteBackendOperation) Section() string {
	return sectionBackend
}

// Priority implements Operation.Priority.
func (op *DeleteBackendOperation) Priority() int {
	return PriorityBackend
}

// Execute deletes the backend via the Dataplane API.
func (op *DeleteBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Backend == nil {
		return fmt.Errorf("backend is nil")
	}
	if op.Backend.Name == "" {
		return fmt.Errorf("backend name is empty")
	}

	apiClient := c.Client()

	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteBackendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteBackend API
	resp, err := apiClient.DeleteBackend(ctx, op.Backend.Name, params)
	if err != nil {
		return fmt.Errorf("failed to delete backend '%s': %w", op.Backend.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("backend deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteBackendOperation) Describe() string {
	name := unknownFallback
	if op.Backend.Name != "" {
		name = op.Backend.Name
	}
	return fmt.Sprintf("Delete backend '%s'", name)
}

// UpdateBackendOperation represents updating an existing backend.
type UpdateBackendOperation struct {
	Backend *models.Backend
}

// NewUpdateBackendOperation creates a new backend update operation.
func NewUpdateBackendOperation(backend *models.Backend) *UpdateBackendOperation {
	return &UpdateBackendOperation{
		Backend: backend,
	}
}

// Type implements Operation.Type.
func (op *UpdateBackendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateBackendOperation) Section() string {
	return sectionBackend
}

// Priority implements Operation.Priority.
func (op *UpdateBackendOperation) Priority() int {
	return PriorityBackend
}

// Execute updates the backend via the Dataplane API.
//
//nolint:dupl // Similar pattern to frontend/defaults operations - each handles different section types
func (op *UpdateBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Backend == nil {
		return fmt.Errorf("backend is nil")
	}
	if op.Backend.Name == "" {
		return fmt.Errorf("backend name is empty")
	}

	apiClient := c.Client()

	// Convert models.Backend to dataplaneapi.Backend using JSON marshaling
	var apiBackend dataplaneapi.Backend
	data, err := json.Marshal(op.Backend)
	if err != nil {
		return fmt.Errorf("failed to marshal backend: %w", err)
	}
	if err := json.Unmarshal(data, &apiBackend); err != nil {
		return fmt.Errorf("failed to unmarshal backend: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceBackendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceBackend API
	resp, err := apiClient.ReplaceBackend(ctx, op.Backend.Name, params, apiBackend)
	if err != nil {
		return fmt.Errorf("failed to update backend '%s': %w", op.Backend.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("backend update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateBackendOperation) Describe() string {
	name := unknownFallback
	if op.Backend.Name != "" {
		name = op.Backend.Name
	}
	return fmt.Sprintf("Update backend '%s'", name)
}
