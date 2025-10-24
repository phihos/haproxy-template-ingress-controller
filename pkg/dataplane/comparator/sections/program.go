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

// PriorityProgram defines priority for program sections.
// Programs should be created early as they might be referenced by other sections.
const PriorityProgram = 10

const (
	sectionProgram = "program"
)

// CreateProgramOperation represents creating a new program section.
type CreateProgramOperation struct {
	Program *models.Program
}

// NewCreateProgramOperation creates a new program section creation operation.
func NewCreateProgramOperation(program *models.Program) *CreateProgramOperation {
	return &CreateProgramOperation{
		Program: program,
	}
}

// Type implements Operation.Type.
func (op *CreateProgramOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateProgramOperation) Section() string {
	return sectionProgram
}

// Priority implements Operation.Priority.
func (op *CreateProgramOperation) Priority() int {
	return PriorityProgram
}

// Execute creates the program section via the Dataplane API.
func (op *CreateProgramOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Program == nil {
		return fmt.Errorf("program section is nil")
	}
	if op.Program.Name == "" {
		return fmt.Errorf("program section name is empty")
	}

	apiClient := c.Client()

	// Convert models.Program to dataplaneapi.Program using transform package
	apiProgram := transform.ToAPIProgram(op.Program)
	if apiProgram == nil {
		return fmt.Errorf("failed to transform program section")
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.CreateProgramParams{}
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

	// Call the CreateProgram API
	resp, err := apiClient.CreateProgram(ctx, params, *apiProgram)
	if err != nil {
		return fmt.Errorf("failed to create program section '%s': %w", op.Program.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("program section creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateProgramOperation) Describe() string {
	name := unknownFallback
	if op.Program.Name != "" {
		name = op.Program.Name
	}
	return fmt.Sprintf("Create program '%s'", name)
}

// DeleteProgramOperation represents deleting an existing program section.
type DeleteProgramOperation struct {
	Program *models.Program
}

// NewDeleteProgramOperation creates a new program section deletion operation.
func NewDeleteProgramOperation(program *models.Program) *DeleteProgramOperation {
	return &DeleteProgramOperation{
		Program: program,
	}
}

// Type implements Operation.Type.
func (op *DeleteProgramOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteProgramOperation) Section() string {
	return sectionProgram
}

// Priority implements Operation.Priority.
func (op *DeleteProgramOperation) Priority() int {
	return PriorityProgram
}

// Execute deletes the program section via the Dataplane API.
func (op *DeleteProgramOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Program == nil {
		return fmt.Errorf("program section is nil")
	}
	if op.Program.Name == "" {
		return fmt.Errorf("program section name is empty")
	}

	apiClient := c.Client()

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.DeleteProgramParams{}
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

	// Call the DeleteProgram API
	resp, err := apiClient.DeleteProgram(ctx, op.Program.Name, params)
	if err != nil {
		return fmt.Errorf("failed to delete program section '%s': %w", op.Program.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("program section deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteProgramOperation) Describe() string {
	name := unknownFallback
	if op.Program.Name != "" {
		name = op.Program.Name
	}
	return fmt.Sprintf("Delete program '%s'", name)
}

// UpdateProgramOperation represents updating an existing program section.
type UpdateProgramOperation struct {
	Program *models.Program
}

// NewUpdateProgramOperation creates a new program section update operation.
func NewUpdateProgramOperation(program *models.Program) *UpdateProgramOperation {
	return &UpdateProgramOperation{
		Program: program,
	}
}

// Type implements Operation.Type.
func (op *UpdateProgramOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateProgramOperation) Section() string {
	return sectionProgram
}

// Priority implements Operation.Priority.
func (op *UpdateProgramOperation) Priority() int {
	return PriorityProgram
}

// Execute updates the program section via the Dataplane API.
func (op *UpdateProgramOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Program == nil {
		return fmt.Errorf("program section is nil")
	}
	if op.Program.Name == "" {
		return fmt.Errorf("program section name is empty")
	}

	apiClient := c.Client()

	// Convert models.Program to dataplaneapi.Program using transform package
	apiProgram := transform.ToAPIProgram(op.Program)
	if apiProgram == nil {
		return fmt.Errorf("failed to transform program section")
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.ReplaceProgramParams{}
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

	// Call the ReplaceProgram API
	resp, err := apiClient.ReplaceProgram(ctx, op.Program.Name, params, *apiProgram)
	if err != nil {
		return fmt.Errorf("failed to update program section '%s': %w", op.Program.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("program section update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateProgramOperation) Describe() string {
	name := unknownFallback
	if op.Program.Name != "" {
		name = op.Program.Name
	}
	return fmt.Sprintf("Update program '%s'", name)
}
