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

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"sigs.k8s.io/e2e-framework/pkg/envconf"
	"sigs.k8s.io/e2e-framework/pkg/features"

	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

const (
	// WebhookServiceName is the name of the webhook service
	WebhookServiceName = "haproxy-template-ic-webhook"

	// WebhookConfigName is the name of the ValidatingWebhookConfiguration
	WebhookConfigName = "haproxy-template-ic-webhook"
)

// TestWebhookValidation verifies that the webhook validation correctly accepts valid
// Ingress resources and rejects invalid ones.
//
// This is an acceptance test for the Phase 3 webhook validation feature, which performs
// full dry-run reconciliation (render + validate) before admitting resources to the cluster.
//
// Test flow:
//  1. Deploy controller with webhook enabled
//  2. Wait for webhook configuration to be created
//  3. Create valid Ingress - should succeed
//  4. Attempt to create invalid Ingress - should be rejected with descriptive error
//  5. Attempt to update valid Ingress with invalid values - should be rejected
//
//nolint:revive // High complexity expected in E2E test scenarios
func TestWebhookValidation(t *testing.T) {
	feature := features.New("Webhook Validation").
		Setup(func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			t.Helper()
			t.Log("Setting up webhook validation test")

			// Generate unique namespace for this test
			namespace := envconf.RandomName("webhook-test", 16)
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

			// Create Role with ConfigMap, Secret, and Pod permissions
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

			// Create ClusterRole for cluster-wide Ingress watching and webhook management (unique per test)
			clusterRole := NewClusterRole(ControllerClusterRoleName, namespace)
			if err := client.Resources().Create(ctx, clusterRole); err != nil {
				t.Fatal("Failed to create clusterrole:", err)
			}
			t.Log("Created controller clusterrole with webhook permissions")

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

			// Create controller ConfigMap with webhook-enabled configuration
			configMap := NewConfigMap(namespace, ControllerConfigMapName, WebhookEnabledConfigYAML)
			if err := client.Resources().Create(ctx, configMap); err != nil {
				t.Fatal("Failed to create configmap:", err)
			}
			t.Log("Created controller configmap with webhook enabled")

			// Create webhook Service
			webhookService := NewWebhookService(namespace, WebhookServiceName)
			if err := client.Resources().Create(ctx, webhookService); err != nil {
				t.Fatal("Failed to create webhook service:", err)
			}
			t.Log("Created webhook service")

			// Create controller Deployment
			deployment := NewControllerDeployment(
				namespace,
				ControllerConfigMapName,
				ControllerSecretName,
				ControllerServiceAccountName,
				DebugPort,
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

			// Wait for ValidatingWebhookConfiguration to be created
			t.Log("Waiting for ValidatingWebhookConfiguration to be created...")
			if err := WaitForWebhookConfiguration(ctx, cfg.Client().RESTConfig(), WebhookConfigName, 1*time.Minute); err != nil {
				// Dump controller logs for debugging
				t.Log("ValidatingWebhookConfiguration was not created, dumping controller logs for debugging...")
				pod, podErr := GetControllerPod(ctx, client, namespace)
				if podErr == nil {
					DumpPodLogs(ctx, t, cfg.Client().RESTConfig(), pod)
				}
				t.Fatal("ValidatingWebhookConfiguration was not created:", err)
			}
			t.Log("ValidatingWebhookConfiguration is ready")

			// Give webhook server a moment to fully start
			time.Sleep(5 * time.Second)

			return ctx
		}).
		Assess("Valid Ingress is accepted", func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			t.Helper()
			t.Log("Testing that valid Ingress is accepted by webhook")

			// Retrieve namespace from context
			namespace, err := GetNamespaceFromContext(ctx)
			if err != nil {
				t.Fatal("Failed to get namespace from context:", err)
			}

			client, err := cfg.NewClient()
			if err != nil {
				t.Fatal("Failed to create client:", err)
			}

			// Create valid Ingress
			validIngress := NewValidIngress(namespace, "valid-ingress")
			err = client.Resources().Create(ctx, validIngress)

			// Should succeed
			if err != nil {
				t.Fatalf("Valid Ingress was rejected: %v", err)
			}

			t.Log("✓ Valid Ingress was accepted")

			// Verify Ingress exists in cluster
			var retrievedIngress = NewValidIngress(namespace, "valid-ingress")
			err = client.Resources().Get(ctx, "valid-ingress", namespace, retrievedIngress)
			require.NoError(t, err, "Failed to retrieve created Ingress")

			t.Log("✓ Valid Ingress exists in cluster")

			return ctx
		}).
		Assess("Invalid Ingress is rejected on CREATE", func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			t.Helper()
			t.Log("Testing that invalid Ingress is rejected on CREATE")

			// Retrieve namespace from context
			namespace, err := GetNamespaceFromContext(ctx)
			if err != nil {
				t.Fatal("Failed to get namespace from context:", err)
			}

			client, err := cfg.NewClient()
			if err != nil {
				t.Fatal("Failed to create client:", err)
			}

			// Attempt to create invalid Ingress
			invalidIngress := NewInvalidIngress(namespace, "invalid-ingress")
			err = client.Resources().Create(ctx, invalidIngress)

			// Should fail
			require.Error(t, err, "Invalid Ingress was accepted (should have been rejected)")

			// Verify error message contains expected keywords
			errMsg := err.Error()
			t.Logf("Rejection error: %s", errMsg)

			// Check for webhook rejection indicators
			assert.Contains(t, errMsg, "admission webhook", "Error should mention admission webhook")
			assert.Contains(t, errMsg, "denied the request", "Error should indicate request was denied")

			// Check for validation failure details
			assert.Contains(t, errMsg, "validation failed", "Error should mention validation failure")
			assert.Contains(t, errMsg, "auth_realm", "Error should mention the problematic field")

			t.Log("✓ Invalid Ingress was rejected with descriptive error")

			// Verify Ingress does NOT exist in cluster
			var retrievedIngress = NewInvalidIngress(namespace, "invalid-ingress")
			err = client.Resources().Get(ctx, "invalid-ingress", namespace, retrievedIngress)
			assert.True(t, apierrors.IsNotFound(err), "Invalid Ingress should not exist in cluster")

			t.Log("✓ Invalid Ingress was not created in cluster")

			return ctx
		}).
		Assess("Invalid Ingress is rejected on UPDATE", func(ctx context.Context, t *testing.T, cfg *envconf.Config) context.Context {
			t.Helper()
			t.Log("Testing that invalid Ingress is rejected on UPDATE")

			// Retrieve namespace from context
			namespace, err := GetNamespaceFromContext(ctx)
			if err != nil {
				t.Fatal("Failed to get namespace from context:", err)
			}

			client, err := cfg.NewClient()
			if err != nil {
				t.Fatal("Failed to create client:", err)
			}

			// Get the valid Ingress created in the first Assess
			validIngress := NewValidIngress(namespace, "valid-ingress")
			err = client.Resources().Get(ctx, "valid-ingress", namespace, validIngress)
			require.NoError(t, err, "Failed to retrieve valid Ingress")

			// Attempt to update with invalid annotation
			t.Logf("Before update - annotations: %v", validIngress.Annotations)
			t.Logf("Before update - generation: %d", validIngress.Generation)
			originalAnnotations := make(map[string]string)
			for k, v := range validIngress.Annotations {
				originalAnnotations[k] = v
			}

			validIngress.Annotations["haproxy.org/auth-realm"] = "Invalid With Spaces"
			t.Logf("After modification - annotations: %v", validIngress.Annotations)
			t.Logf("Ingress resourceVersion: %s, generation: %d", validIngress.ResourceVersion, validIngress.Generation)

			// Verify the annotation actually changed
			if originalAnnotations["haproxy.org/auth-realm"] == validIngress.Annotations["haproxy.org/auth-realm"] {
				t.Fatal("Annotation was not modified - test setup issue!")
			}

			err = client.Resources().Update(ctx, validIngress)
			t.Logf("Update result - error: %v", err)

			// Should fail
			require.Error(t, err, "Invalid Ingress update was accepted (should have been rejected)")

			// Verify error message contains expected keywords
			errMsg := err.Error()
			t.Logf("Update rejection error: %s", errMsg)

			// Check for webhook rejection indicators
			assert.Contains(t, errMsg, "admission webhook", "Error should mention admission webhook")

			// Some webhook rejections may use "denied" or just show the validation error
			hasRejectionKeyword := strings.Contains(errMsg, "denied") ||
				strings.Contains(errMsg, "validation failed") ||
				strings.Contains(errMsg, "configuration validation failed")
			assert.True(t, hasRejectionKeyword, "Error should indicate validation failure")

			t.Log("✓ Invalid Ingress update was rejected")

			// Verify Ingress still has valid annotation value
			var retrievedIngress = NewValidIngress(namespace, "valid-ingress")
			err = client.Resources().Get(ctx, "valid-ingress", namespace, retrievedIngress)
			require.NoError(t, err, "Failed to retrieve Ingress after update attempt")

			// Original value should be preserved
			assert.Equal(t, "Protected", retrievedIngress.Annotations["haproxy.org/auth-realm"],
				"Ingress annotation should still have valid value")

			t.Log("✓ Ingress retained valid configuration")

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

			// Delete valid Ingress (if it exists)
			validIngress := NewValidIngress(namespace, "valid-ingress")
			if err := client.Resources().Delete(ctx, validIngress); err != nil && !apierrors.IsNotFound(err) {
				t.Log("Warning: failed to delete valid ingress:", err)
			}

			// Delete webhook service
			webhookService := NewWebhookService(namespace, WebhookServiceName)
			if err := client.Resources().Delete(ctx, webhookService); err != nil && !apierrors.IsNotFound(err) {
				t.Log("Warning: failed to delete webhook service:", err)
			}

			// Delete deployment
			deployment := NewControllerDeployment(namespace, ControllerConfigMapName, ControllerSecretName, ControllerServiceAccountName, DebugPort)
			if err := client.Resources().Delete(ctx, deployment); err != nil && !apierrors.IsNotFound(err) {
				t.Log("Warning: failed to delete deployment:", err)
			}

			// Delete configmap
			configMap := NewConfigMap(namespace, ControllerConfigMapName, "")
			if err := client.Resources().Delete(ctx, configMap); err != nil && !apierrors.IsNotFound(err) {
				t.Log("Warning: failed to delete configmap:", err)
			}

			// Delete secret
			secret := NewSecret(namespace, ControllerSecretName)
			if err := client.Resources().Delete(ctx, secret); err != nil && !apierrors.IsNotFound(err) {
				t.Log("Warning: failed to delete secret:", err)
			}

			// Delete rolebinding
			roleBinding := NewRoleBinding(namespace, ControllerRoleBindingName, ControllerRoleName, ControllerServiceAccountName)
			if err := client.Resources().Delete(ctx, roleBinding); err != nil && !apierrors.IsNotFound(err) {
				t.Log("Warning: failed to delete rolebinding:", err)
			}

			// Delete role
			role := NewRole(namespace, ControllerRoleName)
			if err := client.Resources().Delete(ctx, role); err != nil && !apierrors.IsNotFound(err) {
				t.Log("Warning: failed to delete role:", err)
			}

			// Delete serviceaccount
			serviceAccount := NewServiceAccount(namespace, ControllerServiceAccountName)
			if err := client.Resources().Delete(ctx, serviceAccount); err != nil && !apierrors.IsNotFound(err) {
				t.Log("Warning: failed to delete serviceaccount:", err)
			}

			// Delete clusterrolebinding (unique per test)
			clusterRoleBinding := NewClusterRoleBinding(ControllerClusterRoleBindingName, ControllerClusterRoleName, ControllerServiceAccountName, namespace, namespace)
			if err := client.Resources().Delete(ctx, clusterRoleBinding); err != nil && !apierrors.IsNotFound(err) {
				t.Log("Warning: failed to delete clusterrolebinding:", err)
			}

			// Delete clusterrole (unique per test)
			clusterRole := NewClusterRole(ControllerClusterRoleName, namespace)
			if err := client.Resources().Delete(ctx, clusterRole); err != nil && !apierrors.IsNotFound(err) {
				t.Log("Warning: failed to delete clusterrole:", err)
			}

			// Delete namespace
			ns := &corev1.Namespace{
				ObjectMeta: metav1.ObjectMeta{
					Name: namespace,
				},
			}
			if err := client.Resources().Delete(ctx, ns); err != nil && !apierrors.IsNotFound(err) {
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
