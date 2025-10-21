package sections

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/codegen/dataplaneapi"
	"haproxy-template-ic/pkg/dataplane/client"
)

const (
	sectionServer = "server"
)

// CreateServerOperation represents creating a new server in a backend.
type CreateServerOperation struct {
	BackendName string
	Server      *models.Server
}

// NewCreateServerOperation creates a new server creation operation.
func NewCreateServerOperation(backendName string, server *models.Server) *CreateServerOperation {
	return &CreateServerOperation{
		BackendName: backendName,
		Server:      server,
	}
}

// Type implements Operation.Type.
func (op *CreateServerOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateServerOperation) Section() string {
	return sectionServer
}

// Priority implements Operation.Priority.
func (op *CreateServerOperation) Priority() int {
	return PriorityServer
}

// Execute creates the server via the Dataplane API.
func (op *CreateServerOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Server == nil {
		return fmt.Errorf("server is nil")
	}
	if op.Server.Name == "" {
		return fmt.Errorf("server name is empty")
	}
	if op.BackendName == "" {
		return fmt.Errorf("backend name is empty")
	}

	apiClient := c.Client()

	// Convert models.Server to dataplaneapi.Server using JSON marshaling
	var apiServer dataplaneapi.Server
	data, err := json.Marshal(op.Server)
	if err != nil {
		return fmt.Errorf("failed to marshal server: %w", err)
	}
	if err := json.Unmarshal(data, &apiServer); err != nil {
		return fmt.Errorf("failed to unmarshal server: %w", err)
	}

	// Prepare parameters and execute with transaction ID or version
	params := &dataplaneapi.CreateServerBackendParams{}

	var resp *http.Response

	if transactionID != "" {
		// Transaction path: use transaction ID
		params.TransactionId = &transactionID
		resp, err = apiClient.CreateServerBackend(ctx, op.BackendName, params, apiServer)
	} else {
		// Runtime API path: use version with automatic retry on conflicts
		resp, err = client.ExecuteWithVersion(ctx, c, func(ctx context.Context, version int) (*http.Response, error) {
			params.Version = &version
			return apiClient.CreateServerBackend(ctx, op.BackendName, params, apiServer)
		})
	}

	if err != nil {
		return fmt.Errorf("failed to create server '%s' in backend '%s': %w", op.Server.Name, op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("server creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateServerOperation) Describe() string {
	serverName := unknownFallback
	if op.Server.Name != "" {
		serverName = op.Server.Name
	}
	return fmt.Sprintf("Create server '%s' in backend '%s'", serverName, op.BackendName)
}

// DeleteServerOperation represents deleting an existing server from a backend.
type DeleteServerOperation struct {
	BackendName string
	Server      *models.Server
}

// NewDeleteServerOperation creates a new server deletion operation.
func NewDeleteServerOperation(backendName string, server *models.Server) *DeleteServerOperation {
	return &DeleteServerOperation{
		BackendName: backendName,
		Server:      server,
	}
}

// Type implements Operation.Type.
func (op *DeleteServerOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteServerOperation) Section() string {
	return sectionServer
}

// Priority implements Operation.Priority.
func (op *DeleteServerOperation) Priority() int {
	return PriorityServer
}

// Execute deletes the server via the Dataplane API.
func (op *DeleteServerOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Server == nil {
		return fmt.Errorf("server is nil")
	}
	if op.Server.Name == "" {
		return fmt.Errorf("server name is empty")
	}
	if op.BackendName == "" {
		return fmt.Errorf("backend name is empty")
	}

	apiClient := c.Client()

	// Prepare parameters and execute with transaction ID or version
	params := &dataplaneapi.DeleteServerBackendParams{}

	var resp *http.Response
	var err error

	if transactionID != "" {
		// Transaction path: use transaction ID
		params.TransactionId = &transactionID
		resp, err = apiClient.DeleteServerBackend(ctx, op.BackendName, op.Server.Name, params)
	} else {
		// Runtime API path: use version with automatic retry on conflicts
		resp, err = client.ExecuteWithVersion(ctx, c, func(ctx context.Context, version int) (*http.Response, error) {
			params.Version = &version
			return apiClient.DeleteServerBackend(ctx, op.BackendName, op.Server.Name, params)
		})
	}

	if err != nil {
		return fmt.Errorf("failed to delete server '%s' from backend '%s': %w", op.Server.Name, op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("server deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteServerOperation) Describe() string {
	serverName := unknownFallback
	if op.Server.Name != "" {
		serverName = op.Server.Name
	}
	return fmt.Sprintf("Delete server '%s' from backend '%s'", serverName, op.BackendName)
}

// UpdateServerOperation represents updating an existing server in a backend.
type UpdateServerOperation struct {
	BackendName string
	Server      *models.Server
}

// NewUpdateServerOperation creates a new server update operation.
func NewUpdateServerOperation(backendName string, server *models.Server) *UpdateServerOperation {
	return &UpdateServerOperation{
		BackendName: backendName,
		Server:      server,
	}
}

// Type implements Operation.Type.
func (op *UpdateServerOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateServerOperation) Section() string {
	return sectionServer
}

// Priority implements Operation.Priority.
func (op *UpdateServerOperation) Priority() int {
	return PriorityServer
}

// Execute updates the server via the Dataplane API.
func (op *UpdateServerOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Server == nil {
		return fmt.Errorf("server is nil")
	}
	if op.Server.Name == "" {
		return fmt.Errorf("server name is empty")
	}
	if op.BackendName == "" {
		return fmt.Errorf("backend name is empty")
	}

	apiClient := c.Client()

	// Convert models.Server to dataplaneapi.Server using JSON marshaling
	var apiServer dataplaneapi.Server
	data, err := json.Marshal(op.Server)
	if err != nil {
		return fmt.Errorf("failed to marshal server: %w", err)
	}
	if err := json.Unmarshal(data, &apiServer); err != nil {
		return fmt.Errorf("failed to unmarshal server: %w", err)
	}

	// Prepare parameters and execute with transaction ID or version
	// When transactionID is empty, use version for runtime API (no reload)
	// When transactionID is set, use transaction for config change (reload)
	params := &dataplaneapi.ReplaceServerBackendParams{}

	var resp *http.Response

	if transactionID != "" {
		// Transaction path: use transaction ID
		params.TransactionId = &transactionID
		resp, err = apiClient.ReplaceServerBackend(ctx, op.BackendName, op.Server.Name, params, apiServer)
	} else {
		// Runtime API path: use version with automatic retry on conflicts
		resp, err = client.ExecuteWithVersion(ctx, c, func(ctx context.Context, version int) (*http.Response, error) {
			params.Version = &version
			return apiClient.ReplaceServerBackend(ctx, op.BackendName, op.Server.Name, params, apiServer)
		})
	}

	if err != nil {
		return fmt.Errorf("failed to update server '%s' in backend '%s': %w", op.Server.Name, op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("server update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateServerOperation) Describe() string {
	serverName := unknownFallback
	if op.Server.Name != "" {
		serverName = op.Server.Name
	}
	return fmt.Sprintf("Update server '%s' in backend '%s'", serverName, op.BackendName)
}
