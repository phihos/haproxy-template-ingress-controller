// Package sections contains section-specific comparison logic and operations
// for HAProxy configuration elements.
package sections

import (
	"context"
	"fmt"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/codegen/dataplaneapi"
	"haproxy-template-ic/pkg/dataplane/client"
	"haproxy-template-ic/pkg/dataplane/transform"
)

// UpdateGlobalOperation represents updating the global section.
// The global section is a singleton - it always exists and can only be updated.
type UpdateGlobalOperation struct {
	Global *models.Global
}

// NewUpdateGlobalOperation creates a new global section update operation.
func NewUpdateGlobalOperation(global *models.Global) *UpdateGlobalOperation {
	return &UpdateGlobalOperation{
		Global: global,
	}
}

// Type implements Operation.Type.
func (op *UpdateGlobalOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateGlobalOperation) Section() string {
	return "global"
}

// Priority implements Operation.Priority.
func (op *UpdateGlobalOperation) Priority() int {
	return PriorityGlobal
}

// Execute updates the global section via the Dataplane API.
func (op *UpdateGlobalOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Global == nil {
		return fmt.Errorf("global section is nil")
	}

	apiClient := c.Client()

	// Convert models.Global to dataplaneapi.Global using transform package
	apiGlobal := transform.ToAPIGlobal(op.Global)
	if apiGlobal == nil {
		return fmt.Errorf("failed to transform global section")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceGlobalParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceGlobal API
	resp, err := apiClient.ReplaceGlobal(ctx, params, *apiGlobal)
	if err != nil {
		return fmt.Errorf("failed to update global section: %w", err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("global section update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateGlobalOperation) Describe() string {
	return "Update global section"
}
