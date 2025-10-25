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

const (
	sectionTCPRequestRule  = "tcp-request-rule"
	sectionTCPResponseRule = "tcp-response-rule"
)

// CreateTCPRequestRuleFrontendOperation represents creating a new TCP request rule in a frontend.
type CreateTCPRequestRuleFrontendOperation struct {
	FrontendName string
	Rule         *models.TCPRequestRule
	Index        int
}

// NewCreateTCPRequestRuleFrontendOperation creates a new TCP request rule creation operation for a frontend.
func NewCreateTCPRequestRuleFrontendOperation(frontendName string, rule *models.TCPRequestRule, index int) *CreateTCPRequestRuleFrontendOperation {
	return &CreateTCPRequestRuleFrontendOperation{
		FrontendName: frontendName,
		Rule:         rule,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *CreateTCPRequestRuleFrontendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateTCPRequestRuleFrontendOperation) Section() string {
	return sectionTCPRequestRule
}

// Priority implements Operation.Priority.
func (op *CreateTCPRequestRuleFrontendOperation) Priority() int {
	return PriorityRule
}

// Execute creates the TCP request rule via the Dataplane API.
func (op *CreateTCPRequestRuleFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Rule == nil {
		return fmt.Errorf("TCP request rule is nil")
	}

	// Convert models.TCPRequestRule to dataplaneapi.TcpRequestRule using JSON marshaling
	apiRule := transform.ToAPITCPRequestRule(op.Rule)
	if apiRule == nil {
		return fmt.Errorf("failed to transform TCP request rule")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateTCPRequestRuleFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateTCPRequestRuleFrontend API
	resp, err := c.Client().CreateTCPRequestRuleFrontend(ctx, op.FrontendName, op.Index, params, *apiRule)
	if err != nil {
		return fmt.Errorf("failed to create TCP request rule in frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("TCP request rule creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateTCPRequestRuleFrontendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Create TCP request rule (%s) in frontend '%s'", ruleType, op.FrontendName)
}

// DeleteTCPRequestRuleFrontendOperation represents deleting a TCP request rule from a frontend.
type DeleteTCPRequestRuleFrontendOperation struct {
	FrontendName string
	Rule         *models.TCPRequestRule
	Index        int
}

// NewDeleteTCPRequestRuleFrontendOperation creates a new TCP request rule deletion operation for a frontend.
func NewDeleteTCPRequestRuleFrontendOperation(frontendName string, rule *models.TCPRequestRule, index int) *DeleteTCPRequestRuleFrontendOperation {
	return &DeleteTCPRequestRuleFrontendOperation{
		FrontendName: frontendName,
		Rule:         rule,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *DeleteTCPRequestRuleFrontendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteTCPRequestRuleFrontendOperation) Section() string {
	return sectionTCPRequestRule
}

// Priority implements Operation.Priority.
func (op *DeleteTCPRequestRuleFrontendOperation) Priority() int {
	return PriorityRule
}

// Execute deletes the TCP request rule via the Dataplane API.
func (op *DeleteTCPRequestRuleFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteTCPRequestRuleFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteTCPRequestRuleFrontend API
	resp, err := c.Client().DeleteTCPRequestRuleFrontend(ctx, op.FrontendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete TCP request rule from frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("TCP request rule deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteTCPRequestRuleFrontendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Delete TCP request rule (%s) from frontend '%s'", ruleType, op.FrontendName)
}

// UpdateTCPRequestRuleFrontendOperation represents updating a TCP request rule in a frontend.
type UpdateTCPRequestRuleFrontendOperation struct {
	FrontendName string
	Rule         *models.TCPRequestRule
	Index        int
}

// NewUpdateTCPRequestRuleFrontendOperation creates a new TCP request rule update operation for a frontend.
func NewUpdateTCPRequestRuleFrontendOperation(frontendName string, rule *models.TCPRequestRule, index int) *UpdateTCPRequestRuleFrontendOperation {
	return &UpdateTCPRequestRuleFrontendOperation{
		FrontendName: frontendName,
		Rule:         rule,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *UpdateTCPRequestRuleFrontendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateTCPRequestRuleFrontendOperation) Section() string {
	return sectionTCPRequestRule
}

// Priority implements Operation.Priority.
func (op *UpdateTCPRequestRuleFrontendOperation) Priority() int {
	return PriorityRule
}

// Execute updates the TCP request rule via the Dataplane API.
func (op *UpdateTCPRequestRuleFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Rule == nil {
		return fmt.Errorf("TCP request rule is nil")
	}

	// Convert models.TCPRequestRule to dataplaneapi.TcpRequestRule using JSON marshaling
	apiRule := transform.ToAPITCPRequestRule(op.Rule)
	if apiRule == nil {
		return fmt.Errorf("failed to transform TCP request rule")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceTCPRequestRuleFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceTCPRequestRuleFrontend API
	resp, err := c.Client().ReplaceTCPRequestRuleFrontend(ctx, op.FrontendName, op.Index, params, *apiRule)
	if err != nil {
		return fmt.Errorf("failed to update TCP request rule in frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("TCP request rule update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateTCPRequestRuleFrontendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Update TCP request rule (%s) in frontend '%s'", ruleType, op.FrontendName)
}

// CreateTCPRequestRuleBackendOperation represents creating a new TCP request rule in a backend.
type CreateTCPRequestRuleBackendOperation struct {
	BackendName string
	Rule        *models.TCPRequestRule
	Index       int
}

// NewCreateTCPRequestRuleBackendOperation creates a new TCP request rule creation operation for a backend.
func NewCreateTCPRequestRuleBackendOperation(backendName string, rule *models.TCPRequestRule, index int) *CreateTCPRequestRuleBackendOperation {
	return &CreateTCPRequestRuleBackendOperation{
		BackendName: backendName,
		Rule:        rule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *CreateTCPRequestRuleBackendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateTCPRequestRuleBackendOperation) Section() string {
	return sectionTCPRequestRule
}

// Priority implements Operation.Priority.
func (op *CreateTCPRequestRuleBackendOperation) Priority() int {
	return PriorityRule
}

// Execute creates the TCP request rule via the Dataplane API.
func (op *CreateTCPRequestRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Rule == nil {
		return fmt.Errorf("TCP request rule is nil")
	}

	// Convert models.TCPRequestRule to dataplaneapi.TcpRequestRule using JSON marshaling
	apiRule := transform.ToAPITCPRequestRule(op.Rule)
	if apiRule == nil {
		return fmt.Errorf("failed to transform TCP request rule")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateTCPRequestRuleBackendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateTCPRequestRuleBackend API
	resp, err := c.Client().CreateTCPRequestRuleBackend(ctx, op.BackendName, op.Index, params, *apiRule)
	if err != nil {
		return fmt.Errorf("failed to create TCP request rule in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("TCP request rule creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateTCPRequestRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Create TCP request rule (%s) in backend '%s'", ruleType, op.BackendName)
}

// DeleteTCPRequestRuleBackendOperation represents deleting a TCP request rule from a backend.
type DeleteTCPRequestRuleBackendOperation struct {
	BackendName string
	Rule        *models.TCPRequestRule
	Index       int
}

// NewDeleteTCPRequestRuleBackendOperation creates a new TCP request rule deletion operation for a backend.
func NewDeleteTCPRequestRuleBackendOperation(backendName string, rule *models.TCPRequestRule, index int) *DeleteTCPRequestRuleBackendOperation {
	return &DeleteTCPRequestRuleBackendOperation{
		BackendName: backendName,
		Rule:        rule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *DeleteTCPRequestRuleBackendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteTCPRequestRuleBackendOperation) Section() string {
	return sectionTCPRequestRule
}

// Priority implements Operation.Priority.
func (op *DeleteTCPRequestRuleBackendOperation) Priority() int {
	return PriorityRule
}

// Execute deletes the TCP request rule via the Dataplane API.
func (op *DeleteTCPRequestRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteTCPRequestRuleBackendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteTCPRequestRuleBackend API
	resp, err := c.Client().DeleteTCPRequestRuleBackend(ctx, op.BackendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete TCP request rule from backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("TCP request rule deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteTCPRequestRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Delete TCP request rule (%s) from backend '%s'", ruleType, op.BackendName)
}

// UpdateTCPRequestRuleBackendOperation represents updating a TCP request rule in a backend.
type UpdateTCPRequestRuleBackendOperation struct {
	BackendName string
	Rule        *models.TCPRequestRule
	Index       int
}

// NewUpdateTCPRequestRuleBackendOperation creates a new TCP request rule update operation for a backend.
func NewUpdateTCPRequestRuleBackendOperation(backendName string, rule *models.TCPRequestRule, index int) *UpdateTCPRequestRuleBackendOperation {
	return &UpdateTCPRequestRuleBackendOperation{
		BackendName: backendName,
		Rule:        rule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *UpdateTCPRequestRuleBackendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateTCPRequestRuleBackendOperation) Section() string {
	return sectionTCPRequestRule
}

// Priority implements Operation.Priority.
func (op *UpdateTCPRequestRuleBackendOperation) Priority() int {
	return PriorityRule
}

// Execute updates the TCP request rule via the Dataplane API.
func (op *UpdateTCPRequestRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Rule == nil {
		return fmt.Errorf("TCP request rule is nil")
	}

	// Convert models.TCPRequestRule to dataplaneapi.TcpRequestRule using JSON marshaling
	apiRule := transform.ToAPITCPRequestRule(op.Rule)
	if apiRule == nil {
		return fmt.Errorf("failed to transform TCP request rule")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceTCPRequestRuleBackendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceTCPRequestRuleBackend API
	resp, err := c.Client().ReplaceTCPRequestRuleBackend(ctx, op.BackendName, op.Index, params, *apiRule)
	if err != nil {
		return fmt.Errorf("failed to update TCP request rule in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("TCP request rule update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateTCPRequestRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Update TCP request rule (%s) in backend '%s'", ruleType, op.BackendName)
}

// CreateTCPResponseRuleBackendOperation represents creating a new TCP response rule in a backend.
type CreateTCPResponseRuleBackendOperation struct {
	BackendName string
	Rule        *models.TCPResponseRule
	Index       int
}

// NewCreateTCPResponseRuleBackendOperation creates a new TCP response rule creation operation for a backend.
func NewCreateTCPResponseRuleBackendOperation(backendName string, rule *models.TCPResponseRule, index int) *CreateTCPResponseRuleBackendOperation {
	return &CreateTCPResponseRuleBackendOperation{
		BackendName: backendName,
		Rule:        rule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *CreateTCPResponseRuleBackendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateTCPResponseRuleBackendOperation) Section() string {
	return sectionTCPResponseRule
}

// Priority implements Operation.Priority.
func (op *CreateTCPResponseRuleBackendOperation) Priority() int {
	return PriorityRule
}

// Execute creates the TCP response rule via the Dataplane API.
func (op *CreateTCPResponseRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Rule == nil {
		return fmt.Errorf("TCP response rule is nil")
	}

	// Convert models.TCPResponseRule to dataplaneapi.TcpResponseRule using JSON marshaling
	apiRule := transform.ToAPITCPResponseRule(op.Rule)
	if apiRule == nil {
		return fmt.Errorf("failed to transform TCP response rule")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateTCPResponseRuleBackendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateTCPResponseRuleBackend API
	resp, err := c.Client().CreateTCPResponseRuleBackend(ctx, op.BackendName, op.Index, params, *apiRule)
	if err != nil {
		return fmt.Errorf("failed to create TCP response rule in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("TCP response rule creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateTCPResponseRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Create TCP response rule (%s) in backend '%s'", ruleType, op.BackendName)
}

// DeleteTCPResponseRuleBackendOperation represents deleting a TCP response rule from a backend.
type DeleteTCPResponseRuleBackendOperation struct {
	BackendName string
	Rule        *models.TCPResponseRule
	Index       int
}

// NewDeleteTCPResponseRuleBackendOperation creates a new TCP response rule deletion operation for a backend.
func NewDeleteTCPResponseRuleBackendOperation(backendName string, rule *models.TCPResponseRule, index int) *DeleteTCPResponseRuleBackendOperation {
	return &DeleteTCPResponseRuleBackendOperation{
		BackendName: backendName,
		Rule:        rule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *DeleteTCPResponseRuleBackendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteTCPResponseRuleBackendOperation) Section() string {
	return sectionTCPResponseRule
}

// Priority implements Operation.Priority.
func (op *DeleteTCPResponseRuleBackendOperation) Priority() int {
	return PriorityRule
}

// Execute deletes the TCP response rule via the Dataplane API.
func (op *DeleteTCPResponseRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteTCPResponseRuleBackendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteTCPResponseRuleBackend API
	resp, err := c.Client().DeleteTCPResponseRuleBackend(ctx, op.BackendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete TCP response rule from backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("TCP response rule deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteTCPResponseRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Delete TCP response rule (%s) from backend '%s'", ruleType, op.BackendName)
}

// UpdateTCPResponseRuleBackendOperation represents updating a TCP response rule in a backend.
type UpdateTCPResponseRuleBackendOperation struct {
	BackendName string
	Rule        *models.TCPResponseRule
	Index       int
}

// NewUpdateTCPResponseRuleBackendOperation creates a new TCP response rule update operation for a backend.
func NewUpdateTCPResponseRuleBackendOperation(backendName string, rule *models.TCPResponseRule, index int) *UpdateTCPResponseRuleBackendOperation {
	return &UpdateTCPResponseRuleBackendOperation{
		BackendName: backendName,
		Rule:        rule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *UpdateTCPResponseRuleBackendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateTCPResponseRuleBackendOperation) Section() string {
	return sectionTCPResponseRule
}

// Priority implements Operation.Priority.
func (op *UpdateTCPResponseRuleBackendOperation) Priority() int {
	return PriorityRule
}

// Execute updates the TCP response rule via the Dataplane API.
func (op *UpdateTCPResponseRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Rule == nil {
		return fmt.Errorf("TCP response rule is nil")
	}

	// Convert models.TCPResponseRule to dataplaneapi.TcpResponseRule using JSON marshaling
	apiRule := transform.ToAPITCPResponseRule(op.Rule)
	if apiRule == nil {
		return fmt.Errorf("failed to transform TCP response rule")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceTCPResponseRuleBackendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceTCPResponseRuleBackend API
	resp, err := c.Client().ReplaceTCPResponseRuleBackend(ctx, op.BackendName, op.Index, params, *apiRule)
	if err != nil {
		return fmt.Errorf("failed to update TCP response rule in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("TCP response rule update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateTCPResponseRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Update TCP response rule (%s) in backend '%s'", ruleType, op.BackendName)
}
