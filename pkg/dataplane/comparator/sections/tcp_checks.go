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

// PriorityTCPCheck defines the priority for TCP check operations.
const PriorityTCPCheck = 60

// CreateTCPCheckBackendOperation represents creating a new TCP check in a backend.
type CreateTCPCheckBackendOperation struct {
	BackendName string
	TCPCheck    *models.TCPCheck
	Index       int
}

// NewCreateTCPCheckBackendOperation creates a new TCP check creation operation for a backend.
func NewCreateTCPCheckBackendOperation(backendName string, tcpCheck *models.TCPCheck, index int) *CreateTCPCheckBackendOperation {
	return &CreateTCPCheckBackendOperation{
		BackendName: backendName,
		TCPCheck:    tcpCheck,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *CreateTCPCheckBackendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateTCPCheckBackendOperation) Section() string {
	return "tcp-check"
}

// Priority implements Operation.Priority.
func (op *CreateTCPCheckBackendOperation) Priority() int {
	return PriorityTCPCheck
}

// Execute creates the TCP check via the Dataplane API.
func (op *CreateTCPCheckBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.TCPCheck == nil {
		return fmt.Errorf("TCP check is nil")
	}

	apiClient := c.Client()

	// Convert models.TCPCheck to dataplaneapi.TcpCheck using JSON marshaling
	var apiTCPCheck dataplaneapi.TcpCheck
	data, err := json.Marshal(op.TCPCheck)
	if err != nil {
		return fmt.Errorf("failed to marshal TCP check: %w", err)
	}
	if err := json.Unmarshal(data, &apiTCPCheck); err != nil {
		return fmt.Errorf("failed to unmarshal TCP check: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateTCPCheckBackendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateTCPCheckBackend API
	resp, err := apiClient.CreateTCPCheckBackend(ctx, op.BackendName, op.Index, params, apiTCPCheck)
	if err != nil {
		return fmt.Errorf("failed to create TCP check in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("TCP check creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateTCPCheckBackendOperation) Describe() string {
	action := "unknown"
	if op.TCPCheck != nil && op.TCPCheck.Action != "" {
		action = op.TCPCheck.Action
	}
	return fmt.Sprintf("Create TCP check (%s) in backend '%s'", action, op.BackendName)
}

// DeleteTCPCheckBackendOperation represents deleting a TCP check from a backend.
type DeleteTCPCheckBackendOperation struct {
	BackendName string
	TCPCheck    *models.TCPCheck
	Index       int
}

// NewDeleteTCPCheckBackendOperation creates a new TCP check deletion operation for a backend.
func NewDeleteTCPCheckBackendOperation(backendName string, tcpCheck *models.TCPCheck, index int) *DeleteTCPCheckBackendOperation {
	return &DeleteTCPCheckBackendOperation{
		BackendName: backendName,
		TCPCheck:    tcpCheck,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *DeleteTCPCheckBackendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteTCPCheckBackendOperation) Section() string {
	return "tcp-check"
}

// Priority implements Operation.Priority.
func (op *DeleteTCPCheckBackendOperation) Priority() int {
	return PriorityTCPCheck
}

// Execute deletes the TCP check via the Dataplane API.
func (op *DeleteTCPCheckBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	apiClient := c.Client()

	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteTCPCheckBackendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteTCPCheckBackend API
	resp, err := apiClient.DeleteTCPCheckBackend(ctx, op.BackendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete TCP check from backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("TCP check deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteTCPCheckBackendOperation) Describe() string {
	action := "unknown"
	if op.TCPCheck != nil && op.TCPCheck.Action != "" {
		action = op.TCPCheck.Action
	}
	return fmt.Sprintf("Delete TCP check (%s) from backend '%s'", action, op.BackendName)
}

// UpdateTCPCheckBackendOperation represents updating a TCP check in a backend.
type UpdateTCPCheckBackendOperation struct {
	BackendName string
	TCPCheck    *models.TCPCheck
	Index       int
}

// NewUpdateTCPCheckBackendOperation creates a new TCP check update operation for a backend.
func NewUpdateTCPCheckBackendOperation(backendName string, tcpCheck *models.TCPCheck, index int) *UpdateTCPCheckBackendOperation {
	return &UpdateTCPCheckBackendOperation{
		BackendName: backendName,
		TCPCheck:    tcpCheck,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *UpdateTCPCheckBackendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateTCPCheckBackendOperation) Section() string {
	return "tcp-check"
}

// Priority implements Operation.Priority.
func (op *UpdateTCPCheckBackendOperation) Priority() int {
	return PriorityTCPCheck
}

// Execute updates the TCP check via the Dataplane API.
func (op *UpdateTCPCheckBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.TCPCheck == nil {
		return fmt.Errorf("TCP check is nil")
	}

	apiClient := c.Client()

	// Convert models.TCPCheck to dataplaneapi.TcpCheck using JSON marshaling
	var apiTCPCheck dataplaneapi.TcpCheck
	data, err := json.Marshal(op.TCPCheck)
	if err != nil {
		return fmt.Errorf("failed to marshal TCP check: %w", err)
	}
	if err := json.Unmarshal(data, &apiTCPCheck); err != nil {
		return fmt.Errorf("failed to unmarshal TCP check: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceTCPCheckBackendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceTCPCheckBackend API
	resp, err := apiClient.ReplaceTCPCheckBackend(ctx, op.BackendName, op.Index, params, apiTCPCheck)
	if err != nil {
		return fmt.Errorf("failed to update TCP check in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("TCP check update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateTCPCheckBackendOperation) Describe() string {
	action := "unknown"
	if op.TCPCheck != nil && op.TCPCheck.Action != "" {
		action = op.TCPCheck.Action
	}
	return fmt.Sprintf("Update TCP check (%s) in backend '%s'", action, op.BackendName)
}
