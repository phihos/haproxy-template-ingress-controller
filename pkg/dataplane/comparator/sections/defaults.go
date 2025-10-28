// Package sections contains section-specific comparison logic and operations
// for HAProxy configuration elements.
package sections

// Section operation files follow similar patterns - each implements type-specific HAProxy API wrappers

import (
	"context"
	"fmt"
	"net/http"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/pkg/dataplane/client"
	"haproxy-template-ic/pkg/dataplane/transform"
	"haproxy-template-ic/pkg/generated/dataplaneapi"
)

const (
	sectionDefaults = "defaults"
)

// CreateDefaultsOperation represents creating a new defaults section.
type CreateDefaultsOperation struct {
	Defaults *models.Defaults
}

// NewCreateDefaultsOperation creates a new defaults section creation operation.
func NewCreateDefaultsOperation(defaults *models.Defaults) *CreateDefaultsOperation {
	return &CreateDefaultsOperation{
		Defaults: defaults,
	}
}

// Type implements Operation.Type.
func (op *CreateDefaultsOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateDefaultsOperation) Section() string {
	return sectionDefaults
}

// Priority implements Operation.Priority.
func (op *CreateDefaultsOperation) Priority() int {
	return PriorityDefaults
}

// Execute creates the defaults section via the Dataplane API.
func (op *CreateDefaultsOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeCreateTransactionOnlyHelper(
		ctx, transactionID, op.Defaults,
		func(m *models.Defaults) string { return m.Name },
		transform.ToAPIDefaults,
		func(txID string) *dataplaneapi.CreateDefaultsSectionParams {
			return &dataplaneapi.CreateDefaultsSectionParams{TransactionId: &txID}
		},
		func(ctx context.Context, params *dataplaneapi.CreateDefaultsSectionParams, apiModel dataplaneapi.Defaults) (*http.Response, error) {
			return c.Client().CreateDefaultsSection(ctx, params, apiModel)
		},
		"defaults section",
	)
}

// Describe returns a human-readable description of this operation.
func (op *CreateDefaultsOperation) Describe() string {
	name := unknownFallback
	if op.Defaults.Name != "" {
		name = op.Defaults.Name
	}
	return fmt.Sprintf("Create defaults section '%s'", name)
}

// DeleteDefaultsOperation represents deleting an existing defaults section.
type DeleteDefaultsOperation struct {
	Defaults *models.Defaults
}

// NewDeleteDefaultsOperation creates a new defaults section deletion operation.
func NewDeleteDefaultsOperation(defaults *models.Defaults) *DeleteDefaultsOperation {
	return &DeleteDefaultsOperation{
		Defaults: defaults,
	}
}

// Type implements Operation.Type.
func (op *DeleteDefaultsOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteDefaultsOperation) Section() string {
	return sectionDefaults
}

// Priority implements Operation.Priority.
func (op *DeleteDefaultsOperation) Priority() int {
	return PriorityDefaults
}

// Execute deletes the defaults section via the Dataplane API.
func (op *DeleteDefaultsOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeDeleteTransactionOnlyHelper(
		ctx, transactionID, op.Defaults,
		func(m *models.Defaults) string { return m.Name },
		func(txID string) *dataplaneapi.DeleteDefaultsSectionParams {
			return &dataplaneapi.DeleteDefaultsSectionParams{TransactionId: &txID}
		},
		func(ctx context.Context, name string, params *dataplaneapi.DeleteDefaultsSectionParams) (*http.Response, error) {
			return c.Client().DeleteDefaultsSection(ctx, name, params)
		},
		"defaults section",
	)
}

// Describe returns a human-readable description of this operation.
func (op *DeleteDefaultsOperation) Describe() string {
	name := unknownFallback
	if op.Defaults.Name != "" {
		name = op.Defaults.Name
	}
	return fmt.Sprintf("Delete defaults section '%s'", name)
}

// UpdateDefaultsOperation represents updating an existing defaults section.
type UpdateDefaultsOperation struct {
	Defaults *models.Defaults
}

// NewUpdateDefaultsOperation creates a new defaults section update operation.
func NewUpdateDefaultsOperation(defaults *models.Defaults) *UpdateDefaultsOperation {
	return &UpdateDefaultsOperation{
		Defaults: defaults,
	}
}

// Type implements Operation.Type.
func (op *UpdateDefaultsOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateDefaultsOperation) Section() string {
	return sectionDefaults
}

// Priority implements Operation.Priority.
func (op *UpdateDefaultsOperation) Priority() int {
	return PriorityDefaults
}

// Execute updates the defaults section via the Dataplane API.
func (op *UpdateDefaultsOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeUpdateTransactionOnlyHelper(
		ctx, transactionID, op.Defaults,
		func(m *models.Defaults) string { return m.Name },
		transform.ToAPIDefaults,
		func(txID string) *dataplaneapi.ReplaceDefaultsSectionParams {
			return &dataplaneapi.ReplaceDefaultsSectionParams{TransactionId: &txID}
		},
		func(ctx context.Context, name string, params *dataplaneapi.ReplaceDefaultsSectionParams, apiModel dataplaneapi.Defaults) (*http.Response, error) {
			return c.Client().ReplaceDefaultsSection(ctx, name, params, apiModel)
		},
		"defaults section",
	)
}

// Describe returns a human-readable description of this operation.
func (op *UpdateDefaultsOperation) Describe() string {
	name := unknownFallback
	if op.Defaults.Name != "" {
		name = op.Defaults.Name
	}
	return fmt.Sprintf("Update defaults section '%s'", name)
}
