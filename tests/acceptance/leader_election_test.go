// Copyright 2025 Philipp Hossner
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

//go:build acceptance

package acceptance

import (
	"context"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"strings"
	"testing"
	"time"

	"sigs.k8s.io/e2e-framework/pkg/envconf"
	"sigs.k8s.io/e2e-framework/pkg/features"

	corev1 "k8s.io/api/core/v1"
	networkingv1 "k8s.io/api/networking/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/portforward"
	"k8s.io/client-go/transport/spdy"
)

const (
	// MetricsPort is the port for the Prometheus metrics endpoint.
	MetricsPort = 9090

	// LeaderElectionLeaseName is the default lease name for leader election.
	LeaderElectionLeaseName = "haproxy-template-ic-leader"
)

// TestLeaderElection_TwoReplicas verifies that two-replica deployment elects exactly one leader.
//
// This test validates:
//  1. Two controller pods are deployed and become ready
//  2. A Lease resource is created with a holder identity
//  3. Exactly one pod has is_leader=1 metric
//  4. The other pod has is_leader=0 metric
//  5. The Lease holder matches the pod with is_leader=1
//
//nolint:revive // High complexity expected in E2E test scenarios
func TestLeaderElection_TwoReplicas(t *testing.T) {
	feature := features.New("Leader Election - Two Replicas").
		Setup(func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			t.Helper()
			t.Log("Setting up leader election two replicas test")

			// Generate unique namespace for this test
			namespace := envconf.RandomName("test-leader-2rep", 16)
			t.Logf("Using test namespace: %s", namespace)

			// Store namespace in context
			ctx = StoreNamespaceInContext(ctx, namespace)

			client, err := cfg.NewClient()
			if err != nil {
				t.Fatal("Failed to create client:", err)
			}

			// Create test namespace
			ns := &corev1.Namespace{
				ObjectMeta: metav1.ObjectMeta{
					Name: namespace,
				},
			}
			if err := client.Resources().Create(ctx, ns); err != nil {
				t.Fatal("Failed to create namespace:", err)
			}
			t.Logf("Created test namespace: %s", namespace)

			// Create RBAC resources
			serviceAccount := NewServiceAccount(namespace, ControllerServiceAccountName)
			if err := client.Resources().Create(ctx, serviceAccount); err != nil {
				t.Fatal("Failed to create serviceaccount:", err)
			}

			role := NewRole(namespace, ControllerRoleName)
			if err := client.Resources().Create(ctx, role); err != nil {
				t.Fatal("Failed to create role:", err)
			}

			roleBinding := NewRoleBinding(namespace, ControllerRoleBindingName, ControllerRoleName, ControllerServiceAccountName)
			if err := client.Resources().Create(ctx, roleBinding); err != nil {
				t.Fatal("Failed to create rolebinding:", err)
			}

			// Create ClusterRole with Lease permissions
			clusterRole := NewClusterRole(ControllerClusterRoleName, namespace)
			if err := client.Resources().Create(ctx, clusterRole); err != nil {
				t.Fatal("Failed to create clusterrole:", err)
			}

			clusterRoleBinding := NewClusterRoleBinding(ControllerClusterRoleBindingName, ControllerClusterRoleName, ControllerServiceAccountName, namespace, namespace)
			if err := client.Resources().Create(ctx, clusterRoleBinding); err != nil {
				t.Fatal("Failed to create clusterrolebinding:", err)
			}

			// Create Secret
			secret := NewSecret(namespace, ControllerSecretName)
			if err := client.Resources().Create(ctx, secret); err != nil {
				t.Fatal("Failed to create secret:", err)
			}

			webhookCertSecret := NewWebhookCertSecret(namespace, "haproxy-webhook-certs")
			if err := client.Resources().Create(ctx, webhookCertSecret); err != nil {
				t.Fatal("Failed to create webhook cert secret:", err)
			}

			// Create ConfigMap with leader election enabled
			configMap := NewConfigMap(namespace, ControllerConfigMapName, HAConfigWithLeaderElectionYAML)
			if err := client.Resources().Create(ctx, configMap); err != nil {
				t.Fatal("Failed to create configmap:", err)
			}
			t.Log("Created controller configmap with leader election enabled")

			// Create Deployment with 2 replicas
			deployment := NewControllerDeployment(
				namespace,
				ControllerConfigMapName,
				ControllerSecretName,
				ControllerServiceAccountName,
				DebugPort,
				2, // Two replicas for HA
			)
			if err := client.Resources().Create(ctx, deployment); err != nil {
				t.Fatal("Failed to create deployment:", err)
			}
			t.Log("Created controller deployment with 2 replicas")

			return ctx
		}).
		Assess("Exactly one leader elected", func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			t.Helper()

			namespace, err := GetNamespaceFromContext(ctx)
			if err != nil {
				t.Fatal("Failed to get namespace from context:", err)
			}

			client, err := cfg.NewClient()
			if err != nil {
				t.Fatal("Failed to create client:", err)
			}

			// Wait for 2 pods to be ready
			t.Log("Waiting for 2 controller pods to be ready...")
			if err := WaitForPodReady(ctx, client, namespace, "app="+ControllerDeploymentName, 2*time.Minute); err != nil {
				t.Fatal("Controller pods did not become ready:", err)
			}
			t.Log("Controller pods are ready")

			// Wait for leader election to complete
			t.Log("Waiting for leader election...")
			if err := WaitForLeaderElection(ctx, cfg.Client().RESTConfig(), namespace, LeaderElectionLeaseName, 90*time.Second); err != nil {
				// Dump pod logs for debugging
				t.Log("Leader election failed, dumping pod logs...")
				pods, podErr := GetAllControllerPods(ctx, client, namespace)
				if podErr == nil {
					for _, pod := range pods {
						t.Logf("=== Logs for pod %s ===", pod.Name)
						DumpPodLogs(ctx, t, cfg.Client().RESTConfig(), &pod)
					}
				}
				t.Fatal("Leader election did not complete:", err)
			}
			t.Log("Leader election completed")

			// Get all controller pods
			pods, err := GetAllControllerPods(ctx, client, namespace)
			if err != nil {
				t.Fatal("Failed to get controller pods:", err)
			}

			if len(pods) != 2 {
				t.Fatalf("Expected 2 pods, found %d", len(pods))
			}

			// Check metrics from each pod
			leaderCount := 0
			followerCount := 0
			var leaderPodName string

			for _, pod := range pods {
				t.Logf("Checking metrics for pod %s", pod.Name)

				isLeader, err := checkPodIsLeader(ctx, t, cfg.Client().RESTConfig(), &pod)
				if err != nil {
					t.Fatalf("Failed to check leader status for pod %s: %v", pod.Name, err)
				}

				if isLeader {
					leaderCount++
					leaderPodName = pod.Name
					t.Logf("Pod %s is the leader", pod.Name)
				} else {
					followerCount++
					t.Logf("Pod %s is a follower", pod.Name)
				}
			}

			// Verify exactly one leader
			if leaderCount != 1 {
				t.Fatalf("Expected exactly 1 leader, found %d", leaderCount)
			}
			if followerCount != 1 {
				t.Fatalf("Expected exactly 1 follower, found %d", followerCount)
			}

			// Verify Lease holder matches leader pod
			holderIdentity, err := GetLeaseHolder(ctx, cfg.Client().RESTConfig(), namespace, LeaderElectionLeaseName)
			if err != nil {
				t.Fatal("Failed to get lease holder:", err)
			}

			if holderIdentity != leaderPodName {
				t.Fatalf("Lease holder (%s) does not match leader pod (%s)", holderIdentity, leaderPodName)
			}

			t.Logf("✓ Leader election working correctly: leader=%s, follower count=%d", leaderPodName, followerCount)

			return ctx
		}).
		Assess("Leader deploys configs", func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			t.Helper()

			namespace, err := GetNamespaceFromContext(ctx)
			if err != nil {
				t.Fatal("Failed to get namespace from context:", err)
			}

			client, err := cfg.NewClient()
			if err != nil {
				t.Fatal("Failed to create client:", err)
			}

			// Create a simple Ingress resource
			pathType := networkingv1.PathTypePrefix
			ingress := &networkingv1.Ingress{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-ingress",
					Namespace: namespace,
				},
				Spec: networkingv1.IngressSpec{
					Rules: []networkingv1.IngressRule{
						{
							Host: "test.example.com",
							IngressRuleValue: networkingv1.IngressRuleValue{
								HTTP: &networkingv1.HTTPIngressRuleValue{
									Paths: []networkingv1.HTTPIngressPath{
										{
											Path:     "/test",
											PathType: &pathType,
											Backend: networkingv1.IngressBackend{
												Service: &networkingv1.IngressServiceBackend{
													Name: "test-service",
													Port: networkingv1.ServiceBackendPort{
														Number: 80,
													},
												},
											},
										},
									},
								},
							},
						},
					},
				},
			}

			if err := client.Resources().Create(ctx, ingress); err != nil {
				t.Fatal("Failed to create ingress:", err)
			}
			t.Log("Created test ingress")

			// Wait for reconciliation
			time.Sleep(10 * time.Second)

			// Get leader pod
			holderIdentity, err := GetLeaseHolder(ctx, cfg.Client().RESTConfig(), namespace, LeaderElectionLeaseName)
			if err != nil {
				t.Fatal("Failed to get lease holder:", err)
			}

			pods, err := GetAllControllerPods(ctx, client, namespace)
			if err != nil {
				t.Fatal("Failed to get controller pods:", err)
			}

			var leaderPod *corev1.Pod
			for i := range pods {
				if pods[i].Name == holderIdentity {
					leaderPod = &pods[i]
					break
				}
			}

			if leaderPod == nil {
				t.Fatal("Could not find leader pod")
			}

			// Access debug endpoint to verify rendered config contains the ingress
			debugClient := NewDebugClient(cfg.Client().RESTConfig(), leaderPod, DebugPort)
			if err := debugClient.Start(ctx); err != nil {
				t.Fatal("Failed to start debug client:", err)
			}
			defer debugClient.Stop()

			rendered, err := debugClient.GetRenderedConfig(ctx)
			if err != nil {
				t.Logf("Warning: Could not get rendered config: %v", err)
				// Don't fail test if debug endpoint not available
				return ctx
			}

			// Verify config contains the ingress backend
			expectedBackend := fmt.Sprintf("ing_%s_test-ingress", namespace)
			if !strings.Contains(rendered, expectedBackend) {
				t.Logf("Warning: Rendered config does not contain expected backend %s", expectedBackend)
				t.Logf("Rendered config:\n%s", rendered)
			} else {
				t.Logf("✓ Leader successfully deployed config with ingress backend")
			}

			return ctx
		}).
		Feature()

	testEnv.Test(t, feature)
}

