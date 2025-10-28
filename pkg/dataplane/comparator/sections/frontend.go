package sections

// Section operation files follow similar patterns - each implements type-specific HAProxy API wrappers

import (
	"context"
	"fmt"
	"net/http"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/pkg/dataplane/client"
	"haproxy-template-ic/pkg/dataplane/transform"
	"haproxy-template-ic/pkg/generated/dataplaneapi"
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
	return executeCreateTransactionOnlyHelper(
		ctx, transactionID, op.Frontend,
		func(m *models.Frontend) string { return m.Name },
		transform.ToAPIFrontend,
		func(txID string) *dataplaneapi.CreateFrontendParams {
			return &dataplaneapi.CreateFrontendParams{TransactionId: &txID}
		},
		func(ctx context.Context, params *dataplaneapi.CreateFrontendParams, apiModel dataplaneapi.Frontend) (*http.Response, error) {
			return c.Client().CreateFrontend(ctx, params, apiModel)
		},
		"frontend",
	)
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
	return executeDeleteTransactionOnlyHelper(
		ctx, transactionID, op.Frontend,
		func(m *models.Frontend) string { return m.Name },
		func(txID string) *dataplaneapi.DeleteFrontendParams {
			return &dataplaneapi.DeleteFrontendParams{TransactionId: &txID}
		},
		func(ctx context.Context, name string, params *dataplaneapi.DeleteFrontendParams) (*http.Response, error) {
			return c.Client().DeleteFrontend(ctx, name, params)
		},
		"frontend",
	)
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
	return executeUpdateTransactionOnlyHelper(
		ctx, transactionID, op.Frontend,
		func(m *models.Frontend) string { return m.Name },
		transform.ToAPIFrontend,
		func(txID string) *dataplaneapi.ReplaceFrontendParams {
			return &dataplaneapi.ReplaceFrontendParams{TransactionId: &txID}
		},
		func(ctx context.Context, name string, params *dataplaneapi.ReplaceFrontendParams, apiModel dataplaneapi.Frontend) (*http.Response, error) {
			return c.Client().ReplaceFrontend(ctx, name, params, apiModel)
		},
		"frontend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *UpdateFrontendOperation) Describe() string {
	name := unknownFallback
	if op.Frontend.Name != "" {
		name = op.Frontend.Name
	}
	return fmt.Sprintf("Update frontend '%s'", name)
}
