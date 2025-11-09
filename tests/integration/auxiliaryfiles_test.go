//go:build integration

package integration

import (
	"context"
	"os"
	"path/filepath"
	"testing"

	"github.com/rekby/fixenv"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"haproxy-template-ic/pkg/dataplane/auxiliaryfiles"
)

// TestGeneralFiles tests Create, Update, and Delete operations for general files
func TestGeneralFiles(t *testing.T) {
	testCases := []struct {
		name      string
		setup     func(t *testing.T, ctx context.Context, env fixenv.Env) // Setup initial state
		operation func(t *testing.T, ctx context.Context, env fixenv.Env) // Perform operation
		verify    func(t *testing.T, ctx context.Context, env fixenv.Env) // Verify result
	}{
		{
			name: "create-single-file",
			setup: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				// Ensure no files exist
				client := TestDataplaneClient(env)
				files, err := client.GetAllGeneralFiles(ctx)
				require.NoError(t, err)
				for _, file := range files {
					_ = client.DeleteGeneralFile(ctx, file)
				}
			},
			operation: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)
				content := LoadTestFileContent(t, "error-files/400.http")
				err := client.CreateGeneralFile(ctx, "400.http", content)
				require.NoError(t, err)
			},
			verify: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)

				// Verify file exists
				files, err := client.GetAllGeneralFiles(ctx)
				require.NoError(t, err)
				assert.Contains(t, files, "400.http", "file should exist")

				// Verify content
				content, err := client.GetGeneralFileContent(ctx, "400.http")
				require.NoError(t, err)
				expectedContent := LoadTestFileContent(t, "error-files/400.http")
				assert.Equal(t, expectedContent, content, "content should match")
			},
		},
		{
			name: "create-multiple-files",
			setup: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				// Ensure no files exist
				client := TestDataplaneClient(env)
				files, err := client.GetAllGeneralFiles(ctx)
				require.NoError(t, err)
				for _, file := range files {
					_ = client.DeleteGeneralFile(ctx, file)
				}
			},
			operation: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)

				files := map[string]string{
					"400.http": "error-files/400.http",
					"403.http": "error-files/403.http",
					"404.http": "error-files/404.http",
				}

				for filename, testdataPath := range files {
					content := LoadTestFileContent(t, testdataPath)
					err := client.CreateGeneralFile(ctx, filename, content)
					require.NoError(t, err)
				}
			},
			verify: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)

				// Verify all files exist
				files, err := client.GetAllGeneralFiles(ctx)
				require.NoError(t, err)
				assert.Len(t, files, 3, "should have 3 files")
				assert.Contains(t, files, "400.http")
				assert.Contains(t, files, "403.http")
				assert.Contains(t, files, "404.http")

				// Verify each file's content
				for filename, testdataPath := range map[string]string{
					"400.http": "error-files/400.http",
					"403.http": "error-files/403.http",
					"404.http": "error-files/404.http",
				} {
					content, err := client.GetGeneralFileContent(ctx, filename)
					require.NoError(t, err)
					expectedContent := LoadTestFileContent(t, testdataPath)
					assert.Equal(t, expectedContent, content, "content for %s should match", filename)
				}
			},
		},
		{
			name: "update-file-content",
			setup: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				// Create initial file
				client := TestDataplaneClient(env)
				content := LoadTestFileContent(t, "error-files/400.http")
				err := client.CreateGeneralFile(ctx, "400.http", content)
				require.NoError(t, err)
			},
			operation: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)
				newContent := LoadTestFileContent(t, "error-files/custom400.http")
				err := client.UpdateGeneralFile(ctx, "400.http", newContent)
				require.NoError(t, err)
			},
			verify: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)

				// Verify file still exists
				files, err := client.GetAllGeneralFiles(ctx)
				require.NoError(t, err)
				assert.Contains(t, files, "400.http", "file should still exist")

				// Verify content was updated
				content, err := client.GetGeneralFileContent(ctx, "400.http")
				require.NoError(t, err)
				expectedContent := LoadTestFileContent(t, "error-files/custom400.http")
				assert.Equal(t, expectedContent, content, "content should be updated")
			},
		},
		{
			name: "delete-single-file",
			setup: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				// Create file to delete
				client := TestDataplaneClient(env)
				content := LoadTestFileContent(t, "error-files/400.http")
				err := client.CreateGeneralFile(ctx, "400.http", content)
				require.NoError(t, err)
			},
			operation: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)
				err := client.DeleteGeneralFile(ctx, "400.http")
				require.NoError(t, err)
			},
			verify: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)

				// Verify file no longer exists
				files, err := client.GetAllGeneralFiles(ctx)
				require.NoError(t, err)
				assert.NotContains(t, files, "400.http", "file should be deleted")
			},
		},
		{
			name: "delete-multiple-files",
			setup: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				// Create multiple files
				client := TestDataplaneClient(env)
				files := map[string]string{
					"400.http": "error-files/400.http",
					"403.http": "error-files/403.http",
					"404.http": "error-files/404.http",
				}

				for filename, testdataPath := range files {
					content := LoadTestFileContent(t, testdataPath)
					err := client.CreateGeneralFile(ctx, filename, content)
					require.NoError(t, err)
				}
			},
			operation: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)
				// Delete two of the three files
				err := client.DeleteGeneralFile(ctx, "400.http")
				require.NoError(t, err)
				err = client.DeleteGeneralFile(ctx, "404.http")
				require.NoError(t, err)
			},
			verify: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)

				// Verify only one file remains
				files, err := client.GetAllGeneralFiles(ctx)
				require.NoError(t, err)
				assert.Len(t, files, 1, "should have 1 file remaining")
				assert.Contains(t, files, "403.http", "403.http should still exist")
				assert.NotContains(t, files, "400.http", "400.http should be deleted")
				assert.NotContains(t, files, "404.http", "404.http should be deleted")
			},
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			env := fixenv.New(t)
			ctx := context.Background()

			// Setup
			if tc.setup != nil {
				tc.setup(t, ctx, env)
			}

			// Operation
			tc.operation(t, ctx, env)

			// Verify
			tc.verify(t, ctx, env)
		})
	}
}

