//go:build integration

package integration

import (
	"context"
	"fmt"
	"os"
	"time"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
	"sigs.k8s.io/kind/pkg/cluster"
	"sigs.k8s.io/kind/pkg/cmd"
)

// KindClusterConfig holds configuration for creating a Kind cluster
type KindClusterConfig struct {
	Name string
	// Image is the Kind node image to use (e.g., "kindest/node:v1.32.0")
	// If empty, uses the image from KIND_NODE_IMAGE env var or defaults to kindest/node:v1.32.0
	Image string
}

// KindCluster represents a Kind (Kubernetes in Docker) cluster for testing
type KindCluster struct {
	Name       string
	Kubeconfig string
	provider   *cluster.Provider
	clientset  *kubernetes.Clientset
}

// SetupKindCluster creates or reuses a Kind cluster for integration testing
func SetupKindCluster(cfg *KindClusterConfig) (*KindCluster, error) {
	provider := cluster.NewProvider(
		cluster.ProviderWithLogger(cmd.NewLogger()),
	)

	// Check if cluster already exists
	clusters, err := provider.List()
	if err != nil {
		return nil, fmt.Errorf("failed to list clusters: %w", err)
	}

	clusterExists := false
	for _, c := range clusters {
		if c == cfg.Name {
			clusterExists = true
			fmt.Printf("♻️  Reusing existing Kind cluster '%s'\n", cfg.Name)
			break
		}
	}

	// Only create if doesn't exist
	if !clusterExists {
		fmt.Printf("🆕 Creating new Kind cluster '%s'\n", cfg.Name)

		// Determine node image to use
		nodeImage := cfg.Image
		if nodeImage == "" {
			// Check environment variable (full image path like "kindest/node:v1.32.0")
			nodeImage = os.Getenv("KIND_NODE_IMAGE")
			// If env var is not set, use default known-working version
			if nodeImage == "" {
				nodeImage = "kindest/node:v1.32.0"
			}
		}

		// Prepare cluster creation options
		createOpts := []cluster.CreateOption{
			cluster.CreateWithWaitForReady(5 * time.Minute),
		}

		// Add node image if specified
		if nodeImage != "" {
			createOpts = append(createOpts, cluster.CreateWithNodeImage(nodeImage))
		}

		// Create the cluster
		if err := provider.Create(cfg.Name, createOpts...); err != nil {
			return nil, fmt.Errorf("failed to create kind cluster: %w", err)
		}
	}

	// Get kubeconfig
	kubeconfig, err := provider.KubeConfig(cfg.Name, false)
	if err != nil {
		return nil, fmt.Errorf("failed to get kubeconfig: %w", err)
	}

	// Create Kubernetes client
	config, err := clientcmd.RESTConfigFromKubeConfig([]byte(kubeconfig))
	if err != nil {
		return nil, fmt.Errorf("failed to create rest config: %w", err)
	}

	// Disable client-side rate limiting for parallel tests
	// Default is QPS=5, Burst=10 which is too restrictive
	// Set to 0 to disable rate limiting entirely
	config.QPS = 0
	config.Burst = 0

	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, fmt.Errorf("failed to create kubernetes client: %w", err)
	}

	cluster := &KindCluster{
		Name:       cfg.Name,
		Kubeconfig: kubeconfig,
		provider:   provider,
		clientset:  clientset,
	}

	// Wait for API server to be fully ready
	// This ensures the API server is accepting connections before tests proceed
	fmt.Printf("⏳ Waiting for API server to become ready...\n")
	if err := waitForAPIServer(clientset, 2*time.Minute); err != nil {
		return nil, fmt.Errorf("API server failed to become ready: %w", err)
	}
	fmt.Printf("✓ API server is ready\n")

	// Trigger background cleanup of old test namespaces
	// This runs asynchronously and doesn't block test execution
	cluster.CleanupOldTestNamespacesAsync()

	return cluster, nil
}

// waitForAPIServer polls the API server until it responds successfully or timeout occurs.
// This is necessary because cluster creation may complete before the API server is fully ready
// to accept connections, leading to "connection refused" errors in tests.
func waitForAPIServer(clientset *kubernetes.Clientset, timeout time.Duration) error {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return fmt.Errorf("timeout waiting for API server to become ready")
		case <-ticker.C:
			// Try to get server version - this is a lightweight API call
			// that confirms the API server is responding
			_, err := clientset.Discovery().ServerVersion()
			if err == nil {
				return nil // API server is ready
			}
			// Continue waiting on connection errors
			fmt.Printf("  API server not ready yet (will retry): %v\n", err)
		}
	}
}

