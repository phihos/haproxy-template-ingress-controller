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

// PriorityBackendSwitchingRule defines the priority for backend switching rule operations.
const (
	sectionBackendSwitchingRule = "backend-switching-rule"
)

const PriorityBackendSwitchingRule = 60

// CreateBackendSwitchingRuleFrontendOperation represents creating a new backend switching rule in a frontend.
type CreateBackendSwitchingRuleFrontendOperation struct {
	FrontendName string
	Rule         *models.BackendSwitchingRule
	Index        int
}

// NewCreateBackendSwitchingRuleFrontendOperation creates a new backend switching rule creation operation for a frontend.
func NewCreateBackendSwitchingRuleFrontendOperation(frontendName string, rule *models.BackendSwitchingRule, index int) *CreateBackendSwitchingRuleFrontendOperation {
	return &CreateBackendSwitchingRuleFrontendOperation{
		FrontendName: frontendName,
		Rule:         rule,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *CreateBackendSwitchingRuleFrontendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateBackendSwitchingRuleFrontendOperation) Section() string {
	return sectionBackendSwitchingRule
}

// Priority implements Operation.Priority.
func (op *CreateBackendSwitchingRuleFrontendOperation) Priority() int {
	return PriorityBackendSwitchingRule
}

// Execute creates the backend switching rule via the Dataplane API.
func (op *CreateBackendSwitchingRuleFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeCreateIndexedRuleHelper(
		ctx, transactionID, op.Rule, op.FrontendName, op.Index,
		transform.ToAPIBackendSwitchingRule,
		func(txID string) *dataplaneapi.CreateBackendSwitchingRuleParams {
			return &dataplaneapi.CreateBackendSwitchingRuleParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.CreateBackendSwitchingRuleParams, apiModel dataplaneapi.BackendSwitchingRule) (*http.Response, error) {
			return c.Client().CreateBackendSwitchingRule(ctx, parent, idx, params, apiModel)
		},
		"backend switching rule",
		"frontend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *CreateBackendSwitchingRuleFrontendOperation) Describe() string {
	backendName := unknownFallback
	if op.Rule != nil && op.Rule.Name != "" {
		backendName = op.Rule.Name
	}
	return fmt.Sprintf("Create backend switching rule (%s) in frontend '%s'", backendName, op.FrontendName)
}

// DeleteBackendSwitchingRuleFrontendOperation represents deleting a backend switching rule from a frontend.
type DeleteBackendSwitchingRuleFrontendOperation struct {
	FrontendName string
	Rule         *models.BackendSwitchingRule
	Index        int
}

// NewDeleteBackendSwitchingRuleFrontendOperation creates a new backend switching rule deletion operation for a frontend.
func NewDeleteBackendSwitchingRuleFrontendOperation(frontendName string, rule *models.BackendSwitchingRule, index int) *DeleteBackendSwitchingRuleFrontendOperation {
	return &DeleteBackendSwitchingRuleFrontendOperation{
		FrontendName: frontendName,
		Rule:         rule,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *DeleteBackendSwitchingRuleFrontendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteBackendSwitchingRuleFrontendOperation) Section() string {
	return sectionBackendSwitchingRule
}

// Priority implements Operation.Priority.
func (op *DeleteBackendSwitchingRuleFrontendOperation) Priority() int {
	return PriorityBackendSwitchingRule
}

// Execute deletes the backend switching rule via the Dataplane API.
func (op *DeleteBackendSwitchingRuleFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeDeleteIndexedRuleHelper(
		ctx, transactionID, op.FrontendName, op.Index,
		func(txID string) *dataplaneapi.DeleteBackendSwitchingRuleParams {
			return &dataplaneapi.DeleteBackendSwitchingRuleParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.DeleteBackendSwitchingRuleParams) (*http.Response, error) {
			return c.Client().DeleteBackendSwitchingRule(ctx, parent, idx, params)
		},
		"backend switching rule",
		"frontend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *DeleteBackendSwitchingRuleFrontendOperation) Describe() string {
	backendName := unknownFallback
	if op.Rule != nil && op.Rule.Name != "" {
		backendName = op.Rule.Name
	}
	return fmt.Sprintf("Delete backend switching rule (%s) from frontend '%s'", backendName, op.FrontendName)
}

// UpdateBackendSwitchingRuleFrontendOperation represents updating a backend switching rule in a frontend.
type UpdateBackendSwitchingRuleFrontendOperation struct {
	FrontendName string
	Rule         *models.BackendSwitchingRule
	Index        int
}

// NewUpdateBackendSwitchingRuleFrontendOperation creates a new backend switching rule update operation for a frontend.
func NewUpdateBackendSwitchingRuleFrontendOperation(frontendName string, rule *models.BackendSwitchingRule, index int) *UpdateBackendSwitchingRuleFrontendOperation {
	return &UpdateBackendSwitchingRuleFrontendOperation{
		FrontendName: frontendName,
		Rule:         rule,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *UpdateBackendSwitchingRuleFrontendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateBackendSwitchingRuleFrontendOperation) Section() string {
	return sectionBackendSwitchingRule
}

// Priority implements Operation.Priority.
func (op *UpdateBackendSwitchingRuleFrontendOperation) Priority() int {
	return PriorityBackendSwitchingRule
}

// Execute updates the backend switching rule via the Dataplane API.
func (op *UpdateBackendSwitchingRuleFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeReplaceIndexedRuleHelper(
		ctx, transactionID, op.Rule, op.FrontendName, op.Index,
		transform.ToAPIBackendSwitchingRule,
		func(txID string) *dataplaneapi.ReplaceBackendSwitchingRuleParams {
			return &dataplaneapi.ReplaceBackendSwitchingRuleParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.ReplaceBackendSwitchingRuleParams, apiModel dataplaneapi.BackendSwitchingRule) (*http.Response, error) {
			return c.Client().ReplaceBackendSwitchingRule(ctx, parent, idx, params, apiModel)
		},
		"backend switching rule",
		"frontend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *UpdateBackendSwitchingRuleFrontendOperation) Describe() string {
	backendName := unknownFallback
	if op.Rule != nil && op.Rule.Name != "" {
		backendName = op.Rule.Name
	}
	return fmt.Sprintf("Update backend switching rule (%s) in frontend '%s'", backendName, op.FrontendName)
}