// TestSSLCertificates tests Create, Update, and Delete operations for SSL certificates
func TestSSLCertificates(t *testing.T) {
	testCases := []struct {
		name      string
		setup     func(t *testing.T, ctx context.Context, env fixenv.Env)
		operation func(t *testing.T, ctx context.Context, env fixenv.Env)
		verify    func(t *testing.T, ctx context.Context, env fixenv.Env)
	}{
		{
			name: "create-single-certificate",
			setup: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				// Ensure no certificates exist
				client := TestDataplaneClient(env)
				certs, err := client.GetAllSSLCertificates(ctx)
				require.NoError(t, err)
				for _, cert := range certs {
					_ = client.DeleteSSLCertificate(ctx, cert)
				}
			},
			operation: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)
				content := LoadTestFileContent(t, "ssl-certs/example.com.pem")
				err := client.CreateSSLCertificate(ctx, "example.com.pem", content)
				require.NoError(t, err)
			},
			verify: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)

				// Verify certificate exists
				certs, err := client.GetAllSSLCertificates(ctx)
				require.NoError(t, err)
				assert.Contains(t, certs, "example.com.pem", "certificate should exist")

				// Verify GetSSLCertificateContent returns fingerprint (or placeholder if API doesn't support it)
				fingerprint, err := client.GetSSLCertificateContent(ctx, "example.com.pem")
				require.NoError(t, err)
				assert.NotEmpty(t, fingerprint, "fingerprint should not be empty")
				// Fingerprint is either a SHA256 hash or "__NO_FINGERPRINT__" placeholder
			},
		},
		{
			name: "create-multiple-certificates",
			setup: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				// Ensure no certificates exist
				client := TestDataplaneClient(env)
				certs, err := client.GetAllSSLCertificates(ctx)
				require.NoError(t, err)
				for _, cert := range certs {
					_ = client.DeleteSSLCertificate(ctx, cert)
				}
			},
			operation: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)

				certs := map[string]string{
					"example.com.pem": "ssl-certs/example.com.pem",
					"test.com.pem":    "ssl-certs/test.com.pem",
				}

				for certName, testdataPath := range certs {
					content := LoadTestFileContent(t, testdataPath)
					err := client.CreateSSLCertificate(ctx, certName, content)
					require.NoError(t, err)
				}
			},
			verify: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)

				// Verify all certificates exist
				certs, err := client.GetAllSSLCertificates(ctx)
				require.NoError(t, err)
				assert.Len(t, certs, 2, "should have 2 certificates")
				assert.Contains(t, certs, "example.com.pem")
				assert.Contains(t, certs, "test.com.pem")

				// Verify each certificate returns a fingerprint (or placeholder if API doesn't support it)
				for _, certName := range []string{"example.com.pem", "test.com.pem"} {
					fingerprint, err := client.GetSSLCertificateContent(ctx, certName)
					require.NoError(t, err)
					assert.NotEmpty(t, fingerprint, "fingerprint for %s should not be empty", certName)
					// Fingerprint is either a SHA256 hash or "__NO_FINGERPRINT__" placeholder
				}
			},
		},
		{
			name: "update-certificate-content",
			setup: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				// Create initial certificate
				client := TestDataplaneClient(env)
				content := LoadTestFileContent(t, "ssl-certs/example.com.pem")
				err := client.CreateSSLCertificate(ctx, "example.com.pem", content)
				require.NoError(t, err)
			},
			operation: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)
				newContent := LoadTestFileContent(t, "ssl-certs/updated.com.pem")
				err := client.UpdateSSLCertificate(ctx, "example.com.pem", newContent)
				require.NoError(t, err)
			},
			verify: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)

				// Verify certificate still exists
				certs, err := client.GetAllSSLCertificates(ctx)
				require.NoError(t, err)
				assert.Contains(t, certs, "example.com.pem", "certificate should still exist")

				// Verify GetSSLCertificateContent returns fingerprint (or placeholder if API doesn't support it)
				fingerprint, err := client.GetSSLCertificateContent(ctx, "example.com.pem")
				require.NoError(t, err)
				assert.NotEmpty(t, fingerprint, "fingerprint should not be empty")
				// Fingerprint is either a SHA256 hash or "__NO_FINGERPRINT__" placeholder
			},
		},
		{
			name: "delete-single-certificate",
			setup: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				// Create certificate to delete
				client := TestDataplaneClient(env)
				content := LoadTestFileContent(t, "ssl-certs/example.com.pem")
				err := client.CreateSSLCertificate(ctx, "example.com.pem", content)
				require.NoError(t, err)
			},
			operation: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)
				err := client.DeleteSSLCertificate(ctx, "example.com.pem")
				require.NoError(t, err)
			},
			verify: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)

				// Verify certificate no longer exists
				certs, err := client.GetAllSSLCertificates(ctx)
				require.NoError(t, err)
				assert.NotContains(t, certs, "example.com.pem", "certificate should be deleted")
			},
		},
		{
			name: "delete-multiple-certificates",
			setup: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				// Create multiple certificates
				client := TestDataplaneClient(env)
				certs := map[string]string{
					"example.com.pem": "ssl-certs/example.com.pem",
					"test.com.pem":    "ssl-certs/test.com.pem",
					"updated.com.pem": "ssl-certs/updated.com.pem",
				}

				for certName, testdataPath := range certs {
					content := LoadTestFileContent(t, testdataPath)
					err := client.CreateSSLCertificate(ctx, certName, content)
					require.NoError(t, err)
				}
			},
			operation: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)
				// Delete two of the three certificates
				err := client.DeleteSSLCertificate(ctx, "example.com.pem")
				require.NoError(t, err)
				err = client.DeleteSSLCertificate(ctx, "updated.com.pem")
				require.NoError(t, err)
			},
			verify: func(t *testing.T, ctx context.Context, env fixenv.Env) {
				client := TestDataplaneClient(env)

				// Verify only one certificate remains
				certs, err := client.GetAllSSLCertificates(ctx)
				require.NoError(t, err)
				assert.Len(t, certs, 1, "should have 1 certificate remaining")
				assert.Contains(t, certs, "test.com.pem", "test.com.pem should still exist")
				assert.NotContains(t, certs, "example.com.pem", "example.com.pem should be deleted")
				assert.NotContains(t, certs, "updated.com.pem", "updated.com.pem should be deleted")
			},
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			env := fixenv.New(t)
			ctx := context.Background()

			// Setup
			if tc.setup != nil {
				tc.setup(t, ctx, env)
			}

			// Operation
			tc.operation(t, ctx, env)

			// Verify
			tc.verify(t, ctx, env)
		})
	}
}

