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

// PriorityMailers defines priority for mailers sections.
// Mailers should be created early as they might be referenced by other sections.
const PriorityMailers = 15

const (
	sectionMailers = "mailers"
)

// CreateMailersOperation represents creating a new mailers section.
type CreateMailersOperation struct {
	Mailers *models.MailersSection
}

// NewCreateMailersOperation creates a new mailers section creation operation.
func NewCreateMailersOperation(mailers *models.MailersSection) *CreateMailersOperation {
	return &CreateMailersOperation{
		Mailers: mailers,
	}
}

// Type implements Operation.Type.
func (op *CreateMailersOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateMailersOperation) Section() string {
	return sectionMailers
}

// Priority implements Operation.Priority.
func (op *CreateMailersOperation) Priority() int {
	return PriorityMailers
}

// Execute creates the mailers section via the Dataplane API.
func (op *CreateMailersOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Mailers == nil {
		return fmt.Errorf("mailers section is nil")
	}
	if op.Mailers.Name == "" {
		return fmt.Errorf("mailers section name is empty")
	}

	apiClient := c.Client()

	// Convert models.MailersSection to dataplaneapi.MailersSection using JSON marshaling
	var apiMailers dataplaneapi.MailersSection
	data, err := json.Marshal(op.Mailers)
	if err != nil {
		return fmt.Errorf("failed to marshal mailers section: %w", err)
	}
	if err := json.Unmarshal(data, &apiMailers); err != nil {
		return fmt.Errorf("failed to unmarshal mailers section: %w", err)
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.CreateMailersSectionParams{}
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

	// Call the CreateMailersSection API
	resp, err := apiClient.CreateMailersSection(ctx, params, apiMailers)
	if err != nil {
		return fmt.Errorf("failed to create mailers section '%s': %w", op.Mailers.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("mailers section creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateMailersOperation) Describe() string {
	name := unknownFallback
	if op.Mailers.Name != "" {
		name = op.Mailers.Name
	}
	return fmt.Sprintf("Create mailers '%s'", name)
}

// DeleteMailersOperation represents deleting an existing mailers section.
type DeleteMailersOperation struct {
	Mailers *models.MailersSection
}

// NewDeleteMailersOperation creates a new mailers section deletion operation.
func NewDeleteMailersOperation(mailers *models.MailersSection) *DeleteMailersOperation {
	return &DeleteMailersOperation{
		Mailers: mailers,
	}
}

// Type implements Operation.Type.
func (op *DeleteMailersOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteMailersOperation) Section() string {
	return sectionMailers
}

// Priority implements Operation.Priority.
func (op *DeleteMailersOperation) Priority() int {
	return PriorityMailers
}

// Execute deletes the mailers section via the Dataplane API.
func (op *DeleteMailersOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Mailers == nil {
		return fmt.Errorf("mailers section is nil")
	}
	if op.Mailers.Name == "" {
		return fmt.Errorf("mailers section name is empty")
	}

	apiClient := c.Client()

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.DeleteMailersSectionParams{}
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

	// Call the DeleteMailersSection API
	resp, err := apiClient.DeleteMailersSection(ctx, op.Mailers.Name, params)
	if err != nil {
		return fmt.Errorf("failed to delete mailers section '%s': %w", op.Mailers.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("mailers section deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteMailersOperation) Describe() string {
	name := unknownFallback
	if op.Mailers.Name != "" {
		name = op.Mailers.Name
	}
	return fmt.Sprintf("Delete mailers '%s'", name)
}

// UpdateMailersOperation represents updating an existing mailers section.
type UpdateMailersOperation struct {
	Mailers *models.MailersSection
}

// NewUpdateMailersOperation creates a new mailers section update operation.
func NewUpdateMailersOperation(mailers *models.MailersSection) *UpdateMailersOperation {
	return &UpdateMailersOperation{
		Mailers: mailers,
	}
}

// Type implements Operation.Type.
func (op *UpdateMailersOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateMailersOperation) Section() string {
	return sectionMailers
}

// Priority implements Operation.Priority.
func (op *UpdateMailersOperation) Priority() int {
	return PriorityMailers
}

// Execute updates the mailers section via the Dataplane API.
func (op *UpdateMailersOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Mailers == nil {
		return fmt.Errorf("mailers section is nil")
	}
	if op.Mailers.Name == "" {
		return fmt.Errorf("mailers section name is empty")
	}

	apiClient := c.Client()

	// Convert models.MailersSection to dataplaneapi.MailersSection using JSON marshaling
	var apiMailers dataplaneapi.MailersSection
	data, err := json.Marshal(op.Mailers)
	if err != nil {
		return fmt.Errorf("failed to marshal mailers section: %w", err)
	}
	if err := json.Unmarshal(data, &apiMailers); err != nil {
		return fmt.Errorf("failed to unmarshal mailers section: %w", err)
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.EditMailersSectionParams{}
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

	// Call the EditMailersSection API
	resp, err := apiClient.EditMailersSection(ctx, op.Mailers.Name, params, apiMailers)
	if err != nil {
		return fmt.Errorf("failed to update mailers section '%s': %w", op.Mailers.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("mailers section update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateMailersOperation) Describe() string {
	name := unknownFallback
	if op.Mailers.Name != "" {
		name = op.Mailers.Name
	}
	return fmt.Sprintf("Update mailers '%s'", name)
}