// CreateNamespace creates a new namespace in the cluster
func (k *KindCluster) CreateNamespace(name string) (*Namespace, error) {
	ctx := context.Background()

	ns := &corev1.Namespace{
		ObjectMeta: metav1.ObjectMeta{
			Name: name,
		},
	}

	created, err := k.clientset.CoreV1().Namespaces().Create(ctx, ns, metav1.CreateOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to create namespace: %w", err)
	}

	return &Namespace{
		Name:      created.Name,
		cluster:   k,
		clientset: k.clientset,
	}, nil
}

// CleanupOldTestNamespacesAsync triggers asynchronous cleanup of old test namespaces.
// This function returns immediately without blocking - cleanup happens in the background.
// It lists all namespaces with the "test-" prefix that are older than 5 minutes and deletes them.
// This prevents race conditions where newly created test namespaces get deleted while tests are running.
func (k *KindCluster) CleanupOldTestNamespacesAsync() {
	go func() {
		// Wait a bit before starting cleanup to allow current tests to create their namespaces
		time.Sleep(2 * time.Second)

		ctx := context.Background()

		// List all namespaces with test- prefix
		namespaces, err := k.clientset.CoreV1().Namespaces().List(ctx, metav1.ListOptions{})
		if err != nil {
			fmt.Printf("Background cleanup: failed to list namespaces: %v\n", err)
			return
		}

		// Current time for age comparison
		now := time.Now()
		ageThreshold := 5 * time.Minute

		// Filter to old test namespaces (created more than 5 minutes ago)
		var oldTestNamespaces []string
		for _, ns := range namespaces.Items {
			if len(ns.Name) >= 5 && ns.Name[:5] == "test-" {
				age := now.Sub(ns.CreationTimestamp.Time)
				if age > ageThreshold {
					oldTestNamespaces = append(oldTestNamespaces, ns.Name)
				}
			}
		}

		if len(oldTestNamespaces) == 0 {
			fmt.Printf("Background cleanup: no old test namespaces found\n")
			return
		}

		fmt.Printf("Background cleanup: deleting %d old test namespaces (>%v old) in background\n", len(oldTestNamespaces), ageThreshold)

		// Delete each old namespace
		for _, nsName := range oldTestNamespaces {
			err := k.clientset.CoreV1().Namespaces().Delete(ctx, nsName, metav1.DeleteOptions{})
			if err != nil {
				fmt.Printf("Background cleanup: failed to delete namespace %s: %v\n", nsName, err)
			}
		}

		fmt.Printf("Background cleanup: completed deletion of %d namespaces\n", len(oldTestNamespaces))
	}()
}

// Teardown destroys the Kind cluster
func (k *KindCluster) Teardown() error {
	if err := k.provider.Delete(k.Name, ""); err != nil {
		return fmt.Errorf("failed to delete kind cluster: %w", err)
	}
	return nil
}

// Namespace represents a Kubernetes namespace for test isolation
type Namespace struct {
	Name      string
	cluster   *KindCluster
	clientset *kubernetes.Clientset
}

// Delete removes the namespace from the cluster
func (n *Namespace) Delete() error {
	ctx := context.Background()
	err := n.clientset.CoreV1().Namespaces().Delete(ctx, n.Name, metav1.DeleteOptions{})
	if err != nil {
		return fmt.Errorf("failed to delete namespace: %w", err)
	}
	return nil
}

// Clientset returns the Kubernetes clientset
func (n *Namespace) Clientset() *kubernetes.Clientset {
	return n.clientset
}

// getRestConfig returns the REST config for the Kind cluster
func (k *KindCluster) getRestConfig() (*rest.Config, error) {
	config, err := clientcmd.RESTConfigFromKubeConfig([]byte(k.Kubeconfig))
	if err != nil {
		return nil, fmt.Errorf("failed to create rest config: %w", err)
	}

	// Disable client-side rate limiting for parallel tests
	// Set to 0 to disable rate limiting entirely
	config.QPS = 0
	config.Burst = 0

	return config, nil
}

// ShouldKeepCluster returns whether the cluster should be kept after tests
// based on the KEEP_CLUSTER environment variable.
// Values: "" (default) - keep cluster for faster subsequent runs, "false" - always cleanup
func ShouldKeepCluster() string {
	val := os.Getenv("KEEP_CLUSTER")
	if val == "" {
		return "true" // Default to keeping cluster for faster test iterations
	}
	return val
}
