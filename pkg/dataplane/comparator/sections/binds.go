package sections

import (
	"context"
	"encoding/json"
	"fmt"

	"haproxy-template-ic/codegen/dataplaneapi"
	"haproxy-template-ic/pkg/dataplane/client"
)

// ==================== CREATE BIND OPERATIONS ====================

// CreateBindFrontendOperation creates a bind in a frontend.
type CreateBindFrontendOperation struct {
	FrontendName string
	Bind         *dataplaneapi.Bind
	BindName     string
}

func NewCreateBindFrontendOperation(frontendName string, bindName string, bind *dataplaneapi.Bind) *CreateBindFrontendOperation {
	return &CreateBindFrontendOperation{
		FrontendName: frontendName,
		BindName:     bindName,
		Bind:         bind,
	}
}

func (op *CreateBindFrontendOperation) Type() OperationType {
	return OperationCreate
}

func (op *CreateBindFrontendOperation) Section() string {
	return "bind"
}

func (op *CreateBindFrontendOperation) Priority() int {
	return PriorityBind
}

func (op *CreateBindFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	apiClient := c.Client()

	params := &dataplaneapi.CreateBindFrontendParams{
		TransactionId: &transactionID,
	}

	resp, err := apiClient.CreateBindFrontend(ctx, op.FrontendName, params, *op.Bind)
	if err != nil {
		return fmt.Errorf("failed to create bind '%s' in frontend '%s': %w", op.BindName, op.FrontendName, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("create bind failed with status %d", resp.StatusCode)
	}

	return nil
}

func (op *CreateBindFrontendOperation) Describe() string {
	// Format bind description based on address and port
	bindDesc := ""
	if op.Bind.Address != nil && op.Bind.Port != nil {
		bindDesc = fmt.Sprintf("%s:%d", *op.Bind.Address, *op.Bind.Port)
	} else if op.Bind.Port != nil {
		bindDesc = fmt.Sprintf("*:%d", *op.Bind.Port)
	} else {
		bindDesc = op.BindName
	}

	// Add SSL info if present
	if op.Bind.Ssl != nil && *op.Bind.Ssl {
		sslInfo := " ssl"
		if op.Bind.SslCertificate != nil {
			sslInfo += fmt.Sprintf(" crt %s", *op.Bind.SslCertificate)
		}
		bindDesc += sslInfo
	}

	return fmt.Sprintf("Create bind '%s' in frontend '%s'", bindDesc, op.FrontendName)
}

// ==================== DELETE BIND OPERATIONS ====================

// DeleteBindFrontendOperation deletes a bind from a frontend.
type DeleteBindFrontendOperation struct {
	FrontendName string
	BindName     string
	Bind         *dataplaneapi.Bind // Kept for description purposes
}

func NewDeleteBindFrontendOperation(frontendName string, bindName string, bind *dataplaneapi.Bind) *DeleteBindFrontendOperation {
	return &DeleteBindFrontendOperation{
		FrontendName: frontendName,
		BindName:     bindName,
		Bind:         bind,
	}
}

func (op *DeleteBindFrontendOperation) Type() OperationType {
	return OperationDelete
}

func (op *DeleteBindFrontendOperation) Section() string {
	return "bind"
}

func (op *DeleteBindFrontendOperation) Priority() int {
	return PriorityBind
}

func (op *DeleteBindFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	apiClient := c.Client()

	params := &dataplaneapi.DeleteBindFrontendParams{
		TransactionId: &transactionID,
	}

	resp, err := apiClient.DeleteBindFrontend(ctx, op.FrontendName, op.BindName, params)
	if err != nil {
		return fmt.Errorf("failed to delete bind '%s' from frontend '%s': %w", op.BindName, op.FrontendName, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("delete bind failed with status %d", resp.StatusCode)
	}

	return nil
}

func (op *DeleteBindFrontendOperation) Describe() string {
	// Format bind description based on address and port
	bindDesc := ""
	if op.Bind != nil {
		if op.Bind.Address != nil && op.Bind.Port != nil {
			bindDesc = fmt.Sprintf("%s:%d", *op.Bind.Address, *op.Bind.Port)
		} else if op.Bind.Port != nil {
			bindDesc = fmt.Sprintf("*:%d", *op.Bind.Port)
		} else {
			bindDesc = op.BindName
		}

		// Add SSL info if present
		if op.Bind.Ssl != nil && *op.Bind.Ssl {
			sslInfo := " ssl"
			if op.Bind.SslCertificate != nil {
				sslInfo += fmt.Sprintf(" crt %s", *op.Bind.SslCertificate)
			}
			bindDesc += sslInfo
		}
	} else {
		bindDesc = op.BindName
	}

	return fmt.Sprintf("Delete bind '%s' from frontend '%s'", bindDesc, op.FrontendName)
}

// ==================== UPDATE BIND OPERATIONS ====================

// UpdateBindFrontendOperation updates a bind in a frontend.
type UpdateBindFrontendOperation struct {
	FrontendName string
	BindName     string
	Bind         *dataplaneapi.Bind
}

func NewUpdateBindFrontendOperation(frontendName string, bindName string, bind *dataplaneapi.Bind) *UpdateBindFrontendOperation {
	return &UpdateBindFrontendOperation{
		FrontendName: frontendName,
		BindName:     bindName,
		Bind:         bind,
	}
}

func (op *UpdateBindFrontendOperation) Type() OperationType {
	return OperationUpdate
}

func (op *UpdateBindFrontendOperation) Section() string {
	return "bind"
}

func (op *UpdateBindFrontendOperation) Priority() int {
	return PriorityBind
}

func (op *UpdateBindFrontendOperation) Execute(ctx context.Context, c *client.DataplaneClient, transactionID string) error {
	apiClient := c.Client()

	params := &dataplaneapi.ReplaceBindFrontendParams{
		TransactionId: &transactionID,
	}

	resp, err := apiClient.ReplaceBindFrontend(ctx, op.FrontendName, op.BindName, params, *op.Bind)
	if err != nil {
		return fmt.Errorf("failed to update bind '%s' in frontend '%s': %w", op.BindName, op.FrontendName, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("update bind failed with status %d", resp.StatusCode)
	}

	return nil
}

func (op *UpdateBindFrontendOperation) Describe() string {
	// Format bind description based on address and port
	bindDesc := ""
	if op.Bind.Address != nil && op.Bind.Port != nil {
		bindDesc = fmt.Sprintf("%s:%d", *op.Bind.Address, *op.Bind.Port)
	} else if op.Bind.Port != nil {
		bindDesc = fmt.Sprintf("*:%d", *op.Bind.Port)
	} else {
		bindDesc = op.BindName
	}

	// Add SSL info if present
	if op.Bind.Ssl != nil && *op.Bind.Ssl {
		sslInfo := " ssl"
		if op.Bind.SslCertificate != nil {
			sslInfo += fmt.Sprintf(" crt %s", *op.Bind.SslCertificate)
		}
		bindDesc += sslInfo
	}

	return fmt.Sprintf("Update bind '%s' in frontend '%s'", bindDesc, op.FrontendName)
}

// ==================== HELPER FUNCTIONS ====================

// bindToString creates a human-readable string representation of a bind configuration.
func bindToString(bind *dataplaneapi.Bind) string {
	if bind == nil {
		return "unknown"
	}

	bindDesc := ""
	if bind.Address != nil && bind.Port != nil {
		bindDesc = fmt.Sprintf("%s:%d", *bind.Address, *bind.Port)
	} else if bind.Port != nil {
		bindDesc = fmt.Sprintf("*:%d", *bind.Port)
	} else if bind.Name != nil {
		bindDesc = *bind.Name
	} else {
		return "unknown"
	}

	// Add SSL info if present
	if bind.Ssl != nil && *bind.Ssl {
		sslInfo := " ssl"
		if bind.SslCertificate != nil {
			sslInfo += fmt.Sprintf(" crt %s", *bind.SslCertificate)
		}
		bindDesc += sslInfo
	}

	return bindDesc
}

// convertToAPIBind converts a models.Bind to dataplaneapi.Bind using JSON marshaling.
func convertToAPIBind(modelBind interface{}) (*dataplaneapi.Bind, error) {
	data, err := json.Marshal(modelBind)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal bind: %w", err)
	}

	var apiBind dataplaneapi.Bind
	if err := json.Unmarshal(data, &apiBind); err != nil {
		return nil, fmt.Errorf("failed to unmarshal bind: %w", err)
	}

	return &apiBind, nil
}
