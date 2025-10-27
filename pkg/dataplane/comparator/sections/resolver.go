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

// PriorityResolver defines priority for resolver sections.
// Resolvers should be created early as they might be referenced by backends.
const PriorityResolver = 15

const (
	sectionResolver = "resolver"
)

// CreateResolverOperation represents creating a new resolver section.
type CreateResolverOperation struct {
	Resolver *models.Resolver
}

// NewCreateResolverOperation creates a new resolver section creation operation.
func NewCreateResolverOperation(resolver *models.Resolver) *CreateResolverOperation {
	return &CreateResolverOperation{
		Resolver: resolver,
	}
}

// Type implements Operation.Type.
func (op *CreateResolverOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateResolverOperation) Section() string {
	return sectionResolver
}

// Priority implements Operation.Priority.
func (op *CreateResolverOperation) Priority() int {
	return PriorityResolver
}

// Execute creates the resolver section via the Dataplane API.
func (op *CreateResolverOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeCreateHelper(
		ctx, transactionID, op.Resolver,
		func(r *models.Resolver) string { return r.Name },
		transform.ToAPIResolver,
		func(ctx context.Context, apiResolver *dataplaneapi.Resolver, txID string) (*http.Response, error) {
			return wrapAPICallWithVersionOrTransaction(
				ctx, c, txID,
				func() *dataplaneapi.CreateResolverParams { return &dataplaneapi.CreateResolverParams{} },
				func(p *dataplaneapi.CreateResolverParams, tid *string) { p.TransactionId = tid },
				func(p *dataplaneapi.CreateResolverParams, v *int) { p.Version = v },
				func(ctx context.Context, params *dataplaneapi.CreateResolverParams) (*http.Response, error) {
					return c.Client().CreateResolver(ctx, params, *apiResolver)
				},
			)
		},
		"resolver section",
	)
}

// Describe returns a human-readable description of this operation.
func (op *CreateResolverOperation) Describe() string {
	name := unknownFallback
	if op.Resolver.Name != "" {
		name = op.Resolver.Name
	}
	return fmt.Sprintf("Create resolver '%s'", name)
}

// DeleteResolverOperation represents deleting an existing resolver section.
type DeleteResolverOperation struct {
	Resolver *models.Resolver
}

// NewDeleteResolverOperation creates a new resolver section deletion operation.
func NewDeleteResolverOperation(resolver *models.Resolver) *DeleteResolverOperation {
	return &DeleteResolverOperation{
		Resolver: resolver,
	}
}

// Type implements Operation.Type.
func (op *DeleteResolverOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteResolverOperation) Section() string {
	return sectionResolver
}

// Priority implements Operation.Priority.
func (op *DeleteResolverOperation) Priority() int {
	return PriorityResolver
}

// Execute deletes the resolver section via the Dataplane API.
func (op *DeleteResolverOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeDeleteHelper(
		ctx, transactionID, op.Resolver,
		func(r *models.Resolver) string { return r.Name },
		func(ctx context.Context, name string, txID string) (*http.Response, error) {
			return wrapAPICallWithVersionOrTransaction(
				ctx, c, txID,
				func() *dataplaneapi.DeleteResolverParams { return &dataplaneapi.DeleteResolverParams{} },
				func(p *dataplaneapi.DeleteResolverParams, tid *string) { p.TransactionId = tid },
				func(p *dataplaneapi.DeleteResolverParams, v *int) { p.Version = v },
				func(ctx context.Context, params *dataplaneapi.DeleteResolverParams) (*http.Response, error) {
					return c.Client().DeleteResolver(ctx, name, params)
				},
			)
		},
		"resolver section",
	)
}

// Describe returns a human-readable description of this operation.
func (op *DeleteResolverOperation) Describe() string {
	name := unknownFallback
	if op.Resolver.Name != "" {
		name = op.Resolver.Name
	}
	return fmt.Sprintf("Delete resolver '%s'", name)
}

// UpdateResolverOperation represents updating an existing resolver section.
type UpdateResolverOperation struct {
	Resolver *models.Resolver
}

// NewUpdateResolverOperation creates a new resolver section update operation.
func NewUpdateResolverOperation(resolver *models.Resolver) *UpdateResolverOperation {
	return &UpdateResolverOperation{
		Resolver: resolver,
	}
}

// Type implements Operation.Type.
func (op *UpdateResolverOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateResolverOperation) Section() string {
	return sectionResolver
}

// Priority implements Operation.Priority.
func (op *UpdateResolverOperation) Priority() int {
	return PriorityResolver
}

// Execute updates the resolver section via the Dataplane API.
func (op *UpdateResolverOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeUpdateHelper(
		ctx, transactionID, op.Resolver,
		func(r *models.Resolver) string { return r.Name },
		transform.ToAPIResolver,
		func(ctx context.Context, name string, apiResolver *dataplaneapi.Resolver, txID string) (*http.Response, error) {
			return wrapAPICallWithVersionOrTransaction(
				ctx, c, txID,
				func() *dataplaneapi.ReplaceResolverParams { return &dataplaneapi.ReplaceResolverParams{} },
				func(p *dataplaneapi.ReplaceResolverParams, tid *string) { p.TransactionId = tid },
				func(p *dataplaneapi.ReplaceResolverParams, v *int) { p.Version = v },
				func(ctx context.Context, params *dataplaneapi.ReplaceResolverParams) (*http.Response, error) {
					return c.Client().ReplaceResolver(ctx, name, params, *apiResolver)
				},
			)
		},
		"resolver section",
	)
}

// Describe returns a human-readable description of this operation.
func (op *UpdateResolverOperation) Describe() string {
	name := unknownFallback
	if op.Resolver.Name != "" {
		name = op.Resolver.Name
	}
	return fmt.Sprintf("Update resolver '%s'", name)
}
