//nolint:dupl // Section operation files follow similar patterns - type-specific HAProxy API wrappers
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
	if op.User == nil {
		return fmt.Errorf("user is nil")
	}
	if op.User.Username == "" {
		return fmt.Errorf("username is empty")
	}
	if op.UserlistName == "" {
		return fmt.Errorf("userlist name is empty")
	}

	apiClient := c.Client()

	// Convert models.User to dataplaneapi.User using transform package
	apiUser := transform.ToAPIUser(op.User)
	if apiUser == nil {
		return fmt.Errorf("failed to transform user")
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.CreateUserParams{
		Userlist: op.UserlistName,
	}

	var resp *http.Response
	var err error

	if transactionID != "" {
		// Transaction path: use transaction ID
		params.TransactionId = &transactionID
		resp, err = apiClient.CreateUser(ctx, params, *apiUser)
	} else {
		// Runtime API path: use version with automatic retry on conflicts
		resp, err = client.ExecuteWithVersion(ctx, c, func(ctx context.Context, version int) (*http.Response, error) {
			params.Version = &version
			return apiClient.CreateUser(ctx, params, *apiUser)
		})
	}

	if err != nil {
		return fmt.Errorf("failed to create user '%s' in userlist '%s': %w", op.User.Username, op.UserlistName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("user creation failed with status %d", resp.StatusCode)
	}

	return nil
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
	if op.User == nil {
		return fmt.Errorf("user is nil")
	}
	if op.User.Username == "" {
		return fmt.Errorf("username is empty")
	}
	if op.UserlistName == "" {
		return fmt.Errorf("userlist name is empty")
	}

	apiClient := c.Client()

	// Convert models.User to dataplaneapi.User using transform package
	apiUser := transform.ToAPIUser(op.User)
	if apiUser == nil {
		return fmt.Errorf("failed to transform user")
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.ReplaceUserParams{
		Userlist: op.UserlistName,
	}

	var resp *http.Response
	var err error

	if transactionID != "" {
		// Transaction path: use transaction ID
		params.TransactionId = &transactionID
		resp, err = apiClient.ReplaceUser(ctx, op.User.Username, params, *apiUser)
	} else {
		// Runtime API path: use version with automatic retry on conflicts
		resp, err = client.ExecuteWithVersion(ctx, c, func(ctx context.Context, version int) (*http.Response, error) {
			params.Version = &version
			return apiClient.ReplaceUser(ctx, op.User.Username, params, *apiUser)
		})
	}

	if err != nil {
		return fmt.Errorf("failed to replace user '%s' in userlist '%s': %w", op.User.Username, op.UserlistName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("user replacement failed with status %d", resp.StatusCode)
	}

	return nil
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
//
//nolint:dupl // Similar pattern to other section operation Execute methods - each handles different API endpoints and contexts
func (op *DeleteUserOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.User == nil {
		return fmt.Errorf("user is nil")
	}
	if op.User.Username == "" {
		return fmt.Errorf("username is empty")
	}
	if op.UserlistName == "" {
		return fmt.Errorf("userlist name is empty")
	}

	apiClient := c.Client()

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.DeleteUserParams{
		Userlist: op.UserlistName,
	}

	var resp *http.Response
	var err error

	if transactionID != "" {
		// Transaction path: use transaction ID
		params.TransactionId = &transactionID
		resp, err = apiClient.DeleteUser(ctx, op.User.Username, params)
	} else {
		// Runtime API path: use version with automatic retry on conflicts
		resp, err = client.ExecuteWithVersion(ctx, c, func(ctx context.Context, version int) (*http.Response, error) {
			params.Version = &version
			return apiClient.DeleteUser(ctx, op.User.Username, params)
		})
	}

	if err != nil {
		return fmt.Errorf("failed to delete user '%s' from userlist '%s': %w", op.User.Username, op.UserlistName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("user deletion failed with status %d", resp.StatusCode)
	}

	return nil
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
