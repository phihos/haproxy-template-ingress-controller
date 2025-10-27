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
	"strings"
	"testing"
	"time"

	"sigs.k8s.io/e2e-framework/pkg/envconf"
	"sigs.k8s.io/e2e-framework/pkg/features"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// TestConfigMapReload verifies that the controller detects and applies ConfigMap changes.
//
// This is a regression test for the bug where ConfigMap changes did not trigger
// application reload, causing the controller to continue using stale configuration.
//
// Test flow:
//  1. Deploy controller with initial configuration (maxconn 2000)
//  2. Wait for controller to start and load initial config
//  3. Verify initial config is loaded via debug endpoint
//  4. Update ConfigMap with new configuration (maxconn 4000)
//  5. Wait for controller to detect change and reload
//  6. Verify updated config is loaded via debug endpoint
//  7. Verify rendered HAProxy config contains updated values
//
//nolint:revive // High complexity expected in E2E test scenarios
func TestConfigMapReload(t *testing.T) {
	feature := features.New("ConfigMap Reload").
		Setup(func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			t.Helper()
			t.Log("Setting up ConfigMap reload test")

			// Generate unique namespace for this test
			namespace := envconf.RandomName("acceptance", 16)
			t.Logf("Using test namespace: %s", namespace)

			// Store namespace in context for use in Assess and Teardown
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

			// Create ServiceAccount for controller
			serviceAccount := NewServiceAccount(namespace, ControllerServiceAccountName)
			if err := client.Resources().Create(ctx, serviceAccount); err != nil {
				t.Fatal("Failed to create serviceaccount:", err)
			}
			t.Log("Created controller serviceaccount")

			// Create Role with ConfigMap and Secret permissions
			role := NewRole(namespace, ControllerRoleName)
			if err := client.Resources().Create(ctx, role); err != nil {
				t.Fatal("Failed to create role:", err)
			}
			t.Log("Created controller role")

			// Create RoleBinding
			roleBinding := NewRoleBinding(namespace, ControllerRoleBindingName, ControllerRoleName, ControllerServiceAccountName)
			if err := client.Resources().Create(ctx, roleBinding); err != nil {
				t.Fatal("Failed to create rolebinding:", err)
			}
			t.Log("Created controller rolebinding")

			// Create ClusterRole for cluster-wide Ingress watching (unique per test)
			clusterRole := NewClusterRole(ControllerClusterRoleName, namespace)
			if err := client.Resources().Create(ctx, clusterRole); err != nil {
				t.Fatal("Failed to create clusterrole:", err)
			}
			t.Log("Created controller clusterrole")

			// Create ClusterRoleBinding (unique per test)
			clusterRoleBinding := NewClusterRoleBinding(ControllerClusterRoleBindingName, ControllerClusterRoleName, ControllerServiceAccountName, namespace, namespace)
			if err := client.Resources().Create(ctx, clusterRoleBinding); err != nil {
				t.Fatal("Failed to create clusterrolebinding:", err)
			}
			t.Log("Created controller clusterrolebinding")

			// Create controller Secret
			secret := NewSecret(namespace, ControllerSecretName)
			if err := client.Resources().Create(ctx, secret); err != nil {
				t.Fatal("Failed to create secret:", err)
			}
			t.Log("Created controller secret")

			// Create webhook certificate Secret
			webhookCertSecret := NewWebhookCertSecret(namespace, "haproxy-webhook-certs")
			if err := client.Resources().Create(ctx, webhookCertSecret); err != nil {
				t.Fatal("Failed to create webhook cert secret:", err)
			}
			t.Log("Created webhook certificate secret")

			// Create controller ConfigMap with initial configuration
			configMap := NewConfigMap(namespace, ControllerConfigMapName, InitialConfigYAML)
			if err := client.Resources().Create(ctx, configMap); err != nil {
				t.Fatal("Failed to create configmap:", err)
			}
			t.Log("Created controller configmap with initial config (maxconn 2000)")

			// Create controller Deployment
			deployment := NewControllerDeployment(
				namespace,
				ControllerConfigMapName,
				ControllerSecretName,
				ControllerServiceAccountName,
				DebugPort,
				1, // Single replica for this test
			)
			if err := client.Resources().Create(ctx, deployment); err != nil {
				t.Fatal("Failed to create deployment:", err)
			}
			t.Log("Created controller deployment")

			// Wait for controller pod to be ready
			t.Log("Waiting for controller pod to be ready...")
			if err := WaitForPodReady(ctx, client, namespace, "app="+ControllerDeploymentName, 2*time.Minute); err != nil {
				t.Fatal("Controller pod did not become ready:", err)
			}
			t.Log("Controller pod is ready")

			return ctx
		}).
		Assess("Initial config loaded", func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			t.Helper()
			t.Log("Verifying initial configuration is loaded")

			// Retrieve namespace from context
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

			// Capture pod logs if test fails
			defer func() {
				if t.Failed() {
					t.Log("Test failed, dumping controller pod logs...")
					// Use a fresh context with timeout for log capture
					logCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
					defer cancel()
					DumpPodLogs(logCtx, t, cfg.Client().RESTConfig(), pod)
				}
			}()

			// Create debug client with port-forward
			debugClient := NewDebugClient(cfg.Client().RESTConfig(), pod, DebugPort)
			if err := debugClient.Start(ctx); err != nil {
				t.Fatal("Failed to start debug client:", err)
			}
			defer debugClient.Stop()

			t.Log("Port-forward established to debug server")

			// Wait for initial config to be loaded (with timeout)
			// Use a separate variable to avoid shadowing the original context
			timeoutCtx, cancel := context.WithTimeout(ctx, 30*time.Second)
			defer cancel()

			var config map[string]interface{}
			ticker := time.NewTicker(2 * time.Second)
			defer ticker.Stop()

			for {
				select {
				case <-timeoutCtx.Done():
					t.Fatal("Timeout waiting for initial config to load")

				case <-ticker.C:
					config, err = debugClient.GetConfig(timeoutCtx)
					if err != nil {
						t.Log("Waiting for config (retry):", err)
						continue
					}

					// Config loaded successfully
					t.Log("Initial config loaded successfully")
					goto ConfigLoaded
				}
			}

		ConfigLoaded:
			// Verify initial config contains expected values
			configData, ok := config["config"].(map[string]interface{})
			if !ok {
				t.Fatal("Config data not found in response")
			}

			// Access HAProxyConfig.Template field (uses Go field names, not YAML tags)
			haproxyConfig, ok := configData["HAProxyConfig"].(map[string]interface{})
			if !ok {
				t.Fatal("HAProxyConfig not found in config")
			}

			mainTemplate, ok := haproxyConfig["Template"].(string)
			if !ok {
				t.Fatal("Template not found in HAProxyConfig")
			}

			if !strings.Contains(mainTemplate, "maxconn 2000") {
				t.Fatalf("Initial config does not contain 'maxconn 2000': %s", mainTemplate)
			}

			if !strings.Contains(mainTemplate, "version 1") {
				t.Fatalf("Initial config does not contain 'version 1': %s", mainTemplate)
			}

			t.Log("✓ Initial config verified: maxconn 2000, version 1")

			return ctx
		}).
		Assess("ConfigMap update triggers reload", func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			t.Helper()
			t.Log("Updating ConfigMap with new configuration")

			// Retrieve namespace from context
			namespace, err := GetNamespaceFromContext(ctx)
			if err != nil {
				t.Fatal("Failed to get namespace from context:", err)
			}

			client, err := cfg.NewClient()
			if err != nil {
				t.Fatal("Failed to create client:", err)
			}

			// Get existing ConfigMap
			var configMap corev1.ConfigMap
			if err := client.Resources().Get(ctx, ControllerConfigMapName, namespace, &configMap); err != nil {
				t.Fatal("Failed to get configmap:", err)
			}

			// Update ConfigMap with new configuration
			configMap.Data["config"] = UpdatedConfigYAML
			if err := client.Resources().Update(ctx, &configMap); err != nil {
				t.Fatal("Failed to update configmap:", err)
			}

			t.Log("ConfigMap updated with new config (maxconn 4000)")

			// Get controller pod for debug client
			pod, err := GetControllerPod(ctx, client, namespace)
			if err != nil {
				t.Fatal("Failed to get controller pod:", err)
			}

			// Create debug client with port-forward
			debugClient := NewDebugClient(cfg.Client().RESTConfig(), pod, DebugPort)
			if err := debugClient.Start(ctx); err != nil {
				t.Fatal("Failed to start debug client:", err)
			}
			defer debugClient.Stop()

			t.Log("Port-forward established to debug server")

			// Wait for updated config to be loaded (controller should detect change and reload)
			t.Log("Waiting for controller to detect ConfigMap change and reload...")

			// Use a separate variable to avoid shadowing the original context
			timeoutCtx, cancel := context.WithTimeout(ctx, 60*time.Second)
			defer cancel()

			ticker := time.NewTicker(2 * time.Second)
			defer ticker.Stop()

			for {
				select {
				case <-timeoutCtx.Done():
					// Dump pod logs for debugging
					t.Log("Dumping controller pod logs for debugging...")
					DumpPodLogs(ctx, t, cfg.Client().RESTConfig(), pod)
					t.Fatal("Timeout waiting for config reload - ConfigMap change was not detected!")

				case <-ticker.C:
					config, err := debugClient.GetConfig(timeoutCtx)
					if err != nil {
						t.Log("Waiting for updated config (retry):", err)
						continue
					}

					// Check if config has been updated
					configData, ok := config["config"].(map[string]interface{})
					if !ok {
						continue
					}

					// Access HAProxyConfig.Template field (uses Go field names, not YAML tags)
					haproxyConfig, ok := configData["HAProxyConfig"].(map[string]interface{})
					if !ok {
						continue
					}

					mainTemplate, ok := haproxyConfig["Template"].(string)
					if !ok {
						continue
					}

					// Check for updated values
					if strings.Contains(mainTemplate, "maxconn 4000") && strings.Contains(mainTemplate, "version 2") {
						t.Log("✓ Updated config detected: maxconn 4000, version 2")
						goto ReloadComplete
					}

					t.Log("Still waiting for updated config...")
				}
			}

		ReloadComplete:
			t.Log("✓ ConfigMap reload successful!")

			return ctx
		}).
		Assess("Rendered config contains updated values", func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			t.Helper()
			t.Log("Verifying rendered HAProxy config contains updated values")

			// Retrieve namespace from context
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

			// Create debug client
			debugClient := NewDebugClient(cfg.Client().RESTConfig(), pod, DebugPort)
			if err := debugClient.Start(ctx); err != nil {
				t.Fatal("Failed to start debug client:", err)
			}
			defer debugClient.Stop()

			// Get rendered config
			rendered, err := debugClient.GetRenderedConfig(ctx)
			if err != nil {
				t.Fatal("Failed to get rendered config:", err)
			}

			// Verify rendered config contains updated values
			if !strings.Contains(rendered, "maxconn 4000") {
				t.Fatalf("Rendered config does not contain 'maxconn 4000': %s", rendered)
			}

			if !strings.Contains(rendered, "version 2") {
				t.Fatalf("Rendered config does not contain 'version 2': %s", rendered)
			}

			t.Log("✓ Rendered config verified: contains updated values from new ConfigMap")

			return ctx
		}).
		Teardown(func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			t.Helper()
			t.Log("Cleaning up test resources")

			// Retrieve namespace from context
			namespace, err := GetNamespaceFromContext(ctx)
			if err != nil {
				t.Log("Warning: failed to get namespace from context:", err)
				return ctx
			}

			client, err := cfg.NewClient()
			if err != nil {
				t.Log("Warning: failed to create client for cleanup:", err)
				return ctx
			}

			// Delete deployment
			deployment := NewControllerDeployment(namespace, ControllerConfigMapName, ControllerSecretName, ControllerServiceAccountName, DebugPort, 1)
			if err := client.Resources().Delete(ctx, deployment); err != nil {
				t.Log("Warning: failed to delete deployment:", err)
			}

			// Delete configmap
			configMap := NewConfigMap(namespace, ControllerConfigMapName, "")
			if err := client.Resources().Delete(ctx, configMap); err != nil {
				t.Log("Warning: failed to delete configmap:", err)
			}

			// Delete secret
			secret := NewSecret(namespace, ControllerSecretName)
			if err := client.Resources().Delete(ctx, secret); err != nil {
				t.Log("Warning: failed to delete secret:", err)
			}

			// Delete rolebinding
			roleBinding := NewRoleBinding(namespace, ControllerRoleBindingName, ControllerRoleName, ControllerServiceAccountName)
			if err := client.Resources().Delete(ctx, roleBinding); err != nil {
				t.Log("Warning: failed to delete rolebinding:", err)
			}

			// Delete role
			role := NewRole(namespace, ControllerRoleName)
			if err := client.Resources().Delete(ctx, role); err != nil {
				t.Log("Warning: failed to delete role:", err)
			}

			// Delete serviceaccount
			serviceAccount := NewServiceAccount(namespace, ControllerServiceAccountName)
			if err := client.Resources().Delete(ctx, serviceAccount); err != nil {
				t.Log("Warning: failed to delete serviceaccount:", err)
			}

			// Delete clusterrolebinding (unique per test)
			clusterRoleBinding := NewClusterRoleBinding(ControllerClusterRoleBindingName, ControllerClusterRoleName, ControllerServiceAccountName, namespace, namespace)
			if err := client.Resources().Delete(ctx, clusterRoleBinding); err != nil {
				t.Log("Warning: failed to delete clusterrolebinding:", err)
			}

			// Delete clusterrole (unique per test)
			clusterRole := NewClusterRole(ControllerClusterRoleName, namespace)
			if err := client.Resources().Delete(ctx, clusterRole); err != nil {
				t.Log("Warning: failed to delete clusterrole:", err)
			}

			// Delete namespace
			ns := &corev1.Namespace{
				ObjectMeta: metav1.ObjectMeta{
					Name: namespace,
				},
			}
			if err := client.Resources().Delete(ctx, ns); err != nil {
				t.Log("Warning: failed to delete namespace:", err)
			} else {
				t.Logf("Deleted test namespace: %s", namespace)
			}

			t.Log("Test cleanup complete")
			return ctx
		}).
		Feature()

	testEnv.Test(t, feature)
}
