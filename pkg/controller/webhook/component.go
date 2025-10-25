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

// Package webhook provides the webhook adapter component that bridges
// the pure webhook library to the event-driven controller architecture.
//
// The webhook component manages the lifecycle of admission webhooks including:
//   - TLS certificate generation and rotation
//   - HTTPS webhook server
//   - Dynamic ValidatingWebhookConfiguration management
//   - Integration with controller validators
package webhook

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"k8s.io/client-go/kubernetes"

	"haproxy-template-ic/pkg/controller/events"
	busevents "haproxy-template-ic/pkg/events"
	"haproxy-template-ic/pkg/webhook"
)

const (
	// DefaultWebhookPort is the default HTTPS port for the webhook server.
	DefaultWebhookPort = 9443

	// DefaultWebhookPath is the default URL path for validation requests.
	DefaultWebhookPath = "/validate"

	// DefaultCertRotationCheckInterval is how often to check if certificates need rotation.
	DefaultCertRotationCheckInterval = 24 * time.Hour

	// EventBufferSize is the size of the event subscription buffer.
	EventBufferSize = 50
)

// Component is the webhook adapter component that manages webhook lifecycle.
//
// It coordinates the pure webhook library components (server, certificates, configuration)
// with the event-driven controller architecture.
type Component struct {
	// Dependencies
	kubeClient kubernetes.Interface
	eventBus   *busevents.EventBus
	logger     *slog.Logger
	metrics    MetricsRecorder

	// Webhook library components
	server       *webhook.Server
	certManager  *webhook.CertificateManager
	configMgr    *webhook.ConfigManager
	certificates *webhook.Certificates

	// Configuration
	config Config

	// Runtime state
	serverCtx    context.Context
	serverCancel context.CancelFunc
}

// MetricsRecorder defines the interface for recording webhook metrics.
// This allows the component to work with or without metrics.
type MetricsRecorder interface {
	RecordWebhookRequest(gvk, result string, durationSeconds float64)
	RecordWebhookValidation(gvk, result string)
	SetWebhookCertExpiry(expiryTime int64)
	RecordWebhookCertRotation()
}

// Config configures the webhook component.
type Config struct {
	// Namespace is the Kubernetes namespace the controller is deployed in.
	Namespace string

	// ServiceName is the Kubernetes service name for the webhook endpoint.
	ServiceName string

	// WebhookConfigName is the name for the ValidatingWebhookConfiguration.
	// Default: "haproxy-template-ic-webhook"
	WebhookConfigName string

	// Port is the HTTPS port for the webhook server.
	// Default: 9443
	Port int

	// Path is the URL path for validation requests.
	// Default: "/validate"
	Path string

	// CertRotationCheckInterval is how often to check if certificates need rotation.
	// Default: 24h
	CertRotationCheckInterval time.Duration

	// Rules defines which resources the webhook validates.
	// Populated from controller configuration based on enable_validation_webhook flags.
	Rules []webhook.WebhookRule
}

// New creates a new webhook component.
//
// Parameters:
//   - kubeClient: Kubernetes client for webhook configuration management
//   - eventBus: EventBus for publishing webhook events
//   - logger: Structured logger
//   - config: Component configuration
//   - metrics: Optional metrics recorder (can be nil)
//
// Returns:
//   - A new Component instance ready to be started
func New(kubeClient kubernetes.Interface, eventBus *busevents.EventBus, logger *slog.Logger, config *Config, metrics MetricsRecorder) *Component {
	// Apply defaults
	if config.WebhookConfigName == "" {
		config.WebhookConfigName = "haproxy-template-ic-webhook"
	}
	if config.Port == 0 {
		config.Port = DefaultWebhookPort
	}
	if config.Path == "" {
		config.Path = DefaultWebhookPath
	}
	if config.CertRotationCheckInterval == 0 {
		config.CertRotationCheckInterval = DefaultCertRotationCheckInterval
	}

	// Create certificate manager
	certManager := webhook.NewCertificateManager(&webhook.CertConfig{
		Namespace:   config.Namespace,
		ServiceName: config.ServiceName,
	})

	return &Component{
		kubeClient:  kubeClient,
		eventBus:    eventBus,
		logger:      logger.With("component", "webhook"),
		metrics:     metrics,
		certManager: certManager,
		config:      *config,
	}
}

