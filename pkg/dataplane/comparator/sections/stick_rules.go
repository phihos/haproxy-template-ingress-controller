// Package sections contains section-specific comparison logic and operations
// for HAProxy configuration elements.
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

// PriorityStickRule defines the priority for stick rule operations.
const PriorityStickRule = 60

const (
	sectionStickRule = "stick-rule"
)

// CreateStickRuleBackendOperation represents creating a new stick rule in a backend.
type CreateStickRuleBackendOperation struct {
	BackendName string
	StickRule   *models.StickRule
	Index       int
}

// NewCreateStickRuleBackendOperation creates a new stick rule creation operation for a backend.
func NewCreateStickRuleBackendOperation(backendName string, stickRule *models.StickRule, index int) *CreateStickRuleBackendOperation {
	return &CreateStickRuleBackendOperation{
		BackendName: backendName,
		StickRule:   stickRule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *CreateStickRuleBackendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateStickRuleBackendOperation) Section() string {
	return sectionStickRule
}

// Priority implements Operation.Priority.
func (op *CreateStickRuleBackendOperation) Priority() int {
	return PriorityStickRule
}

// Execute creates the stick rule via the Dataplane API.
func (op *CreateStickRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeCreateIndexedRuleHelper(
		ctx, transactionID, op.StickRule, op.BackendName, op.Index,
		transform.ToAPIStickRule,
		func(txID string) *dataplaneapi.CreateStickRuleParams {
			return &dataplaneapi.CreateStickRuleParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.CreateStickRuleParams, apiModel dataplaneapi.StickRule) (*http.Response, error) {
			return c.Client().CreateStickRule(ctx, parent, idx, params, apiModel)
		},
		"stick rule",
		"backend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *CreateStickRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.StickRule != nil && op.StickRule.Type != "" {
		ruleType = op.StickRule.Type
	}
	return fmt.Sprintf("Create stick rule (%s) in backend '%s'", ruleType, op.BackendName)
}

// DeleteStickRuleBackendOperation represents deleting a stick rule from a backend.
type DeleteStickRuleBackendOperation struct {
	BackendName string
	StickRule   *models.StickRule
	Index       int
}

// NewDeleteStickRuleBackendOperation creates a new stick rule deletion operation for a backend.
func NewDeleteStickRuleBackendOperation(backendName string, stickRule *models.StickRule, index int) *DeleteStickRuleBackendOperation {
	return &DeleteStickRuleBackendOperation{
		BackendName: backendName,
		StickRule:   stickRule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *DeleteStickRuleBackendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteStickRuleBackendOperation) Section() string {
	return sectionStickRule
}

// Priority implements Operation.Priority.
func (op *DeleteStickRuleBackendOperation) Priority() int {
	return PriorityStickRule
}

// Execute deletes the stick rule via the Dataplane API.
func (op *DeleteStickRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeDeleteIndexedRuleHelper(
		ctx, transactionID, op.BackendName, op.Index,
		func(txID string) *dataplaneapi.DeleteStickRuleParams {
			return &dataplaneapi.DeleteStickRuleParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.DeleteStickRuleParams) (*http.Response, error) {
			return c.Client().DeleteStickRule(ctx, parent, idx, params)
		},
		"stick rule",
		"backend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *DeleteStickRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.StickRule != nil && op.StickRule.Type != "" {
		ruleType = op.StickRule.Type
	}
	return fmt.Sprintf("Delete stick rule (%s) from backend '%s'", ruleType, op.BackendName)
}

// UpdateStickRuleBackendOperation represents updating a stick rule in a backend.
type UpdateStickRuleBackendOperation struct {
	BackendName string
	StickRule   *models.StickRule
	Index       int
}

// NewUpdateStickRuleBackendOperation creates a new stick rule update operation for a backend.
func NewUpdateStickRuleBackendOperation(backendName string, stickRule *models.StickRule, index int) *UpdateStickRuleBackendOperation {
	return &UpdateStickRuleBackendOperation{
		BackendName: backendName,
		StickRule:   stickRule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *UpdateStickRuleBackendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateStickRuleBackendOperation) Section() string {
	return sectionStickRule
}

// Priority implements Operation.Priority.
func (op *UpdateStickRuleBackendOperation) Priority() int {
	return PriorityStickRule
}

// Execute updates the stick rule via the Dataplane API.
func (op *UpdateStickRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeReplaceIndexedRuleHelper(
		ctx, transactionID, op.StickRule, op.BackendName, op.Index,
		transform.ToAPIStickRule,
		func(txID string) *dataplaneapi.ReplaceStickRuleParams {
			return &dataplaneapi.ReplaceStickRuleParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.ReplaceStickRuleParams, apiModel dataplaneapi.StickRule) (*http.Response, error) {
			return c.Client().ReplaceStickRule(ctx, parent, idx, params, apiModel)
		},
		"stick rule",
		"backend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *UpdateStickRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.StickRule != nil && op.StickRule.Type != "" {
		ruleType = op.StickRule.Type
	}
	return fmt.Sprintf("Update stick rule (%s) in backend '%s'", ruleType, op.BackendName)
}
