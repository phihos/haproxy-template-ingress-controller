// Package sections contains section-specific comparison logic and operations
// for HAProxy configuration elements.
package sections

import (
	"context"
	"fmt"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/codegen/dataplaneapi"
	"haproxy-template-ic/pkg/dataplane/client"
	"haproxy-template-ic/pkg/dataplane/transform"
)

const (
	sectionACL      = "acl"
	unknownFallback = "unknown"
)

// CreateAclFrontendOperation represents creating a new ACL in a frontend.
type CreateACLFrontendOperation struct {
	FrontendName string
	ACL          *models.ACL
	Index        int
}

// NewCreateAclFrontendOperation creates a new ACL creation operation for a frontend.
func NewCreateACLFrontendOperation(frontendName string, acl *models.ACL, index int) *CreateACLFrontendOperation {
	return &CreateACLFrontendOperation{
		FrontendName: frontendName,
		ACL:          acl,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *CreateACLFrontendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateACLFrontendOperation) Section() string {
	return sectionACL
}

// Priority implements Operation.Priority.
func (op *CreateACLFrontendOperation) Priority() int {
	return PriorityACL
}

// Execute creates the ACL via the Dataplane API.
func (op *CreateACLFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.ACL == nil {
		return fmt.Errorf("ACL is nil")
	}

	// Convert models.ACL to dataplaneapi.Acl using transform package
	apiACL := transform.ToAPIACL(op.ACL)
	if apiACL == nil {
		return fmt.Errorf("failed to transform ACL")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateAclFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateAclFrontend API
	resp, err := c.Client().CreateAclFrontend(ctx, op.FrontendName, op.Index, params, *apiACL)
	if err != nil {
		return fmt.Errorf("failed to create ACL in frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("ACL creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateACLFrontendOperation) Describe() string {
	aclName := unknownFallback
	if op.ACL != nil && op.ACL.ACLName != "" {
		aclName = op.ACL.ACLName
	}
	return fmt.Sprintf("Create ACL '%s' in frontend '%s'", aclName, op.FrontendName)
}

// DeleteAclFrontendOperation represents deleting an ACL from a frontend.
type DeleteACLFrontendOperation struct {
	FrontendName string
	ACL          *models.ACL
	Index        int
}

// NewDeleteAclFrontendOperation creates a new ACL deletion operation for a frontend.
func NewDeleteACLFrontendOperation(frontendName string, acl *models.ACL, index int) *DeleteACLFrontendOperation {
	return &DeleteACLFrontendOperation{
		FrontendName: frontendName,
		ACL:          acl,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *DeleteACLFrontendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteACLFrontendOperation) Section() string {
	return sectionACL
}

// Priority implements Operation.Priority.
func (op *DeleteACLFrontendOperation) Priority() int {
	return PriorityACL
}

// Execute deletes the ACL via the Dataplane API.
func (op *DeleteACLFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteAclFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteAclFrontend API
	resp, err := c.Client().DeleteAclFrontend(ctx, op.FrontendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete ACL from frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("ACL deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteACLFrontendOperation) Describe() string {
	aclName := unknownFallback
	if op.ACL != nil && op.ACL.ACLName != "" {
		aclName = op.ACL.ACLName
	}
	return fmt.Sprintf("Delete ACL '%s' from frontend '%s'", aclName, op.FrontendName)
}

// UpdateAclFrontendOperation represents updating an ACL in a frontend.
type UpdateACLFrontendOperation struct {
	FrontendName string
	ACL          *models.ACL
	Index        int
}

// NewUpdateAclFrontendOperation creates a new ACL update operation for a frontend.
func NewUpdateACLFrontendOperation(frontendName string, acl *models.ACL, index int) *UpdateACLFrontendOperation {
	return &UpdateACLFrontendOperation{
		FrontendName: frontendName,
		ACL:          acl,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *UpdateACLFrontendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateACLFrontendOperation) Section() string {
	return sectionACL
}

// Priority implements Operation.Priority.
func (op *UpdateACLFrontendOperation) Priority() int {
	return PriorityACL
}

// Execute updates the ACL via the Dataplane API.
func (op *UpdateACLFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.ACL == nil {
		return fmt.Errorf("ACL is nil")
	}

	// Convert models.ACL to dataplaneapi.Acl using transform package
	apiACL := transform.ToAPIACL(op.ACL)
	if apiACL == nil {
		return fmt.Errorf("failed to transform ACL")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceAclFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceAclFrontend API
	resp, err := c.Client().ReplaceAclFrontend(ctx, op.FrontendName, op.Index, params, *apiACL)
	if err != nil {
		return fmt.Errorf("failed to update ACL in frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("ACL update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateACLFrontendOperation) Describe() string {
	aclName := unknownFallback
	if op.ACL != nil && op.ACL.ACLName != "" {
		aclName = op.ACL.ACLName
	}
	return fmt.Sprintf("Update ACL '%s' in frontend '%s'", aclName, op.FrontendName)
}

// CreateAclBackendOperation represents creating a new ACL in a backend.
type CreateACLBackendOperation struct {
	BackendName string
	ACL         *models.ACL
	Index       int
}

// NewCreateAclBackendOperation creates a new ACL creation operation for a backend.
func NewCreateACLBackendOperation(backendName string, acl *models.ACL, index int) *CreateACLBackendOperation {
	return &CreateACLBackendOperation{
		BackendName: backendName,
		ACL:         acl,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *CreateACLBackendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateACLBackendOperation) Section() string {
	return sectionACL
}

// Priority implements Operation.Priority.
func (op *CreateACLBackendOperation) Priority() int {
	return PriorityACL
}

// Execute creates the ACL via the Dataplane API.
func (op *CreateACLBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.ACL == nil {
		return fmt.Errorf("ACL is nil")
	}

	// Convert models.ACL to dataplaneapi.Acl using transform package
	apiACL := transform.ToAPIACL(op.ACL)
	if apiACL == nil {
		return fmt.Errorf("failed to transform ACL")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateAclBackendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateAclBackend API
	resp, err := c.Client().CreateAclBackend(ctx, op.BackendName, op.Index, params, *apiACL)
	if err != nil {
		return fmt.Errorf("failed to create ACL in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("ACL creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateACLBackendOperation) Describe() string {
	aclName := unknownFallback
	if op.ACL != nil && op.ACL.ACLName != "" {
		aclName = op.ACL.ACLName
	}
	return fmt.Sprintf("Create ACL '%s' in backend '%s'", aclName, op.BackendName)
}

// DeleteAclBackendOperation represents deleting an ACL from a backend.
type DeleteACLBackendOperation struct {
	BackendName string
	ACL         *models.ACL
	Index       int
}

// NewDeleteAclBackendOperation creates a new ACL deletion operation for a backend.
func NewDeleteACLBackendOperation(backendName string, acl *models.ACL, index int) *DeleteACLBackendOperation {
	return &DeleteACLBackendOperation{
		BackendName: backendName,
		ACL:         acl,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *DeleteACLBackendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteACLBackendOperation) Section() string {
	return sectionACL
}

// Priority implements Operation.Priority.
func (op *DeleteACLBackendOperation) Priority() int {
	return PriorityACL
}

// Execute deletes the ACL via the Dataplane API.
func (op *DeleteACLBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteAclBackendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteAclBackend API
	resp, err := c.Client().DeleteAclBackend(ctx, op.BackendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete ACL from backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("ACL deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteACLBackendOperation) Describe() string {
	aclName := unknownFallback
	if op.ACL != nil && op.ACL.ACLName != "" {
		aclName = op.ACL.ACLName
	}
	return fmt.Sprintf("Delete ACL '%s' from backend '%s'", aclName, op.BackendName)
}

// UpdateAclBackendOperation represents updating an ACL in a backend.
type UpdateACLBackendOperation struct {
	BackendName string
	ACL         *models.ACL
	Index       int
}

// NewUpdateAclBackendOperation creates a new ACL update operation for a backend.
func NewUpdateACLBackendOperation(backendName string, acl *models.ACL, index int) *UpdateACLBackendOperation {
	return &UpdateACLBackendOperation{
		BackendName: backendName,
		ACL:         acl,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *UpdateACLBackendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateACLBackendOperation) Section() string {
	return sectionACL
}

// Priority implements Operation.Priority.
func (op *UpdateACLBackendOperation) Priority() int {
	return PriorityACL
}

// Execute updates the ACL via the Dataplane API.
func (op *UpdateACLBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.ACL == nil {
		return fmt.Errorf("ACL is nil")
	}

	// Convert models.ACL to dataplaneapi.Acl using transform package
	apiACL := transform.ToAPIACL(op.ACL)
	if apiACL == nil {
		return fmt.Errorf("failed to transform ACL")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceAclBackendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceAclBackend API
	resp, err := c.Client().ReplaceAclBackend(ctx, op.BackendName, op.Index, params, *apiACL)
	if err != nil {
		return fmt.Errorf("failed to update ACL in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("ACL update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateACLBackendOperation) Describe() string {
	aclName := unknownFallback
	if op.ACL != nil && op.ACL.ACLName != "" {
		aclName = op.ACL.ACLName
	}
	return fmt.Sprintf("Update ACL '%s' in backend '%s'", aclName, op.BackendName)
}