// Start begins the webhook component's lifecycle.
//
// This method:
//  1. Generates TLS certificates
//  2. Creates the webhook server
//  3. Registers validators
//  4. Creates ValidatingWebhookConfiguration
//  5. Starts the HTTPS server
//  6. Monitors certificate rotation
//
// The component runs until the context is cancelled.
func (c *Component) Start(ctx context.Context) error {
	c.logger.Info("Webhook component starting",
		"namespace", c.config.Namespace,
		"service", c.config.ServiceName,
		"port", c.config.Port)

	// Generate initial certificates
	if err := c.generateCertificates(); err != nil {
		return fmt.Errorf("failed to generate certificates: %w", err)
	}

	// Create webhook server
	c.createServer()

	// Register validators
	c.registerValidators()

	// Create webhook configuration
	if err := c.createWebhookConfiguration(ctx); err != nil {
		return fmt.Errorf("failed to create webhook configuration: %w", err)
	}

	// Start server in background
	c.startServer(ctx)

	// Monitor certificate rotation
	c.monitorCertificateRotation(ctx)

	return nil
}

// generateCertificates generates initial TLS certificates.
func (c *Component) generateCertificates() error {
	c.logger.Info("Generating TLS certificates")

	certs, err := c.certManager.Generate()
	if err != nil {
		return err
	}

	c.certificates = certs

	// Publish event
	c.eventBus.Publish(events.NewWebhookCertificatesGeneratedEvent(
		certs.ValidUntil,
	))

	// Record metrics
	if c.metrics != nil {
		c.metrics.SetWebhookCertExpiry(certs.ValidUntil.Unix())
	}

	c.logger.Info("TLS certificates generated",
		"valid_until", certs.ValidUntil)

	return nil
}

// createServer creates the webhook HTTPS server.
func (c *Component) createServer() {
	c.server = webhook.NewServer(&webhook.ServerConfig{
		Port:    c.config.Port,
		Path:    c.config.Path,
		CertPEM: c.certificates.ServerCert,
		KeyPEM:  c.certificates.ServerKey,
	})
}

// registerValidators registers validation functions with the webhook server.
//
// This bridges webhook ValidationFunc to controller validators via events.
func (c *Component) registerValidators() {
	c.logger.Info("Registering validators")

	// For each webhook rule, register a validator
	for _, rule := range c.config.Rules {
		// Use Kind (singular) for validator registration, not Resources (plural)
		// The webhook server receives AdmissionRequests with Kind (e.g., "ConfigMap")
		// not resource name (e.g., "configmaps")
		gvk := c.buildGVK(rule.APIGroups[0], rule.APIVersions[0], rule.Kind)

		c.logger.Debug("Registering validator",
			"gvk", gvk,
			"kind", rule.Kind,
			"resources", rule.Resources)

		// Create resource validator
		validator := c.createResourceValidator(gvk)
		c.server.RegisterValidator(gvk, validator)
	}
}

// buildGVK constructs a GVK string from API group, version, and kind.
func (c *Component) buildGVK(apiGroup, version, kind string) string {
	if apiGroup == "" {
		// Core API group
		return fmt.Sprintf("%s.%s", version, kind)
	}
	return fmt.Sprintf("%s/%s.%s", apiGroup, version, kind)
}

// createWebhookConfiguration creates or updates the ValidatingWebhookConfiguration.
func (c *Component) createWebhookConfiguration(ctx context.Context) error {
	c.logger.Info("Creating webhook configuration")

	c.configMgr = webhook.NewConfigManager(c.kubeClient, &webhook.WebhookConfigSpec{
		Name:        c.config.WebhookConfigName,
		Namespace:   c.config.Namespace,
		ServiceName: c.config.ServiceName,
		Path:        c.config.Path,
		CABundle:    c.certificates.CACert,
		Rules:       c.config.Rules,
	})

	if err := c.configMgr.CreateOrUpdate(ctx); err != nil {
		return err
	}

	// Publish event
	c.eventBus.Publish(events.NewWebhookConfigurationCreatedEvent(
		c.config.WebhookConfigName,
		len(c.config.Rules),
	))

	c.logger.Info("Webhook configuration created",
		"name", c.config.WebhookConfigName)

	return nil
}

