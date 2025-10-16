package sections

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/codegen/dataplaneapi"
	"haproxy-template-ic/pkg/dataplane/client"
)

// PriorityHTTPErrors defines priority for http-errors sections.
// HTTPErrors are standalone sections that should be created after defaults
// but before frontends/backends that might reference them.
const PriorityHTTPErrors = 25

// CreateHTTPErrorsOperation represents creating a new http-errors section.
type CreateHTTPErrorsOperation struct {
	HTTPErrors *models.HTTPErrorsSection
}

// NewCreateHTTPErrorsOperation creates a new http-errors section creation operation.
func NewCreateHTTPErrorsOperation(httpErrors *models.HTTPErrorsSection) *CreateHTTPErrorsOperation {
	return &CreateHTTPErrorsOperation{
		HTTPErrors: httpErrors,
	}
}

// Type implements Operation.Type.
func (op *CreateHTTPErrorsOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateHTTPErrorsOperation) Section() string {
	return "http-errors"
}

// Priority implements Operation.Priority.
func (op *CreateHTTPErrorsOperation) Priority() int {
	return PriorityHTTPErrors
}

// Execute creates the http-errors section via the Dataplane API.
func (op *CreateHTTPErrorsOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.HTTPErrors == nil {
		return fmt.Errorf("http-errors section is nil")
	}
	if op.HTTPErrors.Name == "" {
		return fmt.Errorf("http-errors section name is empty")
	}

	apiClient := c.Client()

	// Convert models.HTTPErrorsSection to dataplaneapi.HttpErrorsSection using JSON marshaling
	var apiHTTPErrors dataplaneapi.HttpErrorsSection
	data, err := json.Marshal(op.HTTPErrors)
	if err != nil {
		return fmt.Errorf("failed to marshal http-errors section: %w", err)
	}
	if err := json.Unmarshal(data, &apiHTTPErrors); err != nil {
		return fmt.Errorf("failed to unmarshal http-errors section: %w", err)
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.CreateHTTPErrorsSectionParams{}
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

	// Call the CreateHTTPErrorsSection API
	resp, err := apiClient.CreateHTTPErrorsSection(ctx, params, apiHTTPErrors)
	if err != nil {
		return fmt.Errorf("failed to create http-errors section '%s': %w", op.HTTPErrors.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("http-errors section creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateHTTPErrorsOperation) Describe() string {
	name := "unknown"
	if op.HTTPErrors.Name != "" {
		name = op.HTTPErrors.Name
	}
	return fmt.Sprintf("Create http-errors section '%s'", name)
}

// DeleteHTTPErrorsOperation represents deleting an existing http-errors section.
type DeleteHTTPErrorsOperation struct {
	HTTPErrors *models.HTTPErrorsSection
}

// NewDeleteHTTPErrorsOperation creates a new http-errors section deletion operation.
func NewDeleteHTTPErrorsOperation(httpErrors *models.HTTPErrorsSection) *DeleteHTTPErrorsOperation {
	return &DeleteHTTPErrorsOperation{
		HTTPErrors: httpErrors,
	}
}

// Type implements Operation.Type.
func (op *DeleteHTTPErrorsOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteHTTPErrorsOperation) Section() string {
	return "http-errors"
}

// Priority implements Operation.Priority.
func (op *DeleteHTTPErrorsOperation) Priority() int {
	return PriorityHTTPErrors
}

// Execute deletes the http-errors section via the Dataplane API.
func (op *DeleteHTTPErrorsOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.HTTPErrors == nil {
		return fmt.Errorf("http-errors section is nil")
	}
	if op.HTTPErrors.Name == "" {
		return fmt.Errorf("http-errors section name is empty")
	}

	apiClient := c.Client()

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.DeleteHTTPErrorsSectionParams{}
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

	// Call the DeleteHTTPErrorsSection API
	resp, err := apiClient.DeleteHTTPErrorsSection(ctx, op.HTTPErrors.Name, params)
	if err != nil {
		return fmt.Errorf("failed to delete http-errors section '%s': %w", op.HTTPErrors.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("http-errors section deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteHTTPErrorsOperation) Describe() string {
	name := "unknown"
	if op.HTTPErrors.Name != "" {
		name = op.HTTPErrors.Name
	}
	return fmt.Sprintf("Delete http-errors section '%s'", name)
}

// UpdateHTTPErrorsOperation represents updating an existing http-errors section.
type UpdateHTTPErrorsOperation struct {
	HTTPErrors *models.HTTPErrorsSection
}

// NewUpdateHTTPErrorsOperation creates a new http-errors section update operation.
func NewUpdateHTTPErrorsOperation(httpErrors *models.HTTPErrorsSection) *UpdateHTTPErrorsOperation {
	return &UpdateHTTPErrorsOperation{
		HTTPErrors: httpErrors,
	}
}

// Type implements Operation.Type.
func (op *UpdateHTTPErrorsOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateHTTPErrorsOperation) Section() string {
	return "http-errors"
}

// Priority implements Operation.Priority.
func (op *UpdateHTTPErrorsOperation) Priority() int {
	return PriorityHTTPErrors
}

// Execute updates the http-errors section via the Dataplane API.
func (op *UpdateHTTPErrorsOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.HTTPErrors == nil {
		return fmt.Errorf("http-errors section is nil")
	}
	if op.HTTPErrors.Name == "" {
		return fmt.Errorf("http-errors section name is empty")
	}

	apiClient := c.Client()

	// Convert models.HTTPErrorsSection to dataplaneapi.HttpErrorsSection using JSON marshaling
	var apiHTTPErrors dataplaneapi.HttpErrorsSection
	data, err := json.Marshal(op.HTTPErrors)
	if err != nil {
		return fmt.Errorf("failed to marshal http-errors section: %w", err)
	}
	if err := json.Unmarshal(data, &apiHTTPErrors); err != nil {
		return fmt.Errorf("failed to unmarshal http-errors section: %w", err)
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.ReplaceHTTPErrorsSectionParams{}
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

	// Call the ReplaceHTTPErrorsSection API
	resp, err := apiClient.ReplaceHTTPErrorsSection(ctx, op.HTTPErrors.Name, params, apiHTTPErrors)
	if err != nil {
		return fmt.Errorf("failed to update http-errors section '%s': %w", op.HTTPErrors.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("http-errors section update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateHTTPErrorsOperation) Describe() string {
	name := "unknown"
	if op.HTTPErrors.Name != "" {
		name = op.HTTPErrors.Name
	}
	return fmt.Sprintf("Update http-errors section '%s'", name)
}