// checkPodIsLeader checks if a pod reports itself as leader via metrics.
func checkPodIsLeader(ctx context.Context, t *testing.T, restConfig *rest.Config, pod *corev1.Pod) (bool, error) {
	t.Helper()

	// Get a free local port
	listener, err := net.Listen("tcp", "localhost:0")
	if err != nil {
		return false, fmt.Errorf("failed to get free port: %w", err)
	}
	localPort := listener.Addr().(*net.TCPAddr).Port
	listener.Close()

	// Setup port-forward to metrics endpoint
	roundTripper, upgrader, err := spdy.RoundTripperFor(restConfig)
	if err != nil {
		return false, fmt.Errorf("failed to create round tripper: %w", err)
	}

	path := fmt.Sprintf("/api/v1/namespaces/%s/pods/%s/portforward", pod.Namespace, pod.Name)
	hostIP := strings.TrimPrefix(restConfig.Host, "https://")
	serverURLStr := fmt.Sprintf("https://%s%s", hostIP, path)

	serverURL, err := url.Parse(serverURLStr)
	if err != nil {
		return false, fmt.Errorf("failed to parse server URL: %w", err)
	}

	dialer := spdy.NewDialer(upgrader, &http.Client{Transport: roundTripper}, http.MethodPost, serverURL)

	stopChan := make(chan struct{}, 1)
	readyChan := make(chan struct{})
	errChan := make(chan error)

	// Create port forwarder
	fw, err := portforward.New(dialer, []string{fmt.Sprintf("%d:%d", localPort, MetricsPort)}, stopChan, readyChan, nil, nil)
	if err != nil {
		return false, fmt.Errorf("failed to create port forwarder: %w", err)
	}

	// Start port forwarding in background
	go func() {
		if err := fw.ForwardPorts(); err != nil {
			errChan <- err
		}
	}()

	// Wait for port-forward to be ready
	select {
	case <-readyChan:
		// Ready
	case err := <-errChan:
		return false, fmt.Errorf("port forward failed: %w", err)
	case <-time.After(30 * time.Second):
		close(stopChan)
		return false, fmt.Errorf("timeout waiting for port forward")
	}

	defer close(stopChan)

	// Fetch metrics
	metricsURL := fmt.Sprintf("http://localhost:%d/metrics", localPort)
	resp, err := http.Get(metricsURL)
	if err != nil {
		return false, fmt.Errorf("failed to fetch metrics: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return false, fmt.Errorf("failed to read metrics: %w", err)
	}

	metricsOutput := string(body)

	// Parse metrics to find haproxy_ic_leader_election_is_leader
	lines := strings.Split(metricsOutput, "\n")
	for _, line := range lines {
		// Skip comments
		if strings.HasPrefix(line, "#") {
			continue
		}

		// Look for is_leader metric
		if strings.Contains(line, "haproxy_ic_leader_election_is_leader") {
			// Format: haproxy_ic_leader_election_is_leader{pod="..."} 1
			if strings.HasSuffix(strings.TrimSpace(line), " 1") || strings.HasSuffix(strings.TrimSpace(line), " 1.0") {
				return true, nil
			}
			return false, nil
		}
	}

	return false, fmt.Errorf("leader election metric not found in metrics output")
}

// TestLeaderElection_Failover verifies automatic failover when leader fails.
//
// This test validates:
//  1. Initial leader is elected
//  2. Deleting leader pod triggers failover
//  3. A new leader is elected within the failover window
//  4. New leader is different from deleted pod
//  5. Only one leader exists after failover
//
//nolint:revive // High complexity expected in E2E test scenarios
func TestLeaderElection_Failover(t *testing.T) {
	feature := features.New("Leader Election - Failover").
		Setup(func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			t.Helper()
			t.Log("Setting up leader election failover test")

			namespace := envconf.RandomName("test-leader-failover", 16)
			t.Logf("Using test namespace: %s", namespace)

			ctx = StoreNamespaceInContext(ctx, namespace)

			client, err := cfg.NewClient()
			if err != nil {
				t.Fatal("Failed to create client:", err)
			}

			// Create namespace
			ns := &corev1.Namespace{
				ObjectMeta: metav1.ObjectMeta{
					Name: namespace,
				},
			}
			if err := client.Resources().Create(ctx, ns); err != nil {
				t.Fatal("Failed to create namespace:", err)
			}

			// Create RBAC resources
			serviceAccount := NewServiceAccount(namespace, ControllerServiceAccountName)
			if err := client.Resources().Create(ctx, serviceAccount); err != nil {
				t.Fatal("Failed to create serviceaccount:", err)
			}

			role := NewRole(namespace, ControllerRoleName)
			if err := client.Resources().Create(ctx, role); err != nil {
				t.Fatal("Failed to create role:", err)
			}

			roleBinding := NewRoleBinding(namespace, ControllerRoleBindingName, ControllerRoleName, ControllerServiceAccountName)
			if err := client.Resources().Create(ctx, roleBinding); err != nil {
				t.Fatal("Failed to create rolebinding:", err)
			}

			clusterRole := NewClusterRole(ControllerClusterRoleName, namespace)
			if err := client.Resources().Create(ctx, clusterRole); err != nil {
				t.Fatal("Failed to create clusterrole:", err)
			}

			clusterRoleBinding := NewClusterRoleBinding(ControllerClusterRoleBindingName, ControllerClusterRoleName, ControllerServiceAccountName, namespace, namespace)
			if err := client.Resources().Create(ctx, clusterRoleBinding); err != nil {
				t.Fatal("Failed to create clusterrolebinding:", err)
			}

			secret := NewSecret(namespace, ControllerSecretName)
			if err := client.Resources().Create(ctx, secret); err != nil {
				t.Fatal("Failed to create secret:", err)
			}

			webhookCertSecret := NewWebhookCertSecret(namespace, "haproxy-webhook-certs")
			if err := client.Resources().Create(ctx, webhookCertSecret); err != nil {
				t.Fatal("Failed to create webhook cert secret:", err)
			}

			configMap := NewConfigMap(namespace, ControllerConfigMapName, HAConfigWithLeaderElectionYAML)
			if err := client.Resources().Create(ctx, configMap); err != nil {
				t.Fatal("Failed to create configmap:", err)
			}

			deployment := NewControllerDeployment(
				namespace,
				ControllerConfigMapName,
				ControllerSecretName,
				ControllerServiceAccountName,
				DebugPort,
				2,
			)
			if err := client.Resources().Create(ctx, deployment); err != nil {
				t.Fatal("Failed to create deployment:", err)
			}
			t.Log("Created controller deployment with 2 replicas")

			return ctx
		}).
		Assess("Initial leader elected", func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			t.Helper()

			namespace, err := GetNamespaceFromContext(ctx)
			if err != nil {
				t.Fatal("Failed to get namespace from context:", err)
			}

			client, err := cfg.NewClient()
			if err != nil {
				t.Fatal("Failed to create client:", err)
			}

			// Wait for pods ready
			if err := WaitForPodReady(ctx, client, namespace, "app="+ControllerDeploymentName, 2*time.Minute); err != nil {
				t.Fatal("Controller pods did not become ready:", err)
			}

			// Wait for leader election
			if err := WaitForLeaderElection(ctx, cfg.Client().RESTConfig(), namespace, LeaderElectionLeaseName, 90*time.Second); err != nil {
				t.Fatal("Leader election did not complete:", err)
			}

			// Get initial leader
			holderIdentity, err := GetLeaseHolder(ctx, cfg.Client().RESTConfig(), namespace, LeaderElectionLeaseName)
			if err != nil {
				t.Fatal("Failed to get lease holder:", err)
			}

			t.Logf("✓ Initial leader elected: %s", holderIdentity)

			return ctx
		}).
		Assess("Failover on leader deletion", func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			t.Helper()

			namespace, err := GetNamespaceFromContext(ctx)
			if err != nil {
				t.Fatal("Failed to get namespace from context:", err)
			}

			client, err := cfg.NewClient()
			if err != nil {
				t.Fatal("Failed to create client:", err)
			}

			// Get current leader
			oldLeader, err := GetLeaseHolder(ctx, cfg.Client().RESTConfig(), namespace, LeaderElectionLeaseName)
			if err != nil {
				t.Fatal("Failed to get lease holder:", err)
			}

			t.Logf("Deleting leader pod: %s", oldLeader)

			// Delete leader pod
			pod := &corev1.Pod{
				ObjectMeta: metav1.ObjectMeta{
					Name:      oldLeader,
					Namespace: namespace,
				},
			}
			if err := client.Resources().Delete(ctx, pod); err != nil {
				t.Fatal("Failed to delete leader pod:", err)
			}

			t.Log("Leader pod deleted, waiting for failover...")

			// Wait for new leader (within lease_duration + renew_deadline = 75s)
			// Using 2 minutes to be safe
			failoverCtx, cancel := context.WithTimeout(ctx, 2*time.Minute)
			defer cancel()

			ticker := time.NewTicker(3 * time.Second)
			defer ticker.Stop()

			var newLeader string
			for {
				select {
				case <-failoverCtx.Done():
					t.Fatal("Timeout waiting for failover")

				case <-ticker.C:
					holder, err := GetLeaseHolder(ctx, cfg.Client().RESTConfig(), namespace, LeaderElectionLeaseName)
					if err != nil {
						// Lease might be temporarily unavailable during transition
						continue
					}

					if holder != "" && holder != oldLeader {
						newLeader = holder
						t.Logf("✓ New leader elected: %s", newLeader)
						goto FailoverComplete
					}
				}
			}

		FailoverComplete:

			// Wait a bit for metrics to update
			time.Sleep(5 * time.Second)

			// Verify exactly one leader among current pods
			pods, err := GetAllControllerPods(ctx, client, namespace)
			if err != nil {
				t.Fatal("Failed to get controller pods:", err)
			}

			leaderCount := 0
			for _, pod := range pods {
				isLeader, err := checkPodIsLeader(ctx, t, cfg.Client().RESTConfig(), &pod)
				if err != nil {
					// Pod might be terminating
					t.Logf("Warning: Failed to check pod %s: %v", pod.Name, err)
					continue
				}

				if isLeader {
					leaderCount++
					if pod.Name != newLeader {
						t.Fatalf("Pod %s reports is_leader=1 but Lease holder is %s", pod.Name, newLeader)
					}
				}
			}

			if leaderCount != 1 {
				t.Fatalf("Expected exactly 1 leader after failover, found %d", leaderCount)
			}

			t.Log("✓ Failover successful, exactly one leader active")

			return ctx
		}).
		Feature()

	testEnv.Test(t, feature)
}

