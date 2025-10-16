// Package sections contains section-specific comparison logic and operations
// for HAProxy configuration elements.
package sections

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/codegen/dataplaneapi"
	"haproxy-template-ic/pkg/dataplane/client"
)

// CreateAclFrontendOperation represents creating a new ACL in a frontend.
type CreateAclFrontendOperation struct {
	FrontendName string
	ACL          *models.ACL
	Index        int
}

// NewCreateAclFrontendOperation creates a new ACL creation operation for a frontend.
func NewCreateAclFrontendOperation(frontendName string, acl *models.ACL, index int) *CreateAclFrontendOperation {
	return &CreateAclFrontendOperation{
		FrontendName: frontendName,
		ACL:          acl,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *CreateAclFrontendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateAclFrontendOperation) Section() string {
	return "acl"
}

// Priority implements Operation.Priority.
func (op *CreateAclFrontendOperation) Priority() int {
	return PriorityACL
}

// Execute creates the ACL via the Dataplane API.
func (op *CreateAclFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.ACL == nil {
		return fmt.Errorf("ACL is nil")
	}

	apiClient := c.Client()

	// Convert models.ACL to dataplaneapi.Acl using JSON marshaling
	var apiACL dataplaneapi.Acl
	data, err := json.Marshal(op.ACL)
	if err != nil {
		return fmt.Errorf("failed to marshal ACL: %w", err)
	}
	if err := json.Unmarshal(data, &apiACL); err != nil {
		return fmt.Errorf("failed to unmarshal ACL: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateAclFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateAclFrontend API
	resp, err := apiClient.CreateAclFrontend(ctx, op.FrontendName, op.Index, params, apiACL)
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
func (op *CreateAclFrontendOperation) Describe() string {
	aclName := "unknown"
	if op.ACL != nil && op.ACL.ACLName != "" {
		aclName = op.ACL.ACLName
	}
	return fmt.Sprintf("Create ACL '%s' in frontend '%s'", aclName, op.FrontendName)
}

// DeleteAclFrontendOperation represents deleting an ACL from a frontend.
type DeleteAclFrontendOperation struct {
	FrontendName string
	ACL          *models.ACL
	Index        int
}

// NewDeleteAclFrontendOperation creates a new ACL deletion operation for a frontend.
func NewDeleteAclFrontendOperation(frontendName string, acl *models.ACL, index int) *DeleteAclFrontendOperation {
	return &DeleteAclFrontendOperation{
		FrontendName: frontendName,
		ACL:          acl,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *DeleteAclFrontendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteAclFrontendOperation) Section() string {
	return "acl"
}

// Priority implements Operation.Priority.
func (op *DeleteAclFrontendOperation) Priority() int {
	return PriorityACL
}

// Execute deletes the ACL via the Dataplane API.
func (op *DeleteAclFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	apiClient := c.Client()

	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteAclFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteAclFrontend API
	resp, err := apiClient.DeleteAclFrontend(ctx, op.FrontendName, op.Index, params)
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
func (op *DeleteAclFrontendOperation) Describe() string {
	aclName := "unknown"
	if op.ACL != nil && op.ACL.ACLName != "" {
		aclName = op.ACL.ACLName
	}
	return fmt.Sprintf("Delete ACL '%s' from frontend '%s'", aclName, op.FrontendName)
}

// UpdateAclFrontendOperation represents updating an ACL in a frontend.
type UpdateAclFrontendOperation struct {
	FrontendName string
	ACL          *models.ACL
	Index        int
}

// NewUpdateAclFrontendOperation creates a new ACL update operation for a frontend.
func NewUpdateAclFrontendOperation(frontendName string, acl *models.ACL, index int) *UpdateAclFrontendOperation {
	return &UpdateAclFrontendOperation{
		FrontendName: frontendName,
		ACL:          acl,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *UpdateAclFrontendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateAclFrontendOperation) Section() string {
	return "acl"
}

// Priority implements Operation.Priority.
func (op *UpdateAclFrontendOperation) Priority() int {
	return PriorityACL
}

// Execute updates the ACL via the Dataplane API.
func (op *UpdateAclFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.ACL == nil {
		return fmt.Errorf("ACL is nil")
	}

	apiClient := c.Client()

	// Convert models.ACL to dataplaneapi.Acl using JSON marshaling
	var apiACL dataplaneapi.Acl
	data, err := json.Marshal(op.ACL)
	if err != nil {
		return fmt.Errorf("failed to marshal ACL: %w", err)
	}
	if err := json.Unmarshal(data, &apiACL); err != nil {
		return fmt.Errorf("failed to unmarshal ACL: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceAclFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceAclFrontend API
	resp, err := apiClient.ReplaceAclFrontend(ctx, op.FrontendName, op.Index, params, apiACL)
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
func (op *UpdateAclFrontendOperation) Describe() string {
	aclName := "unknown"
	if op.ACL != nil && op.ACL.ACLName != "" {
		aclName = op.ACL.ACLName
	}
	return fmt.Sprintf("Update ACL '%s' in frontend '%s'", aclName, op.FrontendName)
}

// CreateAclBackendOperation represents creating a new ACL in a backend.
type CreateAclBackendOperation struct {
	BackendName string
	ACL         *models.ACL
	Index       int
}

// NewCreateAclBackendOperation creates a new ACL creation operation for a backend.
func NewCreateAclBackendOperation(backendName string, acl *models.ACL, index int) *CreateAclBackendOperation {
	return &CreateAclBackendOperation{
		BackendName: backendName,
		ACL:         acl,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *CreateAclBackendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateAclBackendOperation) Section() string {
	return "acl"
}

// Priority implements Operation.Priority.
func (op *CreateAclBackendOperation) Priority() int {
	return PriorityACL
}

// Execute creates the ACL via the Dataplane API.
func (op *CreateAclBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.ACL == nil {
		return fmt.Errorf("ACL is nil")
	}

	apiClient := c.Client()

	// Convert models.ACL to dataplaneapi.Acl using JSON marshaling
	var apiACL dataplaneapi.Acl
	data, err := json.Marshal(op.ACL)
	if err != nil {
		return fmt.Errorf("failed to marshal ACL: %w", err)
	}
	if err := json.Unmarshal(data, &apiACL); err != nil {
		return fmt.Errorf("failed to unmarshal ACL: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateAclBackendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateAclBackend API
	resp, err := apiClient.CreateAclBackend(ctx, op.BackendName, op.Index, params, apiACL)
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
func (op *CreateAclBackendOperation) Describe() string {
	aclName := "unknown"
	if op.ACL != nil && op.ACL.ACLName != "" {
		aclName = op.ACL.ACLName
	}
	return fmt.Sprintf("Create ACL '%s' in backend '%s'", aclName, op.BackendName)
}

// DeleteAclBackendOperation represents deleting an ACL from a backend.
type DeleteAclBackendOperation struct {
	BackendName string
	ACL         *models.ACL
	Index       int
}

// NewDeleteAclBackendOperation creates a new ACL deletion operation for a backend.
func NewDeleteAclBackendOperation(backendName string, acl *models.ACL, index int) *DeleteAclBackendOperation {
	return &DeleteAclBackendOperation{
		BackendName: backendName,
		ACL:         acl,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *DeleteAclBackendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteAclBackendOperation) Section() string {
	return "acl"
}

// Priority implements Operation.Priority.
func (op *DeleteAclBackendOperation) Priority() int {
	return PriorityACL
}

// Execute deletes the ACL via the Dataplane API.
func (op *DeleteAclBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	apiClient := c.Client()

	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteAclBackendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteAclBackend API
	resp, err := apiClient.DeleteAclBackend(ctx, op.BackendName, op.Index, params)
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
func (op *DeleteAclBackendOperation) Describe() string {
	aclName := "unknown"
	if op.ACL != nil && op.ACL.ACLName != "" {
		aclName = op.ACL.ACLName
	}
	return fmt.Sprintf("Delete ACL '%s' from backend '%s'", aclName, op.BackendName)
}

// UpdateAclBackendOperation represents updating an ACL in a backend.
type UpdateAclBackendOperation struct {
	BackendName string
	ACL         *models.ACL
	Index       int
}

// NewUpdateAclBackendOperation creates a new ACL update operation for a backend.
func NewUpdateAclBackendOperation(backendName string, acl *models.ACL, index int) *UpdateAclBackendOperation {
	return &UpdateAclBackendOperation{
		BackendName: backendName,
		ACL:         acl,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *UpdateAclBackendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateAclBackendOperation) Section() string {
	return "acl"
}

// Priority implements Operation.Priority.
func (op *UpdateAclBackendOperation) Priority() int {
	return PriorityACL
}

// Execute updates the ACL via the Dataplane API.
func (op *UpdateAclBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.ACL == nil {
		return fmt.Errorf("ACL is nil")
	}

	apiClient := c.Client()

	// Convert models.ACL to dataplaneapi.Acl using JSON marshaling
	var apiACL dataplaneapi.Acl
	data, err := json.Marshal(op.ACL)
	if err != nil {
		return fmt.Errorf("failed to marshal ACL: %w", err)
	}
	if err := json.Unmarshal(data, &apiACL); err != nil {
		return fmt.Errorf("failed to unmarshal ACL: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceAclBackendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceAclBackend API
	resp, err := apiClient.ReplaceAclBackend(ctx, op.BackendName, op.Index, params, apiACL)
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
func (op *UpdateAclBackendOperation) Describe() string {
	aclName := "unknown"
	if op.ACL != nil && op.ACL.ACLName != "" {
		aclName = op.ACL.ACLName
	}
	return fmt.Sprintf("Update ACL '%s' in backend '%s'", aclName, op.BackendName)
}
