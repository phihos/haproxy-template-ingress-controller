// Package sections contains section-specific comparison logic and operations
// for HAProxy configuration elements.
//
//nolint:dupl // Section operation files follow similar patterns - type-specific HAProxy API wrappers
package sections

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/codegen/dataplaneapi"
	"haproxy-template-ic/pkg/dataplane/client"
)

// PriorityHTTPCheck defines the priority for HTTP check operations.
const PriorityHTTPCheck = 60

const (
	sectionHTTPCheck = "http_check"
)

// CreateHTTPCheckBackendOperation represents creating a new HTTP check in a backend.
type CreateHTTPCheckBackendOperation struct {
	BackendName string
	HTTPCheck   *models.HTTPCheck
	Index       int
}

// NewCreateHTTPCheckBackendOperation creates a new HTTP check creation operation for a backend.
func NewCreateHTTPCheckBackendOperation(backendName string, httpCheck *models.HTTPCheck, index int) *CreateHTTPCheckBackendOperation {
	return &CreateHTTPCheckBackendOperation{
		BackendName: backendName,
		HTTPCheck:   httpCheck,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *CreateHTTPCheckBackendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateHTTPCheckBackendOperation) Section() string {
	return sectionHTTPCheck
}

// Priority implements Operation.Priority.
func (op *CreateHTTPCheckBackendOperation) Priority() int {
	return PriorityHTTPCheck
}

// Execute creates the HTTP check via the Dataplane API.
//
//nolint:dupl // Similar pattern to other operation Execute methods - each handles different API endpoints and contexts
func (op *CreateHTTPCheckBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.HTTPCheck == nil {
		return fmt.Errorf("HTTP check is nil")
	}

	apiClient := c.Client()

	// Convert models.HTTPCheck to dataplaneapi.HttpCheck using JSON marshaling
	var apiHTTPCheck dataplaneapi.HttpCheck
	data, err := json.Marshal(op.HTTPCheck)
	if err != nil {
		return fmt.Errorf("failed to marshal HTTP check: %w", err)
	}
	if err := json.Unmarshal(data, &apiHTTPCheck); err != nil {
		return fmt.Errorf("failed to unmarshal HTTP check: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateHTTPCheckBackendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateHTTPCheckBackend API
	resp, err := apiClient.CreateHTTPCheckBackend(ctx, op.BackendName, op.Index, params, apiHTTPCheck)
	if err != nil {
		return fmt.Errorf("failed to create HTTP check in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP check creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateHTTPCheckBackendOperation) Describe() string {
	checkType := unknownFallback
	if op.HTTPCheck != nil && op.HTTPCheck.Type != "" {
		checkType = op.HTTPCheck.Type
	}
	return fmt.Sprintf("Create HTTP check (%s) in backend '%s'", checkType, op.BackendName)
}

// DeleteHTTPCheckBackendOperation represents deleting an HTTP check from a backend.
type DeleteHTTPCheckBackendOperation struct {
	BackendName string
	HTTPCheck   *models.HTTPCheck
	Index       int
}

// NewDeleteHTTPCheckBackendOperation creates a new HTTP check deletion operation for a backend.
func NewDeleteHTTPCheckBackendOperation(backendName string, httpCheck *models.HTTPCheck, index int) *DeleteHTTPCheckBackendOperation {
	return &DeleteHTTPCheckBackendOperation{
		BackendName: backendName,
		HTTPCheck:   httpCheck,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *DeleteHTTPCheckBackendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteHTTPCheckBackendOperation) Section() string {
	return sectionHTTPCheck
}

// Priority implements Operation.Priority.
func (op *DeleteHTTPCheckBackendOperation) Priority() int {
	return PriorityHTTPCheck
}

// Execute deletes the HTTP check via the Dataplane API.
func (op *DeleteHTTPCheckBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	apiClient := c.Client()

	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteHTTPCheckBackendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteHTTPCheckBackend API
	resp, err := apiClient.DeleteHTTPCheckBackend(ctx, op.BackendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete HTTP check from backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP check deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteHTTPCheckBackendOperation) Describe() string {
	checkType := unknownFallback
	if op.HTTPCheck != nil && op.HTTPCheck.Type != "" {
		checkType = op.HTTPCheck.Type
	}
	return fmt.Sprintf("Delete HTTP check (%s) from backend '%s'", checkType, op.BackendName)
}

// UpdateHTTPCheckBackendOperation represents updating an HTTP check in a backend.
type UpdateHTTPCheckBackendOperation struct {
	BackendName string
	HTTPCheck   *models.HTTPCheck
	Index       int
}

// NewUpdateHTTPCheckBackendOperation creates a new HTTP check update operation for a backend.
func NewUpdateHTTPCheckBackendOperation(backendName string, httpCheck *models.HTTPCheck, index int) *UpdateHTTPCheckBackendOperation {
	return &UpdateHTTPCheckBackendOperation{
		BackendName: backendName,
		HTTPCheck:   httpCheck,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *UpdateHTTPCheckBackendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateHTTPCheckBackendOperation) Section() string {
	return sectionHTTPCheck
}

// Priority implements Operation.Priority.
func (op *UpdateHTTPCheckBackendOperation) Priority() int {
	return PriorityHTTPCheck
}

// Execute updates the HTTP check via the Dataplane API.
//
//nolint:dupl // Similar pattern to other operation Execute methods - each handles different API endpoints and contexts
func (op *UpdateHTTPCheckBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.HTTPCheck == nil {
		return fmt.Errorf("HTTP check is nil")
	}

	apiClient := c.Client()

	// Convert models.HTTPCheck to dataplaneapi.HttpCheck using JSON marshaling
	var apiHTTPCheck dataplaneapi.HttpCheck
	data, err := json.Marshal(op.HTTPCheck)
	if err != nil {
		return fmt.Errorf("failed to marshal HTTP check: %w", err)
	}
	if err := json.Unmarshal(data, &apiHTTPCheck); err != nil {
		return fmt.Errorf("failed to unmarshal HTTP check: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceHTTPCheckBackendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceHTTPCheckBackend API
	resp, err := apiClient.ReplaceHTTPCheckBackend(ctx, op.BackendName, op.Index, params, apiHTTPCheck)
	if err != nil {
		return fmt.Errorf("failed to update HTTP check in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP check update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateHTTPCheckBackendOperation) Describe() string {
	checkType := unknownFallback
	if op.HTTPCheck != nil && op.HTTPCheck.Type != "" {
		checkType = op.HTTPCheck.Type
	}
	return fmt.Sprintf("Update HTTP check (%s) in backend '%s'", checkType, op.BackendName)
}
