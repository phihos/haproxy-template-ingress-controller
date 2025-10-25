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

const (
	sectionPeerEntry = "peer_entry"
)

// PriorityPeerEntry defines the priority for peer entry operations.
// Peer entries must be created after their parent peers section.
const PriorityPeerEntry = 40

// CreatePeerEntryOperation represents creating a new peer entry in a peers section.
type CreatePeerEntryOperation struct {
	PeersSection string
	PeerEntry    *models.PeerEntry
}

// NewCreatePeerEntryOperation creates a new peer entry creation operation.
func NewCreatePeerEntryOperation(peersSection string, peerEntry *models.PeerEntry) *CreatePeerEntryOperation {
	return &CreatePeerEntryOperation{
		PeersSection: peersSection,
		PeerEntry:    peerEntry,
	}
}

// Type implements Operation.Type.
func (op *CreatePeerEntryOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreatePeerEntryOperation) Section() string {
	return sectionPeerEntry
}

// Priority implements Operation.Priority.
func (op *CreatePeerEntryOperation) Priority() int {
	return PriorityPeerEntry
}

// Execute creates the peer entry via the Dataplane API.
func (op *CreatePeerEntryOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeCreateChildHelper(
		ctx, c, transactionID, op.PeerEntry, op.PeersSection,
		func(m *models.PeerEntry) string { return m.Name },
		transform.ToAPIPeerEntry,
		func(parent string) *dataplaneapi.CreatePeerEntryParams {
			return &dataplaneapi.CreatePeerEntryParams{PeerSection: parent}
		},
		func(p *dataplaneapi.CreatePeerEntryParams, tid *string) { p.TransactionId = tid },
		func(p *dataplaneapi.CreatePeerEntryParams, v *int) { p.Version = v },
		func(ctx context.Context, params *dataplaneapi.CreatePeerEntryParams, apiModel dataplaneapi.PeerEntry) (*http.Response, error) {
			return c.Client().CreatePeerEntry(ctx, params, apiModel)
		},
		"peer entry",
		"peers section",
	)
}

// Describe returns a human-readable description of this operation.
func (op *CreatePeerEntryOperation) Describe() string {
	peerName := unknownFallback
	if op.PeerEntry.Name != "" {
		peerName = op.PeerEntry.Name
	}
	return fmt.Sprintf("Create peer entry '%s' in peers section '%s'", peerName, op.PeersSection)
}

// DeletePeerEntryOperation represents deleting an existing peer entry from a peers section.
type DeletePeerEntryOperation struct {
	PeersSection string
	PeerEntry    *models.PeerEntry
}

// NewDeletePeerEntryOperation creates a new peer entry deletion operation.
func NewDeletePeerEntryOperation(peersSection string, peerEntry *models.PeerEntry) *DeletePeerEntryOperation {
	return &DeletePeerEntryOperation{
		PeersSection: peersSection,
		PeerEntry:    peerEntry,
	}
}

// Type implements Operation.Type.
func (op *DeletePeerEntryOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeletePeerEntryOperation) Section() string {
	return sectionPeerEntry
}

// Priority implements Operation.Priority.
func (op *DeletePeerEntryOperation) Priority() int {
	return PriorityPeerEntry
}

// Execute deletes the peer entry via the Dataplane API.
func (op *DeletePeerEntryOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	return executeDeleteChildHelper(
		ctx, c, transactionID, op.PeerEntry, op.PeersSection,
		func(m *models.PeerEntry) string { return m.Name },
		func(parent string) *dataplaneapi.DeletePeerEntryParams {
			return &dataplaneapi.DeletePeerEntryParams{PeerSection: parent}
		},
		func(p *dataplaneapi.DeletePeerEntryParams, tid *string) { p.TransactionId = tid },
		func(p *dataplaneapi.DeletePeerEntryParams, v *int) { p.Version = v },
		func(ctx context.Context, name string, params *dataplaneapi.DeletePeerEntryParams) (*http.Response, error) {
			return c.Client().DeletePeerEntry(ctx, name, params)
		},
		"peer entry",
		"peers section",
	)
}

// Describe returns a human-readable description of this operation.
func (op *DeletePeerEntryOperation) Describe() string {
	peerName := unknownFallback
	if op.PeerEntry.Name != "" {
		peerName = op.PeerEntry.Name
	}
	return fmt.Sprintf("Delete peer entry '%s' from peers section '%s'", peerName, op.PeersSection)
}

// UpdatePeerEntryOperation represents updating an existing peer entry in a peers section.
type UpdatePeerEntryOperation struct {
	PeersSection string
	PeerEntry    *models.PeerEntry
}

// NewUpdatePeerEntryOperation creates a new peer entry update operation.
func NewUpdatePeerEntryOperation(peersSection string, peerEntry *models.PeerEntry) *UpdatePeerEntryOperation {
	return &UpdatePeerEntryOperation{
		PeersSection: peersSection,
		PeerEntry:    peerEntry,
	}
}

// Type implements Operation.Type.
func (op *UpdatePeerEntryOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdatePeerEntryOperation) Section() string {
	return sectionPeerEntry
}

// Priority implements Operation.Priority.
func (op *UpdatePeerEntryOperation) Priority() int {
	return PriorityPeerEntry
}

// Execute updates the peer entry via the Dataplane API.
func (op *UpdatePeerEntryOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.PeerEntry == nil {
		return fmt.Errorf("peer entry is nil")
	}
	if op.PeerEntry.Name == "" {
		return fmt.Errorf("peer entry name is empty")
	}
	if op.PeersSection == "" {
		return fmt.Errorf("peers section name is empty")
	}

	// Convert models.PeerEntry to dataplaneapi.PeerEntry using JSON marshaling
	apiPeerEntry := transform.ToAPIPeerEntry(op.PeerEntry)
	if apiPeerEntry == nil {
		return fmt.Errorf("failed to transform peer entry")
	}

	// Prepare parameters and execute with transaction ID or version
	// When transactionID is empty, use version for runtime API (no reload)
	// When transactionID is set, use transaction for config change (reload)
	params := &dataplaneapi.ReplacePeerEntryParams{
		PeerSection: op.PeersSection,
	}

	var resp *http.Response
	var err error

	if transactionID != "" {
		// Transaction path: use transaction ID
		params.TransactionId = &transactionID
		resp, err = c.Client().ReplacePeerEntry(ctx, op.PeerEntry.Name, params, *apiPeerEntry)
	} else {
		// Runtime API path: use version with automatic retry on conflicts
		resp, err = client.ExecuteWithVersion(ctx, c, func(ctx context.Context, version int) (*http.Response, error) {
			params.Version = &version
			return c.Client().ReplacePeerEntry(ctx, op.PeerEntry.Name, params, *apiPeerEntry)
		})
	}

	if err != nil {
		return fmt.Errorf("failed to update peer entry '%s' in peers section '%s': %w", op.PeerEntry.Name, op.PeersSection, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("peer entry update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdatePeerEntryOperation) Describe() string {
	peerName := unknownFallback
	if op.PeerEntry.Name != "" {
		peerName = op.PeerEntry.Name
	}
	return fmt.Sprintf("Update peer entry '%s' in peers section '%s'", peerName, op.PeersSection)
}
