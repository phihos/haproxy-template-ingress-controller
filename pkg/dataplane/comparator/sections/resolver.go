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

// PriorityResolver defines priority for resolver sections.
// Resolvers should be created early as they might be referenced by backends.
const PriorityResolver = 15

const (
	sectionResolver = "resolver"
)

// CreateResolverOperation represents creating a new resolver section.
type CreateResolverOperation struct {
	Resolver *models.Resolver
}

// NewCreateResolverOperation creates a new resolver section creation operation.
func NewCreateResolverOperation(resolver *models.Resolver) *CreateResolverOperation {
	return &CreateResolverOperation{
		Resolver: resolver,
	}
}

// Type implements Operation.Type.
func (op *CreateResolverOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateResolverOperation) Section() string {
	return sectionResolver
}

// Priority implements Operation.Priority.
func (op *CreateResolverOperation) Priority() int {
	return PriorityResolver
}

// Execute creates the resolver section via the Dataplane API.
func (op *CreateResolverOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Resolver == nil {
		return fmt.Errorf("resolver section is nil")
	}
	if op.Resolver.Name == "" {
		return fmt.Errorf("resolver section name is empty")
	}

	apiClient := c.Client()

	// Convert models.Resolver to dataplaneapi.Resolver using JSON marshaling
	var apiResolver dataplaneapi.Resolver
	data, err := json.Marshal(op.Resolver)
	if err != nil {
		return fmt.Errorf("failed to marshal resolver section: %w", err)
	}
	if err := json.Unmarshal(data, &apiResolver); err != nil {
		return fmt.Errorf("failed to unmarshal resolver section: %w", err)
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.CreateResolverParams{}
	if transactionID != "" {
		params.TransactionId = &transactionID
	} else {
		v, err := c.GetVersion(ctx)
		if err != nil {
			return fmt.Errorf("failed to get version: %w", err)
		}
		version := int(v)
		params.Version = &version
	}

	// Call the CreateResolver API
	resp, err := apiClient.CreateResolver(ctx, params, apiResolver)
	if err != nil {
		return fmt.Errorf("failed to create resolver section '%s': %w", op.Resolver.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("resolver section creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateResolverOperation) Describe() string {
	name := unknownFallback
	if op.Resolver.Name != "" {
		name = op.Resolver.Name
	}
	return fmt.Sprintf("Create resolver '%s'", name)
}

// DeleteResolverOperation represents deleting an existing resolver section.
type DeleteResolverOperation struct {
	Resolver *models.Resolver
}

// NewDeleteResolverOperation creates a new resolver section deletion operation.
func NewDeleteResolverOperation(resolver *models.Resolver) *DeleteResolverOperation {
	return &DeleteResolverOperation{
		Resolver: resolver,
	}
}

// Type implements Operation.Type.
func (op *DeleteResolverOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteResolverOperation) Section() string {
	return sectionResolver
}

// Priority implements Operation.Priority.
func (op *DeleteResolverOperation) Priority() int {
	return PriorityResolver
}

// Execute deletes the resolver section via the Dataplane API.
func (op *DeleteResolverOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Resolver == nil {
		return fmt.Errorf("resolver section is nil")
	}
	if op.Resolver.Name == "" {
		return fmt.Errorf("resolver section name is empty")
	}

	apiClient := c.Client()

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.DeleteResolverParams{}
	if transactionID != "" {
		params.TransactionId = &transactionID
	} else {
		v, err := c.GetVersion(ctx)
		if err != nil {
			return fmt.Errorf("failed to get version: %w", err)
		}
		version := int(v)
		params.Version = &version
	}

	// Call the DeleteResolver API
	resp, err := apiClient.DeleteResolver(ctx, op.Resolver.Name, params)
	if err != nil {
		return fmt.Errorf("failed to delete resolver section '%s': %w", op.Resolver.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("resolver section deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteResolverOperation) Describe() string {
	name := unknownFallback
	if op.Resolver.Name != "" {
		name = op.Resolver.Name
	}
	return fmt.Sprintf("Delete resolver '%s'", name)
}

// UpdateResolverOperation represents updating an existing resolver section.
type UpdateResolverOperation struct {
	Resolver *models.Resolver
}

// NewUpdateResolverOperation creates a new resolver section update operation.
func NewUpdateResolverOperation(resolver *models.Resolver) *UpdateResolverOperation {
	return &UpdateResolverOperation{
		Resolver: resolver,
	}
}

// Type implements Operation.Type.
func (op *UpdateResolverOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateResolverOperation) Section() string {
	return sectionResolver
}

// Priority implements Operation.Priority.
func (op *UpdateResolverOperation) Priority() int {
	return PriorityResolver
}

// Execute updates the resolver section via the Dataplane API.
func (op *UpdateResolverOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Resolver == nil {
		return fmt.Errorf("resolver section is nil")
	}
	if op.Resolver.Name == "" {
		return fmt.Errorf("resolver section name is empty")
	}

	apiClient := c.Client()

	// Convert models.Resolver to dataplaneapi.Resolver using JSON marshaling
	var apiResolver dataplaneapi.Resolver
	data, err := json.Marshal(op.Resolver)
	if err != nil {
		return fmt.Errorf("failed to marshal resolver section: %w", err)
	}
	if err := json.Unmarshal(data, &apiResolver); err != nil {
		return fmt.Errorf("failed to unmarshal resolver section: %w", err)
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.ReplaceResolverParams{}
	if transactionID != "" {
		params.TransactionId = &transactionID
	} else {
		v, err := c.GetVersion(ctx)
		if err != nil {
			return fmt.Errorf("failed to get version: %w", err)
		}
		version := int(v)
		params.Version = &version
	}

	// Call the ReplaceResolver API
	resp, err := apiClient.ReplaceResolver(ctx, op.Resolver.Name, params, apiResolver)
	if err != nil {
		return fmt.Errorf("failed to update resolver section '%s': %w", op.Resolver.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("resolver section update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateResolverOperation) Describe() string {
	name := unknownFallback
	if op.Resolver.Name != "" {
		name = op.Resolver.Name
	}
	return fmt.Sprintf("Update resolver '%s'", name)
}
