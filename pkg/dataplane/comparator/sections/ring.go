package sections

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/codegen/dataplaneapi"
	"haproxy-template-ic/pkg/dataplane/client"
)

// PriorityRing defines priority for ring sections.
// Rings should be created early as they might be referenced by backends.
const PriorityRing = 15

// CreateRingOperation represents creating a new ring section.
type CreateRingOperation struct {
	Ring *models.Ring
}

// NewCreateRingOperation creates a new ring section creation operation.
func NewCreateRingOperation(ring *models.Ring) *CreateRingOperation {
	return &CreateRingOperation{
		Ring: ring,
	}
}

// Type implements Operation.Type.
func (op *CreateRingOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateRingOperation) Section() string {
	return "ring"
}

// Priority implements Operation.Priority.
func (op *CreateRingOperation) Priority() int {
	return PriorityRing
}

// Execute creates the ring section via the Dataplane API.
func (op *CreateRingOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Ring == nil {
		return fmt.Errorf("ring section is nil")
	}
	if op.Ring.Name == "" {
		return fmt.Errorf("ring section name is empty")
	}

	apiClient := c.Client()

	// Convert models.Ring to dataplaneapi.Ring using JSON marshaling
	var apiRing dataplaneapi.Ring
	data, err := json.Marshal(op.Ring)
	if err != nil {
		return fmt.Errorf("failed to marshal ring section: %w", err)
	}
	if err := json.Unmarshal(data, &apiRing); err != nil {
		return fmt.Errorf("failed to unmarshal ring section: %w", err)
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.CreateRingParams{}
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

	// Call the CreateRing API
	resp, err := apiClient.CreateRing(ctx, params, apiRing)
	if err != nil {
		return fmt.Errorf("failed to create ring section '%s': %w", op.Ring.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("ring section creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateRingOperation) Describe() string {
	name := "unknown"
	if op.Ring.Name != "" {
		name = op.Ring.Name
	}
	return fmt.Sprintf("Create ring '%s'", name)
}

// DeleteRingOperation represents deleting an existing ring section.
type DeleteRingOperation struct {
	Ring *models.Ring
}

// NewDeleteRingOperation creates a new ring section deletion operation.
func NewDeleteRingOperation(ring *models.Ring) *DeleteRingOperation {
	return &DeleteRingOperation{
		Ring: ring,
	}
}

// Type implements Operation.Type.
func (op *DeleteRingOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteRingOperation) Section() string {
	return "ring"
}

// Priority implements Operation.Priority.
func (op *DeleteRingOperation) Priority() int {
	return PriorityRing
}

// Execute deletes the ring section via the Dataplane API.
func (op *DeleteRingOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Ring == nil {
		return fmt.Errorf("ring section is nil")
	}
	if op.Ring.Name == "" {
		return fmt.Errorf("ring section name is empty")
	}

	apiClient := c.Client()

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.DeleteRingParams{}
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

	// Call the DeleteRing API
	resp, err := apiClient.DeleteRing(ctx, op.Ring.Name, params)
	if err != nil {
		return fmt.Errorf("failed to delete ring section '%s': %w", op.Ring.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("ring section deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteRingOperation) Describe() string {
	name := "unknown"
	if op.Ring.Name != "" {
		name = op.Ring.Name
	}
	return fmt.Sprintf("Delete ring '%s'", name)
}

// UpdateRingOperation represents updating an existing ring section.
type UpdateRingOperation struct {
	Ring *models.Ring
}

// NewUpdateRingOperation creates a new ring section update operation.
func NewUpdateRingOperation(ring *models.Ring) *UpdateRingOperation {
	return &UpdateRingOperation{
		Ring: ring,
	}
}

// Type implements Operation.Type.
func (op *UpdateRingOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateRingOperation) Section() string {
	return "ring"
}

// Priority implements Operation.Priority.
func (op *UpdateRingOperation) Priority() int {
	return PriorityRing
}

// Execute updates the ring section via the Dataplane API.
func (op *UpdateRingOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Ring == nil {
		return fmt.Errorf("ring section is nil")
	}
	if op.Ring.Name == "" {
		return fmt.Errorf("ring section name is empty")
	}

	apiClient := c.Client()

	// Convert models.Ring to dataplaneapi.Ring using JSON marshaling
	var apiRing dataplaneapi.Ring
	data, err := json.Marshal(op.Ring)
	if err != nil {
		return fmt.Errorf("failed to marshal ring section: %w", err)
	}
	if err := json.Unmarshal(data, &apiRing); err != nil {
		return fmt.Errorf("failed to unmarshal ring section: %w", err)
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.ReplaceRingParams{}
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

	// Call the ReplaceRing API
	resp, err := apiClient.ReplaceRing(ctx, op.Ring.Name, params, apiRing)
	if err != nil {
		return fmt.Errorf("failed to update ring section '%s': %w", op.Ring.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("ring section update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateRingOperation) Describe() string {
	name := "unknown"
	if op.Ring.Name != "" {
		name = op.Ring.Name
	}
	return fmt.Sprintf("Update ring '%s'", name)
}
