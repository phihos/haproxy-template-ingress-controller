// Package sections contains section-specific comparison logic and operations
// for HAProxy configuration elements.
package sections

import (
	"context"
	"fmt"
	"net/http"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/pkg/dataplane/client"
	"haproxy-template-ic/pkg/dataplane/transform"
	"haproxy-template-ic/pkg/generated/dataplaneapi"
)

// PriorityTCPCheck defines the priority for TCP check operations.
const PriorityTCPCheck = 60

const (
	sectionTCPCheck = "tcp-check"
)

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
	return sectionTCPCheck
}

// Priority implements Operation.Priority.
func (op *CreateTCPCheckBackendOperation) Priority() int {
	return PriorityTCPCheck
}

// Execute creates the tcp check via the Dataplane API.
func (op *CreateTCPCheckBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeCreateIndexedRuleHelper(
		ctx, transactionID, op.TCPCheck, op.BackendName, op.Index,
		transform.ToAPITCPCheck,
		func(txID string) *dataplaneapi.CreateTCPCheckBackendParams {
			return &dataplaneapi.CreateTCPCheckBackendParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.CreateTCPCheckBackendParams, apiModel dataplaneapi.TcpCheck) (*http.Response, error) {
			return c.Client().CreateTCPCheckBackend(ctx, parent, idx, params, apiModel)
		},
		"tcp check",
		"backend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *CreateTCPCheckBackendOperation) Describe() string {
	action := unknownFallback
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
	return sectionTCPCheck
}

// Priority implements Operation.Priority.
func (op *DeleteTCPCheckBackendOperation) Priority() int {
	return PriorityTCPCheck
}

// Execute deletes the tcp check via the Dataplane API.
func (op *DeleteTCPCheckBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeDeleteIndexedRuleHelper(
		ctx, transactionID, op.BackendName, op.Index,
		func(txID string) *dataplaneapi.DeleteTCPCheckBackendParams {
			return &dataplaneapi.DeleteTCPCheckBackendParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.DeleteTCPCheckBackendParams) (*http.Response, error) {
			return c.Client().DeleteTCPCheckBackend(ctx, parent, idx, params)
		},
		"tcp check",
		"backend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *DeleteTCPCheckBackendOperation) Describe() string {
	action := unknownFallback
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
	return sectionTCPCheck
}

// Priority implements Operation.Priority.
func (op *UpdateTCPCheckBackendOperation) Priority() int {
	return PriorityTCPCheck
}

// Execute updates the tcp check via the Dataplane API.
func (op *UpdateTCPCheckBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeReplaceIndexedRuleHelper(
		ctx, transactionID, op.TCPCheck, op.BackendName, op.Index,
		transform.ToAPITCPCheck,
		func(txID string) *dataplaneapi.ReplaceTCPCheckBackendParams {
			return &dataplaneapi.ReplaceTCPCheckBackendParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.ReplaceTCPCheckBackendParams, apiModel dataplaneapi.TcpCheck) (*http.Response, error) {
			return c.Client().ReplaceTCPCheckBackend(ctx, parent, idx, params, apiModel)
		},
		"tcp check",
		"backend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *UpdateTCPCheckBackendOperation) Describe() string {
	action := unknownFallback
	if op.TCPCheck != nil && op.TCPCheck.Action != "" {
		action = op.TCPCheck.Action
	}
	return fmt.Sprintf("Update TCP check (%s) in backend '%s'", action, op.BackendName)
}
