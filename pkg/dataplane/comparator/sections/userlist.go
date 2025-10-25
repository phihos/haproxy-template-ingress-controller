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

// PriorityUserlist defines priority for userlist sections.
// Userlists should be created early as they might be referenced by frontends/backends.
const PriorityUserlist = 10

const (
	sectionUserlist = "userlist"
)

// CreateUserlistOperation represents creating a new userlist section.
type CreateUserlistOperation struct {
	Userlist *models.Userlist
}

// NewCreateUserlistOperation creates a new userlist section creation operation.
func NewCreateUserlistOperation(userlist *models.Userlist) *CreateUserlistOperation {
	return &CreateUserlistOperation{
		Userlist: userlist,
	}
}

// Type implements Operation.Type.
func (op *CreateUserlistOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateUserlistOperation) Section() string {
	return sectionUserlist
}

// Priority implements Operation.Priority.
func (op *CreateUserlistOperation) Priority() int {
	return PriorityUserlist
}

// Execute creates the userlist section via the Dataplane API.
func (op *CreateUserlistOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeCreateHelper(
		ctx, transactionID, op.Userlist,
		func(r *models.Userlist) string { return r.Name },
		transform.ToAPIUserlist,
		func(ctx context.Context, apiUserlist *dataplaneapi.Userlist, txID string) (*http.Response, error) {
			return wrapAPICallWithVersionOrTransaction(
				ctx, c, txID,
				func() *dataplaneapi.CreateUserlistParams { return &dataplaneapi.CreateUserlistParams{} },
				func(p *dataplaneapi.CreateUserlistParams, tid *string) { p.TransactionId = tid },
				func(p *dataplaneapi.CreateUserlistParams, v *int) { p.Version = v },
				func(ctx context.Context, params *dataplaneapi.CreateUserlistParams) (*http.Response, error) {
					return c.Client().CreateUserlist(ctx, params, *apiUserlist)
				},
			)
		},
		"userlist section",
	)
}

// Describe returns a human-readable description of this operation.
func (op *CreateUserlistOperation) Describe() string {
	name := unknownFallback
	if op.Userlist.Name != "" {
		name = op.Userlist.Name
	}
	return fmt.Sprintf("Create userlist '%s'", name)
}

// DeleteUserlistOperation represents deleting an existing userlist section.
type DeleteUserlistOperation struct {
	Userlist *models.Userlist
}

// NewDeleteUserlistOperation creates a new userlist section deletion operation.
func NewDeleteUserlistOperation(userlist *models.Userlist) *DeleteUserlistOperation {
	return &DeleteUserlistOperation{
		Userlist: userlist,
	}
}

// Type implements Operation.Type.
func (op *DeleteUserlistOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteUserlistOperation) Section() string {
	return sectionUserlist
}

// Priority implements Operation.Priority.
func (op *DeleteUserlistOperation) Priority() int {
	return PriorityUserlist
}

// Execute deletes the userlist section via the Dataplane API.
func (op *DeleteUserlistOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeDeleteHelper(
		ctx, transactionID, op.Userlist,
		func(r *models.Userlist) string { return r.Name },
		func(ctx context.Context, name string, txID string) (*http.Response, error) {
			return wrapAPICallWithVersionOrTransaction(
				ctx, c, txID,
				func() *dataplaneapi.DeleteUserlistParams { return &dataplaneapi.DeleteUserlistParams{} },
				func(p *dataplaneapi.DeleteUserlistParams, tid *string) { p.TransactionId = tid },
				func(p *dataplaneapi.DeleteUserlistParams, v *int) { p.Version = v },
				func(ctx context.Context, params *dataplaneapi.DeleteUserlistParams) (*http.Response, error) {
					return c.Client().DeleteUserlist(ctx, name, params)
				},
			)
		},
		"userlist section",
	)
}

// Describe returns a human-readable description of this operation.
func (op *DeleteUserlistOperation) Describe() string {
	name := unknownFallback
	if op.Userlist.Name != "" {
		name = op.Userlist.Name
	}
	return fmt.Sprintf("Delete userlist '%s'", name)
}
