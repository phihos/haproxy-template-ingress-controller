//nolint:dupl // Section operation files follow similar patterns - type-specific HAProxy API wrappers
package sections

// Section operation files follow similar patterns - each implements type-specific HAProxy API wrappers

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/codegen/dataplaneapi"
	"haproxy-template-ic/pkg/dataplane/client"
)

const (
	sectionFrontend = "frontend"
)

// CreateFrontendOperation represents creating a new frontend.
type CreateFrontendOperation struct {
	Frontend *models.Frontend
}

// NewCreateFrontendOperation creates a new frontend creation operation.
func NewCreateFrontendOperation(frontend *models.Frontend) *CreateFrontendOperation {
	return &CreateFrontendOperation{
		Frontend: frontend,
	}
}

// Type implements Operation.Type.
func (op *CreateFrontendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateFrontendOperation) Section() string {
	return sectionFrontend
}

// Priority implements Operation.Priority.
func (op *CreateFrontendOperation) Priority() int {
	return PriorityFrontend
}

// Execute creates the frontend via the Dataplane API.
func (op *CreateFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Frontend == nil {
		return fmt.Errorf("frontend is nil")
	}
	if op.Frontend.Name == "" {
		return fmt.Errorf("frontend name is empty")
	}

	apiClient := c.Client()

	// Convert models.Frontend to dataplaneapi.Frontend using JSON marshaling
	var apiFrontend dataplaneapi.Frontend
	data, err := json.Marshal(op.Frontend)
	if err != nil {
		return fmt.Errorf("failed to marshal frontend: %w", err)
	}
	if err := json.Unmarshal(data, &apiFrontend); err != nil {
		return fmt.Errorf("failed to unmarshal frontend: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateFrontend API
	resp, err := apiClient.CreateFrontend(ctx, params, apiFrontend)
	if err != nil {
		return fmt.Errorf("failed to create frontend '%s': %w", op.Frontend.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("frontend creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateFrontendOperation) Describe() string {
	name := unknownFallback
	if op.Frontend.Name != "" {
		name = op.Frontend.Name
	}
	return fmt.Sprintf("Create frontend '%s'", name)
}

// DeleteFrontendOperation represents deleting an existing frontend.
type DeleteFrontendOperation struct {
	Frontend *models.Frontend
}

// NewDeleteFrontendOperation creates a new frontend deletion operation.
func NewDeleteFrontendOperation(frontend *models.Frontend) *DeleteFrontendOperation {
	return &DeleteFrontendOperation{
		Frontend: frontend,
	}
}

// Type implements Operation.Type.
func (op *DeleteFrontendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteFrontendOperation) Section() string {
	return sectionFrontend
}

// Priority implements Operation.Priority.
func (op *DeleteFrontendOperation) Priority() int {
	return PriorityFrontend
}

// Execute deletes the frontend via the Dataplane API.
func (op *DeleteFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Frontend == nil {
		return fmt.Errorf("frontend is nil")
	}
	if op.Frontend.Name == "" {
		return fmt.Errorf("frontend name is empty")
	}

	apiClient := c.Client()

	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteFrontend API
	resp, err := apiClient.DeleteFrontend(ctx, op.Frontend.Name, params)
	if err != nil {
		return fmt.Errorf("failed to delete frontend '%s': %w", op.Frontend.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("frontend deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteFrontendOperation) Describe() string {
	name := unknownFallback
	if op.Frontend.Name != "" {
		name = op.Frontend.Name
	}
	return fmt.Sprintf("Delete frontend '%s'", name)
}

// UpdateFrontendOperation represents updating an existing frontend.
type UpdateFrontendOperation struct {
	Frontend *models.Frontend
}

// NewUpdateFrontendOperation creates a new frontend update operation.
func NewUpdateFrontendOperation(frontend *models.Frontend) *UpdateFrontendOperation {
	return &UpdateFrontendOperation{
		Frontend: frontend,
	}
}

// Type implements Operation.Type.
func (op *UpdateFrontendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateFrontendOperation) Section() string {
	return sectionFrontend
}

// Priority implements Operation.Priority.
func (op *UpdateFrontendOperation) Priority() int {
	return PriorityFrontend
}

// Execute updates the frontend via the Dataplane API.
func (op *UpdateFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Frontend == nil {
		return fmt.Errorf("frontend is nil")
	}
	if op.Frontend.Name == "" {
		return fmt.Errorf("frontend name is empty")
	}

	apiClient := c.Client()

	// Convert models.Frontend to dataplaneapi.Frontend using JSON marshaling
	var apiFrontend dataplaneapi.Frontend
	data, err := json.Marshal(op.Frontend)
	if err != nil {
		return fmt.Errorf("failed to marshal frontend: %w", err)
	}
	if err := json.Unmarshal(data, &apiFrontend); err != nil {
		return fmt.Errorf("failed to unmarshal frontend: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceFrontend API
	resp, err := apiClient.ReplaceFrontend(ctx, op.Frontend.Name, params, apiFrontend)
	if err != nil {
		return fmt.Errorf("failed to update frontend '%s': %w", op.Frontend.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("frontend update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateFrontendOperation) Describe() string {
	name := unknownFallback
	if op.Frontend.Name != "" {
		name = op.Frontend.Name
	}
	return fmt.Sprintf("Update frontend '%s'", name)
}
