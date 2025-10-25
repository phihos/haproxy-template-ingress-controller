// Package sections contains section-specific comparison logic and operations
// for HAProxy configuration elements.
package sections

import (
	"context"
	"fmt"
	"net/http"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/codegen/dataplaneapi"
	"haproxy-template-ic/pkg/dataplane/client"
	"haproxy-template-ic/pkg/dataplane/transform"
)

// PriorityCapture defines the priority for capture operations.
const PriorityCapture = 60

const (
	sectionCapture = "capture"
)

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
	return sectionCapture
}

// Priority implements Operation.Priority.
func (op *CreateCaptureFrontendOperation) Priority() int {
	return PriorityCapture
}

// Execute creates the capture via the Dataplane API.
func (op *CreateCaptureFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeCreateIndexedRuleHelper(
		ctx, transactionID, op.Capture, op.FrontendName, op.Index,
		transform.ToAPICapture,
		func(txID string) *dataplaneapi.CreateDeclareCaptureParams {
			return &dataplaneapi.CreateDeclareCaptureParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.CreateDeclareCaptureParams, apiModel dataplaneapi.Capture) (*http.Response, error) {
			return c.Client().CreateDeclareCapture(ctx, parent, idx, params, apiModel)
		},
		"capture",
		"frontend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *CreateCaptureFrontendOperation) Describe() string {
	captureType := unknownFallback
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
	return sectionCapture
}

// Priority implements Operation.Priority.
func (op *DeleteCaptureFrontendOperation) Priority() int {
	return PriorityCapture
}

// Execute deletes the capture via the Dataplane API.
func (op *DeleteCaptureFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeDeleteIndexedRuleHelper(
		ctx, transactionID, op.FrontendName, op.Index,
		func(txID string) *dataplaneapi.DeleteDeclareCaptureParams {
			return &dataplaneapi.DeleteDeclareCaptureParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.DeleteDeclareCaptureParams) (*http.Response, error) {
			return c.Client().DeleteDeclareCapture(ctx, parent, idx, params)
		},
		"capture",
		"frontend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *DeleteCaptureFrontendOperation) Describe() string {
	captureType := unknownFallback
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
	return sectionCapture
}

// Priority implements Operation.Priority.
func (op *UpdateCaptureFrontendOperation) Priority() int {
	return PriorityCapture
}

// Execute updates the capture via the Dataplane API.
func (op *UpdateCaptureFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeReplaceIndexedRuleHelper(
		ctx, transactionID, op.Capture, op.FrontendName, op.Index,
		transform.ToAPICapture,
		func(txID string) *dataplaneapi.ReplaceDeclareCaptureParams {
			return &dataplaneapi.ReplaceDeclareCaptureParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.ReplaceDeclareCaptureParams, apiModel dataplaneapi.Capture) (*http.Response, error) {
			return c.Client().ReplaceDeclareCapture(ctx, parent, idx, params, apiModel)
		},
		"capture",
		"frontend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *UpdateCaptureFrontendOperation) Describe() string {
	captureType := unknownFallback
	if op.Capture != nil && op.Capture.Type != "" {
		captureType = op.Capture.Type
	}
	return fmt.Sprintf("Update capture (%s) in frontend '%s'", captureType, op.FrontendName)
}
