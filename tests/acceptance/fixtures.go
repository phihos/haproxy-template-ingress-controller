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
	"fmt"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	networkingv1 "k8s.io/api/networking/v1"
	rbacv1 "k8s.io/api/rbac/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"
)

// InitialConfigYAML is the initial controller configuration.
const InitialConfigYAML = `
pod_selector:
  match_labels:
    app: haproxy
    component: loadbalancer

controller:
  healthz_port: 8080
  metrics_port: 9090

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
    resources: ingresses
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

controller:
  healthz_port: 8080
  metrics_port: 9090

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
    resources: ingresses
    index_by:
      - metadata.namespace
      - metadata.name
`

// WebhookEnabledConfigYAML is the controller configuration with webhook validation enabled.
const WebhookEnabledConfigYAML = `
pod_selector:
  match_labels:
    app: haproxy
    component: loadbalancer

controller:
  healthz_port: 8080
  metrics_port: 9090

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
      {%- for ingress in resources.ingresses.List() %}
      {%- for rule in ingress.spec.rules %}
      {%- for path in rule.http.paths %}
      {%- if path.backend.service %}
      use_backend {% include "backend-name" %} if { path_beg {{ path.path }} }
      {%- endif %}
      {%- endfor %}
      {%- endfor %}
      {%- endfor %}
      default_backend test-backend

    {%- for ingress in resources.ingresses.List() %}
    {%- for rule in ingress.spec.rules %}
    {%- for path in rule.http.paths %}
    {%- if path.backend.service %}

    backend {% include "backend-name" %}
      {%- include "backend-annotation-haproxytech-auth" %}
      server test-server 127.0.0.1:8080
    {%- endif %}
    {%- endfor %}
    {%- endfor %}
    {%- endfor %}

    backend test-backend
      server test-server 127.0.0.1:9999

watched_resources:
  ingresses:
    api_version: networking.k8s.io/v1
    resources: ingresses
    enable_validation_webhook: true
    index_by:
      - metadata.namespace
      - metadata.name
  services:
    api_version: v1
    resources: services
    index_by:
      - metadata.namespace
      - metadata.name
  secrets:
    api_version: v1
    resources: secrets
    store: on-demand
    index_by:
      - metadata.namespace
      - metadata.name

template_snippets:
  backend-name:
    name: backend-name
    template: >-
      {{- " " -}}ing_{{ ingress.metadata.namespace }}_{{ ingress.metadata.name }}_{{ path.backend.service.name }}_{{ path.backend.service.port.name | default(path.backend.service.port.number) }}

  backend-annotation-haproxytech-auth:
    name: backend-annotation-haproxytech-auth
    priority: 500
    template: |
      {#- Generate http-request auth directives for backends requiring authentication #}
      {%- set auth_type = ingress.metadata.annotations["haproxy.org/auth-type"] | default("") %}
      {%- if auth_type == "basic-auth" %}
        {%- set auth_realm = ingress.metadata.annotations["haproxy.org/auth-realm"] | default("Protected") %}
      http-request auth realm "{{ auth_realm }}"
      {%- endif %}
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

// NewWebhookCertSecret creates a Secret with dummy TLS certificates for webhook testing.
// The certificates are self-signed and only used for controller startup - acceptance tests
// don't actually use the webhook endpoint.
func NewWebhookCertSecret(namespace, name string) *corev1.Secret {
	// Minimal self-signed certificate (valid for 10 years, CN=webhook)
	// Generated with: openssl req -x509 -newkey rsa:2048 -nodes -days 3650 -subj "/CN=webhook"
	cert := `-----BEGIN CERTIFICATE-----
MIIDCzCCAfOgAwIBAgIUFQ7xGq8VPvT8wF8nVqHt0TkGYCwwDQYJKoZIhvcNAQEL
BQAwFTETMBEGA1UEAwwKd2ViaG9vazEwMB4XDTI1MDEyNjAwMDAwMFoXDTM1MDEy
NDAwMDAwMFowFTETMBEGA1UEAwwKd2ViaG9vazEwMIIBIjANBgkqhkiG9w0BAQEF
AAOCAQ8AMIIBCgKCAQEAr8VQqLFfhkX2YJ4KGg9kPMYxGh2vH2xK3fY5N8nY8fXJ
eDGH8ZfX4V5YQj4C5H9xBjR7CJdN3jJ8WYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V
5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9x
H5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8
fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH
4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7Y
fC8VQwIDAQABo1MwUTAdBgNVHQ4EFgQU5Q9xH5C8fYqH4J7YfC8V5Q9xH5AwHwYD
VR0jBBgwFoAU5Q9xH5C8fYqH4J7YfC8V5Q9xH5AwDwYDVR0TAQH/BAUwAwEB/zAN
BgkqhkiG9w0BAQsFAAOCAQEAC8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5
C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fY
qH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J
7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC
8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q
9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5
C8fYqH4J7YfC8V5Q9xH5Cw==
-----END CERTIFICATE-----`

	key := `-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCvxVCosV+GRfZg