// startServer starts the webhook HTTPS server in the background.
func (c *Component) startServer(ctx context.Context) {
	c.logger.Info("Starting webhook server",
		"port", c.config.Port,
		"path", c.config.Path)

	// Create cancelable context for server
	c.serverCtx, c.serverCancel = context.WithCancel(ctx)

	// Start server in goroutine
	go func() {
		if err := c.server.Start(c.serverCtx); err != nil && err != context.Canceled {
			c.logger.Error("Webhook server error", "error", err)
		}
	}()

	// Give server time to start
	time.Sleep(100 * time.Millisecond)

	// Publish event
	c.eventBus.Publish(events.NewWebhookServerStartedEvent(
		c.config.Port,
		c.config.Path,
	))

	c.logger.Info("Webhook server started")
}

// monitorCertificateRotation periodically checks if certificates need rotation.
func (c *Component) monitorCertificateRotation(ctx context.Context) {
	ticker := time.NewTicker(c.config.CertRotationCheckInterval)
	defer ticker.Stop()

	go func() {
		for {
			select {
			case <-ticker.C:
				c.checkCertificateRotation(ctx)

			case <-ctx.Done():
				c.logger.Info("Certificate rotation monitor stopping")
				return
			}
		}
	}()
}

// checkCertificateRotation checks if certificates need rotation and rotates if needed.
func (c *Component) checkCertificateRotation(ctx context.Context) {
	if !c.certManager.NeedsRotation(c.certificates) {
		c.logger.Debug("Certificates do not need rotation",
			"valid_until", c.certificates.ValidUntil)
		return
	}

	c.logger.Info("Rotating certificates",
		"valid_until", c.certificates.ValidUntil)

	// Generate new certificates
	newCerts, err := c.certManager.Generate()
	if err != nil {
		c.logger.Error("Certificate rotation failed", "error", err)
		return
	}

	oldValidUntil := c.certificates.ValidUntil
	c.certificates = newCerts

	// Update webhook configuration with new CA bundle
	c.configMgr = webhook.NewConfigManager(c.kubeClient, &webhook.WebhookConfigSpec{
		Name:        c.config.WebhookConfigName,
		Namespace:   c.config.Namespace,
		ServiceName: c.config.ServiceName,
		Path:        c.config.Path,
		CABundle:    newCerts.CACert,
		Rules:       c.config.Rules,
	})

	if err := c.configMgr.CreateOrUpdate(ctx); err != nil {
		c.logger.Error("Failed to update webhook configuration after rotation", "error", err)
		return
	}

	// Restart server with new certificates
	c.logger.Info("Restarting webhook server with new certificates")

	// Stop old server
	if c.serverCancel != nil {
		c.serverCancel()
	}

	// Create new server with new certificates
	c.createServer()

	// Re-register validators
	c.registerValidators()

	// Start new server
	c.startServer(ctx)

	// Publish event
	c.eventBus.Publish(events.NewWebhookCertificatesRotatedEvent(
		oldValidUntil,
		newCerts.ValidUntil,
	))

	// Record metrics
	if c.metrics != nil {
		c.metrics.RecordWebhookCertRotation()
		c.metrics.SetWebhookCertExpiry(newCerts.ValidUntil.Unix())
	}

	c.logger.Info("Certificate rotation completed",
		"new_valid_until", newCerts.ValidUntil)
}

// Stop gracefully shuts down the webhook component.
func (c *Component) Stop(ctx context.Context) error {
	c.logger.Info("Stopping webhook component")

	// Stop server
	if c.serverCancel != nil {
		c.serverCancel()
	}

	// Delete webhook configuration
	if c.configMgr != nil {
		if err := c.configMgr.Delete(ctx); err != nil {
			c.logger.Error("Failed to delete webhook configuration", "error", err)
			// Continue with shutdown even if deletion fails
		}
	}

	// Publish event
	c.eventBus.Publish(events.NewWebhookServerStoppedEvent("shutdown"))

	c.logger.Info("Webhook component stopped")

	return nil
}
