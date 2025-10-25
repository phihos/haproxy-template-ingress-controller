//go:build integration

package integration

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"strings"
	"time"

	"github.com/rekby/fixenv"
	"haproxy-template-ic/pkg/dataplane"
	"haproxy-template-ic/pkg/dataplane/client"
	"haproxy-template-ic/pkg/dataplane/comparator"
	"haproxy-template-ic/pkg/dataplane/parser"
)

const (
	// maxK8sNameLength is the maximum length for Kubernetes resource names (RFC 1123)
	maxK8sNameLength = 63
	// hashSuffixLength is the length of the hash suffix used to ensure uniqueness
	hashSuffixLength = 8
)

// generateSafeNamespaceName creates a Kubernetes-compliant namespace name that never exceeds 63 characters.
// It uses a combination of the test name (truncated if needed) and a unique hash suffix.
//
// Strategy:
// 1. Normalize test name (lowercase, replace "/" with "-")
// 2. If the name would exceed 63 chars with hash suffix, truncate intelligently
// 3. Add an 8-character hash suffix for uniqueness (derived from full test name + timestamp)
// 4. Ensure total length is always <= 63 characters
//
// Example outputs:
//   - "test-add-backend-a1b2c3d4" (short test name)
//   - "test-backend-add-http-response-rule-a1b2c3d4" (truncated long name)
func generateSafeNamespaceName(testName string) string {
	// Normalize test name: lowercase and replace "/" with "-"
	normalized := strings.ToLower(strings.ReplaceAll(testName, "/", "-"))

	// Generate unique hash from test name + timestamp for uniqueness
	// This ensures the same test run at different times gets different namespaces
	timestamp := fmt.Sprintf("%d", time.Now().UnixNano())
	hashInput := fmt.Sprintf("%s-%s", normalized, timestamp)
	hash := sha256.Sum256([]byte(hashInput))
	hashSuffix := hex.EncodeToString(hash[:])[:hashSuffixLength]

	maxBaseLength := maxK8sNameLength - 5 - 1 - hashSuffixLength

	// Truncate normalized name if needed
	baseName := normalized
	if len(baseName) > maxBaseLength {
		baseName = baseName[:maxBaseLength]
	}

	// Construct final name
	finalName := fmt.Sprintf("test-%s-%s", baseName, hashSuffix)

	// Sanity check: ensure we never exceed the limit
	if len(finalName) > maxK8sNameLength {
		panic(fmt.Sprintf("BUG: generated namespace name '%s' exceeds %d characters (length: %d)",
			finalName, maxK8sNameLength, len(finalName)))
	}

	return finalName
}

// SharedCluster provides a package-scoped Kind cluster shared across all tests
// This fixture runs only once per test package and is kept by default for faster test iterations
// The cluster is automatically reused if it already exists
// Set KEEP_CLUSTER=false to force cleanup after tests
func SharedCluster(env fixenv.Env) *KindCluster {
	return fixenv.CacheResult(env, func() (*fixenv.GenericResult[*KindCluster], error) {
		cluster, err := SetupKindCluster(&KindClusterConfig{
			Name: "haproxy-test",
		})
		if err != nil {
			return nil, fmt.Errorf("failed to setup kind cluster: %w", err)
		}

		// Return with conditional cleanup function
		return fixenv.NewGenericResultWithCleanup(cluster, func() {
			keepCluster := ShouldKeepCluster()
			if keepCluster == "true" {
				fmt.Printf("\n🔒 Keeping Kind cluster '%s' (KEEP_CLUSTER=true)\n", cluster.Name)
				fmt.Printf("🧹 To manually clean up: kind delete cluster --name=%s\n", cluster.Name)
				return
			}
			// Default: always clean up
			_ = cluster.Teardown()
		}), nil
	}, fixenv.CacheOptions{Scope: fixenv.ScopePackage})
}