ngoad2Q8xjEaHa8fbErd9jk3ydjx9cl4MYfxl9fhXlhCPgLkf3EGNHsIl03eMnxZ
iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofg
nth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8
LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXl
D3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3Ef
kLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxVDAgMBAAEC
ggEAC8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5
C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fY
qH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J
7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC
8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q
9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5QQKBg
QDlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXl
D3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3Ef
kLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LwKBgQDBXlD3
EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3EfkL
x9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9io
fgnth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgQKBgC8V5Q9xH5C8fYqH4J7Y
fC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V
5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfC8V5Q9x
H5C8fYqH4J7YfC8V5Q9xH5C8fYqH4J7YfAoGBALx9iofgnth8LxXlD3EfkLx9iofg
nth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8
LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXl
D3EfkLx9iofgnth8LxXlBAoGAD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXl
D3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3Ef
kLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9iofgnth8LxXlD3EfkLx9
iofgnth8Lw==
-----END PRIVATE KEY-----`

	return &corev1.Secret{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
		},
		Data: map[string][]byte{
			"tls.crt": []byte(cert),
			"tls.key": []byte(key),
		},
		Type: corev1.SecretTypeTLS,
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

// NewClusterRole creates a ClusterRole with a unique name for test isolation.
// The name parameter is the base name, and namespace is appended to ensure uniqueness.
func NewClusterRole(name, namespace string) *rbacv1.ClusterRole {
	return &rbacv1.ClusterRole{
		ObjectMeta: metav1.ObjectMeta{
			Name: fmt.Sprintf("%s-%s", name, namespace),
			Labels: map[string]string{
				"app.kubernetes.io/name": ControllerDeploymentName,
				"test-namespace":         namespace,
			},
		},
		Rules: []rbacv1.PolicyRule{
			{
				APIGroups: []string{"networking.k8s.io"},
				Resources: []string{"ingresses"},
				Verbs:     []string{"get", "watch", "list"},
			},
			{
				APIGroups: []string{""},
				Resources: []string{"services", "secrets"},
				Verbs:     []string{"get", "watch", "list"},
			},
			{
				APIGroups: []string{"admissionregistration.k8s.io"},
				Resources: []string{"validatingwebhookconfigurations"},
				Verbs:     []string{"create", "update", "get", "list", "watch", "delete"},
			},
		},
	}
}

// NewClusterRoleBinding creates a ClusterRoleBinding with a unique name for test isolation.
// The name parameter is the base name, clusterRoleName is the base ClusterRole name,
// and testNamespace is appended to both to ensure uniqueness and proper references.
func NewClusterRoleBinding(name, clusterRoleName, serviceAccountName, serviceAccountNamespace, testNamespace string) *rbacv1.ClusterRoleBinding {
	return &rbacv1.ClusterRoleBinding{
		ObjectMeta: metav1.ObjectMeta{
			Name: fmt.Sprintf("%s-%s", name, testNamespace),
			Labels: map[string]string{
				"app.kubernetes.io/name": ControllerDeploymentName,
				"test-namespace":         testNamespace,
			},
		},
		RoleRef: rbacv1.RoleRef{
			APIGroup: "rbac.authorization.k8s.io",
			Kind:     "ClusterRole",
			Name:     fmt.Sprintf("%s-%s", clusterRoleName, testNamespace),
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
								{
									Name:  "WEBHOOK_SERVICE_NAME",
									Value: "haproxy-template-ic-webhook",
								},
							},
							Ports: []corev1.ContainerPort{
								{
									Name:          "debug",
									ContainerPort: debugPort,
									Protocol:      corev1.ProtocolTCP,
								},
								{
									Name:          "webhook",
									ContainerPort: 9443,
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

// NewWebhookService creates a Service for webhook endpoint.
// The service routes traffic from the Kubernetes API server to the controller's webhook server.
func NewWebhookService(namespace, serviceName string) *corev1.Service {
	return &corev1.Service{
		ObjectMeta: metav1.ObjectMeta{
			Name:      serviceName,
			Namespace: namespace,
			Labels: map[string]string{
				"app": ControllerDeploymentName,
			},
		},
		Spec: corev1.ServiceSpec{
			Type: corev1.ServiceTypeClusterIP,
			Ports: []corev1.ServicePort{
				{
					Name:       "webhook",
					Port:       443,
					TargetPort: intstr.FromInt(9443),
					Protocol:   corev1.ProtocolTCP,
				},
			},
			Selector: map[string]string{
				"app": ControllerDeploymentName,
			},
		},
	}
}

// NewValidIngress creates an Ingress with valid auth annotations.
// This Ingress should pass webhook validation.
func NewValidIngress(namespace, name string) *networkingv1.Ingress {
	pathType := networkingv1.PathTypePrefix

	return &networkingv1.Ingress{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
			Annotations: map[string]string{
				"haproxy.org/auth-type":  "basic-auth",
				"haproxy.org/auth-realm": "Protected", // Valid: no whitespace
			},
		},
		Spec: networkingv1.IngressSpec{
			Rules: []networkingv1.IngressRule{
				{
					Host: "example.com",
					IngressRuleValue: networkingv1.IngressRuleValue{
						HTTP: &networkingv1.HTTPIngressRuleValue{
							Paths: []networkingv1.HTTPIngressPath{
								{
									Path:     "/",
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
}

// NewInvalidIngress creates an Ingress with invalid auth annotations.
// This Ingress should be rejected by webhook validation because auth_realm contains whitespace.
func NewInvalidIngress(namespace, name string) *networkingv1.Ingress {
	pathType := networkingv1.PathTypePrefix

	return &networkingv1.Ingress{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
			Annotations: map[string]string{
				"haproxy.org/auth-type":  "basic-auth",
				"haproxy.org/auth-realm": "Invalid With Spaces", // Invalid: contains whitespace
			},
		},
		Spec: networkingv1.IngressSpec{
			Rules: []networkingv1.IngressRule{
				{
					Host: "example.com",
					IngressRuleValue: networkingv1.IngressRuleValue{
						HTTP: &networkingv1.HTTPIngressRuleValue{
							Paths: []networkingv1.HTTPIngressPath{
								{
									Path:     "/",
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
}
