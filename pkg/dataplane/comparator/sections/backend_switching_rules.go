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
//
//nolint:dupl // Similar pattern to other backend switching rule operation Execute methods - each handles different API endpoints and contexts
func (op *CreateBackendSwitchingRuleFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Rule == nil {
		return fmt.Errorf("backend switching rule is nil")
	}

	apiClient := c.Client()

	// Convert models.BackendSwitchingRule to dataplaneapi.BackendSwitchingRule using JSON marshaling
	var apiRule dataplaneapi.BackendSwitchingRule
	data, err := json.Marshal(op.Rule)
	if err != nil {
		return fmt.Errorf("failed to marshal backend switching rule: %w", err)
	}
	if err := json.Unmarshal(data, &apiRule); err != nil {
		return fmt.Errorf("failed to unmarshal backend switching rule: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateBackendSwitchingRuleParams{
		TransactionId: &transactionID,
	}

	// Call the CreateBackendSwitchingRule API
	resp, err := apiClient.CreateBackendSwitchingRule(ctx, op.FrontendName, op.Index, params, apiRule)
	if err != nil {
		return fmt.Errorf("failed to create backend switching rule in frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("backend switching rule creation failed with status %d", resp.StatusCode)
	}

	return nil
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
	apiClient := c.Client()

	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteBackendSwitchingRuleParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteBackendSwitchingRule API
	resp, err := apiClient.DeleteBackendSwitchingRule(ctx, op.FrontendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete backend switching rule from frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("backend switching rule deletion failed with status %d", resp.StatusCode)
	}

	return nil
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
//
//nolint:dupl // Similar pattern to other backend switching rule operation Execute methods - each handles different API endpoints and contexts
func (op *UpdateBackendSwitchingRuleFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Rule == nil {
		return fmt.Errorf("backend switching rule is nil")
	}

	apiClient := c.Client()

	// Convert models.BackendSwitchingRule to dataplaneapi.BackendSwitchingRule using JSON marshaling
	var apiRule dataplaneapi.BackendSwitchingRule
	data, err := json.Marshal(op.Rule)
	if err != nil {
		return fmt.Errorf("failed to marshal backend switching rule: %w", err)
	}
	if err := json.Unmarshal(data, &apiRule); err != nil {
		return fmt.Errorf("failed to unmarshal backend switching rule: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceBackendSwitchingRuleParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceBackendSwitchingRule API
	resp, err := apiClient.ReplaceBackendSwitchingRule(ctx, op.FrontendName, op.Index, params, apiRule)
	if err != nil {
		return fmt.Errorf("failed to update backend switching rule in frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("backend switching rule update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateBackendSwitchingRuleFrontendOperation) Describe() string {
	backendName := unknownFallback
	if op.Rule != nil && op.Rule.Name != "" {
		backendName = op.Rule.Name
	}
	return fmt.Sprintf("Update backend switching rule (%s) in frontend '%s'", backendName, op.FrontendName)
}
