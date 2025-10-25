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
func (op *CreateHTTPCheckBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeCreateIndexedRuleHelper(
		ctx, transactionID, op.HTTPCheck, op.BackendName, op.Index,
		transform.ToAPIHTTPCheck,
		func(txID string) *dataplaneapi.CreateHTTPCheckBackendParams {
			return &dataplaneapi.CreateHTTPCheckBackendParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.CreateHTTPCheckBackendParams, apiModel dataplaneapi.HttpCheck) (*http.Response, error) {
			return c.Client().CreateHTTPCheckBackend(ctx, parent, idx, params, apiModel)
		},
		"HTTP check",
		"backend",
	)
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
	return executeDeleteIndexedRuleHelper(
		ctx, transactionID, op.BackendName, op.Index,
		func(txID string) *dataplaneapi.DeleteHTTPCheckBackendParams {
			return &dataplaneapi.DeleteHTTPCheckBackendParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.DeleteHTTPCheckBackendParams) (*http.Response, error) {
			return c.Client().DeleteHTTPCheckBackend(ctx, parent, idx, params)
		},
		"HTTP check",
		"backend",
	)
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
func (op *UpdateHTTPCheckBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeReplaceIndexedRuleHelper(
		ctx, transactionID, op.HTTPCheck, op.BackendName, op.Index,
		transform.ToAPIHTTPCheck,
		func(txID string) *dataplaneapi.ReplaceHTTPCheckBackendParams {
			return &dataplaneapi.ReplaceHTTPCheckBackendParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.ReplaceHTTPCheckBackendParams, apiModel dataplaneapi.HttpCheck) (*http.Response, error) {
			return c.Client().ReplaceHTTPCheckBackend(ctx, parent, idx, params, apiModel)
		},
		"HTTP check",
		"backend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *UpdateHTTPCheckBackendOperation) Describe() string {
	checkType := unknownFallback
	if op.HTTPCheck != nil && op.HTTPCheck.Type != "" {
		checkType = op.HTTPCheck.Type
	}
	return fmt.Sprintf("Update HTTP check (%s) in backend '%s'", checkType, op.BackendName)
}
