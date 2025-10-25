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

// PriorityServerSwitchingRule defines the priority for server switching rule operations.
const PriorityServerSwitchingRule = 60

const (
	sectionServerSwitchingRule = "server-switching-rule"
)

// CreateServerSwitchingRuleBackendOperation represents creating a new server switching rule in a backend.
type CreateServerSwitchingRuleBackendOperation struct {
	BackendName string
	Rule        *models.ServerSwitchingRule
	Index       int
}

// NewCreateServerSwitchingRuleBackendOperation creates a new server switching rule creation operation for a backend.
func NewCreateServerSwitchingRuleBackendOperation(backendName string, rule *models.ServerSwitchingRule, index int) *CreateServerSwitchingRuleBackendOperation {
	return &CreateServerSwitchingRuleBackendOperation{
		BackendName: backendName,
		Rule:        rule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *CreateServerSwitchingRuleBackendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateServerSwitchingRuleBackendOperation) Section() string {
	return sectionServerSwitchingRule
}

// Priority implements Operation.Priority.
func (op *CreateServerSwitchingRuleBackendOperation) Priority() int {
	return PriorityServerSwitchingRule
}

// Execute creates the server switching rule via the Dataplane API.
func (op *CreateServerSwitchingRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeCreateIndexedRuleHelper(
		ctx, transactionID, op.Rule, op.BackendName, op.Index,
		transform.ToAPIServerSwitchingRule,
		func(txID string) *dataplaneapi.CreateServerSwitchingRuleParams {
			return &dataplaneapi.CreateServerSwitchingRuleParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.CreateServerSwitchingRuleParams, apiModel dataplaneapi.ServerSwitchingRule) (*http.Response, error) {
			return c.Client().CreateServerSwitchingRule(ctx, parent, idx, params, apiModel)
		},
		"server switching rule",
		"backend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *CreateServerSwitchingRuleBackendOperation) Describe() string {
	serverName := unknownFallback
	if op.Rule != nil && op.Rule.TargetServer != "" {
		serverName = op.Rule.TargetServer
	}
	return fmt.Sprintf("Create server switching rule (%s) in backend '%s'", serverName, op.BackendName)
}

// DeleteServerSwitchingRuleBackendOperation represents deleting a server switching rule from a backend.
type DeleteServerSwitchingRuleBackendOperation struct {
	BackendName string
	Rule        *models.ServerSwitchingRule
	Index       int
}

// NewDeleteServerSwitchingRuleBackendOperation creates a new server switching rule deletion operation for a backend.
func NewDeleteServerSwitchingRuleBackendOperation(backendName string, rule *models.ServerSwitchingRule, index int) *DeleteServerSwitchingRuleBackendOperation {
	return &DeleteServerSwitchingRuleBackendOperation{
		BackendName: backendName,
		Rule:        rule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *DeleteServerSwitchingRuleBackendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteServerSwitchingRuleBackendOperation) Section() string {
	return sectionServerSwitchingRule
}

// Priority implements Operation.Priority.
func (op *DeleteServerSwitchingRuleBackendOperation) Priority() int {
	return PriorityServerSwitchingRule
}

// Execute deletes the server switching rule via the Dataplane API.
func (op *DeleteServerSwitchingRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeDeleteIndexedRuleHelper(
		ctx, transactionID, op.BackendName, op.Index,
		func(txID string) *dataplaneapi.DeleteServerSwitchingRuleParams {
			return &dataplaneapi.DeleteServerSwitchingRuleParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.DeleteServerSwitchingRuleParams) (*http.Response, error) {
			return c.Client().DeleteServerSwitchingRule(ctx, parent, idx, params)
		},
		"server switching rule",
		"backend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *DeleteServerSwitchingRuleBackendOperation) Describe() string {
	serverName := unknownFallback
	if op.Rule != nil && op.Rule.TargetServer != "" {
		serverName = op.Rule.TargetServer
	}
	return fmt.Sprintf("Delete server switching rule (%s) from backend '%s'", serverName, op.BackendName)
}

// UpdateServerSwitchingRuleBackendOperation represents updating a server switching rule in a backend.
type UpdateServerSwitchingRuleBackendOperation struct {
	BackendName string
	Rule        *models.ServerSwitchingRule
	Index       int
}

// NewUpdateServerSwitchingRuleBackendOperation creates a new server switching rule update operation for a backend.
func NewUpdateServerSwitchingRuleBackendOperation(backendName string, rule *models.ServerSwitchingRule, index int) *UpdateServerSwitchingRuleBackendOperation {
	return &UpdateServerSwitchingRuleBackendOperation{
		BackendName: backendName,
		Rule:        rule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *UpdateServerSwitchingRuleBackendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateServerSwitchingRuleBackendOperation) Section() string {
	return sectionServerSwitchingRule
}

// Priority implements Operation.Priority.
func (op *UpdateServerSwitchingRuleBackendOperation) Priority() int {
	return PriorityServerSwitchingRule
}

// Execute updates the server switching rule via the Dataplane API.
func (op *UpdateServerSwitchingRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeReplaceIndexedRuleHelper(
		ctx, transactionID, op.Rule, op.BackendName, op.Index,
		transform.ToAPIServerSwitchingRule,
		func(txID string) *dataplaneapi.ReplaceServerSwitchingRuleParams {
			return &dataplaneapi.ReplaceServerSwitchingRuleParams{TransactionId: &txID}
		},
		func(ctx context.Context, parent string, idx int, params *dataplaneapi.ReplaceServerSwitchingRuleParams, apiModel dataplaneapi.ServerSwitchingRule) (*http.Response, error) {
			return c.Client().ReplaceServerSwitchingRule(ctx, parent, idx, params, apiModel)
		},
		"server switching rule",
		"backend",
	)
}

// Describe returns a human-readable description of this operation.
func (op *UpdateServerSwitchingRuleBackendOperation) Describe() string {
	serverName := unknownFallback
	if op.Rule != nil && op.Rule.TargetServer != "" {
		serverName = op.Rule.TargetServer
	}
	return fmt.Sprintf("Update server switching rule (%s) in backend '%s'", serverName, op.BackendName)
}
