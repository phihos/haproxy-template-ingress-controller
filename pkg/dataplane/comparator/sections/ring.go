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

// PriorityRing defines priority for ring sections.
// Rings should be created early as they might be referenced by backends.
const PriorityRing = 15

const (
	sectionRing = "ring"
)

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
	return sectionRing
}

// Priority implements Operation.Priority.
func (op *CreateRingOperation) Priority() int {
	return PriorityRing
}

// Execute creates the ring section via the Dataplane API.
func (op *CreateRingOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeCreateHelper(
		ctx, transactionID, op.Ring,
		func(r *models.Ring) string { return r.Name },
		transform.ToAPIRing,
		func(ctx context.Context, apiRing *dataplaneapi.Ring, txID string) (*http.Response, error) {
			return wrapAPICallWithVersionOrTransaction(
				ctx, c, txID,
				func() *dataplaneapi.CreateRingParams { return &dataplaneapi.CreateRingParams{} },
				func(p *dataplaneapi.CreateRingParams, tid *string) { p.TransactionId = tid },
				func(p *dataplaneapi.CreateRingParams, v *int) { p.Version = v },
				func(ctx context.Context, params *dataplaneapi.CreateRingParams) (*http.Response, error) {
					return c.Client().CreateRing(ctx, params, *apiRing)
				},
			)
		},
		"ring section",
	)
}

// Describe returns a human-readable description of this operation.
func (op *CreateRingOperation) Describe() string {
	name := unknownFallback
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
	return sectionRing
}

// Priority implements Operation.Priority.
func (op *DeleteRingOperation) Priority() int {
	return PriorityRing
}

// Execute deletes the ring section via the Dataplane API.
func (op *DeleteRingOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeDeleteHelper(
		ctx, transactionID, op.Ring,
		func(r *models.Ring) string { return r.Name },
		func(ctx context.Context, name string, txID string) (*http.Response, error) {
			return wrapAPICallWithVersionOrTransaction(
				ctx, c, txID,
				func() *dataplaneapi.DeleteRingParams { return &dataplaneapi.DeleteRingParams{} },
				func(p *dataplaneapi.DeleteRingParams, tid *string) { p.TransactionId = tid },
				func(p *dataplaneapi.DeleteRingParams, v *int) { p.Version = v },
				func(ctx context.Context, params *dataplaneapi.DeleteRingParams) (*http.Response, error) {
					return c.Client().DeleteRing(ctx, name, params)
				},
			)
		},
		"ring section",
	)
}

// Describe returns a human-readable description of this operation.
func (op *DeleteRingOperation) Describe() string {
	name := unknownFallback
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
	return sectionRing
}

// Priority implements Operation.Priority.
func (op *UpdateRingOperation) Priority() int {
	return PriorityRing
}

// Execute updates the ring section via the Dataplane API.
func (op *UpdateRingOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeUpdateHelper(
		ctx, transactionID, op.Ring,
		func(r *models.Ring) string { return r.Name },
		transform.ToAPIRing,
		func(ctx context.Context, name string, apiRing *dataplaneapi.Ring, txID string) (*http.Response, error) {
			return wrapAPICallWithVersionOrTransaction(
				ctx, c, txID,
				func() *dataplaneapi.ReplaceRingParams { return &dataplaneapi.ReplaceRingParams{} },
				func(p *dataplaneapi.ReplaceRingParams, tid *string) { p.TransactionId = tid },
				func(p *dataplaneapi.ReplaceRingParams, v *int) { p.Version = v },
				func(ctx context.Context, params *dataplaneapi.ReplaceRingParams) (*http.Response, error) {
					return c.Client().ReplaceRing(ctx, name, params, *apiRing)
				},
			)
		},
		"ring section",
	)
}

// Describe returns a human-readable description of this operation.
func (op *UpdateRingOperation) Describe() string {
	name := unknownFallback
	if op.Ring.Name != "" {
		name = op.Ring.Name
	}
	return fmt.Sprintf("Update ring '%s'", name)
}
