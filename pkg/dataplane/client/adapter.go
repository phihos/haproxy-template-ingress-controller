package client

import (
	"context"
	"errors"
	"fmt"
	"strconv"
)

// VersionAdapter wraps a DataplaneClient to provide automatic version management
// and 409 conflict retry logic.
//
// When a version conflict occurs (409 response), the adapter automatically:
// 1. Extracts the new version from the response header
// 2. Retries the operation with the new version
// 3. Repeats up to MaxRetries times
//
// This handles the common case of concurrent configuration updates without
// requiring manual retry logic in application code.
type VersionAdapter struct {
	client     *DataplaneClient
	maxRetries int
}

// NewVersionAdapter creates a new VersionAdapter with the specified client and retry limit.
//
// Parameters:
//   - client: The underlying DataplaneClient
//   - maxRetries: Maximum number of retry attempts on 409 conflicts (default: 3)
//
// Example:
//
//	client, _ := client.New(client.Config{...})
//	adapter := client.NewVersionAdapter(client, 3)
//	err := adapter.ExecuteTransaction(ctx, func(ctx context.Context, tx *Transaction) error {
//	    // Execute operations within transaction
//	    return nil
//	})
func NewVersionAdapter(client *DataplaneClient, maxRetries int) *VersionAdapter {
	if maxRetries <= 0 {
		maxRetries = 3 // Default to 3 retries
	}

	return &VersionAdapter{
		client:     client,
		maxRetries: maxRetries,
	}
}

// TransactionFunc is a function that executes operations within a transaction.
// The function receives the transaction and should perform all desired operations.
// If the function returns an error, the transaction will be aborted.
type TransactionFunc func(ctx context.Context, tx *Transaction) error

// ExecuteTransaction executes a transactional operation with automatic 409 retry.
//
// This method:
// 1. Fetches the current configuration version
// 2. Creates a transaction with that version
// 3. Executes the provided function within the transaction
// 4. Commits the transaction if successful
// 5. Aborts the transaction if an error occurs
// 6. Retries on 409 conflicts with the new version
//
// Example:
//
//	adapter := client.NewVersionAdapter(client, 3)
//	err := adapter.ExecuteTransaction(ctx, func(ctx context.Context, tx *Transaction) error {
//	    // Create backend
//	    backend := &models.Backend{Name: "web"}
//	    _, err := client.Client().CreateBackend(ctx, &CreateBackendParams{
//	        TransactionID: &tx.ID,
//	    }, backend)
//	    return err
//	})
func (a *VersionAdapter) ExecuteTransaction(ctx context.Context, fn TransactionFunc) error {
	var lastErr error

	for attempt := 0; attempt <= a.maxRetries; attempt++ {
		// Get current version
		version, err := a.client.GetVersion(ctx)
		if err != nil {
			return fmt.Errorf("failed to get version: %w", err)
		}

		// Create transaction
		tx, err := a.client.CreateTransaction(ctx, version)
		if err != nil {
			var versionErr *VersionConflictError
			if errors.As(err, &versionErr) {
				// Version conflict on transaction creation - retry with new version
				lastErr = err
				continue
			}
			return fmt.Errorf("failed to create transaction: %w", err)
		}

		// Execute operations within transaction
		err = fn(ctx, tx)
		if err != nil {
			// Abort transaction on error
			_ = tx.Abort(ctx) // Ignore abort errors
			return fmt.Errorf("transaction operation failed: %w", err)
		}

		// Commit transaction
		_, err = tx.Commit(ctx)
		if err != nil {
			var versionErr *VersionConflictError
			if errors.As(err, &versionErr) {
				// Version conflict on commit - retry with new version
				lastErr = err
				_ = tx.Abort(ctx) // Ensure cleanup
				continue
			}
			_ = tx.Abort(ctx) // Ensure cleanup
			return fmt.Errorf("failed to commit transaction: %w", err)
		}

		// Success
		return nil
	}

	// Max retries exceeded
	return fmt.Errorf("transaction failed after %d retries: %w", a.maxRetries, lastErr)
}

// ExecuteTransactionWithVersion executes a transactional operation with a specific version.
//
// This is similar to ExecuteTransaction but allows specifying the version explicitly
// instead of fetching it. Useful when you already know the current version.
//
// Parameters:
//   - ctx: Context for the operation
//   - version: The configuration version to use
//   - fn: The function to execute within the transaction
//
// Returns an error if the operation fails or max retries are exceeded.
func (a *VersionAdapter) ExecuteTransactionWithVersion(ctx context.Context, version int64, fn TransactionFunc) error {
	var lastErr error

	for attempt := 0; attempt <= a.maxRetries; attempt++ {
		currentVersion := version

		// If we're retrying, fetch the new version
		if attempt > 0 {
			var err error
			currentVersion, err = a.client.GetVersion(ctx)
			if err != nil {
				return fmt.Errorf("failed to get version on retry: %w", err)
			}
		}

		// Create transaction
		tx, err := a.client.CreateTransaction(ctx, currentVersion)
		if err != nil {
			var versionErr *VersionConflictError
			if errors.As(err, &versionErr) {
				lastErr = err
				continue
			}
			return fmt.Errorf("failed to create transaction: %w", err)
		}

		// Execute operations within transaction
		err = fn(ctx, tx)
		if err != nil {
			_ = tx.Abort(ctx)
			return fmt.Errorf("transaction operation failed: %w", err)
		}

		// Commit transaction
		_, err = tx.Commit(ctx)
		if err != nil {
			var versionErr *VersionConflictError
			if errors.As(err, &versionErr) {
				lastErr = err
				_ = tx.Abort(ctx)
				continue
			}
			_ = tx.Abort(ctx)
			return fmt.Errorf("failed to commit transaction: %w", err)
		}

		return nil
	}

	return fmt.Errorf("transaction failed after %d retries: %w", a.maxRetries, lastErr)
}

// ParseVersionFromHeader extracts the version number from a Configuration-Version header.
func ParseVersionFromHeader(header string) (int64, error) {
	if header == "" {
		return 0, fmt.Errorf("empty version header")
	}

	version, err := strconv.ParseInt(header, 10, 64)
	if err != nil {
		return 0, fmt.Errorf("invalid version header %q: %w", header, err)
	}

	return version, nil
}
