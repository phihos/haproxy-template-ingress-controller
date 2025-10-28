// Package sections contains section-specific comparison logic and operations
// for HAProxy configuration elements.
package sections

import (
	"context"
	"fmt"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/pkg/dataplane/client"
	"haproxy-template-ic/pkg/dataplane/transform"
	"haproxy-template-ic/pkg/generated/dataplaneapi"
)

// PriorityLogTarget defines the priority for log target operations.
const PriorityLogTarget = 60

const (
	sectionLogTarget = "log-target"
)

// CreateLogTargetFrontendOperation represents creating a new log target in a frontend.
type CreateLogTargetFrontendOperation struct {
	FrontendName string
	LogTarget    *models.LogTarget
	Index        int
}

// NewCreateLogTargetFrontendOperation creates a new log target creation operation for a frontend.
func NewCreateLogTargetFrontendOperation(frontendName string, logTarget *models.LogTarget, index int) *CreateLogTargetFrontendOperation {
	return &CreateLogTargetFrontendOperation{
		FrontendName: frontendName,
		LogTarget:    logTarget,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *CreateLogTargetFrontendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateLogTargetFrontendOperation) Section() string {
	return sectionLogTarget
}

// Priority implements Operation.Priority.
func (op *CreateLogTargetFrontendOperation) Priority() int {
	return PriorityLogTarget
}

// Execute creates the log target via the Dataplane API.
func (op *CreateLogTargetFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.LogTarget == nil {
		return fmt.Errorf("log target is nil")
	}

	// Convert models.LogTarget to dataplaneapi.LogTarget using JSON marshaling
	apiLogTarget := transform.ToAPILogTarget(op.LogTarget)
	if apiLogTarget == nil {
		return fmt.Errorf("failed to transform log target")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateLogTargetFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateLogTargetFrontend API
	resp, err := c.Client().CreateLogTargetFrontend(ctx, op.FrontendName, op.Index, params, *apiLogTarget)
	if err != nil {
		return fmt.Errorf("failed to create log target in frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("log target creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateLogTargetFrontendOperation) Describe() string {
	address := unknownFallback
	if op.LogTarget != nil && op.LogTarget.Address != "" {
		address = op.LogTarget.Address
	}
	return fmt.Sprintf("Create log target (%s) in frontend '%s'", address, op.FrontendName)
}

// DeleteLogTargetFrontendOperation represents deleting a log target from a frontend.
type DeleteLogTargetFrontendOperation struct {
	FrontendName string
	LogTarget    *models.LogTarget
	Index        int
}

// NewDeleteLogTargetFrontendOperation creates a new log target deletion operation for a frontend.
func NewDeleteLogTargetFrontendOperation(frontendName string, logTarget *models.LogTarget, index int) *DeleteLogTargetFrontendOperation {
	return &DeleteLogTargetFrontendOperation{
		FrontendName: frontendName,
		LogTarget:    logTarget,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *DeleteLogTargetFrontendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteLogTargetFrontendOperation) Section() string {
	return sectionLogTarget
}

// Priority implements Operation.Priority.
func (op *DeleteLogTargetFrontendOperation) Priority() int {
	return PriorityLogTarget
}

// Execute deletes the log target via the Dataplane API.
func (op *DeleteLogTargetFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteLogTargetFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteLogTargetFrontend API
	resp, err := c.Client().DeleteLogTargetFrontend(ctx, op.FrontendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete log target from frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("log target deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteLogTargetFrontendOperation) Describe() string {
	address := unknownFallback
	if op.LogTarget != nil && op.LogTarget.Address != "" {
		address = op.LogTarget.Address
	}
	return fmt.Sprintf("Delete log target (%s) from frontend '%s'", address, op.FrontendName)
}

// UpdateLogTargetFrontendOperation represents updating a log target in a frontend.
type UpdateLogTargetFrontendOperation struct {
	FrontendName string
	LogTarget    *models.LogTarget
	Index        int
}

// NewUpdateLogTargetFrontendOperation creates a new log target update operation for a frontend.
func NewUpdateLogTargetFrontendOperation(frontendName string, logTarget *models.LogTarget, index int) *UpdateLogTargetFrontendOperation {
	return &UpdateLogTargetFrontendOperation{
		FrontendName: frontendName,
		LogTarget:    logTarget,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *UpdateLogTargetFrontendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateLogTargetFrontendOperation) Section() string {
	return sectionLogTarget
}

// Priority implements Operation.Priority.
func (op *UpdateLogTargetFrontendOperation) Priority() int {
	return PriorityLogTarget
}

// Execute updates the log target via the Dataplane API.
func (op *UpdateLogTargetFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.LogTarget == nil {
		return fmt.Errorf("log target is nil")
	}

	// Convert models.LogTarget to dataplaneapi.LogTarget using JSON marshaling
	apiLogTarget := transform.ToAPILogTarget(op.LogTarget)
	if apiLogTarget == nil {
		return fmt.Errorf("failed to transform log target")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceLogTargetFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceLogTargetFrontend API
	resp, err := c.Client().ReplaceLogTargetFrontend(ctx, op.FrontendName, op.Index, params, *apiLogTarget)
	if err != nil {
		return fmt.Errorf("failed to update log target in frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("log target update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateLogTargetFrontendOperation) Describe() string {
	address := unknownFallback
	if op.LogTarget != nil && op.LogTarget.Address != "" {
		address = op.LogTarget.Address
	}
	return fmt.Sprintf("Update log target (%s) in frontend '%s'", address, op.FrontendName)
}

// CreateLogTargetBackendOperation represents creating a new log target in a backend.
type CreateLogTargetBackendOperation struct {
	BackendName string
	LogTarget   *models.LogTarget
	Index       int
}

// NewCreateLogTargetBackendOperation creates a new log target creation operation for a backend.
func NewCreateLogTargetBackendOperation(backendName string, logTarget *models.LogTarget, index int) *CreateLogTargetBackendOperation {
	return &CreateLogTargetBackendOperation{
		BackendName: backendName,
		LogTarget:   logTarget,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *CreateLogTargetBackendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateLogTargetBackendOperation) Section() string {
	return sectionLogTarget
}

// Priority implements Operation.Priority.
func (op *CreateLogTargetBackendOperation) Priority() int {
	return PriorityLogTarget
}

// Execute creates the log target via the Dataplane API.
func (op *CreateLogTargetBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.LogTarget == nil {
		return fmt.Errorf("log target is nil")
	}

	// Convert models.LogTarget to dataplaneapi.LogTarget using JSON marshaling
	apiLogTarget := transform.ToAPILogTarget(op.LogTarget)
	if apiLogTarget == nil {
		return fmt.Errorf("failed to transform log target")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateLogTargetBackendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateLogTargetBackend API
	resp, err := c.Client().CreateLogTargetBackend(ctx, op.BackendName, op.Index, params, *apiLogTarget)
	if err != nil {
		return fmt.Errorf("failed to create log target in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("log target creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateLogTargetBackendOperation) Describe() string {
	address := unknownFallback
	if op.LogTarget != nil && op.LogTarget.Address != "" {
		address = op.LogTarget.Address
	}
	return fmt.Sprintf("Create log target (%s) in backend '%s'", address, op.BackendName)
}

// DeleteLogTargetBackendOperation represents deleting a log target from a backend.
type DeleteLogTargetBackendOperation struct {
	BackendName string
	LogTarget   *models.LogTarget
	Index       int
}

// NewDeleteLogTargetBackendOperation creates a new log target deletion operation for a backend.
func NewDeleteLogTargetBackendOperation(backendName string, logTarget *models.LogTarget, index int) *DeleteLogTargetBackendOperation {
	return &DeleteLogTargetBackendOperation{
		BackendName: backendName,
		LogTarget:   logTarget,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *DeleteLogTargetBackendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteLogTargetBackendOperation) Section() string {
	return sectionLogTarget
}

// Priority implements Operation.Priority.
func (op *DeleteLogTargetBackendOperation) Priority() int {
	return PriorityLogTarget
}

// Execute deletes the log target via the Dataplane API.
func (op *DeleteLogTargetBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteLogTargetBackendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteLogTargetBackend API
	resp, err := c.Client().DeleteLogTargetBackend(ctx, op.BackendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete log target from backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("log target deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteLogTargetBackendOperation) Describe() string {
	address := unknownFallback
	if op.LogTarget != nil && op.LogTarget.Address != "" {
		address = op.LogTarget.Address
	}
	return fmt.Sprintf("Delete log target (%s) from backend '%s'", address, op.BackendName)
}

// UpdateLogTargetBackendOperation represents updating a log target in a backend.
type UpdateLogTargetBackendOperation struct {
	BackendName string
	LogTarget   *models.LogTarget
	Index       int
}

// NewUpdateLogTargetBackendOperation creates a new log target update operation for a backend.
func NewUpdateLogTargetBackendOperation(backendName string, logTarget *models.LogTarget, index int) *UpdateLogTargetBackendOperation {
	return &UpdateLogTargetBackendOperation{
		BackendName: backendName,
		LogTarget:   logTarget,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *UpdateLogTargetBackendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateLogTargetBackendOperation) Section() string {
	return sectionLogTarget
}

// Priority implements Operation.Priority.
func (op *UpdateLogTargetBackendOperation) Priority() int {
	return PriorityLogTarget
}

// Execute updates the log target via the Dataplane API.
func (op *UpdateLogTargetBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.LogTarget == nil {
		return fmt.Errorf("log target is nil")
	}

	// Convert models.LogTarget to dataplaneapi.LogTarget using JSON marshaling
	apiLogTarget := transform.ToAPILogTarget(op.LogTarget)
	if apiLogTarget == nil {
		return fmt.Errorf("failed to transform log target")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceLogTargetBackendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceLogTargetBackend API
	resp, err := c.Client().ReplaceLogTargetBackend(ctx, op.BackendName, op.Index, params, *apiLogTarget)
	if err != nil {
		return fmt.Errorf("failed to update log target in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("log target update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateLogTargetBackendOperation) Describe() string {
	address := unknownFallback
	if op.LogTarget != nil && op.LogTarget.Address != "" {
		address = op.LogTarget.Address
	}
	return fmt.Sprintf("Update log target (%s) in backend '%s'", address, op.BackendName)
}
