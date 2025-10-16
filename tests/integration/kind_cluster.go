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
	// Image is the Kind node image to use (e.g., "kindest/node:v1.34.0")
	// If empty, uses the version from KIND_NODE_VERSION env var or Kind's default
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
			// Check environment variable
			nodeImage = os.Getenv("KIND_NODE_VERSION")
			// If env var is set, format it as a full image reference
			if nodeImage != "" {
				nodeImage = fmt.Sprintf("kindest/node:%s", nodeImage)
			}
			// If still empty, Kind will use its default version
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

	// Trigger background cleanup of old test namespaces
	// This runs asynchronously and doesn't block test execution
	cluster.CleanupOldTestNamespacesAsync()

	return cluster, nil
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
// It lists all namespaces with the "test-" prefix and deletes them in a goroutine.
func (k *KindCluster) CleanupOldTestNamespacesAsync() {
	go func() {
		ctx := context.Background()

		// List all namespaces with test- prefix
		namespaces, err := k.clientset.CoreV1().Namespaces().List(ctx, metav1.ListOptions{})
		if err != nil {
			fmt.Printf("Background cleanup: failed to list namespaces: %v\n", err)
			return
		}

		// Filter to test namespaces
		var testNamespaces []string
		for _, ns := range namespaces.Items {
			if len(ns.Name) >= 5 && ns.Name[:5] == "test-" {
				testNamespaces = append(testNamespaces, ns.Name)
			}
		}

		if len(testNamespaces) == 0 {
			fmt.Printf("Background cleanup: no old test namespaces found\n")
			return
		}

		fmt.Printf("Background cleanup: deleting %d old test namespaces in background\n", len(testNamespaces))

		// Delete each namespace
		for _, nsName := range testNamespaces {
			err := k.clientset.CoreV1().Namespaces().Delete(ctx, nsName, metav1.DeleteOptions{})
			if err != nil {
				fmt.Printf("Background cleanup: failed to delete namespace %s: %v\n", nsName, err)
			}
		}

		fmt.Printf("Background cleanup: completed deletion of %d namespaces\n", len(testNamespaces))
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
