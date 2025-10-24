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
	sectionMailerEntry = "mailer_entry"
)

// PriorityMailerEntry defines the priority for mailer entry operations.
// Mailer entries must be created after their parent mailers section.
const PriorityMailerEntry = 40

// CreateMailerEntryOperation represents creating a new mailer entry in a mailers section.
type CreateMailerEntryOperation struct {
	MailersSection string
	MailerEntry    *models.MailerEntry
}

// NewCreateMailerEntryOperation creates a new mailer entry creation operation.
func NewCreateMailerEntryOperation(mailersSection string, mailerEntry *models.MailerEntry) *CreateMailerEntryOperation {
	return &CreateMailerEntryOperation{
		MailersSection: mailersSection,
		MailerEntry:    mailerEntry,
	}
}

// Type implements Operation.Type.
func (op *CreateMailerEntryOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateMailerEntryOperation) Section() string {
	return sectionMailerEntry
}

// Priority implements Operation.Priority.
func (op *CreateMailerEntryOperation) Priority() int {
	return PriorityMailerEntry
}

// Execute creates the mailer entry via the Dataplane API.
func (op *CreateMailerEntryOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.MailerEntry == nil {
		return fmt.Errorf("mailer entry is nil")
	}
	if op.MailerEntry.Name == "" {
		return fmt.Errorf("mailer entry name is empty")
	}
	if op.MailersSection == "" {
		return fmt.Errorf("mailers section name is empty")
	}

	apiClient := c.Client()

	// Convert models.MailerEntry to dataplaneapi.MailerEntry using JSON marshaling
	apiMailerEntry := transform.ToAPIMailerEntry(op.MailerEntry)
	if apiMailerEntry == nil {
		return fmt.Errorf("failed to transform mailer entry")
	}

	// Prepare parameters and execute with transaction ID or version
	params := &dataplaneapi.CreateMailerEntryParams{
		MailersSection: op.MailersSection,
	}

	var resp *http.Response
	var err error

	if transactionID != "" {
		// Transaction path: use transaction ID
		params.TransactionId = &transactionID
		resp, err = apiClient.CreateMailerEntry(ctx, params, *apiMailerEntry)
	} else {
		// Runtime API path: use version with automatic retry on conflicts
		resp, err = client.ExecuteWithVersion(ctx, c, func(ctx context.Context, version int) (*http.Response, error) {
			params.Version = &version
			return apiClient.CreateMailerEntry(ctx, params, *apiMailerEntry)
		})
	}

	if err != nil {
		return fmt.Errorf("failed to create mailer entry '%s' in mailers section '%s': %w", op.MailerEntry.Name, op.MailersSection, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("mailer entry creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateMailerEntryOperation) Describe() string {
	mailerName := unknownFallback
	if op.MailerEntry.Name != "" {
		mailerName = op.MailerEntry.Name
	}
	return fmt.Sprintf("Create mailer entry '%s' in mailers section '%s'", mailerName, op.MailersSection)
}

// DeleteMailerEntryOperation represents deleting an existing mailer entry from a mailers section.
type DeleteMailerEntryOperation struct {
	MailersSection string
	MailerEntry    *models.MailerEntry
}

// NewDeleteMailerEntryOperation creates a new mailer entry deletion operation.
func NewDeleteMailerEntryOperation(mailersSection string, mailerEntry *models.MailerEntry) *DeleteMailerEntryOperation {
	return &DeleteMailerEntryOperation{
		MailersSection: mailersSection,
		MailerEntry:    mailerEntry,
	}
}

// Type implements Operation.Type.
func (op *DeleteMailerEntryOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteMailerEntryOperation) Section() string {
	return sectionMailerEntry
}

// Priority implements Operation.Priority.
func (op *DeleteMailerEntryOperation) Priority() int {
	return PriorityMailerEntry
}

// Execute deletes the mailer entry via the Dataplane API.
func (op *DeleteMailerEntryOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.MailerEntry == nil {
		return fmt.Errorf("mailer entry is nil")
	}
	if op.MailerEntry.Name == "" {
		return fmt.Errorf("mailer entry name is empty")
	}
	if op.MailersSection == "" {
		return fmt.Errorf("mailers section name is empty")
	}

	apiClient := c.Client()

	// Prepare parameters and execute with transaction ID or version
	params := &dataplaneapi.DeleteMailerEntryParams{
		MailersSection: op.MailersSection,
	}

	var resp *http.Response
	var err error

	if transactionID != "" {
		// Transaction path: use transaction ID
		params.TransactionId = &transactionID
		resp, err = apiClient.DeleteMailerEntry(ctx, op.MailerEntry.Name, params)
	} else {
		// Runtime API path: use version with automatic retry on conflicts
		resp, err = client.ExecuteWithVersion(ctx, c, func(ctx context.Context, version int) (*http.Response, error) {
			params.Version = &version
			return apiClient.DeleteMailerEntry(ctx, op.MailerEntry.Name, params)
		})
	}

	if err != nil {
		return fmt.Errorf("failed to delete mailer entry '%s' from mailers section '%s': %w", op.MailerEntry.Name, op.MailersSection, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("mailer entry deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteMailerEntryOperation) Describe() string {
	mailerName := unknownFallback
	if op.MailerEntry.Name != "" {
		mailerName = op.MailerEntry.Name
	}
	return fmt.Sprintf("Delete mailer entry '%s' from mailers section '%s'", mailerName, op.MailersSection)
}

// UpdateMailerEntryOperation represents updating an existing mailer entry in a mailers section.
type UpdateMailerEntryOperation struct {
	MailersSection string
	MailerEntry    *models.MailerEntry
}

// NewUpdateMailerEntryOperation creates a new mailer entry update operation.
func NewUpdateMailerEntryOperation(mailersSection string, mailerEntry *models.MailerEntry) *UpdateMailerEntryOperation {
	return &UpdateMailerEntryOperation{
		MailersSection: mailersSection,
		MailerEntry:    mailerEntry,
	}
}

// Type implements Operation.Type.
func (op *UpdateMailerEntryOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateMailerEntryOperation) Section() string {
	return sectionMailerEntry
}

// Priority implements Operation.Priority.
func (op *UpdateMailerEntryOperation) Priority() int {
	return PriorityMailerEntry
}

// Execute updates the mailer entry via the Dataplane API.
func (op *UpdateMailerEntryOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.MailerEntry == nil {
		return fmt.Errorf("mailer entry is nil")
	}
	if op.MailerEntry.Name == "" {
		return fmt.Errorf("mailer entry name is empty")
	}
	if op.MailersSection == "" {
		return fmt.Errorf("mailers section name is empty")
	}

	apiClient := c.Client()

	// Convert models.MailerEntry to dataplaneapi.MailerEntry using JSON marshaling
	apiMailerEntry := transform.ToAPIMailerEntry(op.MailerEntry)
	if apiMailerEntry == nil {
		return fmt.Errorf("failed to transform mailer entry")
	}

	// Prepare parameters and execute with transaction ID or version
	// When transactionID is empty, use version for runtime API (no reload)
	// When transactionID is set, use transaction for config change (reload)
	params := &dataplaneapi.ReplaceMailerEntryParams{
		MailersSection: op.MailersSection,
	}

	var resp *http.Response
	var err error

	if transactionID != "" {
		// Transaction path: use transaction ID
		params.TransactionId = &transactionID
		resp, err = apiClient.ReplaceMailerEntry(ctx, op.MailerEntry.Name, params, *apiMailerEntry)
	} else {
		// Runtime API path: use version with automatic retry on conflicts
		resp, err = client.ExecuteWithVersion(ctx, c, func(ctx context.Context, version int) (*http.Response, error) {
			params.Version = &version
			return apiClient.ReplaceMailerEntry(ctx, op.MailerEntry.Name, params, *apiMailerEntry)
		})
	}

	if err != nil {
		return fmt.Errorf("failed to update mailer entry '%s' in mailers section '%s': %w", op.MailerEntry.Name, op.MailersSection, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("mailer entry update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateMailerEntryOperation) Describe() string {
	mailerName := unknownFallback
	if op.MailerEntry.Name != "" {
		mailerName = op.MailerEntry.Name
	}
	return fmt.Sprintf("Update mailer entry '%s' in mailers section '%s'", mailerName, op.MailersSection)
}
