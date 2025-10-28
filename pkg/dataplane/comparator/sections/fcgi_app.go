package sections

import (
	"context"
	"fmt"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/pkg/dataplane/client"
	"haproxy-template-ic/pkg/dataplane/transform"
	"haproxy-template-ic/pkg/generated/dataplaneapi"
)

// PriorityFCGIApp defines priority for fcgi-app sections.
const PriorityFCGIApp = 10

const (
	sectionFCGIApp = "fcgi-app"
)

// CreateFCGIAppOperation represents creating a new fcgi-app section.
type CreateFCGIAppOperation struct {
	FCGIApp *models.FCGIApp
}

// NewCreateFCGIAppOperation creates a new fcgi-app section creation operation.
func NewCreateFCGIAppOperation(fcgiApp *models.FCGIApp) *CreateFCGIAppOperation {
	return &CreateFCGIAppOperation{
		FCGIApp: fcgiApp,
	}
}

// Type implements Operation.Type.
func (op *CreateFCGIAppOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateFCGIAppOperation) Section() string {
	return sectionFCGIApp
}

// Priority implements Operation.Priority.
func (op *CreateFCGIAppOperation) Priority() int {
	return PriorityFCGIApp
}

// Execute creates the fcgi-app section via the Dataplane API.
func (op *CreateFCGIAppOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.FCGIApp == nil {
		return fmt.Errorf("fcgi-app section is nil")
	}
	if op.FCGIApp.Name == "" {
		return fmt.Errorf("fcgi-app section name is empty")
	}

	// Convert models.FCGIApp to dataplaneapi.FcgiApp using transform package
	apiFCGIApp := transform.ToAPIFCGIApp(op.FCGIApp)
	if apiFCGIApp == nil {
		return fmt.Errorf("failed to transform fcgi-app section")
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.CreateFCGIAppParams{}
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

	// Call the CreateFCGIApp API
	resp, err := c.Client().CreateFCGIApp(ctx, params, *apiFCGIApp)
	if err != nil {
		return fmt.Errorf("failed to create fcgi-app section '%s': %w", op.FCGIApp.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("fcgi-app section creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateFCGIAppOperation) Describe() string {
	name := unknownFallback
	if op.FCGIApp.Name != "" {
		name = op.FCGIApp.Name
	}
	return fmt.Sprintf("Create fcgi-app '%s'", name)
}

// DeleteFCGIAppOperation represents deleting an existing fcgi-app section.
type DeleteFCGIAppOperation struct {
	FCGIApp *models.FCGIApp
}

// NewDeleteFCGIAppOperation creates a new fcgi-app section deletion operation.
func NewDeleteFCGIAppOperation(fcgiApp *models.FCGIApp) *DeleteFCGIAppOperation {
	return &DeleteFCGIAppOperation{
		FCGIApp: fcgiApp,
	}
}

// Type implements Operation.Type.
func (op *DeleteFCGIAppOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteFCGIAppOperation) Section() string {
	return sectionFCGIApp
}

// Priority implements Operation.Priority.
func (op *DeleteFCGIAppOperation) Priority() int {
	return PriorityFCGIApp
}

// Execute deletes the fcgi-app section via the Dataplane API.
func (op *DeleteFCGIAppOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.FCGIApp == nil {
		return fmt.Errorf("fcgi-app section is nil")
	}
	if op.FCGIApp.Name == "" {
		return fmt.Errorf("fcgi-app section name is empty")
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.DeleteFCGIAppParams{}
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

	// Call the DeleteFCGIApp API
	resp, err := c.Client().DeleteFCGIApp(ctx, op.FCGIApp.Name, params)
	if err != nil {
		return fmt.Errorf("failed to delete fcgi-app section '%s': %w", op.FCGIApp.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("fcgi-app section deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteFCGIAppOperation) Describe() string {
	name := unknownFallback
	if op.FCGIApp.Name != "" {
		name = op.FCGIApp.Name
	}
	return fmt.Sprintf("Delete fcgi-app '%s'", name)
}

// UpdateFCGIAppOperation represents updating an existing fcgi-app section.
type UpdateFCGIAppOperation struct {
	FCGIApp *models.FCGIApp
}

// NewUpdateFCGIAppOperation creates a new fcgi-app section update operation.
func NewUpdateFCGIAppOperation(fcgiApp *models.FCGIApp) *UpdateFCGIAppOperation {
	return &UpdateFCGIAppOperation{
		FCGIApp: fcgiApp,
	}
}

// Type implements Operation.Type.
func (op *UpdateFCGIAppOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateFCGIAppOperation) Section() string {
	return sectionFCGIApp
}

// Priority implements Operation.Priority.
func (op *UpdateFCGIAppOperation) Priority() int {
	return PriorityFCGIApp
}

// Execute updates the fcgi-app section via the Dataplane API.
func (op *UpdateFCGIAppOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.FCGIApp == nil {
		return fmt.Errorf("fcgi-app section is nil")
	}
	if op.FCGIApp.Name == "" {
		return fmt.Errorf("fcgi-app section name is empty")
	}

	// Convert models.FCGIApp to dataplaneapi.FcgiApp using transform package
	apiFCGIApp := transform.ToAPIFCGIApp(op.FCGIApp)
	if apiFCGIApp == nil {
		return fmt.Errorf("failed to transform fcgi-app section")
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.ReplaceFCGIAppParams{}
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

	// Call the ReplaceFCGIApp API
	resp, err := c.Client().ReplaceFCGIApp(ctx, op.FCGIApp.Name, params, *apiFCGIApp)
	if err != nil {
		return fmt.Errorf("failed to update fcgi-app section '%s': %w", op.FCGIApp.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("fcgi-app section update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateFCGIAppOperation) Describe() string {
	name := unknownFallback
	if op.FCGIApp.Name != "" {
		name = op.FCGIApp.Name
	}
	return fmt.Sprintf("Update fcgi-app '%s'", name)
}
