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
	return executeCreateTransactionOnlyHelper(
		ctx, transactionID, op.Backend,
		func(m *models.Backend) string { return m.Name },
		transform.ToAPIBackend,
		func(txID string) *dataplaneapi.CreateBackendParams {
			return &dataplaneapi.CreateBackendParams{TransactionId: &txID}
		},
		func(ctx context.Context, params *dataplaneapi.CreateBackendParams, apiModel dataplaneapi.Backend) (*http.Response, error) {
			return c.Client().CreateBackend(ctx, params, apiModel)
		},
		"backend",
	)
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
	return executeDeleteTransactionOnlyHelper(
		ctx, transactionID, op.Backend,
		func(m *models.Backend) string { return m.Name },
		func(txID string) *dataplaneapi.DeleteBackendParams {
			return &dataplaneapi.DeleteBackendParams{TransactionId: &txID}
		},
		func(ctx context.Context, name string, params *dataplaneapi.DeleteBackendParams) (*http.Response, error) {
			return c.Client().DeleteBackend(ctx, name, params)
		},
		"backend",
	)
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
func (op *UpdateBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeUpdateTransactionOnlyHelper(
		ctx, transactionID, op.Backend,
		func(m *models.Backend) string { return m.Name },
		transform.ToAPIBackend,
		func(txID string) *dataplaneapi.ReplaceBackendParams {
			return &dataplaneapi.ReplaceBackendParams{TransactionId: &txID}
		},
		func(ctx context.Context, name string, params *dataplaneapi.ReplaceBackendParams, apiModel dataplaneapi.Backend) (*http.Response, error) {
			return c.Client().ReplaceBackend(ctx, name, params, apiModel)
		},
		"backend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *UpdateBackendOperation) Describe() string {
	name := unknownFallback
	if op.Backend.Name != "" {
		name = op.Backend.Name
	}
	return fmt.Sprintf("Update backend '%s'", name)
}
