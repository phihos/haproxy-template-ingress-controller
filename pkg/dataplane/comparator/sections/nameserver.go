package sections

import (
	"context"
	"fmt"
	"net/http"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/pkg/dataplane/client"
	"haproxy-template-ic/pkg/dataplane/transform"
	"haproxy-template-ic/pkg/generated/dataplaneapi"
)

const (
	sectionNameserver = "nameserver"
)

// PriorityNameserver defines the priority for nameserver operations.
// Nameservers must be created after their parent resolvers section.
const PriorityNameserver = 40

// CreateNameserverOperation represents creating a new nameserver in a resolvers section.
type CreateNameserverOperation struct {
	ResolversSection string
	Nameserver       *models.Nameserver
}

// NewCreateNameserverOperation creates a new nameserver creation operation.
func NewCreateNameserverOperation(resolversSection string, nameserver *models.Nameserver) *CreateNameserverOperation {
	return &CreateNameserverOperation{
		ResolversSection: resolversSection,
		Nameserver:       nameserver,
	}
}

// Type implements Operation.Type.
func (op *CreateNameserverOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateNameserverOperation) Section() string {
	return sectionNameserver
}

// Priority implements Operation.Priority.
func (op *CreateNameserverOperation) Priority() int {
	return PriorityNameserver
}

