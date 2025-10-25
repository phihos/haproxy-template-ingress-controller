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

// PriorityCrtStore defines priority for crt-store sections.
const PriorityCrtStore = 10

const (
	sectionCRTStore = "crt-store"
)

// CreateCrtStoreOperation represents creating a new crt-store section.
type CreateCrtStoreOperation struct {
	CrtStore *models.CrtStore
}

// NewCreateCrtStoreOperation creates a new crt-store section creation operation.
func NewCreateCrtStoreOperation(crtStore *models.CrtStore) *CreateCrtStoreOperation {
	return &CreateCrtStoreOperation{
		CrtStore: crtStore,
	}
}

// Type implements Operation.Type.
func (op *CreateCrtStoreOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateCrtStoreOperation) Section() string {
	return sectionCRTStore
}

// Priority implements Operation.Priority.
func (op *CreateCrtStoreOperation) Priority() int {
	return PriorityCrtStore
}

// Execute creates the crt-store section via the Dataplane API.
func (op *CreateCrtStoreOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeCreateHelper(
		ctx, transactionID, op.CrtStore,
		func(r *models.CrtStore) string { return r.Name },
		transform.ToAPICrtStore,
		func(ctx context.Context, apiCrtStore *dataplaneapi.CrtStore, txID string) (*http.Response, error) {
			return wrapAPICallWithVersionOrTransaction(
				ctx, c, txID,
				func() *dataplaneapi.CreateCrtStoreParams { return &dataplaneapi.CreateCrtStoreParams{} },
				func(p *dataplaneapi.CreateCrtStoreParams, tid *string) { p.TransactionId = tid },
				func(p *dataplaneapi.CreateCrtStoreParams, v *int) { p.Version = v },
				func(ctx context.Context, params *dataplaneapi.CreateCrtStoreParams) (*http.Response, error) {
					return c.Client().CreateCrtStore(ctx, params, *apiCrtStore)
				},
			)
		},
		"crt-store section",
	)
}

// Describe returns a human-readable description of this operation.
func (op *CreateCrtStoreOperation) Describe() string {
	name := unknownFallback
	if op.CrtStore.Name != "" {
		name = op.CrtStore.Name
	}
	return fmt.Sprintf("Create crt-store '%s'", name)
}

// DeleteCrtStoreOperation represents deleting an existing crt-store section.
type DeleteCrtStoreOperation struct {
	CrtStore *models.CrtStore
}

// NewDeleteCrtStoreOperation creates a new crt-store section deletion operation.
func NewDeleteCrtStoreOperation(crtStore *models.CrtStore) *DeleteCrtStoreOperation {
	return &DeleteCrtStoreOperation{
		CrtStore: crtStore,
	}
}

// Type implements Operation.Type.
func (op *DeleteCrtStoreOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteCrtStoreOperation) Section() string {
	return sectionCRTStore
}

// Priority implements Operation.Priority.
func (op *DeleteCrtStoreOperation) Priority() int {
	return PriorityCrtStore
}

// Execute deletes the crt-store section via the Dataplane API.
func (op *DeleteCrtStoreOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeDeleteHelper(
		ctx, transactionID, op.CrtStore,
		func(r *models.CrtStore) string { return r.Name },
		func(ctx context.Context, name string, txID string) (*http.Response, error) {
			return wrapAPICallWithVersionOrTransaction(
				ctx, c, txID,
				func() *dataplaneapi.DeleteCrtStoreParams { return &dataplaneapi.DeleteCrtStoreParams{} },
				func(p *dataplaneapi.DeleteCrtStoreParams, tid *string) { p.TransactionId = tid },
				func(p *dataplaneapi.DeleteCrtStoreParams, v *int) { p.Version = v },
				func(ctx context.Context, params *dataplaneapi.DeleteCrtStoreParams) (*http.Response, error) {
					return c.Client().DeleteCrtStore(ctx, name, params)
				},
			)
		},
		"crt-store section",
	)
}

// Describe returns a human-readable description of this operation.
func (op *DeleteCrtStoreOperation) Describe() string {
	name := unknownFallback
	if op.CrtStore.Name != "" {
		name = op.CrtStore.Name
	}
	return fmt.Sprintf("Delete crt-store '%s'", name)
}

// UpdateCrtStoreOperation represents updating an existing crt-store section.
type UpdateCrtStoreOperation struct {
	CrtStore *models.CrtStore
}

// NewUpdateCrtStoreOperation creates a new crt-store section update operation.
func NewUpdateCrtStoreOperation(crtStore *models.CrtStore) *UpdateCrtStoreOperation {
	return &UpdateCrtStoreOperation{
		CrtStore: crtStore,
	}
}

// Type implements Operation.Type.
func (op *UpdateCrtStoreOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateCrtStoreOperation) Section() string {
	return sectionCRTStore
}

// Priority implements Operation.Priority.
func (op *UpdateCrtStoreOperation) Priority() int {
	return PriorityCrtStore
}

// Execute updates the crt-store section via the Dataplane API.
func (op *UpdateCrtStoreOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeUpdateHelper(
		ctx, transactionID, op.CrtStore,
		func(r *models.CrtStore) string { return r.Name },
		transform.ToAPICrtStore,
		func(ctx context.Context, name string, apiCrtStore *dataplaneapi.CrtStore, txID string) (*http.Response, error) {
			return wrapAPICallWithVersionOrTransaction(
				ctx, c, txID,
				func() *dataplaneapi.EditCrtStoreParams { return &dataplaneapi.EditCrtStoreParams{} },
				func(p *dataplaneapi.EditCrtStoreParams, tid *string) { p.TransactionId = tid },
				func(p *dataplaneapi.EditCrtStoreParams, v *int) { p.Version = v },
				func(ctx context.Context, params *dataplaneapi.EditCrtStoreParams) (*http.Response, error) {
					return c.Client().EditCrtStore(ctx, name, params, *apiCrtStore)
				},
			)
		},
		"crt-store section",
	)
}

// Describe returns a human-readable description of this operation.
func (op *UpdateCrtStoreOperation) Describe() string {
	name := unknownFallback
	if op.CrtStore.Name != "" {
		name = op.CrtStore.Name
	}
	return fmt.Sprintf("Update crt-store '%s'", name)
}
