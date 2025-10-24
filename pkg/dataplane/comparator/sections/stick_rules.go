// Package sections contains section-specific comparison logic and operations
// for HAProxy configuration elements.
//
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
//
//nolint:dupl // Similar pattern to other operation Execute methods - each handles different API endpoints and contexts
func (op *CreateStickRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.StickRule == nil {
		return fmt.Errorf("stick rule is nil")
	}

	apiClient := c.Client()

	// Convert models.StickRule to dataplaneapi.StickRule using JSON marshaling
	apiStickRule := transform.ToAPIStickRule(op.StickRule)
	if apiStickRule == nil {
		return fmt.Errorf("failed to transform stick rule")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateStickRuleParams{
		TransactionId: &transactionID,
	}

	// Call the CreateStickRule API
	resp, err := apiClient.CreateStickRule(ctx, op.BackendName, op.Index, params, *apiStickRule)
	if err != nil {
		return fmt.Errorf("failed to create stick rule in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("stick rule creation failed with status %d", resp.StatusCode)
	}

	return nil
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
	apiClient := c.Client()

	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteStickRuleParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteStickRule API
	resp, err := apiClient.DeleteStickRule(ctx, op.BackendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete stick rule from backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("stick rule deletion failed with status %d", resp.StatusCode)
	}

	return nil
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
	if op.StickRule == nil {
		return fmt.Errorf("stick rule is nil")
	}

	apiClient := c.Client()

	// Convert models.StickRule to dataplaneapi.StickRule using JSON marshaling
	apiStickRule := transform.ToAPIStickRule(op.StickRule)
	if apiStickRule == nil {
		return fmt.Errorf("failed to transform stick rule")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceStickRuleParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceStickRule API
	resp, err := apiClient.ReplaceStickRule(ctx, op.BackendName, op.Index, params, *apiStickRule)
	if err != nil {
		return fmt.Errorf("failed to update stick rule in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("stick rule update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateStickRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.StickRule != nil && op.StickRule.Type != "" {
		ruleType = op.StickRule.Type
	}
	return fmt.Sprintf("Update stick rule (%s) in backend '%s'", ruleType, op.BackendName)
}
