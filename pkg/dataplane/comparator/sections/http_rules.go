// Package sections contains section-specific comparison logic and operations
// for HAProxy configuration elements.
package sections

import (
	"context"
	"fmt"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/pkg/dataplane/client"
	"haproxy-template-ic/pkg/dataplane/transform"
	"haproxy-template-ic/pkg/generated/dataplaneapi"
)

const (
	sectionHTTPRequestRule  = "http_request_rule"
	sectionHTTPResponseRule = "http_response_rule"
)

// CreateHTTPRequestRuleFrontendOperation represents creating a new HTTP request rule in a frontend.
type CreateHTTPRequestRuleFrontendOperation struct {
	FrontendName string
	Rule         *models.HTTPRequestRule
	Index        int
}

// NewCreateHTTPRequestRuleFrontendOperation creates a new HTTP request rule creation operation for a frontend.
func NewCreateHTTPRequestRuleFrontendOperation(frontendName string, rule *models.HTTPRequestRule, index int) *CreateHTTPRequestRuleFrontendOperation {
	return &CreateHTTPRequestRuleFrontendOperation{
		FrontendName: frontendName,
		Rule:         rule,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *CreateHTTPRequestRuleFrontendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateHTTPRequestRuleFrontendOperation) Section() string {
	return sectionHTTPRequestRule
}

// Priority implements Operation.Priority.
func (op *CreateHTTPRequestRuleFrontendOperation) Priority() int {
	return PriorityRule
}

// Execute creates the HTTP request rule via the Dataplane API.
func (op *CreateHTTPRequestRuleFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Rule == nil {
		return fmt.Errorf("HTTP request rule is nil")
	}

	// Convert models.HTTPRequestRule to dataplaneapi.HttpRequestRule using JSON marshaling
	apiRule := transform.ToAPIHTTPRequestRule(op.Rule)
	if apiRule == nil {
		return fmt.Errorf("failed to transform HTTP request rule")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateHTTPRequestRuleFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateHTTPRequestRuleFrontend API
	resp, err := c.Client().CreateHTTPRequestRuleFrontend(ctx, op.FrontendName, op.Index, params, *apiRule)
	if err != nil {
		return fmt.Errorf("failed to create HTTP request rule in frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP request rule creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateHTTPRequestRuleFrontendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Create HTTP request rule (%s) in frontend '%s'", ruleType, op.FrontendName)
}

// DeleteHTTPRequestRuleFrontendOperation represents deleting an HTTP request rule from a frontend.
type DeleteHTTPRequestRuleFrontendOperation struct {
	FrontendName string
	Rule         *models.HTTPRequestRule
	Index        int
}

// NewDeleteHTTPRequestRuleFrontendOperation creates a new HTTP request rule deletion operation for a frontend.
func NewDeleteHTTPRequestRuleFrontendOperation(frontendName string, rule *models.HTTPRequestRule, index int) *DeleteHTTPRequestRuleFrontendOperation {
	return &DeleteHTTPRequestRuleFrontendOperation{
		FrontendName: frontendName,
		Rule:         rule,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *DeleteHTTPRequestRuleFrontendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteHTTPRequestRuleFrontendOperation) Section() string {
	return sectionHTTPRequestRule
}

// Priority implements Operation.Priority.
func (op *DeleteHTTPRequestRuleFrontendOperation) Priority() int {
	return PriorityRule
}

// Execute deletes the HTTP request rule via the Dataplane API.
func (op *DeleteHTTPRequestRuleFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteHTTPRequestRuleFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteHTTPRequestRuleFrontend API
	resp, err := c.Client().DeleteHTTPRequestRuleFrontend(ctx, op.FrontendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete HTTP request rule from frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP request rule deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteHTTPRequestRuleFrontendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Delete HTTP request rule (%s) from frontend '%s'", ruleType, op.FrontendName)
}

// UpdateHTTPRequestRuleFrontendOperation represents updating an HTTP request rule in a frontend.
type UpdateHTTPRequestRuleFrontendOperation struct {
	FrontendName string
	Rule         *models.HTTPRequestRule
	Index        int
}

// NewUpdateHTTPRequestRuleFrontendOperation creates a new HTTP request rule update operation for a frontend.
func NewUpdateHTTPRequestRuleFrontendOperation(frontendName string, rule *models.HTTPRequestRule, index int) *UpdateHTTPRequestRuleFrontendOperation {
	return &UpdateHTTPRequestRuleFrontendOperation{
		FrontendName: frontendName,
		Rule:         rule,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *UpdateHTTPRequestRuleFrontendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateHTTPRequestRuleFrontendOperation) Section() string {
	return sectionHTTPRequestRule
}

// Priority implements Operation.Priority.
func (op *UpdateHTTPRequestRuleFrontendOperation) Priority() int {
	return PriorityRule
}

// Execute updates the HTTP request rule via the Dataplane API.
func (op *UpdateHTTPRequestRuleFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Rule == nil {
		return fmt.Errorf("HTTP request rule is nil")
	}

	// Convert models.HTTPRequestRule to dataplaneapi.HttpRequestRule using JSON marshaling
	apiRule := transform.ToAPIHTTPRequestRule(op.Rule)
	if apiRule == nil {
		return fmt.Errorf("failed to transform HTTP request rule")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceHTTPRequestRuleFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceHTTPRequestRuleFrontend API
	resp, err := c.Client().ReplaceHTTPRequestRuleFrontend(ctx, op.FrontendName, op.Index, params, *apiRule)
	if err != nil {
		return fmt.Errorf("failed to update HTTP request rule in frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP request rule update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateHTTPRequestRuleFrontendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Update HTTP request rule (%s) in frontend '%s'", ruleType, op.FrontendName)
}

// CreateHTTPRequestRuleBackendOperation represents creating a new HTTP request rule in a backend.
type CreateHTTPRequestRuleBackendOperation struct {
	BackendName string
	Rule        *models.HTTPRequestRule
	Index       int
}

// NewCreateHTTPRequestRuleBackendOperation creates a new HTTP request rule creation operation for a backend.
func NewCreateHTTPRequestRuleBackendOperation(backendName string, rule *models.HTTPRequestRule, index int) *CreateHTTPRequestRuleBackendOperation {
	return &CreateHTTPRequestRuleBackendOperation{
		BackendName: backendName,
		Rule:        rule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *CreateHTTPRequestRuleBackendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateHTTPRequestRuleBackendOperation) Section() string {
	return sectionHTTPRequestRule
}

// Priority implements Operation.Priority.
func (op *CreateHTTPRequestRuleBackendOperation) Priority() int {
	return PriorityRule
}

// Execute creates the HTTP request rule via the Dataplane API.
func (op *CreateHTTPRequestRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Rule == nil {
		return fmt.Errorf("HTTP request rule is nil")
	}

	// Convert models.HTTPRequestRule to dataplaneapi.HttpRequestRule using JSON marshaling
	apiRule := transform.ToAPIHTTPRequestRule(op.Rule)
	if apiRule == nil {
		return fmt.Errorf("failed to transform HTTP request rule")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateHTTPRequestRuleBackendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateHTTPRequestRuleBackend API
	resp, err := c.Client().CreateHTTPRequestRuleBackend(ctx, op.BackendName, op.Index, params, *apiRule)
	if err != nil {
		return fmt.Errorf("failed to create HTTP request rule in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP request rule creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateHTTPRequestRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Create HTTP request rule (%s) in backend '%s'", ruleType, op.BackendName)
}

// DeleteHTTPRequestRuleBackendOperation represents deleting an HTTP request rule from a backend.
type DeleteHTTPRequestRuleBackendOperation struct {
	BackendName string
	Rule        *models.HTTPRequestRule
	Index       int
}

// NewDeleteHTTPRequestRuleBackendOperation creates a new HTTP request rule deletion operation for a backend.
func NewDeleteHTTPRequestRuleBackendOperation(backendName string, rule *models.HTTPRequestRule, index int) *DeleteHTTPRequestRuleBackendOperation {
	return &DeleteHTTPRequestRuleBackendOperation{
		BackendName: backendName,
		Rule:        rule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *DeleteHTTPRequestRuleBackendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteHTTPRequestRuleBackendOperation) Section() string {
	return sectionHTTPRequestRule
}

// Priority implements Operation.Priority.
func (op *DeleteHTTPRequestRuleBackendOperation) Priority() int {
	return PriorityRule
}

// Execute deletes the HTTP request rule via the Dataplane API.
func (op *DeleteHTTPRequestRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteHTTPRequestRuleBackendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteHTTPRequestRuleBackend API
	resp, err := c.Client().DeleteHTTPRequestRuleBackend(ctx, op.BackendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete HTTP request rule from backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP request rule deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteHTTPRequestRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Delete HTTP request rule (%s) from backend '%s'", ruleType, op.BackendName)
}

// UpdateHTTPRequestRuleBackendOperation represents updating an HTTP request rule in a backend.
type UpdateHTTPRequestRuleBackendOperation struct {
	BackendName string
	Rule        *models.HTTPRequestRule
	Index       int
}

// NewUpdateHTTPRequestRuleBackendOperation creates a new HTTP request rule update operation for a backend.
func NewUpdateHTTPRequestRuleBackendOperation(backendName string, rule *models.HTTPRequestRule, index int) *UpdateHTTPRequestRuleBackendOperation {
	return &UpdateHTTPRequestRuleBackendOperation{
		BackendName: backendName,
		Rule:        rule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *UpdateHTTPRequestRuleBackendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateHTTPRequestRuleBackendOperation) Section() string {
	return sectionHTTPRequestRule
}

// Priority implements Operation.Priority.
func (op *UpdateHTTPRequestRuleBackendOperation) Priority() int {
	return PriorityRule
}

// Execute updates the HTTP request rule via the Dataplane API.
func (op *UpdateHTTPRequestRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Rule == nil {
		return fmt.Errorf("HTTP request rule is nil")
	}

	// Convert models.HTTPRequestRule to dataplaneapi.HttpRequestRule using JSON marshaling
	apiRule := transform.ToAPIHTTPRequestRule(op.Rule)
	if apiRule == nil {
		return fmt.Errorf("failed to transform HTTP request rule")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceHTTPRequestRuleBackendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceHTTPRequestRuleBackend API
	resp, err := c.Client().ReplaceHTTPRequestRuleBackend(ctx, op.BackendName, op.Index, params, *apiRule)
	if err != nil {
		return fmt.Errorf("failed to update HTTP request rule in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP request rule update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateHTTPRequestRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Update HTTP request rule (%s) in backend '%s'", ruleType, op.BackendName)
}

// CreateHTTPResponseRuleFrontendOperation represents creating a new HTTP response rule in a frontend.
type CreateHTTPResponseRuleFrontendOperation struct {
	FrontendName string
	Rule         *models.HTTPResponseRule
	Index        int
}

// NewCreateHTTPResponseRuleFrontendOperation creates a new HTTP response rule creation operation for a frontend.
func NewCreateHTTPResponseRuleFrontendOperation(frontendName string, rule *models.HTTPResponseRule, index int) *CreateHTTPResponseRuleFrontendOperation {
	return &CreateHTTPResponseRuleFrontendOperation{
		FrontendName: frontendName,
		Rule:         rule,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *CreateHTTPResponseRuleFrontendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateHTTPResponseRuleFrontendOperation) Section() string {
	return sectionHTTPResponseRule
}

// Priority implements Operation.Priority.
func (op *CreateHTTPResponseRuleFrontendOperation) Priority() int {
	return PriorityRule
}

// Execute creates the HTTP response rule via the Dataplane API.
func (op *CreateHTTPResponseRuleFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Rule == nil {
		return fmt.Errorf("HTTP response rule is nil")
	}

	// Convert models.HTTPResponseRule to dataplaneapi.HttpResponseRule using JSON marshaling
	apiRule := transform.ToAPIHTTPResponseRule(op.Rule)
	if apiRule == nil {
		return fmt.Errorf("failed to transform HTTP response rule")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateHTTPResponseRuleFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateHTTPResponseRuleFrontend API
	resp, err := c.Client().CreateHTTPResponseRuleFrontend(ctx, op.FrontendName, op.Index, params, *apiRule)
	if err != nil {
		return fmt.Errorf("failed to create HTTP response rule in frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP response rule creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateHTTPResponseRuleFrontendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Create HTTP response rule (%s) in frontend '%s'", ruleType, op.FrontendName)
}

// DeleteHTTPResponseRuleFrontendOperation represents deleting an HTTP response rule from a frontend.
type DeleteHTTPResponseRuleFrontendOperation struct {
	FrontendName string
	Rule         *models.HTTPResponseRule
	Index        int
}

// NewDeleteHTTPResponseRuleFrontendOperation creates a new HTTP response rule deletion operation for a frontend.
func NewDeleteHTTPResponseRuleFrontendOperation(frontendName string, rule *models.HTTPResponseRule, index int) *DeleteHTTPResponseRuleFrontendOperation {
	return &DeleteHTTPResponseRuleFrontendOperation{
		FrontendName: frontendName,
		Rule:         rule,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *DeleteHTTPResponseRuleFrontendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteHTTPResponseRuleFrontendOperation) Section() string {
	return sectionHTTPResponseRule
}

// Priority implements Operation.Priority.
func (op *DeleteHTTPResponseRuleFrontendOperation) Priority() int {
	return PriorityRule
}

// Execute deletes the HTTP response rule via the Dataplane API.
func (op *DeleteHTTPResponseRuleFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteHTTPResponseRuleFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteHTTPResponseRuleFrontend API
	resp, err := c.Client().DeleteHTTPResponseRuleFrontend(ctx, op.FrontendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete HTTP response rule from frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP response rule deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteHTTPResponseRuleFrontendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Delete HTTP response rule (%s) from frontend '%s'", ruleType, op.FrontendName)
}

// UpdateHTTPResponseRuleFrontendOperation represents updating an HTTP response rule in a frontend.
type UpdateHTTPResponseRuleFrontendOperation struct {
	FrontendName string
	Rule         *models.HTTPResponseRule
	Index        int
}

// NewUpdateHTTPResponseRuleFrontendOperation creates a new HTTP response rule update operation for a frontend.
func NewUpdateHTTPResponseRuleFrontendOperation(frontendName string, rule *models.HTTPResponseRule, index int) *UpdateHTTPResponseRuleFrontendOperation {
	return &UpdateHTTPResponseRuleFrontendOperation{
		FrontendName: frontendName,
		Rule:         rule,
		Index:        index,
	}
}

// Type implements Operation.Type.
func (op *UpdateHTTPResponseRuleFrontendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateHTTPResponseRuleFrontendOperation) Section() string {
	return sectionHTTPResponseRule
}

// Priority implements Operation.Priority.
func (op *UpdateHTTPResponseRuleFrontendOperation) Priority() int {
	return PriorityRule
}

// Execute updates the HTTP response rule via the Dataplane API.
func (op *UpdateHTTPResponseRuleFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Rule == nil {
		return fmt.Errorf("HTTP response rule is nil")
	}

	// Convert models.HTTPResponseRule to dataplaneapi.HttpResponseRule using JSON marshaling
	apiRule := transform.ToAPIHTTPResponseRule(op.Rule)
	if apiRule == nil {
		return fmt.Errorf("failed to transform HTTP response rule")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceHTTPResponseRuleFrontendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceHTTPResponseRuleFrontend API
	resp, err := c.Client().ReplaceHTTPResponseRuleFrontend(ctx, op.FrontendName, op.Index, params, *apiRule)
	if err != nil {
		return fmt.Errorf("failed to update HTTP response rule in frontend '%s': %w", op.FrontendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP response rule update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateHTTPResponseRuleFrontendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Update HTTP response rule (%s) in frontend '%s'", ruleType, op.FrontendName)
}

// CreateHTTPResponseRuleBackendOperation represents creating a new HTTP response rule in a backend.
type CreateHTTPResponseRuleBackendOperation struct {
	BackendName string
	Rule        *models.HTTPResponseRule
	Index       int
}

// NewCreateHTTPResponseRuleBackendOperation creates a new HTTP response rule creation operation for a backend.
func NewCreateHTTPResponseRuleBackendOperation(backendName string, rule *models.HTTPResponseRule, index int) *CreateHTTPResponseRuleBackendOperation {
	return &CreateHTTPResponseRuleBackendOperation{
		BackendName: backendName,
		Rule:        rule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *CreateHTTPResponseRuleBackendOperation) Type() OperationType {
	return OperationCreate
}

// Section implements Operation.Section.
func (op *CreateHTTPResponseRuleBackendOperation) Section() string {
	return sectionHTTPResponseRule
}

// Priority implements Operation.Priority.
func (op *CreateHTTPResponseRuleBackendOperation) Priority() int {
	return PriorityRule
}

// Execute creates the HTTP response rule via the Dataplane API.
func (op *CreateHTTPResponseRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Rule == nil {
		return fmt.Errorf("HTTP response rule is nil")
	}

	// Convert models.HTTPResponseRule to dataplaneapi.HttpResponseRule using JSON marshaling
	apiRule := transform.ToAPIHTTPResponseRule(op.Rule)
	if apiRule == nil {
		return fmt.Errorf("failed to transform HTTP response rule")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.CreateHTTPResponseRuleBackendParams{
		TransactionId: &transactionID,
	}

	// Call the CreateHTTPResponseRuleBackend API
	resp, err := c.Client().CreateHTTPResponseRuleBackend(ctx, op.BackendName, op.Index, params, *apiRule)
	if err != nil {
		return fmt.Errorf("failed to create HTTP response rule in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP response rule creation failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *CreateHTTPResponseRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Create HTTP response rule (%s) in backend '%s'", ruleType, op.BackendName)
}

// DeleteHTTPResponseRuleBackendOperation represents deleting an HTTP response rule from a backend.
type DeleteHTTPResponseRuleBackendOperation struct {
	BackendName string
	Rule        *models.HTTPResponseRule
	Index       int
}

// NewDeleteHTTPResponseRuleBackendOperation creates a new HTTP response rule deletion operation for a backend.
func NewDeleteHTTPResponseRuleBackendOperation(backendName string, rule *models.HTTPResponseRule, index int) *DeleteHTTPResponseRuleBackendOperation {
	return &DeleteHTTPResponseRuleBackendOperation{
		BackendName: backendName,
		Rule:        rule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *DeleteHTTPResponseRuleBackendOperation) Type() OperationType {
	return OperationDelete
}

// Section implements Operation.Section.
func (op *DeleteHTTPResponseRuleBackendOperation) Section() string {
	return sectionHTTPResponseRule
}

// Priority implements Operation.Priority.
func (op *DeleteHTTPResponseRuleBackendOperation) Priority() int {
	return PriorityRule
}

// Execute deletes the HTTP response rule via the Dataplane API.
func (op *DeleteHTTPResponseRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	// Prepare parameters with transaction ID
	params := &dataplaneapi.DeleteHTTPResponseRuleBackendParams{
		TransactionId: &transactionID,
	}

	// Call the DeleteHTTPResponseRuleBackend API
	resp, err := c.Client().DeleteHTTPResponseRuleBackend(ctx, op.BackendName, op.Index, params)
	if err != nil {
		return fmt.Errorf("failed to delete HTTP response rule from backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP response rule deletion failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *DeleteHTTPResponseRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Delete HTTP response rule (%s) from backend '%s'", ruleType, op.BackendName)
}

// UpdateHTTPResponseRuleBackendOperation represents updating an HTTP response rule in a backend.
type UpdateHTTPResponseRuleBackendOperation struct {
	BackendName string
	Rule        *models.HTTPResponseRule
	Index       int
}

// NewUpdateHTTPResponseRuleBackendOperation creates a new HTTP response rule update operation for a backend.
func NewUpdateHTTPResponseRuleBackendOperation(backendName string, rule *models.HTTPResponseRule, index int) *UpdateHTTPResponseRuleBackendOperation {
	return &UpdateHTTPResponseRuleBackendOperation{
		BackendName: backendName,
		Rule:        rule,
		Index:       index,
	}
}

// Type implements Operation.Type.
func (op *UpdateHTTPResponseRuleBackendOperation) Type() OperationType {
	return OperationUpdate
}

// Section implements Operation.Section.
func (op *UpdateHTTPResponseRuleBackendOperation) Section() string {
	return sectionHTTPResponseRule
}

// Priority implements Operation.Priority.
func (op *UpdateHTTPResponseRuleBackendOperation) Priority() int {
	return PriorityRule
}

// Execute updates the HTTP response rule via the Dataplane API.
func (op *UpdateHTTPResponseRuleBackendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	if op.Rule == nil {
		return fmt.Errorf("HTTP response rule is nil")
	}

	// Convert models.HTTPResponseRule to dataplaneapi.HttpResponseRule using JSON marshaling
	apiRule := transform.ToAPIHTTPResponseRule(op.Rule)
	if apiRule == nil {
		return fmt.Errorf("failed to transform HTTP response rule")
	}

	// Prepare parameters with transaction ID
	params := &dataplaneapi.ReplaceHTTPResponseRuleBackendParams{
		TransactionId: &transactionID,
	}

	// Call the ReplaceHTTPResponseRuleBackend API
	resp, err := c.Client().ReplaceHTTPResponseRuleBackend(ctx, op.BackendName, op.Index, params, *apiRule)
	if err != nil {
		return fmt.Errorf("failed to update HTTP response rule in backend '%s': %w", op.BackendName, err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP response rule update failed with status %d", resp.StatusCode)
	}

	return nil
}

// Describe returns a human-readable description of this operation.
func (op *UpdateHTTPResponseRuleBackendOperation) Describe() string {
	ruleType := unknownFallback
	if op.Rule != nil && op.Rule.Type != "" {
		ruleType = op.Rule.Type
	}
	return fmt.Sprintf("Update HTTP response rule (%s) in backend '%s'", ruleType, op.BackendName)
}
