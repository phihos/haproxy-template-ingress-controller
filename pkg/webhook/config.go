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

package webhook

import (
	"context"
	"fmt"
	"strings"

	admissionv1 "k8s.io/api/admissionregistration/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
)

// ConfigManager handles dynamic creation and updates of ValidatingWebhookConfiguration.
//
// This manager automatically creates the webhook configuration in the cluster,
// injects the CA bundle, and updates the configuration when webhook rules change.
type ConfigManager struct {
	client kubernetes.Interface
	spec   WebhookConfigSpec
}

// NewConfigManager creates a new webhook configuration manager.
//
// The client parameter should be a Kubernetes clientset with permissions to
// create and update ValidatingWebhookConfiguration resources.
func NewConfigManager(client kubernetes.Interface, spec *WebhookConfigSpec) *ConfigManager {
	// Apply defaults
	if spec.Path == "" {
		spec.Path = "/validate"
	}

	// Default policies
	if spec.FailurePolicy == nil {
		fail := admissionv1.Fail
		spec.FailurePolicy = &fail
	}
	if spec.MatchPolicy == nil {
		equivalent := admissionv1.Equivalent
		spec.MatchPolicy = &equivalent
	}
	if spec.SideEffects == nil {
		none := admissionv1.SideEffectClassNone
		spec.SideEffects = &none
	}
	if spec.TimeoutSeconds == nil {
		timeout := int32(10)
		spec.TimeoutSeconds = &timeout
	}

	return &ConfigManager{
		client: client,
		spec:   *spec,
	}
}

// CreateOrUpdate creates or updates the ValidatingWebhookConfiguration in the cluster.
//
// If the configuration already exists, it will be updated with the current spec.
// The CA bundle from the spec will be injected into all webhooks.
//
// Returns an error if the operation fails.
func (cm *ConfigManager) CreateOrUpdate(ctx context.Context) error {
	// Build ValidatingWebhookConfiguration
	config := cm.buildConfiguration()

	// Try to get existing configuration
	existing, err := cm.client.AdmissionregistrationV1().ValidatingWebhookConfigurations().Get(ctx, cm.spec.Name, metav1.GetOptions{})
	if err != nil {
		if !apierrors.IsNotFound(err) {
			return fmt.Errorf("failed to get webhook configuration: %w", err)
		}

		// Create new configuration
		_, err = cm.client.AdmissionregistrationV1().ValidatingWebhookConfigurations().Create(ctx, config, metav1.CreateOptions{})
		if err != nil {
			return fmt.Errorf("failed to create webhook configuration: %w", err)
		}

		return nil
	}

	// Update existing configuration
	existing.Webhooks = config.Webhooks
	_, err = cm.client.AdmissionregistrationV1().ValidatingWebhookConfigurations().Update(ctx, existing, metav1.UpdateOptions{})
	if err != nil {
		return fmt.Errorf("failed to update webhook configuration: %w", err)
	}

	return nil
}

// Delete removes the ValidatingWebhookConfiguration from the cluster.
//
// Returns nil if the configuration doesn't exist.
func (cm *ConfigManager) Delete(ctx context.Context) error {
	err := cm.client.AdmissionregistrationV1().ValidatingWebhookConfigurations().Delete(ctx, cm.spec.Name, metav1.DeleteOptions{})
	if err != nil && !apierrors.IsNotFound(err) {
		return fmt.Errorf("failed to delete webhook configuration: %w", err)
	}
	return nil
}

// buildConfiguration constructs a ValidatingWebhookConfiguration from the spec.
func (cm *ConfigManager) buildConfiguration() *admissionv1.ValidatingWebhookConfiguration {
	webhooks := make([]admissionv1.ValidatingWebhook, len(cm.spec.Rules))

	for i, rule := range cm.spec.Rules {
		// Build webhook name from rule
		// Must be a valid DNS subdomain (RFC 1123) with at least 3 segments
		// Format: {kind}.validation.{config-name}
		webhookName := fmt.Sprintf("%s.validation.%s",
			strings.ToLower(rule.Kind),
			cm.spec.Name)

		// Build client config
		clientConfig := admissionv1.WebhookClientConfig{
			CABundle: cm.spec.CABundle,
			Service: &admissionv1.ServiceReference{
				Namespace: cm.spec.Namespace,
				Name:      cm.spec.ServiceName,
				Path:      &cm.spec.Path,
			},
		}

		// Build operations (default to CREATE and UPDATE)
		operations := rule.Operations
		if len(operations) == 0 {
			operations = []admissionv1.OperationType{
				admissionv1.Create,
				admissionv1.Update,
			}
		}

		// Build scope (default to all scopes)
		scope := rule.Scope
		if scope == nil {
			allScopes := admissionv1.AllScopes
			scope = &allScopes
		}

		// Build admission rule
		admissionRule := admissionv1.RuleWithOperations{
			Operations: operations,
			Rule: admissionv1.Rule{
				APIGroups:   rule.APIGroups,
				APIVersions: rule.APIVersions,
				Resources:   rule.Resources,
				Scope:       scope,
			},
		}

		webhooks[i] = admissionv1.ValidatingWebhook{
			Name:                    webhookName,
			ClientConfig:            clientConfig,
			Rules:                   []admissionv1.RuleWithOperations{admissionRule},
			FailurePolicy:           cm.spec.FailurePolicy,
			MatchPolicy:             cm.spec.MatchPolicy,
			SideEffects:             cm.spec.SideEffects,
			TimeoutSeconds:          cm.spec.TimeoutSeconds,
			AdmissionReviewVersions: []string{"v1"},
		}
	}

	return &admissionv1.ValidatingWebhookConfiguration{
		ObjectMeta: metav1.ObjectMeta{
			Name: cm.spec.Name,
		},
		Webhooks: webhooks,
	}
}

// UpdateRules updates the webhook rules in the spec.
//
// Call CreateOrUpdate() after updating rules to apply changes to the cluster.
func (cm *ConfigManager) UpdateRules(rules []WebhookRule) {
	cm.spec.Rules = rules
}

// UpdateCABundle updates the CA bundle in the spec.
//
// Call CreateOrUpdate() after updating the CA bundle to apply changes to the cluster.
func (cm *ConfigManager) UpdateCABundle(caBundle []byte) {
	cm.spec.CABundle = caBundle
}
