// Package sections contains section-specific comparison logic and operations
// for HAProxy configuration elements.
package sections

import (
	"context"
	"fmt"
	"net/http"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/pkg/dataplane/client"
	"haproxy-template-ic/pkg/dataplane/transform"
	"haproxy-template-ic/pkg/generated/dataplaneapi"
)

// PriorityHTTPAfterRule defines the priority for HTTP after response rule operations.
const PriorityHTTPAfterRule = 60

const (
	sectionHTTPAfterRule = "http-after-response-rule"
)

// CreateHTTPAfterResponseRuleBackendOperation represents creating a new HTTP after response rule in a backend.
type CreateHTTPAfterResponseRuleBackendOperation struct {
	BackendName string
	Rule        *models.HTTPAfterResponseRule
	Index       int
}

// NewCreateHTTPAfterResponseRuleBackendOperation creates a new HTTP after response rule creation operation for a backend.
func NewCreateHTTPAfterResponseRuleBackendOperation(backendName string, rule *models.HTTPAfterResponseRule, index int) *CreateHTTPAfterResponseRuleBackendOperation {
	return &CreateHTTPAfterResponseRuleBackendOperation{
		BackendName: backendName,
		Rule:        rule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *CreateHTTPAfterResponseRuleBackendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateHTTPAfterResponseRuleBackendOperation) Section() string {
	return sectionHTTPAfterRule
}

// Priority implements Operation.Priority.
func (op *CreateHTTPAfterResponseRuleBackendOperation) Priority() int {
	return PriorityHTTPAfterRule
}

// Execute creates the HTTP after response rule via the Dataplane API.
func (op *CreateHTTPAfterResponseRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeCreateIndexedRuleHelper(
		ctx, transactionID, op.Rule, op.BackendName, op.Index,
		transform.ToAPIHTTPAfterResponseRule,
		func(txID string) *dataplaneapi.CreateHTTPAfterResponseRuleBackendParams {
			return &dataplaneapi.CreateHTTPAfterResponseRuleBackendParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.CreateHTTPAfterResponseRuleBackendParams, apiModel dataplaneapi.HttpAfterResponseRule) (*http.Response, error) {
			return c.Client().CreateHTTPAfterResponseRuleBackend(ctx, parent, idx, params, apiModel)
		},
		"HTTP after response rule",
		"frontend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *CreateHTTPAfterResponseRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Create HTTP after response rule (%s) in backend '%s'", ruleType, op.BackendName)
}

// DeleteHTTPAfterResponseRuleBackendOperation represents deleting a HTTP after response rule from a backend.
type DeleteHTTPAfterResponseRuleBackendOperation struct {
	BackendName string
	Rule        *models.HTTPAfterResponseRule
	Index       int
}

// NewDeleteHTTPAfterResponseRuleBackendOperation creates a new HTTP after response rule deletion operation for a backend.
func NewDeleteHTTPAfterResponseRuleBackendOperation(backendName string, rule *models.HTTPAfterResponseRule, index int) *DeleteHTTPAfterResponseRuleBackendOperation {
	return &DeleteHTTPAfterResponseRuleBackendOperation{
		BackendName: backendName,
		Rule:        rule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *DeleteHTTPAfterResponseRuleBackendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteHTTPAfterResponseRuleBackendOperation) Section() string {
	return sectionHTTPAfterRule
}

// Priority implements Operation.Priority.
func (op *DeleteHTTPAfterResponseRuleBackendOperation) Priority() int {
	return PriorityHTTPAfterRule
}

// Execute deletes the HTTP after response rule via the Dataplane API.
func (op *DeleteHTTPAfterResponseRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeDeleteIndexedRuleHelper(
		ctx, transactionID, op.BackendName, op.Index,
		func(txID string) *dataplaneapi.DeleteHTTPAfterResponseRuleBackendParams {
			return &dataplaneapi.DeleteHTTPAfterResponseRuleBackendParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.DeleteHTTPAfterResponseRuleBackendParams) (*http.Response, error) {
			return c.Client().DeleteHTTPAfterResponseRuleBackend(ctx, parent, idx, params)
		},
		"HTTP after response rule",
		"frontend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *DeleteHTTPAfterResponseRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Delete HTTP after response rule (%s) from backend '%s'", ruleType, op.BackendName)
}

// UpdateHTTPAfterResponseRuleBackendOperation represents updating a HTTP after response rule in a backend.
type UpdateHTTPAfterResponseRuleBackendOperation struct {
	BackendName string
	Rule        *models.HTTPAfterResponseRule
	Index       int
}

// NewUpdateHTTPAfterResponseRuleBackendOperation creates a new HTTP after response rule update operation for a backend.
func NewUpdateHTTPAfterResponseRuleBackendOperation(backendName string, rule *models.HTTPAfterResponseRule, index int) *UpdateHTTPAfterResponseRuleBackendOperation {
	return &UpdateHTTPAfterResponseRuleBackendOperation{
		BackendName: backendName,
		Rule:        rule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *UpdateHTTPAfterResponseRuleBackendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateHTTPAfterResponseRuleBackendOperation) Section() string {
	return sectionHTTPAfterRule
}

// Priority implements Operation.Priority.
func (op *UpdateHTTPAfterResponseRuleBackendOperation) Priority() int {
	return PriorityHTTPAfterRule
}

// Execute updates the HTTP after response rule via the Dataplane API.
func (op *UpdateHTTPAfterResponseRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeReplaceIndexedRuleHelper(
		ctx, transactionID, op.Rule, op.BackendName, op.Index,
		transform.ToAPIHTTPAfterResponseRule,
		func(txID string) *dataplaneapi.ReplaceHTTPAfterResponseRuleBackendParams {
			return &dataplaneapi.ReplaceHTTPAfterResponseRuleBackendParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.ReplaceHTTPAfterResponseRuleBackendParams, apiModel dataplaneapi.HttpAfterResponseRule) (*http.Response, error) {
			return c.Client().ReplaceHTTPAfterResponseRuleBackend(ctx, parent, idx, params, apiModel)
		},
		"HTTP after response rule",
		"frontend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *UpdateHTTPAfterResponseRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Update HTTP after response rule (%s) in backend '%s'", ruleType, op.BackendName)
}
