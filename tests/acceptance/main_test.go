//go:build acceptance

package acceptance

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"testing"

	"sigs.k8s.io/e2e-framework/pkg/env"
	"sigs.k8s.io/e2e-framework/pkg/envconf"
	"sigs.k8s.io/e2e-framework/support/kind"

	corev1 "k8s.io/api/core/v1"
)

const (
	// TestKubeconfigPath is the isolated kubeconfig file for acceptance tests.
	// This prevents tests from accidentally modifying the user's default kubeconfig.
	TestKubeconfigPath = "/tmp/haproxy-test-kubeconfig"
)

// TestMain is the entry point for acceptance tests.
// It sets up the test environment with a kind cluster and ensures
// all Setup/Finish actions are properly executed.
func TestMain(m *testing.M) {
	fmt.Println("DEBUG: TestMain is running!")

	// SAFETY: Isolate kubeconfig to prevent production cluster access
	// Set KUBECONFIG environment variable BEFORE creating any clusters
	if err := os.Setenv("KUBECONFIG", TestKubeconfigPath); err != nil {
		fmt.Printf("FATAL: Failed to set KUBECONFIG: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("DEBUG: Using isolated kubeconfig: %s\n", TestKubeconfigPath)

	// Create test environment
	testEnv = env.New()
	fmt.Println("DEBUG: testEnv created:", testEnv != nil)

	// Use kind cluster for testing
	kindClusterName := "haproxy-test"
	kindCluster := kind.NewProvider().WithName(kindClusterName)

	// Setup: Create kind cluster and validate connection
	testEnv.Setup(
		func(ctx context.Context, cfg *envconf.Config) (context.Context, error) {
			// Create cluster
			kubeconfigPath, err := kindCluster.Create(ctx)
			if err != nil {
				return ctx, fmt.Errorf("failed to create kind cluster: %w", err)
			}

			// Update kubeconfig in context
			cfg.WithKubeconfigFile(kubeconfigPath)

			// SAFETY: Verify context switched to kind cluster
			// Kind clusters use localhost IP addresses, so we verify by checking
			// that nodes exist in the cluster (empty production clusters would fail this)
			client, err := cfg.NewClient()
			if err != nil {
				return ctx, fmt.Errorf("failed to create client: %w", err)
			}

			// Validate cluster has nodes (kind cluster just created should have nodes)
			var nodeList corev1.NodeList
			if err := client.Resources().List(ctx, &nodeList); err != nil {
				return ctx, fmt.Errorf("SAFETY CHECK FAILED: Cannot list nodes: %w", err)
			}
			if len(nodeList.Items) == 0 {
				return ctx, fmt.Errorf("SAFETY CHECK FAILED: Cluster has no nodes (unexpected for fresh kind cluster)")
			}

			fmt.Println("DEBUG: Loading controller image into kind cluster...")
			// Load controller Docker image into kind cluster using kind CLI
			cmd := exec.CommandContext(ctx, "kind", "load", "docker-image", "haproxy-template-ic:test", "--name", kindClusterName)
			if output, err := cmd.CombinedOutput(); err != nil {
				return ctx, fmt.Errorf("failed to load controller image into kind cluster: %w\nOutput: %s", err, string(output))
			}
			fmt.Println("DEBUG: Controller image loaded successfully")

			return ctx, nil
		},
	)

	// Finish: Cleanup resources
	testEnv.Finish(
		func(ctx context.Context, cfg *envconf.Config) (context.Context, error) {
			// Destroy kind cluster
			if err := kindCluster.Destroy(ctx); err != nil {
				// Log but don't fail on cleanup
				fmt.Printf("Warning: failed to destroy kind cluster: %v\n", err)
			}
			return ctx, nil
		},
		func(ctx context.Context, cfg *envconf.Config) (context.Context, error) {
			// Remove isolated kubeconfig file
			if err := os.Remove(TestKubeconfigPath); err != nil && !os.IsNotExist(err) {
				fmt.Printf("Warning: failed to remove test kubeconfig %s: %v\n", TestKubeconfigPath, err)
			} else {
				fmt.Printf("DEBUG: Removed test kubeconfig: %s\n", TestKubeconfigPath)
			}
			return ctx, nil
		},
	)

	// Run tests
	os.Exit(testEnv.Run(m))
}
