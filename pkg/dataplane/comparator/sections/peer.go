package sections

import (
	"context"
	"fmt"
	"net/http"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/codegen/dataplaneapi"
	"haproxy-template-ic/pkg/dataplane/client"
	"haproxy-template-ic/pkg/dataplane/transform"
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
	return executeCreateHelper(
		ctx, transactionID, op.Peer,
		func(r *models.PeerSection) string { return r.Name },
		transform.ToAPIPeerSection,
		func(ctx context.Context, apiPeer *dataplaneapi.PeerSection, txID string) (*http.Response, error) {
			return wrapAPICallWithVersionOrTransaction(
				ctx, c, txID,
				func() *dataplaneapi.CreatePeerParams { return &dataplaneapi.CreatePeerParams{} },
				func(p *dataplaneapi.CreatePeerParams, tid *string) { p.TransactionId = tid },
				func(p *dataplaneapi.CreatePeerParams, v *int) { p.Version = v },
				func(ctx context.Context, params *dataplaneapi.CreatePeerParams) (*http.Response, error) {
					return c.Client().CreatePeer(ctx, params, *apiPeer)
				},
			)
		},
		"peer section",
	)
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
	return executeDeleteHelper(
		ctx, transactionID, op.Peer,
		func(r *models.PeerSection) string { return r.Name },
		func(ctx context.Context, name string, txID string) (*http.Response, error) {
			return wrapAPICallWithVersionOrTransaction(
				ctx, c, txID,
				func() *dataplaneapi.DeletePeerParams { return &dataplaneapi.DeletePeerParams{} },
				func(p *dataplaneapi.DeletePeerParams, tid *string) { p.TransactionId = tid },
				func(p *dataplaneapi.DeletePeerParams, v *int) { p.Version = v },
				func(ctx context.Context, params *dataplaneapi.DeletePeerParams) (*http.Response, error) {
					return c.Client().DeletePeer(ctx, name, params)
				},
			)
		},
		"peer section",
	)
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