// Execute creates the nameserver via the Dataplane API.
func (op *CreateNameserverOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Nameserver == nil {
		return fmt.Errorf("nameserver is nil")
	}
	if op.Nameserver.Name == "" {
		return fmt.Errorf("nameserver name is empty")
	}
	if op.ResolversSection == "" {
		return fmt.Errorf("resolvers section name is empty")
	}

	// Convert models.Nameserver to dataplaneapi.Nameserver using JSON marshaling
	apiNameserver := transform.ToAPINameserver(op.Nameserver)
	if apiNameserver == nil {
		return fmt.Errorf("failed to transform nameserver")
	}

	// Prepare parameters and execute with transaction ID or version
	params := &dataplaneapi.CreateNameserverParams{
		Resolver: op.ResolversSection,
	}

	var resp *http.Response
	var err error

	if transactionID != "" {
		// Transaction path: use transaction ID
		params.TransactionId = &transactionID
		resp, err = c.Client().CreateNameserver(ctx, params, *apiNameserver)
	} else {
		// Runtime API path: use version with automatic retry on conflicts
		resp, err = client.ExecuteWithVersion(ctx, c, func(ctx context.Context, version int) (*http.Response, error) {
			params.Version = &version
			return c.Client().CreateNameserver(ctx, params, *apiNameserver)
		})
	}

	if err != nil {
		return fmt.Errorf("failed to create nameserver '%s' in resolvers section '%s': %w", op.Nameserver.Name, op.ResolversSection, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("nameserver creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateNameserverOperation) Describe() string {
	nameserverName := unknownFallback
	if op.Nameserver.Name != "" {
		nameserverName = op.Nameserver.Name
	}
	return fmt.Sprintf("Create nameserver '%s' in resolvers section '%s'", nameserverName, op.ResolversSection)
}

// DeleteNameserverOperation represents deleting an existing nameserver from a resolvers section.
type DeleteNameserverOperation struct {
	ResolversSection string
	Nameserver       *models.Nameserver
}

// NewDeleteNameserverOperation creates a new nameserver deletion operation.
func NewDeleteNameserverOperation(resolversSection string, nameserver *models.Nameserver) *DeleteNameserverOperation {
	return &DeleteNameserverOperation{
		ResolversSection: resolversSection,
		Nameserver:       nameserver,
	}
}

// Type implements Operation.Type.
func (op *DeleteNameserverOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteNameserverOperation) Section() string {
	return sectionNameserver
}

// Priority implements Operation.Priority.
func (op *DeleteNameserverOperation) Priority() int {
	return PriorityNameserver
}

// Execute deletes the nameserver via the Dataplane API.
func (op *DeleteNameserverOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Nameserver == nil {
		return fmt.Errorf("nameserver is nil")
	}
	if op.Nameserver.Name == "" {
		return fmt.Errorf("nameserver name is empty")
	}
	if op.ResolversSection == "" {
		return fmt.Errorf("resolvers section name is empty")
	}

	// Prepare parameters and execute with transaction ID or version
	params := &dataplaneapi.DeleteNameserverParams{
		Resolver: op.ResolversSection,
	}

	var resp *http.Response
	var err error

	if transactionID != "" {
		// Transaction path: use transaction ID
		params.TransactionId = &transactionID
		resp, err = c.Client().DeleteNameserver(ctx, op.Nameserver.Name, params)
	} else {
		// Runtime API path: use version with automatic retry on conflicts
		resp, err = client.ExecuteWithVersion(ctx, c, func(ctx context.Context, version int) (*http.Response, error) {
			params.Version = &version
			return c.Client().DeleteNameserver(ctx, op.Nameserver.Name, params)
		})
	}

	if err != nil {
		return fmt.Errorf("failed to delete nameserver '%s' from resolvers section '%s': %w", op.Nameserver.Name, op.ResolversSection, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("nameserver deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteNameserverOperation) Describe() string {
	nameserverName := unknownFallback
	if op.Nameserver.Name != "" {
		nameserverName = op.Nameserver.Name
	}
	return fmt.Sprintf("Delete nameserver '%s' from resolvers section '%s'", nameserverName, op.ResolversSection)
}

// UpdateNameserverOperation represents updating an existing nameserver in a resolvers section.
type UpdateNameserverOperation struct {
	ResolversSection string
	Nameserver       *models.Nameserver
}

// NewUpdateNameserverOperation creates a new nameserver update operation.
func NewUpdateNameserverOperation(resolversSection string, nameserver *models.Nameserver) *UpdateNameserverOperation {
	return &UpdateNameserverOperation{
		ResolversSection: resolversSection,
		Nameserver:       nameserver,
	}
}

// Type implements Operation.Type.
func (op *UpdateNameserverOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateNameserverOperation) Section() string {
	return sectionNameserver
}

// Priority implements Operation.Priority.
func (op *UpdateNameserverOperation) Priority() int {
	return PriorityNameserver
}

// Execute updates the nameserver via the Dataplane API.
func (op *UpdateNameserverOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Nameserver == nil {
		return fmt.Errorf("nameserver is nil")
	}
	if op.Nameserver.Name == "" {
		return fmt.Errorf("nameserver name is empty")
	}
	if op.ResolversSection == "" {
		return fmt.Errorf("resolvers section name is empty")
	}

	// Convert models.Nameserver to dataplaneapi.Nameserver using JSON marshaling
	apiNameserver := transform.ToAPINameserver(op.Nameserver)
	if apiNameserver == nil {
		return fmt.Errorf("failed to transform nameserver")
	}

	// Prepare parameters and execute with transaction ID or version
	// When transactionID is empty, use version for runtime API (no reload)
	// When transactionID is set, use transaction for config change (reload)
	params := &dataplaneapi.ReplaceNameserverParams{
		Resolver: op.ResolversSection,
	}

	var resp *http.Response
	var err error

	if transactionID != "" {
		// Transaction path: use transaction ID
		params.TransactionId = &transactionID
		resp, err = c.Client().ReplaceNameserver(ctx, op.Nameserver.Name, params, *apiNameserver)
	} else {
		// Runtime API path: use version with automatic retry on conflicts
		resp, err = client.ExecuteWithVersion(ctx, c, func(ctx context.Context, version int) (*http.Response, error) {
			params.Version = &version
			return c.Client().ReplaceNameserver(ctx, op.Nameserver.Name, params, *apiNameserver)
		})
	}

	if err != nil {
		return fmt.Errorf("failed to update nameserver '%s' in resolvers section '%s': %w", op.Nameserver.Name, op.ResolversSection, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("nameserver update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateNameserverOperation) Describe() string {
	nameserverName := unknownFallback
	if op.Nameserver.Name != "" {
		nameserverName = op.Nameserver.Name
	}
	return fmt.Sprintf("Update nameserver '%s' in resolvers section '%s'", nameserverName, op.ResolversSection)
}
