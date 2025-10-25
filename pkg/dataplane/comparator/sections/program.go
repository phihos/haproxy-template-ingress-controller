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
	return executeCreateHelper(
		ctx, transactionID, op.Program,
		func(r *models.Program) string { return r.Name },
		transform.ToAPIProgram,
		func(ctx context.Context, apiProgram *dataplaneapi.Program, txID string) (*http.Response, error) {
			return wrapAPICallWithVersionOrTransaction(
				ctx, c, txID,
				func() *dataplaneapi.CreateProgramParams { return &dataplaneapi.CreateProgramParams{} },
				func(p *dataplaneapi.CreateProgramParams, tid *string) { p.TransactionId = tid },
				func(p *dataplaneapi.CreateProgramParams, v *int) { p.Version = v },
				func(ctx context.Context, params *dataplaneapi.CreateProgramParams) (*http.Response, error) {
					return c.Client().CreateProgram(ctx, params, *apiProgram)
				},
			)
		},
		"program section",
	)
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
	return executeDeleteHelper(
		ctx, transactionID, op.Program,
		func(r *models.Program) string { return r.Name },
		func(ctx context.Context, name string, txID string) (*http.Response, error) {
			return wrapAPICallWithVersionOrTransaction(
				ctx, c, txID,
				func() *dataplaneapi.DeleteProgramParams { return &dataplaneapi.DeleteProgramParams{} },
				func(p *dataplaneapi.DeleteProgramParams, tid *string) { p.TransactionId = tid },
				func(p *dataplaneapi.DeleteProgramParams, v *int) { p.Version = v },
				func(ctx context.Context, params *dataplaneapi.DeleteProgramParams) (*http.Response, error) {
					return c.Client().DeleteProgram(ctx, name, params)
				},
			)
		},
		"program section",
	)
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
	return executeUpdateHelper(
		ctx, transactionID, op.Program,
		func(r *models.Program) string { return r.Name },
		transform.ToAPIProgram,
		func(ctx context.Context, name string, apiProgram *dataplaneapi.Program, txID string) (*http.Response, error) {
			return wrapAPICallWithVersionOrTransaction(
				ctx, c, txID,
				func() *dataplaneapi.ReplaceProgramParams { return &dataplaneapi.ReplaceProgramParams{} },
				func(p *dataplaneapi.ReplaceProgramParams, tid *string) { p.TransactionId = tid },
				func(p *dataplaneapi.ReplaceProgramParams, v *int) { p.Version = v },
				func(ctx context.Context, params *dataplaneapi.ReplaceProgramParams) (*http.Response, error) {
					return c.Client().ReplaceProgram(ctx, name, params, *apiProgram)
				},
			)
		},
		"program section",
	)
}

// Describe returns a human-readable description of this operation.
func (op *UpdateProgramOperation) Describe() string {
	name := unknownFallback
	if op.Program.Name != "" {
		name = op.Program.Name
	}
	return fmt.Sprintf("Update program '%s'", name)
}
