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

// PriorityCapture defines the priority for capture operations.
const PriorityCapture = 60

// CreateCaptureFrontendOperation represents creating a new capture in a frontend.
type CreateCaptureFrontendOperation struct {
	FrontendName string
	Capture      *models.Capture
	Index        int
}

// NewCreateCaptureFrontendOperation creates a new capture creation operation for a frontend.
func NewCreateCaptureFrontendOperation(frontendName string, capture *models.Capture, index int) *CreateCaptureFrontendOperation {
	return &CreateCaptureFrontendOperation{
		FrontendName: frontendName,
		Capture:      capture,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *CreateCaptureFrontendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateCaptureFrontendOperation) Section() string {
	return "capture"
}

// Priority implements Operation.Priority.
func (op *CreateCaptureFrontendOperation) Priority() int {
	return PriorityCapture
}

// Execute creates the capture via the Dataplane API.
func (op *CreateCaptureFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Capture == nil {
		return fmt.Errorf("capture is nil")
	}

	apiClient := c.Client()

	// Convert models.Capture to dataplaneapi.Capture using JSON marshaling
	var apiCapture dataplaneapi.Capture
	data, err := json.Marshal(op.Capture)
	if err != nil {
		return fmt.Errorf("failed to marshal capture: %w", err)
	}
	if err := json.Unmarshal(data, &apiCapture); err != nil {
		return fmt.Errorf("failed to unmarshal capture: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateDeclareCaptureParams{
		TransactionId: &transactionID,
	}

	// Call the CreateDeclareCapture API
	resp, err := apiClient.CreateDeclareCapture(ctx, op.FrontendName, op.Index, params, apiCapture)
	if err != nil {
		return fmt.Errorf("failed to create capture in frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("capture creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateCaptureFrontendOperation) Describe() string {
	captureType := "unknown"
	if op.Capture != nil && op.Capture.Type != "" {
		captureType = op.Capture.Type
	}
	return fmt.Sprintf("Create capture (%s) in frontend '%s'", captureType, op.FrontendName)
}

// DeleteCaptureFrontendOperation represents deleting a capture from a frontend.
type DeleteCaptureFrontendOperation struct {
	FrontendName string
	Capture      *models.Capture
	Index        int
}

// NewDeleteCaptureFrontendOperation creates a new capture deletion operation for a frontend.
func NewDeleteCaptureFrontendOperation(frontendName string, capture *models.Capture, index int) *DeleteCaptureFrontendOperation {
	return &DeleteCaptureFrontendOperation{
		FrontendName: frontendName,
		Capture:      capture,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *DeleteCaptureFrontendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteCaptureFrontendOperation) Section() string {
	return "capture"
}

// Priority implements Operation.Priority.
func (op *DeleteCaptureFrontendOperation) Priority() int {
	return PriorityCapture
}

// Execute deletes the capture via the Dataplane API.
func (op *DeleteCaptureFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	apiClient := c.Client()

	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteDeclareCaptureParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteDeclareCapture API
	resp, err := apiClient.DeleteDeclareCapture(ctx, op.FrontendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete capture from frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("capture deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteCaptureFrontendOperation) Describe() string {
	captureType := "unknown"
	if op.Capture != nil && op.Capture.Type != "" {
		captureType = op.Capture.Type
	}
	return fmt.Sprintf("Delete capture (%s) from frontend '%s'", captureType, op.FrontendName)
}

// UpdateCaptureFrontendOperation represents updating a capture in a frontend.
type UpdateCaptureFrontendOperation struct {
	FrontendName string
	Capture      *models.Capture
	Index        int
}

// NewUpdateCaptureFrontendOperation creates a new capture update operation for a frontend.
func NewUpdateCaptureFrontendOperation(frontendName string, capture *models.Capture, index int) *UpdateCaptureFrontendOperation {
	return &UpdateCaptureFrontendOperation{
		FrontendName: frontendName,
		Capture:      capture,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *UpdateCaptureFrontendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateCaptureFrontendOperation) Section() string {
	return "capture"
}

// Priority implements Operation.Priority.
func (op *UpdateCaptureFrontendOperation) Priority() int {
	return PriorityCapture
}

// Execute updates the capture via the Dataplane API.
func (op *UpdateCaptureFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Capture == nil {
		return fmt.Errorf("capture is nil")
	}

	apiClient := c.Client()

	// Convert models.Capture to dataplaneapi.Capture using JSON marshaling
	var apiCapture dataplaneapi.Capture
	data, err := json.Marshal(op.Capture)
	if err != nil {
		return fmt.Errorf("failed to marshal capture: %w", err)
	}
	if err := json.Unmarshal(data, &apiCapture); err != nil {
		return fmt.Errorf("failed to unmarshal capture: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceDeclareCaptureParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceDeclareCapture API
	resp, err := apiClient.ReplaceDeclareCapture(ctx, op.FrontendName, op.Index, params, apiCapture)
	if err != nil {
		return fmt.Errorf("failed to update capture in frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("capture update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateCaptureFrontendOperation) Describe() string {
	captureType := "unknown"
	if op.Capture != nil && op.Capture.Type != "" {
		captureType = op.Capture.Type
	}
	return fmt.Sprintf("Update capture (%s) in frontend '%s'", captureType, op.FrontendName)
}
