//nolint:dupl // Section operation files follow similar patterns - type-specific HAProxy API wrappers
package sections

import (
	"context"
	"fmt"

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
	if op.Userlist == nil {
		return fmt.Errorf("userlist section is nil")
	}
	if op.Userlist.Name == "" {
		return fmt.Errorf("userlist section name is empty")
	}

	apiClient := c.Client()

	// Convert models.Userlist to dataplaneapi.Userlist using transform package
	apiUserlist := transform.ToAPIUserlist(op.Userlist)
	if apiUserlist == nil {
		return fmt.Errorf("failed to transform userlist section")
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.CreateUserlistParams{}
	if transactionID != "" {
		params.TransactionId = &transactionID
	} else {
		v, err := c.GetVersion(ctx)
		if err != nil {
			return fmt.Errorf("failed to get version: %w", err)
		}
		version := int(v)
		params.Version = &version
	}

	// Call the CreateUserlist API
	resp, err := apiClient.CreateUserlist(ctx, params, *apiUserlist)
	if err != nil {
		return fmt.Errorf("failed to create userlist section '%s': %w", op.Userlist.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("userlist section creation failed with status %d", resp.StatusCode)
	}

	return nil
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
//
//nolint:dupl // Similar pattern to other section operation Execute methods - each handles different API endpoints and contexts
func (op *DeleteUserlistOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Userlist == nil {
		return fmt.Errorf("userlist section is nil")
	}
	if op.Userlist.Name == "" {
		return fmt.Errorf("userlist section name is empty")
	}

	apiClient := c.Client()

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.DeleteUserlistParams{}
	if transactionID != "" {
		params.TransactionId = &transactionID
	} else {
		v, err := c.GetVersion(ctx)
		if err != nil {
			return fmt.Errorf("failed to get version: %w", err)
		}
		version := int(v)
		params.Version = &version
	}

	// Call the DeleteUserlist API
	resp, err := apiClient.DeleteUserlist(ctx, op.Userlist.Name, params)
	if err != nil {
		return fmt.Errorf("failed to delete userlist section '%s': %w", op.Userlist.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("userlist section deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteUserlistOperation) Describe() string {
	name := unknownFallback
	if op.Userlist.Name != "" {
		name = op.Userlist.Name
	}
	return fmt.Sprintf("Delete userlist '%s'", name)
}
