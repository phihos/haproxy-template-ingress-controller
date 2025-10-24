// Package sections contains section-specific comparison logic and operations
// for HAProxy configuration elements.
//
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

// PriorityFilter defines the priority for filter operations.
const PriorityFilter = 60

const (
	sectionFilter = "filter"
)

// CreateFilterFrontendOperation represents creating a new filter in a frontend.
type CreateFilterFrontendOperation struct {
	FrontendName string
	Filter       *models.Filter
	Index        int
}

// NewCreateFilterFrontendOperation creates a new filter creation operation for a frontend.
func NewCreateFilterFrontendOperation(frontendName string, filter *models.Filter, index int) *CreateFilterFrontendOperation {
	return &CreateFilterFrontendOperation{
		FrontendName: frontendName,
		Filter:       filter,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *CreateFilterFrontendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateFilterFrontendOperation) Section() string {
	return sectionFilter
}

// Priority implements Operation.Priority.
func (op *CreateFilterFrontendOperation) Priority() int {
	return PriorityFilter
}

// Execute creates the filter via the Dataplane API.
//
//nolint:dupl // Similar pattern to other filter operation Execute methods - each handles different API endpoints and contexts
func (op *CreateFilterFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Filter == nil {
		return fmt.Errorf("filter is nil")
	}

	apiClient := c.Client()

	// Convert models.Filter to dataplaneapi.Filter using JSON marshaling
	apiFilter := transform.ToAPIFilter(op.Filter)
	if apiFilter == nil {
		return fmt.Errorf("failed to transform filter")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateFilterFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateFilterFrontend API
	resp, err := apiClient.CreateFilterFrontend(ctx, op.FrontendName, op.Index, params, *apiFilter)
	if err != nil {
		return fmt.Errorf("failed to create filter in frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("filter creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateFilterFrontendOperation) Describe() string {
	filterType := unknownFallback
	if op.Filter != nil && op.Filter.Type != "" {
		filterType = op.Filter.Type
	}
	return fmt.Sprintf("Create filter (%s) in frontend '%s'", filterType, op.FrontendName)
}

// DeleteFilterFrontendOperation represents deleting a filter from a frontend.
type DeleteFilterFrontendOperation struct {
	FrontendName string
	Filter       *models.Filter
	Index        int
}

// NewDeleteFilterFrontendOperation creates a new filter deletion operation for a frontend.
func NewDeleteFilterFrontendOperation(frontendName string, filter *models.Filter, index int) *DeleteFilterFrontendOperation {
	return &DeleteFilterFrontendOperation{
		FrontendName: frontendName,
		Filter:       filter,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *DeleteFilterFrontendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteFilterFrontendOperation) Section() string {
	return sectionFilter
}

// Priority implements Operation.Priority.
func (op *DeleteFilterFrontendOperation) Priority() int {
	return PriorityFilter
}

// Execute deletes the filter via the Dataplane API.
func (op *DeleteFilterFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	apiClient := c.Client()

	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteFilterFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteFilterFrontend API
	resp, err := apiClient.DeleteFilterFrontend(ctx, op.FrontendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete filter from frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("filter deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteFilterFrontendOperation) Describe() string {
	filterType := unknownFallback
	if op.Filter != nil && op.Filter.Type != "" {
		filterType = op.Filter.Type
	}
	return fmt.Sprintf("Delete filter (%s) from frontend '%s'", filterType, op.FrontendName)
}

// UpdateFilterFrontendOperation represents updating a filter in a frontend.
type UpdateFilterFrontendOperation struct {
	FrontendName string
	Filter       *models.Filter
	Index        int
}

// NewUpdateFilterFrontendOperation creates a new filter update operation for a frontend.
func NewUpdateFilterFrontendOperation(frontendName string, filter *models.Filter, index int) *UpdateFilterFrontendOperation {
	return &UpdateFilterFrontendOperation{
		FrontendName: frontendName,
		Filter:       filter,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *UpdateFilterFrontendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateFilterFrontendOperation) Section() string {
	return sectionFilter
}

// Priority implements Operation.Priority.
func (op *UpdateFilterFrontendOperation) Priority() int {
	return PriorityFilter
}

// Execute updates the filter via the Dataplane API.
//
//nolint:dupl // Similar pattern to other filter operation Execute methods - each handles different API endpoints and contexts
func (op *UpdateFilterFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Filter == nil {
		return fmt.Errorf("filter is nil")
	}

	apiClient := c.Client()

	// Convert models.Filter to dataplaneapi.Filter using JSON marshaling
	apiFilter := transform.ToAPIFilter(op.Filter)
	if apiFilter == nil {
		return fmt.Errorf("failed to transform filter")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceFilterFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceFilterFrontend API
	resp, err := apiClient.ReplaceFilterFrontend(ctx, op.FrontendName, op.Index, params, *apiFilter)
	if err != nil {
		return fmt.Errorf("failed to update filter in frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("filter update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateFilterFrontendOperation) Describe() string {
	filterType := unknownFallback
	if op.Filter != nil && op.Filter.Type != "" {
		filterType = op.Filter.Type
	}
	return fmt.Sprintf("Update filter (%s) in frontend '%s'", filterType, op.FrontendName)
}

// CreateFilterBackendOperation represents creating a new filter in a backend.
type CreateFilterBackendOperation struct {
	BackendName string
	Filter      *models.Filter
	Index       int
}

// NewCreateFilterBackendOperation creates a new filter creation operation for a backend.
func NewCreateFilterBackendOperation(backendName string, filter *models.Filter, index int) *CreateFilterBackendOperation {
	return &CreateFilterBackendOperation{
		BackendName: backendName,
		Filter:      filter,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *CreateFilterBackendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateFilterBackendOperation) Section() string {
	return sectionFilter
}

// Priority implements Operation.Priority.
func (op *CreateFilterBackendOperation) Priority() int {
	return PriorityFilter
}

// Execute creates the filter via the Dataplane API.
//
//nolint:dupl // Similar pattern to other filter operation Execute methods - each handles different API endpoints and contexts
func (op *CreateFilterBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Filter == nil {
		return fmt.Errorf("filter is nil")
	}

	apiClient := c.Client()

	// Convert models.Filter to dataplaneapi.Filter using JSON marshaling
	apiFilter := transform.ToAPIFilter(op.Filter)
	if apiFilter == nil {
		return fmt.Errorf("failed to transform filter")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateFilterBackendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateFilterBackend API
	resp, err := apiClient.CreateFilterBackend(ctx, op.BackendName, op.Index, params, *apiFilter)
	if err != nil {
		return fmt.Errorf("failed to create filter in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("filter creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateFilterBackendOperation) Describe() string {
	filterType := unknownFallback
	if op.Filter != nil && op.Filter.Type != "" {
		filterType = op.Filter.Type
	}
	return fmt.Sprintf("Create filter (%s) in backend '%s'", filterType, op.BackendName)
}

// DeleteFilterBackendOperation represents deleting a filter from a backend.
type DeleteFilterBackendOperation struct {
	BackendName string
	Filter      *models.Filter
	Index       int
}

// NewDeleteFilterBackendOperation creates a new filter deletion operation for a backend.
func NewDeleteFilterBackendOperation(backendName string, filter *models.Filter, index int) *DeleteFilterBackendOperation {
	return &DeleteFilterBackendOperation{
		BackendName: backendName,
		Filter:      filter,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *DeleteFilterBackendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteFilterBackendOperation) Section() string {
	return sectionFilter
}

// Priority implements Operation.Priority.
func (op *DeleteFilterBackendOperation) Priority() int {
	return PriorityFilter
}

// Execute deletes the filter via the Dataplane API.
func (op *DeleteFilterBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	apiClient := c.Client()

	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteFilterBackendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteFilterBackend API
	resp, err := apiClient.DeleteFilterBackend(ctx, op.BackendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete filter from backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("filter deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteFilterBackendOperation) Describe() string {
	filterType := unknownFallback
	if op.Filter != nil && op.Filter.Type != "" {
		filterType = op.Filter.Type
	}
	return fmt.Sprintf("Delete filter (%s) from backend '%s'", filterType, op.BackendName)
}

// UpdateFilterBackendOperation represents updating a filter in a backend.
type UpdateFilterBackendOperation struct {
	BackendName string
	Filter      *models.Filter
	Index       int
}

// NewUpdateFilterBackendOperation creates a new filter update operation for a backend.
func NewUpdateFilterBackendOperation(backendName string, filter *models.Filter, index int) *UpdateFilterBackendOperation {
	return &UpdateFilterBackendOperation{
		BackendName: backendName,
		Filter:      filter,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *UpdateFilterBackendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateFilterBackendOperation) Section() string {
	return sectionFilter
}

// Priority implements Operation.Priority.
func (op *UpdateFilterBackendOperation) Priority() int {
	return PriorityFilter
}

// Execute updates the filter via the Dataplane API.
//
//nolint:dupl // Similar pattern to other filter operation Execute methods - each handles different API endpoints and contexts
func (op *UpdateFilterBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Filter == nil {
		return fmt.Errorf("filter is nil")
	}

	apiClient := c.Client()

	// Convert models.Filter to dataplaneapi.Filter using JSON marshaling
	apiFilter := transform.ToAPIFilter(op.Filter)
	if apiFilter == nil {
		return fmt.Errorf("failed to transform filter")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceFilterBackendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceFilterBackend API
	resp, err := apiClient.ReplaceFilterBackend(ctx, op.BackendName, op.Index, params, *apiFilter)
	if err != nil {
		return fmt.Errorf("failed to update filter in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("filter update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateFilterBackendOperation) Describe() string {
	filterType := unknownFallback
	if op.Filter != nil && op.Filter.Type != "" {
		filterType = op.Filter.Type
	}
	return fmt.Sprintf("Update filter (%s) in backend '%s'", filterType, op.BackendName)
}
