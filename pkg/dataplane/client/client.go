// Package client provides a high-level wrapper around the generated HAProxy Dataplane API client.
//
// This wrapper adds:
// - Basic authentication
// - Version management
// - Transaction lifecycle management
// - Configuration fetch/push operations
// - Error handling and retry logic
package client

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/http"

	"haproxy-template-ic/codegen/dataplaneapi"
)

// Endpoint represents HAProxy Dataplane API connection information.
// This is a convenience type alias to avoid circular imports.
type Endpoint struct {
	URL      string
	Username string
	Password string
	PodName  string // Kubernetes pod name for observability
}

// DataplaneClient wraps the generated API client with additional functionality
// for HAProxy Dataplane API operations.
type DataplaneClient struct {
	client   *dataplaneapi.Client
	Endpoint Endpoint // Embedded endpoint information
}

// Config contains configuration options for creating a DataplaneClient.
type Config struct {
	// BaseURL is the HAProxy Dataplane API endpoint (e.g., "http://localhost:5555/v2")
	BaseURL string

	// Username for basic authentication
	Username string

	// Password for basic authentication
	Password string

	// PodName is the Kubernetes pod name (for observability)
	PodName string

	// HTTPClient allows injecting a custom HTTP client (useful for testing)
	HTTPClient *http.Client
}

// New creates a new DataplaneClient with the provided configuration.
//
// Example:
//
//	client, err := client.New(client.Config{
//	    BaseURL:  "http://haproxy-dataplane:5555/v2",
//	    Username: "admin",
//	    Password: "password",
//	})
func New(cfg Config) (*DataplaneClient, error) {
	if cfg.BaseURL == "" {
		return nil, fmt.Errorf("baseURL is required")
	}
	if cfg.Username == "" {
		return nil, fmt.Errorf("username is required")
	}
	if cfg.Password == "" {
		return nil, fmt.Errorf("password is required")
	}

	// Create request editor for basic auth
	authEditor := func(ctx context.Context, req *http.Request) error {
		auth := cfg.Username + ":" + cfg.Password
		encoded := base64.StdEncoding.EncodeToString([]byte(auth))
		req.Header.Set("Authorization", "Basic "+encoded)
		return nil
	}

	// Configure options for generated client
	opts := []dataplaneapi.ClientOption{
		dataplaneapi.WithRequestEditorFn(authEditor),
	}

	// Add custom HTTP client if provided
	if cfg.HTTPClient != nil {
		opts = append(opts, dataplaneapi.WithHTTPClient(cfg.HTTPClient))
	}

	// Create generated client
	genClient, err := dataplaneapi.NewClient(cfg.BaseURL, opts...)
	if err != nil {
		return nil, fmt.Errorf("failed to create dataplane client: %w", err)
	}

	return &DataplaneClient{
		client: genClient,
		Endpoint: Endpoint{
			URL:      cfg.BaseURL,
			Username: cfg.Username,
			Password: cfg.Password,
			PodName:  cfg.PodName,
		},
	}, nil
}

// Client returns the underlying generated client for direct access to API methods.
// This should be used when the wrapper doesn't provide a convenience method.
func (c *DataplaneClient) Client() *dataplaneapi.Client {
	return c.client
}

// BaseURL returns the configured base URL for the Dataplane API.
func (c *DataplaneClient) BaseURL() string {
	return c.Endpoint.URL
}

// NewFromEndpoint creates a new DataplaneClient from an Endpoint.
// This is a convenience function for creating a client with default options.
func NewFromEndpoint(endpoint Endpoint) (*DataplaneClient, error) {
	return New(Config{
		BaseURL:  endpoint.URL,
		Username: endpoint.Username,
		Password: endpoint.Password,
		PodName:  endpoint.PodName,
	})
}

// StartTransaction creates a new configuration transaction.
// Returns the transaction ID which must be used in subsequent API calls.
func (c *DataplaneClient) StartTransaction(ctx context.Context, version int) (string, error) {
	params := &dataplaneapi.StartTransactionParams{
		Version: version,
	}

	resp, err := c.client.StartTransaction(ctx, params)
	if err != nil {
		return "", fmt.Errorf("failed to start transaction: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return "", fmt.Errorf("start transaction failed with status %d", resp.StatusCode)
	}

	// Parse response body to get transaction ID
	var transaction dataplaneapi.Transaction
	if err := json.NewDecoder(resp.Body).Decode(&transaction); err != nil {
		return "", fmt.Errorf("failed to decode transaction response: %w", err)
	}

	if transaction.Id == nil {
		return "", fmt.Errorf("transaction ID is nil in response")
	}

	return *transaction.Id, nil
}

// CommitTransaction commits a configuration transaction.
// This applies all changes made within the transaction to the HAProxy configuration.
func (c *DataplaneClient) CommitTransaction(ctx context.Context, transactionID string) error {
	params := &dataplaneapi.CommitTransactionParams{}

	resp, err := c.client.CommitTransaction(ctx, transactionID, params)
	if err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("commit transaction failed with status %d", resp.StatusCode)
	}

	return nil
}

// DeleteTransaction deletes a configuration transaction without committing it.
// This is useful for rolling back changes.
func (c *DataplaneClient) DeleteTransaction(ctx context.Context, transactionID string) error {
	resp, err := c.client.DeleteTransaction(ctx, transactionID)
	if err != nil {
		return fmt.Errorf("failed to delete transaction: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("delete transaction failed with status %d", resp.StatusCode)
	}

	return nil
}