// TestNamespace provides a test-scoped namespace (fresh for each test)
// Automatically depends on SharedCluster fixture
// Namespaces are kept by default for faster test iterations
// Set KEEP_CLUSTER=false to force cleanup after tests
func TestNamespace(env fixenv.Env) *Namespace {
	// Automatic dependency: request SharedCluster fixture
	cluster := SharedCluster(env)

	return fixenv.CacheResult(env, func() (*fixenv.GenericResult[*Namespace], error) {
		// Generate unique namespace name for this test
		// Uses generateSafeNamespaceName to ensure Kubernetes compliance (max 63 chars)
		name := generateSafeNamespaceName(env.T().Name())

		ns, err := cluster.CreateNamespace(name)
		if err != nil {
			return nil, fmt.Errorf("failed to create namespace: %w", err)
		}

		// Return with conditional cleanup function
		return fixenv.NewGenericResultWithCleanup(ns, func() {
			keepCluster := ShouldKeepCluster()
			if keepCluster == "true" {
				fmt.Printf("🔒 Keeping namespace '%s' (KEEP_CLUSTER=true)\n", ns.Name)
				return
			}
			// Default: always clean up
			_ = ns.Delete()
		}), nil
	})
}

// TestHAProxy provides a test-scoped HAProxy deployment
// Automatically depends on TestNamespace fixture (which depends on SharedCluster)
// HAProxy instances are kept by default for faster test iterations
// Set KEEP_CLUSTER=false to force cleanup after tests
func TestHAProxy(env fixenv.Env) *HAProxyInstance {
	// Automatic dependency chain: TestNamespace -> SharedCluster
	ns := TestNamespace(env)

	return fixenv.CacheResult(env, func() (*fixenv.GenericResult[*HAProxyInstance], error) {
		haproxy, err := DeployHAProxy(ns, DefaultHAProxyConfig())
		if err != nil {
			return nil, fmt.Errorf("failed to deploy haproxy: %w", err)
		}

		return fixenv.NewGenericResultWithCleanup(haproxy, func() {
			keepCluster := ShouldKeepCluster()
			if keepCluster == "true" {
				fmt.Printf("🔒 Keeping HAProxy instance '%s' in namespace '%s' (KEEP_CLUSTER=true)\n", haproxy.Name, haproxy.Namespace)
				return
			}
			// Default: always clean up
			_ = haproxy.Delete()
		}), nil
	})
}

// TestDataplaneClient provides a configured Dataplane API client
// Automatically depends on TestHAProxy fixture
func TestDataplaneClient(env fixenv.Env) *client.DataplaneClient {
	// Automatic dependency chain: TestHAProxy -> TestNamespace -> SharedCluster
	haproxy := TestHAProxy(env)

	return fixenv.CacheResult(env, func() (*fixenv.GenericResult[*client.DataplaneClient], error) {
		endpoint := haproxy.GetDataplaneEndpoint()

		dataplaneClient, err := client.New(&client.Config{
			BaseURL:  endpoint.URL,
			Username: endpoint.Username,
			Password: endpoint.Password,
		})
		if err != nil {
			return nil, fmt.Errorf("failed to create dataplane client: %w", err)
		}

		return fixenv.NewGenericResult(dataplaneClient), nil
	})
}

// TestParser provides a configuration parser instance
func TestParser(env fixenv.Env) *parser.Parser {
	return fixenv.CacheResult(env, func() (*fixenv.GenericResult[*parser.Parser], error) {
		p, err := parser.New()
		if err != nil {
			return nil, fmt.Errorf("failed to create parser: %w", err)
		}
		return fixenv.NewGenericResult(p), nil
	})
}

// TestComparator provides a comparator instance
func TestComparator(env fixenv.Env) *comparator.Comparator {
	return fixenv.CacheResult(env, func() (*fixenv.GenericResult[*comparator.Comparator], error) {
		return fixenv.NewGenericResult(comparator.New()), nil
	})
}

// TestDataplaneHighLevelClient provides a high-level dataplane.Client
// This uses the public Sync API that other components will use
// Automatically depends on TestHAProxy fixture
func TestDataplaneHighLevelClient(env fixenv.Env) *dataplane.Client {
	// Automatic dependency chain: TestHAProxy -> TestNamespace -> SharedCluster
	haproxy := TestHAProxy(env)

	return fixenv.CacheResult(env, func() (*fixenv.GenericResult[*dataplane.Client], error) {
		endpoint := haproxy.GetDataplaneEndpoint()

		dpEndpoint := dataplane.Endpoint{
			URL:      endpoint.URL,
			Username: endpoint.Username,
			Password: endpoint.Password,
		}

		client, err := dataplane.NewClient(context.Background(), dpEndpoint)
		if err != nil {
			return nil, fmt.Errorf("failed to create dataplane client: %w", err)
		}

		return fixenv.NewGenericResult(client), nil
	})
}
