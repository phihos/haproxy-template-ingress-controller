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

// PriorityUser defines priority for user operations within userlists.
// Users must be created after their parent userlist exists.
const PriorityUser = 15

const (
	sectionUser = "user"
)

// CreateUserOperation represents creating a new user in a userlist.
type CreateUserOperation struct {
	UserlistName string
	User         *models.User
}

// NewCreateUserOperation creates a new user creation operation.
func NewCreateUserOperation(userlistName string, user *models.User) *CreateUserOperation {
	return &CreateUserOperation{
		UserlistName: userlistName,
		User:         user,
	}
}

// Type implements Operation.Type.
func (op *CreateUserOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateUserOperation) Section() string {
	return sectionUser
}

// Priority implements Operation.Priority.
func (op *CreateUserOperation) Priority() int {
	return PriorityUser
}

// Execute creates the user via the Dataplane API.
func (op *CreateUserOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeCreateChildHelper(
		ctx, c, transactionID, op.User, op.UserlistName,
		func(m *models.User) string { return m.Username },
		transform.ToAPIUser,
		func(parent string) *dataplaneapi.CreateUserParams {
			return &dataplaneapi.CreateUserParams{Userlist: parent}
		},
		func(p *dataplaneapi.CreateUserParams, tid *string) { p.TransactionId = tid },
		func(p *dataplaneapi.CreateUserParams, v *int) { p.Version = v },
		func(ctx context.Context, params *dataplaneapi.CreateUserParams, apiModel dataplaneapi.User) (*http.Response, error) {
			return c.Client().CreateUser(ctx, params, apiModel)
		},
		"user",
		"userlist",
	)
}

// Describe returns a human-readable description of this operation.
func (op *CreateUserOperation) Describe() string {
	username := unknownFallback
	if op.User != nil && op.User.Username != "" {
		username = op.User.Username
	}
	userlist := unknownFallback
	if op.UserlistName != "" {
		userlist = op.UserlistName
	}
	return fmt.Sprintf("Create user '%s' in userlist '%s'", username, userlist)
}

// ReplaceUserOperation represents updating an existing user in a userlist.
type ReplaceUserOperation struct {
	UserlistName string
	User         *models.User
}

// NewReplaceUserOperation creates a new user update operation.
func NewReplaceUserOperation(userlistName string, user *models.User) *ReplaceUserOperation {
	return &ReplaceUserOperation{
		UserlistName: userlistName,
		User:         user,
	}
}

// Type implements Operation.Type.
func (op *ReplaceUserOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *ReplaceUserOperation) Section() string {
	return sectionUser
}

// Priority implements Operation.Priority.
func (op *ReplaceUserOperation) Priority() int {
	return PriorityUser
}

// Execute replaces the user via the Dataplane API.
func (op *ReplaceUserOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeReplaceChildHelper(
		ctx, c, transactionID, op.User, op.UserlistName,
		func(m *models.User) string { return m.Username },
		transform.ToAPIUser,
		func(parent string) *dataplaneapi.ReplaceUserParams {
			return &dataplaneapi.ReplaceUserParams{Userlist: parent}
		},
		func(p *dataplaneapi.ReplaceUserParams, tid *string) { p.TransactionId = tid },
		func(p *dataplaneapi.ReplaceUserParams, v *int) { p.Version = v },
		func(ctx context.Context, name string, params *dataplaneapi.ReplaceUserParams, apiModel dataplaneapi.User) (*http.Response, error) {
			return c.Client().ReplaceUser(ctx, name, params, apiModel)
		},
		"user",
		"userlist",
	)
}

// Describe returns a human-readable description of this operation.
func (op *ReplaceUserOperation) Describe() string {
	username := unknownFallback
	if op.User != nil && op.User.Username != "" {
		username = op.User.Username
	}
	userlist := unknownFallback
	if op.UserlistName != "" {
		userlist = op.UserlistName
	}
	return fmt.Sprintf("Replace user '%s' in userlist '%s'", username, userlist)
}

// DeleteUserOperation represents deleting an existing user from a userlist.
type DeleteUserOperation struct {
	UserlistName string
	User         *models.User
}

// NewDeleteUserOperation creates a new user deletion operation.
func NewDeleteUserOperation(userlistName string, user *models.User) *DeleteUserOperation {
	return &DeleteUserOperation{
		UserlistName: userlistName,
		User:         user,
	}
}

// Type implements Operation.Type.
func (op *DeleteUserOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteUserOperation) Section() string {
	return sectionUser
}

// Priority implements Operation.Priority.
func (op *DeleteUserOperation) Priority() int {
	return PriorityUser
}

// Execute deletes the user via the Dataplane API.
func (op *DeleteUserOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeDeleteChildHelper(
		ctx, c, transactionID, op.User, op.UserlistName,
		func(m *models.User) string { return m.Username },
		func(parent string) *dataplaneapi.DeleteUserParams {
			return &dataplaneapi.DeleteUserParams{Userlist: parent}
		},
		func(p *dataplaneapi.DeleteUserParams, tid *string) { p.TransactionId = tid },
		func(p *dataplaneapi.DeleteUserParams, v *int) { p.Version = v },
		func(ctx context.Context, name string, params *dataplaneapi.DeleteUserParams) (*http.Response, error) {
			return c.Client().DeleteUser(ctx, name, params)
		},
		"user",
		"userlist",
	)
}

// Describe returns a human-readable description of this operation.
func (op *DeleteUserOperation) Describe() string {
	username := unknownFallback
	if op.User != nil && op.User.Username != "" {
		username = op.User.Username
	}
	userlist := unknownFallback
	if op.UserlistName != "" {
		userlist = op.UserlistName
	}
	return fmt.Sprintf("Delete user '%s' from userlist '%s'", username, userlist)
}
