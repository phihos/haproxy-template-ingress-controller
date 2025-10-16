package sections

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/codegen/dataplaneapi"
	"haproxy-template-ic/pkg/dataplane/client"
)

// CreateServerTemplateOperation represents creating a new server template in a backend.
type CreateServerTemplateOperation struct {
	BackendName    string
	ServerTemplate *models.ServerTemplate
}

// NewCreateServerTemplateOperation creates a new server template creation operation.
func NewCreateServerTemplateOperation(backendName string, serverTemplate *models.ServerTemplate) *CreateServerTemplateOperation {
	return &CreateServerTemplateOperation{
		BackendName:    backendName,
		ServerTemplate: serverTemplate,
	}
}

// Type implements Operation.Type.
func (op *CreateServerTemplateOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateServerTemplateOperation) Section() string {
	return "server-template"
}

// Priority implements Operation.Priority.
func (op *CreateServerTemplateOperation) Priority() int {
	return PriorityServer
}

// Execute creates the server template via the Dataplane API.
func (op *CreateServerTemplateOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.ServerTemplate == nil {
		return fmt.Errorf("server template is nil")
	}
	if op.ServerTemplate.Prefix == "" {
		return fmt.Errorf("server template prefix is empty")
	}
	if op.BackendName == "" {
		return fmt.Errorf("backend name is empty")
	}

	apiClient := c.Client()

	// Convert models.ServerTemplate to dataplaneapi.ServerTemplate using JSON marshaling
	var apiServerTemplate dataplaneapi.ServerTemplate
	data, err := json.Marshal(op.ServerTemplate)
	if err != nil {
		return fmt.Errorf("failed to marshal server template: %w", err)
	}
	if err := json.Unmarshal(data, &apiServerTemplate); err != nil {
		return fmt.Errorf("failed to unmarshal server template: %w", err)
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.CreateServerTemplateParams{}
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

	// Call the CreateServerTemplate API
	resp, err := apiClient.CreateServerTemplate(ctx, op.BackendName, params, apiServerTemplate)
	if err != nil {
		return fmt.Errorf("failed to create server template '%s' in backend '%s': %w", op.ServerTemplate.Prefix, op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("server template creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateServerTemplateOperation) Describe() string {
	prefix := "unknown"
	if op.ServerTemplate.Prefix != "" {
		prefix = op.ServerTemplate.Prefix
	}
	return fmt.Sprintf("Create server template '%s' in backend '%s'", prefix, op.BackendName)
}

// DeleteServerTemplateOperation represents deleting an existing server template from a backend.
type DeleteServerTemplateOperation struct {
	BackendName    string
	ServerTemplate *models.ServerTemplate
}

// NewDeleteServerTemplateOperation creates a new server template deletion operation.
func NewDeleteServerTemplateOperation(backendName string, serverTemplate *models.ServerTemplate) *DeleteServerTemplateOperation {
	return &DeleteServerTemplateOperation{
		BackendName:    backendName,
		ServerTemplate: serverTemplate,
	}
}

// Type implements Operation.Type.
func (op *DeleteServerTemplateOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteServerTemplateOperation) Section() string {
	return "server-template"
}

// Priority implements Operation.Priority.
func (op *DeleteServerTemplateOperation) Priority() int {
	return PriorityServer
}

// Execute deletes the server template via the Dataplane API.
func (op *DeleteServerTemplateOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.ServerTemplate == nil {
		return fmt.Errorf("server template is nil")
	}
	if op.ServerTemplate.Prefix == "" {
		return fmt.Errorf("server template prefix is empty")
	}
	if op.BackendName == "" {
		return fmt.Errorf("backend name is empty")
	}

	apiClient := c.Client()

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.DeleteServerTemplateParams{}
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

	// Call the DeleteServerTemplate API
	resp, err := apiClient.DeleteServerTemplate(ctx, op.BackendName, op.ServerTemplate.Prefix, params)
	if err != nil {
		return fmt.Errorf("failed to delete server template '%s' from backend '%s': %w", op.ServerTemplate.Prefix, op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("server template deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteServerTemplateOperation) Describe() string {
	prefix := "unknown"
	if op.ServerTemplate.Prefix != "" {
		prefix = op.ServerTemplate.Prefix
	}
	return fmt.Sprintf("Delete server template '%s' from backend '%s'", prefix, op.BackendName)
}

// UpdateServerTemplateOperation represents updating an existing server template in a backend.
type UpdateServerTemplateOperation struct {
	BackendName    string
	ServerTemplate *models.ServerTemplate
}

// NewUpdateServerTemplateOperation creates a new server template update operation.
func NewUpdateServerTemplateOperation(backendName string, serverTemplate *models.ServerTemplate) *UpdateServerTemplateOperation {
	return &UpdateServerTemplateOperation{
		BackendName:    backendName,
		ServerTemplate: serverTemplate,
	}
}

// Type implements Operation.Type.
func (op *UpdateServerTemplateOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateServerTemplateOperation) Section() string {
	return "server-template"
}

// Priority implements Operation.Priority.
func (op *UpdateServerTemplateOperation) Priority() int {
	return PriorityServer
}

// Execute updates the server template via the Dataplane API.
func (op *UpdateServerTemplateOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.ServerTemplate == nil {
		return fmt.Errorf("server template is nil")
	}
	if op.ServerTemplate.Prefix == "" {
		return fmt.Errorf("server template prefix is empty")
	}
	if op.BackendName == "" {
		return fmt.Errorf("backend name is empty")
	}

	apiClient := c.Client()

	// Convert models.ServerTemplate to dataplaneapi.ServerTemplate using JSON marshaling
	var apiServerTemplate dataplaneapi.ServerTemplate
	data, err := json.Marshal(op.ServerTemplate)
	if err != nil {
		return fmt.Errorf("failed to marshal server template: %w", err)
	}
	if err := json.Unmarshal(data, &apiServerTemplate); err != nil {
		return fmt.Errorf("failed to unmarshal server template: %w", err)
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.ReplaceServerTemplateParams{}
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

	// Call the ReplaceServerTemplate API
	resp, err := apiClient.ReplaceServerTemplate(ctx, op.BackendName, op.ServerTemplate.Prefix, params, apiServerTemplate)
	if err != nil {
		return fmt.Errorf("failed to update server template '%s' in backend '%s': %w", op.ServerTemplate.Prefix, op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("server template update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateServerTemplateOperation) Describe() string {
	prefix := "unknown"
	if op.ServerTemplate.Prefix != "" {
		prefix = op.ServerTemplate.Prefix
	}
	return fmt.Sprintf("Update server template '%s' in backend '%s'", prefix, op.BackendName)
}
