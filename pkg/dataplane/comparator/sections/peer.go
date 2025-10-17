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

// PriorityPeer defines priority for peer sections.
// Peers should be created early as they might be referenced by backends.
const PriorityPeer = 15

const (
	sectionPeer = "peer"
)

// CreatePeerOperation represents creating a new peer section.
type CreatePeerOperation struct {
	Peer *models.PeerSection
}

// NewCreatePeerOperation creates a new peer section creation operation.
func NewCreatePeerOperation(peer *models.PeerSection) *CreatePeerOperation {
	return &CreatePeerOperation{
		Peer: peer,
	}
}

// Type implements Operation.Type.
func (op *CreatePeerOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreatePeerOperation) Section() string {
	return sectionPeer
}

// Priority implements Operation.Priority.
func (op *CreatePeerOperation) Priority() int {
	return PriorityPeer
}

// Execute creates the peer section via the Dataplane API.
func (op *CreatePeerOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Peer == nil {
		return fmt.Errorf("peer section is nil")
	}
	if op.Peer.Name == "" {
		return fmt.Errorf("peer section name is empty")
	}

	apiClient := c.Client()

	// Convert models.PeerSection to dataplaneapi.PeerSection using JSON marshaling
	var apiPeer dataplaneapi.PeerSection
	data, err := json.Marshal(op.Peer)
	if err != nil {
		return fmt.Errorf("failed to marshal peer section: %w", err)
	}
	if err := json.Unmarshal(data, &apiPeer); err != nil {
		return fmt.Errorf("failed to unmarshal peer section: %w", err)
	}

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.CreatePeerParams{}
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

	// Call the CreatePeer API
	resp, err := apiClient.CreatePeer(ctx, params, apiPeer)
	if err != nil {
		return fmt.Errorf("failed to create peer section '%s': %w", op.Peer.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("peer section creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreatePeerOperation) Describe() string {
	name := unknownFallback
	if op.Peer.Name != "" {
		name = op.Peer.Name
	}
	return fmt.Sprintf("Create peer section '%s'", name)
}

// DeletePeerOperation represents deleting an existing peer section.
type DeletePeerOperation struct {
	Peer *models.PeerSection
}

// NewDeletePeerOperation creates a new peer section deletion operation.
func NewDeletePeerOperation(peer *models.PeerSection) *DeletePeerOperation {
	return &DeletePeerOperation{
		Peer: peer,
	}
}

// Type implements Operation.Type.
func (op *DeletePeerOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeletePeerOperation) Section() string {
	return sectionPeer
}

// Priority implements Operation.Priority.
func (op *DeletePeerOperation) Priority() int {
	return PriorityPeer
}

// Execute deletes the peer section via the Dataplane API.
func (op *DeletePeerOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Peer == nil {
		return fmt.Errorf("peer section is nil")
	}
	if op.Peer.Name == "" {
		return fmt.Errorf("peer section name is empty")
	}

	apiClient := c.Client()

	// Prepare parameters with transaction ID or version
	params := &dataplaneapi.DeletePeerParams{}
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

	// Call the DeletePeer API
	resp, err := apiClient.DeletePeer(ctx, op.Peer.Name, params)
	if err != nil {
		return fmt.Errorf("failed to delete peer section '%s': %w", op.Peer.Name, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("peer section deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeletePeerOperation) Describe() string {
	name := unknownFallback
	if op.Peer.Name != "" {
		name = op.Peer.Name
	}
	return fmt.Sprintf("Delete peer section '%s'", name)
}

// UpdatePeerOperation represents updating an existing peer section.
// Note: The HAProxy Dataplane API does not support updating peer sections directly.
// Updates require deleting and recreating the peer section.
type UpdatePeerOperation struct {
	Peer *models.PeerSection
}

// NewUpdatePeerOperation creates a new peer section update operation.
func NewUpdatePeerOperation(peer *models.PeerSection) *UpdatePeerOperation {
	return &UpdatePeerOperation{
		Peer: peer,
	}
}

// Type implements Operation.Type.
func (op *UpdatePeerOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdatePeerOperation) Section() string {
	return sectionPeer
}

// Priority implements Operation.Priority.
func (op *UpdatePeerOperation) Priority() int {
	return PriorityPeer
}

// Execute updates the peer section via delete and recreate.
func (op *UpdatePeerOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	// The HAProxy Dataplane API does not provide a direct update/replace endpoint for peer sections.
	// To update a peer section, we need to delete it and recreate it.
	// However, this is risky as it may cause disruptions. For now, return an error.
	return fmt.Errorf("peer section updates are not supported by HAProxy Dataplane API (section: %s)", op.Peer.Name)
}

// Describe returns a human-readable description of this operation.
func (op *UpdatePeerOperation) Describe() string {
	name := unknownFallback
	if op.Peer.Name != "" {
		name = op.Peer.Name
	}
	return fmt.Sprintf("Update peer section '%s'", name)
}
