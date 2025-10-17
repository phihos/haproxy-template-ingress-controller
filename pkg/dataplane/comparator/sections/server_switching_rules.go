// Package sections contains section-specific comparison logic and operations
// for HAProxy configuration elements.
//
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
//
//nolint:dupl // Similar pattern to other operation Execute methods - each handles different API endpoints and contexts
func (op *CreateServerSwitchingRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Rule == nil {
		return fmt.Errorf("server switching rule is nil")
	}

	apiClient := c.Client()

	// Convert models.ServerSwitchingRule to dataplaneapi.ServerSwitchingRule using JSON marshaling
	var apiRule dataplaneapi.ServerSwitchingRule
	data, err := json.Marshal(op.Rule)
	if err != nil {
		return fmt.Errorf("failed to marshal server switching rule: %w", err)
	}
	if err := json.Unmarshal(data, &apiRule); err != nil {
		return fmt.Errorf("failed to unmarshal server switching rule: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateServerSwitchingRuleParams{
		TransactionId: &transactionID,
	}

	// Call the CreateServerSwitchingRule API
	resp, err := apiClient.CreateServerSwitchingRule(ctx, op.BackendName, op.Index, params, apiRule)
	if err != nil {
		return fmt.Errorf("failed to create server switching rule in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("server switching rule creation failed with status %d", resp.StatusCode)
	}

	return nil
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
	apiClient := c.Client()

	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteServerSwitchingRuleParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteServerSwitchingRule API
	resp, err := apiClient.DeleteServerSwitchingRule(ctx, op.BackendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete server switching rule from backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("server switching rule deletion failed with status %d", resp.StatusCode)
	}

	return nil
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
	if op.Rule == nil {
		return fmt.Errorf("server switching rule is nil")
	}

	apiClient := c.Client()

	// Convert models.ServerSwitchingRule to dataplaneapi.ServerSwitchingRule using JSON marshaling
	var apiRule dataplaneapi.ServerSwitchingRule
	data, err := json.Marshal(op.Rule)
	if err != nil {
		return fmt.Errorf("failed to marshal server switching rule: %w", err)
	}
	if err := json.Unmarshal(data, &apiRule); err != nil {
		return fmt.Errorf("failed to unmarshal server switching rule: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceServerSwitchingRuleParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceServerSwitchingRule API
	resp, err := apiClient.ReplaceServerSwitchingRule(ctx, op.BackendName, op.Index, params, apiRule)
	if err != nil {
		return fmt.Errorf("failed to update server switching rule in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("server switching rule update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateServerSwitchingRuleBackendOperation) Describe() string {
	serverName := unknownFallback
	if op.Rule != nil && op.Rule.TargetServer != "" {
		serverName = op.Rule.TargetServer
	}
	return fmt.Sprintf("Update server switching rule (%s) in backend '%s'", serverName, op.BackendName)
}