// TestSSLCertificatesCompareAndSync tests the Compare and Sync functions for SSL certificates
func TestSSLCertificatesCompareAndSync(t *testing.T) {
	env := fixenv.New(t)
	ctx := context.Background()
	client := TestDataplaneClient(env)

	// Clean up any existing certificates
	certs, err := client.GetAllSSLCertificates(ctx)
	require.NoError(t, err)
	for _, cert := range certs {
		_ = client.DeleteSSLCertificate(ctx, cert)
	}

	// Test: Compare empty state to desired certificates (should show all creates)
	t.Run("compare-empty-to-desired", func(t *testing.T) {
		desired := []auxiliaryfiles.SSLCertificate{
			{Path: "example.com.pem", Content: LoadTestFileContent(t, "ssl-certs/example.com.pem")},
			{Path: "test.com.pem", Content: LoadTestFileContent(t, "ssl-certs/test.com.pem")},
		}

		diff, err := auxiliaryfiles.CompareSSLCertificates(ctx, client, desired)
		require.NoError(t, err)

		assert.Len(t, diff.ToCreate, 2, "should have 2 certificates to create")
		assert.Len(t, diff.ToUpdate, 0, "should have 0 certificates to update")
		assert.Len(t, diff.ToDelete, 0, "should have 0 certificates to delete")
	})

	// Test: Sync creates certificates
	t.Run("sync-create-certificates", func(t *testing.T) {
		desired := []auxiliaryfiles.SSLCertificate{
			{Path: "example.com.pem", Content: LoadTestFileContent(t, "ssl-certs/example.com.pem")},
			{Path: "test.com.pem", Content: LoadTestFileContent(t, "ssl-certs/test.com.pem")},
		}

		diff, err := auxiliaryfiles.CompareSSLCertificates(ctx, client, desired)
		require.NoError(t, err)

		err = auxiliaryfiles.SyncSSLCertificates(ctx, client, diff)
		require.NoError(t, err)

		// Verify certificates were created
		certs, err := client.GetAllSSLCertificates(ctx)
		require.NoError(t, err)
		assert.Len(t, certs, 2)
		assert.Contains(t, certs, "example.com.pem")
		assert.Contains(t, certs, "test.com.pem")
	})

	// Test: Compare with certificates already present
	// NOTE: Behavior depends on whether Dataplane API provides sha256_finger_print:
	//  - With fingerprints: accurately detects changes (0 create, 1 update, 0 delete)
	//  - Without fingerprints: uses CREATE-first approach (2 create, 0 update, 0 delete)
	t.Run("compare-with-existing-certs", func(t *testing.T) {
		desired := []auxiliaryfiles.SSLCertificate{
			{Path: "example.com.pem", Content: LoadTestFileContent(t, "ssl-certs/updated.com.pem")}, // Changed content
			{Path: "test.com.pem", Content: LoadTestFileContent(t, "ssl-certs/test.com.pem")},       // Same content
		}

		diff, err := auxiliaryfiles.CompareSSLCertificates(ctx, client, desired)
		require.NoError(t, err)

		// Verify total operations match expected (either fingerprint-based or CREATE-first)
		totalOps := len(diff.ToCreate) + len(diff.ToUpdate)
		assert.Equal(t, 2, totalOps, "should have 2 total operations (create or update)")
		assert.Len(t, diff.ToDelete, 0, "should have 0 certificates to delete")
	})

	// Test: Sync updates certificates (proper UPDATE or CREATE-with-fallback)
	t.Run("sync-update-certificates", func(t *testing.T) {
		desired := []auxiliaryfiles.SSLCertificate{
			{Path: "example.com.pem", Content: LoadTestFileContent(t, "ssl-certs/updated.com.pem")},
			{Path: "test.com.pem", Content: LoadTestFileContent(t, "ssl-certs/test.com.pem")},
		}

		diff, err := auxiliaryfiles.CompareSSLCertificates(ctx, client, desired)
		require.NoError(t, err)

		err = auxiliaryfiles.SyncSSLCertificates(ctx, client, diff)
		require.NoError(t, err)

		// Verify certificates still exist
		certs, err := client.GetAllSSLCertificates(ctx)
		require.NoError(t, err)
		assert.Len(t, certs, 2)
		assert.Contains(t, certs, "example.com.pem")
		assert.Contains(t, certs, "test.com.pem")
	})

	// Test: Compare with one certificate removed
	t.Run("compare-with-delete", func(t *testing.T) {
		desired := []auxiliaryfiles.SSLCertificate{
			{Path: "test.com.pem", Content: LoadTestFileContent(t, "ssl-certs/test.com.pem")},
			// example.com.pem is not in desired, so it should be deleted
		}

		diff, err := auxiliaryfiles.CompareSSLCertificates(ctx, client, desired)
		require.NoError(t, err)

		// At least one DELETE operation (example.com.pem should be deleted)
		assert.Len(t, diff.ToDelete, 1, "should have 1 certificate to delete")
		assert.Equal(t, "example.com.pem", diff.ToDelete[0])

		// Remaining certificate may be CREATE (no fingerprints) or no-op (with fingerprints)
		totalOps := len(diff.ToCreate) + len(diff.ToUpdate)
		assert.LessOrEqual(t, totalOps, 1, "should have at most 1 operation for test.com.pem")
	})

	// Test: Sync deletes certificates
	t.Run("sync-delete-certificates", func(t *testing.T) {
		desired := []auxiliaryfiles.SSLCertificate{
			{Path: "test.com.pem", Content: LoadTestFileContent(t, "ssl-certs/test.com.pem")},
		}

		diff, err := auxiliaryfiles.CompareSSLCertificates(ctx, client, desired)
		require.NoError(t, err)

		err = auxiliaryfiles.SyncSSLCertificates(ctx, client, diff)
		require.NoError(t, err)

		// Verify certificate was deleted
		certs, err := client.GetAllSSLCertificates(ctx)
		require.NoError(t, err)
		assert.Len(t, certs, 1)
		assert.Contains(t, certs, "test.com.pem")
		assert.NotContains(t, certs, "example.com.pem")
	})

	// Test: Idempotency - running sync again with same desired state
	t.Run("sync-idempotent", func(t *testing.T) {
		desired := []auxiliaryfiles.SSLCertificate{
			{Path: "test.com.pem", Content: LoadTestFileContent(t, "ssl-certs/test.com.pem")},
		}

		diff, err := auxiliaryfiles.CompareSSLCertificates(ctx, client, desired)
		require.NoError(t, err)

		// Verify no DELETE operations (content hasn't been removed)
		assert.Len(t, diff.ToDelete, 0, "should have 0 certificates to delete")

		// With fingerprints: no operations. Without fingerprints: CREATE with fallback
		totalOps := len(diff.ToCreate) + len(diff.ToUpdate)
		assert.LessOrEqual(t, totalOps, 1, "should have at most 1 operation")

		// Verify syncing again doesn't fail (idempotent via CREATE→UPDATE fallback)
		err = auxiliaryfiles.SyncSSLCertificates(ctx, client, diff)
		require.NoError(t, err, "sync should be idempotent")
	})

	// Test: Bug regression - cert doesn't exist should CREATE, not UPDATE
	// This specifically tests the bug that was fixed where non-existent certs were marked for UPDATE
	t.Run("non-existent-cert-creates-not-updates", func(t *testing.T) {
		// Clean up all certificates
		certs, err := client.GetAllSSLCertificates(ctx)
		require.NoError(t, err)
		for _, cert := range certs {
			_ = client.DeleteSSLCertificate(ctx, cert)
		}

		// Request a certificate that doesn't exist
		desired := []auxiliaryfiles.SSLCertificate{
			{Path: "new-cert.pem", Content: LoadTestFileContent(t, "ssl-certs/example.com.pem")},
		}

		diff, err := auxiliaryfiles.CompareSSLCertificates(ctx, client, desired)
		require.NoError(t, err)

		// CRITICAL: Should be marked for CREATE, not UPDATE
		assert.Len(t, diff.ToCreate, 1, "non-existent cert should be marked for CREATE")
		assert.Len(t, diff.ToUpdate, 0, "non-existent cert should NOT be marked for UPDATE")
		assert.Len(t, diff.ToDelete, 0, "should have 0 certificates to delete")

		// Verify sync succeeds (would fail with old bug when trying to UPDATE non-existent cert)
		err = auxiliaryfiles.SyncSSLCertificates(ctx, client, diff)
		require.NoError(t, err, "sync should succeed when creating new certificate")

		// Verify certificate was actually created
		certs, err = client.GetAllSSLCertificates(ctx)
		require.NoError(t, err)
		assert.Contains(t, certs, "new-cert.pem", "certificate should exist after sync")
	})
}

