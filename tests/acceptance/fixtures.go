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
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	rbacv1 "k8s.io/api/rbac/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// InitialConfigYAML is the initial controller configuration.
const InitialConfigYAML = `
pod_selector:
  match_labels:
    app: haproxy
    component: loadbalancer

haproxy_config:
  template: |
    global
      maxconn 2000
      # Initial config - version 1

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
    kind: Ingress
    index_by:
      - metadata.namespace
      - metadata.name
`

// UpdatedConfigYAML is the updated controller configuration.
const UpdatedConfigYAML = `
pod_selector:
  match_labels:
    app: haproxy
    component: loadbalancer

haproxy_config:
  template: |
    global
      maxconn 4000
      # Updated config - version 2

    defaults
      mode http
      timeout connect 10000ms
      timeout client 100000ms
      timeout server 100000ms

    frontend test-frontend
      bind :8080
      default_backend test-backend

    backend test-backend
      server test-server 127.0.0.1:9999

watched_resources:
  ingresses:
    api_version: networking.k8s.io/v1
    kind: Ingress
    index_by:
      - metadata.namespace
      - metadata.name
`

// NewConfigMap creates a ConfigMap with the given configuration.
func NewConfigMap(namespace, name, configYAML string) *corev1.ConfigMap {
	return &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
		},
		Data: map[string]string{
			"config": configYAML,
		},
	}
}

// NewSecret creates a Secret with HAProxy credentials.
func NewSecret(namespace, name string) *corev1.Secret {
	return &corev1.Secret{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
		},
		StringData: map[string]string{
			"dataplane_username": "admin",
			"dataplane_password": "password",
		},
	}
}

// NewServiceAccount creates a ServiceAccount for the controller.
func NewServiceAccount(namespace, name string) *corev1.ServiceAccount {
	return &corev1.ServiceAccount{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
		},
	}
}

// NewRole creates a Role with permissions for ConfigMaps, Secrets, Pods, and Ingresses.
func NewRole(namespace, name string) *rbacv1.Role {
	return &rbacv1.Role{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
		},
		Rules: []rbacv1.PolicyRule{
			{
				APIGroups: []string{""},
				Resources: []string{"configmaps"},
				Verbs:     []string{"get", "watch", "list"},
			},
			{
				APIGroups: []string{""},
				Resources: []string{"secrets"},
				Verbs:     []string{"get", "watch", "list"},
			},
			{
				APIGroups: []string{""},
				Resources: []string{"pods"},
				Verbs:     []string{"get", "watch", "list"},
			},
			{
				APIGroups: []string{"networking.k8s.io"},
				Resources: []string{"ingresses"},
				Verbs:     []string{"get", "watch", "list"},
			},
		},
	}
}

// NewRoleBinding creates a RoleBinding that binds the Role to the ServiceAccount.
func NewRoleBinding(namespace, name, roleName, serviceAccountName string) *rbacv1.RoleBinding {
	return &rbacv1.RoleBinding{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
		},
		RoleRef: rbacv1.RoleRef{
			APIGroup: "rbac.authorization.k8s.io",
			Kind:     "Role",
			Name:     roleName,
		},
		Subjects: []rbacv1.Subject{
			{
				Kind:      "ServiceAccount",
				Name:      serviceAccountName,
				Namespace: namespace,
			},
		},
	}
}

// NewClusterRole creates a ClusterRole with permissions for cluster-wide resource watching.
func NewClusterRole(name string) *rbacv1.ClusterRole {
	return &rbacv1.ClusterRole{
		ObjectMeta: metav1.ObjectMeta{
			Name: name,
		},
		Rules: []rbacv1.PolicyRule{
			{
				APIGroups: []string{"networking.k8s.io"},
				Resources: []string{"ingresses"},
				Verbs:     []string{"get", "watch", "list"},
			},
		},
	}
}

// NewClusterRoleBinding creates a ClusterRoleBinding that binds the ClusterRole to the ServiceAccount.
func NewClusterRoleBinding(name, clusterRoleName, serviceAccountName, serviceAccountNamespace string) *rbacv1.ClusterRoleBinding {
	return &rbacv1.ClusterRoleBinding{
		ObjectMeta: metav1.ObjectMeta{
			Name: name,
		},
		RoleRef: rbacv1.RoleRef{
			APIGroup: "rbac.authorization.k8s.io",
			Kind:     "ClusterRole",
			Name:     clusterRoleName,
		},
		Subjects: []rbacv1.Subject{
			{
				Kind:      "ServiceAccount",
				Name:      serviceAccountName,
				Namespace: serviceAccountNamespace,
			},
		},
	}
}

// NewControllerDeployment creates a controller deployment.
func NewControllerDeployment(namespace, configMapName, secretName, serviceAccountName string, debugPort int32) *appsv1.Deployment {
	replicas := int32(1)

	return &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      ControllerDeploymentName,
			Namespace: namespace,
			Labels: map[string]string{
				"app": ControllerDeploymentName,
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: &replicas,
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{
					"app": ControllerDeploymentName,
				},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{
						"app": ControllerDeploymentName,
					},
				},
				Spec: corev1.PodSpec{
					ServiceAccountName: serviceAccountName,
					Containers: []corev1.Container{
						{
							Name:  "controller",
							Image: "haproxy-template-ic:test",
							Env: []corev1.EnvVar{
								{
									Name:  "CONFIGMAP_NAME",
									Value: configMapName,
								},
								{
									Name:  "SECRET_NAME",
									Value: secretName,
								},
								{
									Name:  "DEBUG_PORT",
									Value: "6060",
								},
								{
									Name:  "VERBOSE",
									Value: "2", // DEBUG level
								},
							},
							Ports: []corev1.ContainerPort{
								{
									Name:          "debug",
									ContainerPort: debugPort,
									Protocol:      corev1.ProtocolTCP,
								},
							},
						},
					},
				},
			},
		},
	}
}