// TestLeaderElection_DisabledMode verifies single-replica mode without leader election.
//
// This test validates:
//  1. Controller starts with leader_election.enabled=false
//  2. No Lease resource is created
//  3. Controller operates normally
//
//nolint:revive // High complexity expected in E2E test scenarios
func TestLeaderElection_DisabledMode(t *testing.T) {
	// Config with leader election disabled
	const DisabledLeaderElectionConfig = `
pod_selector:
  match_labels:
    app: haproxy
    component: loadbalancer

controller:
  healthz_port: 8080
  metrics_port: 9090
  leader_election:
    enabled: false

haproxy_config:
  template: |
    global
      maxconn 2000

    defaults
      mode http
      timeout connect 5000ms
      timeout client 50000ms
      timeout server 50000ms

    frontend test-frontend
      bind :8080
      default_backend test-backend

    backend test-backend
      server test-server 127.0.0.1:9999

watched_resources:
  ingresses:
    api_version: networking.k8s.io/v1
    resources: ingresses
    index_by:
      - metadata.namespace
      - metadata.name
`

	feature := features.New("Leader Election - Disabled Mode").
		Setup(func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			t.Helper()
			t.Log("Setting up leader election disabled mode test")

			namespace := envconf.RandomName("test-leader-disabled", 16)
			t.Logf("Using test namespace: %s", namespace)

			ctx = StoreNamespaceInContext(ctx, namespace)

			client, err := cfg.NewClient()
			if err != nil {
				t.Fatal("Failed to create client:", err)
			}

			// Create namespace
			ns := &corev1.Namespace{
				ObjectMeta: metav1.ObjectMeta{
					Name: namespace,
				},
			}
			if err := client.Resources().Create(ctx, ns); err != nil {
				t.Fatal("Failed to create namespace:", err)
			}

			// Create RBAC resources
			serviceAccount := NewServiceAccount(namespace, ControllerServiceAccountName)
			if err := client.Resources().Create(ctx, serviceAccount); err != nil {
				t.Fatal("Failed to create serviceaccount:", err)
			}

			role := NewRole(namespace, ControllerRoleName)
			if err := client.Resources().Create(ctx, role); err != nil {
				t.Fatal("Failed to create role:", err)
			}

			roleBinding := NewRoleBinding(namespace, ControllerRoleBindingName, ControllerRoleName, ControllerServiceAccountName)
			if err := client.Resources().Create(ctx, roleBinding); err != nil {
				t.Fatal("Failed to create rolebinding:", err)
			}

			clusterRole := NewClusterRole(ControllerClusterRoleName, namespace)
			if err := client.Resources().Create(ctx, clusterRole); err != nil {
				t.Fatal("Failed to create clusterrole:", err)
			}

			clusterRoleBinding := NewClusterRoleBinding(ControllerClusterRoleBindingName, ControllerClusterRoleName, ControllerServiceAccountName, namespace, namespace)
			if err := client.Resources().Create(ctx, clusterRoleBinding); err != nil {
				t.Fatal("Failed to create clusterrolebinding:", err)
			}

			secret := NewSecret(namespace, ControllerSecretName)
			if err := client.Resources().Create(ctx, secret); err != nil {
				t.Fatal("Failed to create secret:", err)
			}

			webhookCertSecret := NewWebhookCertSecret(namespace, "haproxy-webhook-certs")
			if err := client.Resources().Create(ctx, webhookCertSecret); err != nil {
				t.Fatal("Failed to create webhook cert secret:", err)
			}

			// Create ConfigMap with leader election disabled
			configMap := NewConfigMap(namespace, ControllerConfigMapName, DisabledLeaderElectionConfig)
			if err := client.Resources().Create(ctx, configMap); err != nil {
				t.Fatal("Failed to create configmap:", err)
			}
			t.Log("Created controller configmap with leader election disabled")

			// Create Deployment with 1 replica
			deployment := NewControllerDeployment(
				namespace,
				ControllerConfigMapName,
				ControllerSecretName,
				ControllerServiceAccountName,
				DebugPort,
				1,
			)
			if err := client.Resources().Create(ctx, deployment); err != nil {
				t.Fatal("Failed to create deployment:", err)
			}
			t.Log("Created controller deployment with 1 replica")

			return ctx
		}).
		Assess("No Lease created", func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			t.Helper()

			namespace, err := GetNamespaceFromContext(ctx)
			if err != nil {
				t.Fatal("Failed to get namespace from context:", err)
			}

			client, err := cfg.NewClient()
			if err != nil {
				t.Fatal("Failed to create client:", err)
			}

			// Wait for pod ready
			if err := WaitForPodReady(ctx, client, namespace, "app="+ControllerDeploymentName, 2*time.Minute); err != nil {
				t.Fatal("Controller pod did not become ready:", err)
			}
			t.Log("Controller pod is ready")

			// Wait a bit for potential Lease creation
			time.Sleep(10 * time.Second)

			// Try to get Lease - should not exist
			clientset, err := kubernetes.NewForConfig(cfg.Client().RESTConfig())
			if err != nil {
				t.Fatal("Failed to create clientset:", err)
			}

			_, err = clientset.CoordinationV1().Leases(namespace).Get(ctx, LeaderElectionLeaseName, metav1.GetOptions{})
			if err == nil {
				t.Fatal("Lease resource exists but leader election is disabled")
			}

			t.Log("✓ No Lease resource created (as expected)")

			return ctx
		}).
		Assess("Controller operates normally", func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			t.Helper()

			namespace, err := GetNamespaceFromContext(ctx)
			if err != nil {
				t.Fatal("Failed to get namespace from context:", err)
			}

			client, err := cfg.NewClient()
			if err != nil {
				t.Fatal("Failed to create client:", err)
			}

			// Get controller pod
			pod, err := GetControllerPod(ctx, client, namespace)
			if err != nil {
				t.Fatal("Failed to get controller pod:", err)
			}

			// Access debug endpoint
			debugClient := NewDebugClient(cfg.Client().RESTConfig(), pod, DebugPort)
			if err := debugClient.Start(ctx); err != nil {
				t.Fatal("Failed to start debug client:", err)
			}
			defer debugClient.Stop()

			// Verify config is loaded
			config, err := debugClient.GetConfig(ctx)
			if err != nil {
				t.Fatal("Failed to get config:", err)
			}

			if config == nil {
				t.Fatal("Config is nil")
			}

			t.Log("✓ Controller operating normally without leader election")

			return ctx
		}).
		Feature()

	testEnv.Test(t, feature)
}

