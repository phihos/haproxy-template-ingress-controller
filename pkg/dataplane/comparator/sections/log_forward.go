//nolint:dupl // Section operation files follow similar patterns - type-specific HAProxy API wrappers
package sections

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/codegen/dataplaneapi"
	"haproxy-template-ic/pkg/dataplane/client"
)

// PriorityLogForward defines priority for log-forward sections.
const PriorityLogForward = 10

const (
	sectionLogForward = "log-forward"
)

// CreateLogForwardOperation represents creating a new log-forward section.
type CreateLogForwardOperation struct {
	LogForward *models.LogForward
}

// NewCreateLogForwardOperation creates a new log-forward section creation operation.
func NewCreateLogForwardOperation(logForward *models.LogForward) *CreateLogForwardOperation {
	return &CreateLogForwardOperation{
		LogForward: logForward,
	}
}

// Type implements Operation.Type.
func (op *CreateLogForwardOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateLogForwardOperation) Section() string {
	return sectionLogForward
}

// Priority implements Operation.Priority.
func (op *CreateLogForwardOperation) Priority() int {
	return PriorityLogForward
}

// Execute creates the log-forward section via the Dataplane API.
func (op *CreateLogForwardOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.LogForward == nil {
		return fmt.Errorf("log-forward section is nil")
	}
	if op.LogForward.Name == "" {
		return fmt.Errorf("log-forward section name is empty")
	}

	apiClient := c.Client()

	// Convert models.LogForward to dataplaneapi.LogForward using JSON marshaling
	var apiLogForward dataplaneapi.LogForward
	data, err := json.Marshal(op.LogForward)
	if err != nil {
		return fmt.Errorf("failed to marshal log-forward section: %w", err)
	}
	if err := json.Unmarshal(data, &apiLogForward); err != nil {
		return fmt.Errorf("failed to unmarshal log-forward section: %w", err)
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.CreateLogForwardParams{}
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

	// Call the CreateLogForward API
	resp, err := apiClient.CreateLogForward(ctx, params, apiLogForward)
	if err != nil {
		return fmt.Errorf("failed to create log-forward section '%s': %w", op.LogForward.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("log-forward section creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateLogForwardOperation) Describe() string {
	name := unknownFallback
	if op.LogForward.Name != "" {
		name = op.LogForward.Name
	}
	return fmt.Sprintf("Create log-forward '%s'", name)
}

// DeleteLogForwardOperation represents deleting an existing log-forward section.
type DeleteLogForwardOperation struct {
	LogForward *models.LogForward
}

// NewDeleteLogForwardOperation creates a new log-forward section deletion operation.
func NewDeleteLogForwardOperation(logForward *models.LogForward) *DeleteLogForwardOperation {
	return &DeleteLogForwardOperation{
		LogForward: logForward,
	}
}

// Type implements Operation.Type.
func (op *DeleteLogForwardOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteLogForwardOperation) Section() string {
	return sectionLogForward
}

// Priority implements Operation.Priority.
func (op *DeleteLogForwardOperation) Priority() int {
	return PriorityLogForward
}

// Execute deletes the log-forward section via the Dataplane API.
func (op *DeleteLogForwardOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.LogForward == nil {
		return fmt.Errorf("log-forward section is nil")
	}
	if op.LogForward.Name == "" {
		return fmt.Errorf("log-forward section name is empty")
	}

	apiClient := c.Client()

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.DeleteLogForwardParams{}
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

	// Call the DeleteLogForward API
	resp, err := apiClient.DeleteLogForward(ctx, op.LogForward.Name, params)
	if err != nil {
		return fmt.Errorf("failed to delete log-forward section '%s': %w", op.LogForward.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("log-forward section deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteLogForwardOperation) Describe() string {
	name := unknownFallback
	if op.LogForward.Name != "" {
		name = op.LogForward.Name
	}
	return fmt.Sprintf("Delete log-forward '%s'", name)
}

// UpdateLogForwardOperation represents updating an existing log-forward section.
type UpdateLogForwardOperation struct {
	LogForward *models.LogForward
}

// NewUpdateLogForwardOperation creates a new log-forward section update operation.
func NewUpdateLogForwardOperation(logForward *models.LogForward) *UpdateLogForwardOperation {
	return &UpdateLogForwardOperation{
		LogForward: logForward,
	}
}

// Type implements Operation.Type.
func (op *UpdateLogForwardOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateLogForwardOperation) Section() string {
	return sectionLogForward
}

// Priority implements Operation.Priority.
func (op *UpdateLogForwardOperation) Priority() int {
	return PriorityLogForward
}

// Execute updates the log-forward section via the Dataplane API.
func (op *UpdateLogForwardOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.LogForward == nil {
		return fmt.Errorf("log-forward section is nil")
	}
	if op.LogForward.Name == "" {
		return fmt.Errorf("log-forward section name is empty")
	}

	apiClient := c.Client()

	// Convert models.LogForward to dataplaneapi.LogForward using JSON marshaling
	var apiLogForward dataplaneapi.LogForward
	data, err := json.Marshal(op.LogForward)
	if err != nil {
		return fmt.Errorf("failed to marshal log-forward section: %w", err)
	}
	if err := json.Unmarshal(data, &apiLogForward); err != nil {
		return fmt.Errorf("failed to unmarshal log-forward section: %w", err)
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.ReplaceLogForwardParams{}
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

	// Call the ReplaceLogForward API
	resp, err := apiClient.ReplaceLogForward(ctx, op.LogForward.Name, params, apiLogForward)
	if err != nil {
		return fmt.Errorf("failed to update log-forward section '%s': %w", op.LogForward.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("log-forward section update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateLogForwardOperation) Describe() string {
	name := unknownFallback
	if op.LogForward.Name != "" {
		name = op.LogForward.Name
	}
	return fmt.Sprintf("Update log-forward '%s'", name)
}