// TestGeneralFilesCompareAndSync tests the Compare and Sync functions for general files
func TestGeneralFilesCompareAndSync(t *testing.T) {
	env := fixenv.New(t)
	ctx := context.Background()
	client := TestDataplaneClient(env)

	// Clean up any existing files
	files, err := client.GetAllGeneralFiles(ctx)
	require.NoError(t, err)
	for _, file := range files {
		_ = client.DeleteGeneralFile(ctx, file)
	}

	// Test: Compare empty state to desired files (should show all creates)
	t.Run("compare-empty-to-desired", func(t *testing.T) {
		desired := []auxiliaryfiles.GeneralFile{
			{Filename: "400.http", Content: LoadTestFileContent(t, "error-files/400.http")},
			{Filename: "403.http", Content: LoadTestFileContent(t, "error-files/403.http")},
		}

		diff, err := auxiliaryfiles.CompareGeneralFiles(ctx, client, desired)
		require.NoError(t, err)

		assert.Len(t, diff.ToCreate, 2, "should have 2 files to create")
		assert.Len(t, diff.ToUpdate, 0, "should have 0 files to update")
		assert.Len(t, diff.ToDelete, 0, "should have 0 files to delete")
	})

	// Test: Sync creates files
	t.Run("sync-create-files", func(t *testing.T) {
		desired := []auxiliaryfiles.GeneralFile{
			{Filename: "400.http", Content: LoadTestFileContent(t, "error-files/400.http")},
			{Filename: "403.http", Content: LoadTestFileContent(t, "error-files/403.http")},
		}

		diff, err := auxiliaryfiles.CompareGeneralFiles(ctx, client, desired)
		require.NoError(t, err)

		err = auxiliaryfiles.SyncGeneralFiles(ctx, client, diff)
		require.NoError(t, err)

		// Verify files were created
		files, err := client.GetAllGeneralFiles(ctx)
		require.NoError(t, err)
		assert.Len(t, files, 2)
		assert.Contains(t, files, "400.http")
		assert.Contains(t, files, "403.http")
	})

	// Test: Compare with one file changed (should show update)
	t.Run("compare-with-update", func(t *testing.T) {
		desired := []auxiliaryfiles.GeneralFile{
			{Filename: "400.http", Content: LoadTestFileContent(t, "error-files/custom400.http")}, // Changed
			{Filename: "403.http", Content: LoadTestFileContent(t, "error-files/403.http")},       // Same
		}

		diff, err := auxiliaryfiles.CompareGeneralFiles(ctx, client, desired)
		require.NoError(t, err)

		assert.Len(t, diff.ToCreate, 0, "should have 0 files to create")
		assert.Len(t, diff.ToUpdate, 1, "should have 1 file to update")
		assert.Len(t, diff.ToDelete, 0, "should have 0 files to delete")
		assert.Equal(t, "400.http", diff.ToUpdate[0].Filename)
	})

	// Test: Sync updates files
	t.Run("sync-update-files", func(t *testing.T) {
		desired := []auxiliaryfiles.GeneralFile{
			{Filename: "400.http", Content: LoadTestFileContent(t, "error-files/custom400.http")},
			{Filename: "403.http", Content: LoadTestFileContent(t, "error-files/403.http")},
		}

		diff, err := auxiliaryfiles.CompareGeneralFiles(ctx, client, desired)
		require.NoError(t, err)

		err = auxiliaryfiles.SyncGeneralFiles(ctx, client, diff)
		require.NoError(t, err)

		// Verify file content was updated
		content, err := client.GetGeneralFileContent(ctx, "400.http")
		require.NoError(t, err)
		expectedContent := LoadTestFileContent(t, "error-files/custom400.http")
		assert.Equal(t, expectedContent, content)
	})

	// Test: Compare with one file removed (should show delete)
	t.Run("compare-with-delete", func(t *testing.T) {
		desired := []auxiliaryfiles.GeneralFile{
			{Filename: "403.http", Content: LoadTestFileContent(t, "error-files/403.http")},
			// 400.http is not in desired, so it should be deleted
		}

		diff, err := auxiliaryfiles.CompareGeneralFiles(ctx, client, desired)
		require.NoError(t, err)

		assert.Len(t, diff.ToCreate, 0, "should have 0 files to create")
		assert.Len(t, diff.ToUpdate, 0, "should have 0 files to update")
		assert.Len(t, diff.ToDelete, 1, "should have 1 file to delete")
		assert.Equal(t, "400.http", diff.ToDelete[0])
	})

	// Test: Sync deletes files
	t.Run("sync-delete-files", func(t *testing.T) {
		desired := []auxiliaryfiles.GeneralFile{
			{Filename: "403.http", Content: LoadTestFileContent(t, "error-files/403.http")},
		}

		diff, err := auxiliaryfiles.CompareGeneralFiles(ctx, client, desired)
		require.NoError(t, err)

		err = auxiliaryfiles.SyncGeneralFiles(ctx, client, diff)
		require.NoError(t, err)

		// Verify file was deleted
		files, err := client.GetAllGeneralFiles(ctx)
		require.NoError(t, err)
		assert.Len(t, files, 1)
		assert.Contains(t, files, "403.http")
		assert.NotContains(t, files, "400.http")
	})

	// Test: Idempotency - running sync again with same desired state should do nothing
	t.Run("sync-idempotent", func(t *testing.T) {
		desired := []auxiliaryfiles.GeneralFile{
			{Filename: "403.http", Content: LoadTestFileContent(t, "error-files/403.http")},
		}

		diff, err := auxiliaryfiles.CompareGeneralFiles(ctx, client, desired)
		require.NoError(t, err)

		assert.Len(t, diff.ToCreate, 0, "should have 0 files to create")
		assert.Len(t, diff.ToUpdate, 0, "should have 0 files to update")
		assert.Len(t, diff.ToDelete, 0, "should have 0 files to delete")
	})
}

// LoadTestFileContent loads a file from testdata and returns its content as a string
func LoadTestFileContent(t *testing.T, relativePath string) string {
	fullPath := filepath.Join("testdata", relativePath)
	content, err := os.ReadFile(fullPath)
	require.NoError(t, err, "failed to read test file %s", relativePath)
	return string(content)
}
