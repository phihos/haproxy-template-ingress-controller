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

// CreateDefaultsOperation represents creating a new defaults section.
type CreateDefaultsOperation struct {
	Defaults *models.Defaults
}

// NewCreateDefaultsOperation creates a new defaults section creation operation.
func NewCreateDefaultsOperation(defaults *models.Defaults) *CreateDefaultsOperation {
	return &CreateDefaultsOperation{
		Defaults: defaults,
	}
}

// Type implements Operation.Type.
func (op *CreateDefaultsOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateDefaultsOperation) Section() string {
	return "defaults"
}

// Priority implements Operation.Priority.
func (op *CreateDefaultsOperation) Priority() int {
	return PriorityDefaults
}

// Execute creates the defaults section via the Dataplane API.
func (op *CreateDefaultsOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Defaults == nil {
		return fmt.Errorf("defaults section is nil")
	}
	if op.Defaults.Name == "" {
		return fmt.Errorf("defaults section name is empty")
	}

	apiClient := c.Client()

	// Convert models.Defaults to dataplaneapi.Defaults using JSON marshaling
	// This is necessary because they are incompatible types
	var apiDefaults dataplaneapi.Defaults
	data, err := json.Marshal(op.Defaults)
	if err != nil {
		return fmt.Errorf("failed to marshal defaults section: %w", err)
	}
	if err := json.Unmarshal(data, &apiDefaults); err != nil {
		return fmt.Errorf("failed to unmarshal defaults section: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateDefaultsSectionParams{
		TransactionId: &transactionID,
	}

	// Call the CreateDefaultsSection API
	resp, err := apiClient.CreateDefaultsSection(ctx, params, apiDefaults)
	if err != nil {
		return fmt.Errorf("failed to create defaults section '%s': %w", op.Defaults.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("defaults section creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateDefaultsOperation) Describe() string {
	name := "unknown"
	if op.Defaults.Name != "" {
		name = op.Defaults.Name
	}
	return fmt.Sprintf("Create defaults section '%s'", name)
}

// DeleteDefaultsOperation represents deleting an existing defaults section.
type DeleteDefaultsOperation struct {
	Defaults *models.Defaults
}

// NewDeleteDefaultsOperation creates a new defaults section deletion operation.
func NewDeleteDefaultsOperation(defaults *models.Defaults) *DeleteDefaultsOperation {
	return &DeleteDefaultsOperation{
		Defaults: defaults,
	}
}

// Type implements Operation.Type.
func (op *DeleteDefaultsOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteDefaultsOperation) Section() string {
	return "defaults"
}

// Priority implements Operation.Priority.
func (op *DeleteDefaultsOperation) Priority() int {
	return PriorityDefaults
}

// Execute deletes the defaults section via the Dataplane API.
func (op *DeleteDefaultsOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Defaults == nil {
		return fmt.Errorf("defaults section is nil")
	}
	if op.Defaults.Name == "" {
		return fmt.Errorf("defaults section name is empty")
	}

	apiClient := c.Client()

	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteDefaultsSectionParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteDefaultsSection API
	resp, err := apiClient.DeleteDefaultsSection(ctx, op.Defaults.Name, params)
	if err != nil {
		return fmt.Errorf("failed to delete defaults section '%s': %w", op.Defaults.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("defaults section deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteDefaultsOperation) Describe() string {
	name := "unknown"
	if op.Defaults.Name != "" {
		name = op.Defaults.Name
	}
	return fmt.Sprintf("Delete defaults section '%s'", name)
}

// UpdateDefaultsOperation represents updating an existing defaults section.
type UpdateDefaultsOperation struct {
	Defaults *models.Defaults
}

// NewUpdateDefaultsOperation creates a new defaults section update operation.
func NewUpdateDefaultsOperation(defaults *models.Defaults) *UpdateDefaultsOperation {
	return &UpdateDefaultsOperation{
		Defaults: defaults,
	}
}

// Type implements Operation.Type.
func (op *UpdateDefaultsOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateDefaultsOperation) Section() string {
	return "defaults"
}

// Priority implements Operation.Priority.
func (op *UpdateDefaultsOperation) Priority() int {
	return PriorityDefaults
}

// Execute updates the defaults section via the Dataplane API.
func (op *UpdateDefaultsOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Defaults == nil {
		return fmt.Errorf("defaults section is nil")
	}
	if op.Defaults.Name == "" {
		return fmt.Errorf("defaults section name is empty")
	}

	apiClient := c.Client()

	// Convert models.Defaults to dataplaneapi.Defaults using JSON marshaling
	var apiDefaults dataplaneapi.Defaults
	data, err := json.Marshal(op.Defaults)
	if err != nil {
		return fmt.Errorf("failed to marshal defaults section: %w", err)
	}
	if err := json.Unmarshal(data, &apiDefaults); err != nil {
		return fmt.Errorf("failed to unmarshal defaults section: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceDefaultsSectionParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceDefaultsSection API
	resp, err := apiClient.ReplaceDefaultsSection(ctx, op.Defaults.Name, params, apiDefaults)
	if err != nil {
		return fmt.Errorf("failed to update defaults section '%s': %w", op.Defaults.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("defaults section update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateDefaultsOperation) Describe() string {
	name := "unknown"
	if op.Defaults.Name != "" {
		name = op.Defaults.Name
	}
	return fmt.Sprintf("Update defaults section '%s'", name)
}
