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

// Package acceptance provides acceptance tests for the HAProxy Template Ingress Controller.
//
// These tests run against a real Kubernetes cluster (kind) and verify end-to-end behavior
// including configuration reloading, template rendering, and HAProxy deployment.
package acceptance

import (
	"context"
	"fmt"
	"io"
	"testing"
	"time"

	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"sigs.k8s.io/e2e-framework/klient"
	"sigs.k8s.io/e2e-framework/klient/k8s/resources"
	"sigs.k8s.io/e2e-framework/pkg/env"

	corev1 "k8s.io/api/core/v1"
)

const (
	// TestNamespace is the namespace where test resources are created.
	TestNamespace = "haproxy-test"

	// ControllerDeploymentName is the name of the controller deployment.
	ControllerDeploymentName = "haproxy-template-ic"

	// ControllerConfigMapName is the name of the controller configuration ConfigMap.
	ControllerConfigMapName = "haproxy-config"

	// ControllerSecretName is the name of the controller credentials Secret.
	//nolint:gosec // G101: This is a Kubernetes Secret name, not actual credentials
	ControllerSecretName = "haproxy-credentials"

	// ControllerServiceAccountName is the name of the controller ServiceAccount.
	ControllerServiceAccountName = "haproxy-template-ic"

	// ControllerRoleName is the name of the controller Role.
	ControllerRoleName = "haproxy-template-ic"

	// ControllerRoleBindingName is the name of the controller RoleBinding.
	ControllerRoleBindingName = "haproxy-template-ic"

	// ControllerClusterRoleName is the name of the controller ClusterRole.
	ControllerClusterRoleName = "haproxy-template-ic"

	// ControllerClusterRoleBindingName is the name of the controller ClusterRoleBinding.
	ControllerClusterRoleBindingName = "haproxy-template-ic"

	// DebugPort is the port for the debug HTTP server.
	DebugPort = 6060

	// DefaultTimeout for operations.
	DefaultTimeout = 2 * time.Minute
)

var (
	// testEnv is the shared test environment.
	testEnv env.Environment
)


// WaitForPodReady waits for a pod matching the label selector to be ready.
func WaitForPodReady(ctx context.Context, client klient.Client, namespace, labelSelector string, timeout time.Duration) error {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return fmt.Errorf("timeout waiting for pod to be ready")

		case <-ticker.C:
			var podList corev1.PodList
			res := client.Resources(namespace)

			// List pods with label selector
			if err := res.List(ctx, &podList, resources.WithLabelSelector(labelSelector)); err != nil {
				continue
			}

			// Check if any pod is ready
			for i := range podList.Items {
				pod := &podList.Items[i]
				for _, condition := range pod.Status.Conditions {
					if condition.Type == corev1.PodReady && condition.Status == corev1.ConditionTrue {
						return nil
					}
				}
			}
		}
	}
}

// GetControllerPod returns the controller pod.
func GetControllerPod(ctx context.Context, client klient.Client, namespace string) (*corev1.Pod, error) {
	var podList corev1.PodList
	res := client.Resources(namespace)
	if err := res.List(ctx, &podList, resources.WithLabelSelector("app="+ControllerDeploymentName)); err != nil {
		return nil, fmt.Errorf("failed to list pods: %w", err)
	}

	if len(podList.Items) == 0 {
		return nil, fmt.Errorf("no controller pods found")
	}

	return &podList.Items[0], nil
}

// DumpPodLogs captures and prints pod logs to test output.
// This is useful for debugging test failures by providing visibility into what
// happened inside the pod.
func DumpPodLogs(ctx context.Context, t *testing.T, restConfig *rest.Config, pod *corev1.Pod) {
	t.Helper()

	// Create Kubernetes clientset
	clientset, err := kubernetes.NewForConfig(restConfig)
	if err != nil {
		t.Logf("Failed to create Kubernetes clientset for log capture: %v", err)
		return
	}

	t.Logf("=== Pod %s/%s logs ===", pod.Namespace, pod.Name)

	// Capture logs for each container in the pod
	for _, container := range pod.Spec.Containers {
		t.Logf("--- Container: %s ---", container.Name)

		// Get pod logs
		podLogOpts := corev1.PodLogOptions{
			Container: container.Name,
		}

		req := clientset.CoreV1().Pods(pod.Namespace).GetLogs(pod.Name, &podLogOpts)
		podLogs, err := req.Stream(ctx)
		if err != nil {
			t.Logf("Error getting logs for container %s: %v", container.Name, err)
			continue
		}
		defer podLogs.Close()

		// Read and print logs
		buf := make([]byte, 2048)
		for {
			n, err := podLogs.Read(buf)
			if n > 0 {
				t.Logf("%s", string(buf[:n]))
			}
			if err == io.EOF {
				break
			}
			if err != nil {
				t.Logf("Error reading logs: %v", err)
				break
			}
		}
	}

	t.Logf("=== End of pod logs ===")
}
