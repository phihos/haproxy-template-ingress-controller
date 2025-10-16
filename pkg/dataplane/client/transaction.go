package client

import (
	"context"
	"encoding/json"
	"fmt"
	"io"

	"haproxy-template-ic/codegen/dataplaneapi"
)

// Transaction represents an HAProxy Dataplane API transaction.
//
// Transactions provide atomic configuration changes - all operations within
// a transaction are applied together or none are applied. This prevents
// partial configuration updates that could leave HAProxy in an inconsistent state.
//
// Transaction lifecycle:
//  1. Create transaction with current version
//  2. Execute operations within transaction (passing transaction ID)
//  3. Commit transaction to apply all changes
//  4. OR Abort transaction to discard all changes
type Transaction struct {
	ID      string
	Version int64
	client  *DataplaneClient
}

// TransactionResponse represents the response when creating a transaction.
type TransactionResponse struct {
	ID      string `json:"id"`
	Version int    `json:"version"`
}

// CreateTransaction creates a new transaction with the specified configuration version.
//
// The version parameter enables optimistic locking - if another process has
// modified the configuration since you fetched the version, transaction creation
// will fail with a 409 Conflict error.
//
// Example:
//
//	version, _ := client.GetVersion(context.Background())
//	tx, err := client.CreateTransaction(context.Background(), version)
//	if err != nil {
//	    log.Fatal(err)
//	}
//	defer tx.Abort(context.Background()) // Ensure cleanup on error
//
//	// Execute operations with tx.ID
//	// ...
//
//	err = tx.Commit(context.Background())
func (c *DataplaneClient) CreateTransaction(ctx context.Context, version int64) (*Transaction, error) {
	params := &dataplaneapi.StartTransactionParams{
		Version: int(version),
	}

	resp, err := c.client.StartTransaction(ctx, params)
	if err != nil {
		return nil, fmt.Errorf("failed to start transaction: %w", err)
	}
	defer resp.Body.Close()

	// Check for version conflicts (both 409 and 406 indicate version conflicts)
	if resp.StatusCode == 409 || resp.StatusCode == 406 {
		// Version conflict - extract new version from header if available
		// 409 = Conflict (typical version mismatch)
		// 406 = Not Acceptable (transaction is outdated)
		newVersion := resp.Header.Get("Configuration-Version")
		if newVersion != "" {
			return nil, &VersionConflictError{
				ExpectedVersion: version,
				ActualVersion:   newVersion,
			}
		}
		// If no version header, still return VersionConflictError for retry logic
		return nil, &VersionConflictError{
			ExpectedVersion: version,
			ActualVersion:   "unknown",
		}
	}

	if resp.StatusCode != 201 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("failed to start transaction: status %d: %s", resp.StatusCode, string(body))
	}

	// Parse transaction response
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read transaction response: %w", err)
	}

	var txResp TransactionResponse
	if err := json.Unmarshal(body, &txResp); err != nil {
		return nil, fmt.Errorf("failed to parse transaction response: %w", err)
	}

	return &Transaction{
		ID:      txResp.ID,
		Version: version,
		client:  c,
	}, nil
}

// CommitResult contains information about a transaction commit operation.
type CommitResult struct {
	// StatusCode is the HTTP status code from the commit response.
	// 200 = configuration applied without reload
	// 202 = configuration applied with reload triggered
	StatusCode int

	// ReloadID is the reload identifier from the Reload-ID response header.
	// Only set when StatusCode is 202 (reload triggered).
	ReloadID string
}

// Commit commits all changes made within this transaction.
//
// After successful commit, all operations executed with this transaction ID
// are applied atomically to the HAProxy configuration. If commit fails,
// no changes are applied.
//
// The transaction is invalidated after commit (whether successful or not)
// and should not be reused.
//
// Returns CommitResult containing status code and reload ID (if reload triggered).
func (tx *Transaction) Commit(ctx context.Context) (*CommitResult, error) {
	forceReload := false
	params := &dataplaneapi.CommitTransactionParams{
		ForceReload: &forceReload,
	}

	resp, err := tx.client.client.CommitTransaction(ctx, tx.ID, params)
	if err != nil {
		return nil, fmt.Errorf("failed to commit transaction: %w", err)
	}
	defer resp.Body.Close()

	// Check for version conflicts (both 409 and 406 indicate version conflicts)
	if resp.StatusCode == 409 || resp.StatusCode == 406 {
		// Version conflict during commit
		// 409 = Conflict (typical version mismatch)
		// 406 = Not Acceptable (transaction is outdated)
		newVersion := resp.Header.Get("Configuration-Version")
		if newVersion != "" {
			return nil, &VersionConflictError{
				ExpectedVersion: tx.Version,
				ActualVersion:   newVersion,
			}
		}
		// If no version header, still return VersionConflictError for retry logic
		return nil, &VersionConflictError{
			ExpectedVersion: tx.Version,
			ActualVersion:   "unknown",
		}
	}

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("failed to commit transaction: status %d: %s", resp.StatusCode, string(body))
	}

	// Extract reload information
	result := &CommitResult{
		StatusCode: resp.StatusCode,
	}

	// Status 202 indicates reload was triggered
	if resp.StatusCode == 202 {
		result.ReloadID = resp.Header.Get("Reload-ID")
	}

	return result, nil
}

// Abort aborts and discards all changes made within this transaction.
//
// All operations executed with this transaction ID are discarded and the
// HAProxy configuration remains unchanged. This is useful for cleanup
// when an error occurs during transaction execution.
//
// It's safe to call Abort multiple times or after Commit - subsequent
// calls will return an error but not cause problems.
func (tx *Transaction) Abort(ctx context.Context) error {
	resp, err := tx.client.client.DeleteTransaction(ctx, tx.ID)
	if err != nil {
		return fmt.Errorf("failed to abort transaction: %w", err)
	}
	defer resp.Body.Close()

	// 404 means transaction already gone (committed or aborted) - that's ok
	if resp.StatusCode == 404 {
		return nil
	}

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("failed to abort transaction: status %d: %s", resp.StatusCode, string(body))
	}

	return nil
}
