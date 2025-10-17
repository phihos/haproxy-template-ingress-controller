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
//
//nolint:dupl // Similar pattern to other operation Execute methods - each handles different API endpoints and contexts
func (op *CreateHTTPAfterResponseRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Rule == nil {
		return fmt.Errorf("HTTP after response rule is nil")
	}

	apiClient := c.Client()

	// Convert models.HTTPAfterResponseRule to dataplaneapi.HttpAfterResponseRule using JSON marshaling
	var apiRule dataplaneapi.HttpAfterResponseRule
	data, err := json.Marshal(op.Rule)
	if err != nil {
		return fmt.Errorf("failed to marshal HTTP after response rule: %w", err)
	}
	if err := json.Unmarshal(data, &apiRule); err != nil {
		return fmt.Errorf("failed to unmarshal HTTP after response rule: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateHTTPAfterResponseRuleBackendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateHTTPAfterResponseRuleBackend API
	resp, err := apiClient.CreateHTTPAfterResponseRuleBackend(ctx, op.BackendName, op.Index, params, apiRule)
	if err != nil {
		return fmt.Errorf("failed to create HTTP after response rule in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP after response rule creation failed with status %d", resp.StatusCode)
	}

	return nil
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
	apiClient := c.Client()

	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteHTTPAfterResponseRuleBackendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteHTTPAfterResponseRuleBackend API
	resp, err := apiClient.DeleteHTTPAfterResponseRuleBackend(ctx, op.BackendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete HTTP after response rule from backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP after response rule deletion failed with status %d", resp.StatusCode)
	}

	return nil
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
	if op.Rule == nil {
		return fmt.Errorf("HTTP after response rule is nil")
	}

	apiClient := c.Client()

	// Convert models.HTTPAfterResponseRule to dataplaneapi.HttpAfterResponseRule using JSON marshaling
	var apiRule dataplaneapi.HttpAfterResponseRule
	data, err := json.Marshal(op.Rule)
	if err != nil {
		return fmt.Errorf("failed to marshal HTTP after response rule: %w", err)
	}
	if err := json.Unmarshal(data, &apiRule); err != nil {
		return fmt.Errorf("failed to unmarshal HTTP after response rule: %w", err)
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceHTTPAfterResponseRuleBackendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceHTTPAfterResponseRuleBackend API
	resp, err := apiClient.ReplaceHTTPAfterResponseRuleBackend(ctx, op.BackendName, op.Index, params, apiRule)
	if err != nil {
		return fmt.Errorf("failed to update HTTP after response rule in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP after response rule update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateHTTPAfterResponseRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Update HTTP after response rule (%s) in backend '%s'", ruleType, op.BackendName)
}
