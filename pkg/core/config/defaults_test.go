package config

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestSetDefaults_AllUnset(t *testing.T) {
	cfg := &Config{
		PodSelector: PodSelector{
			MatchLabels: map[string]string{"app": "haproxy"},
		},
	}

	SetDefaults(cfg)

	// Controller defaults
	assert.Equal(t, DefaultHealthzPort, cfg.Controller.HealthzPort)
	assert.Equal(t, DefaultMetricsPort, cfg.Controller.MetricsPort)

	// Validation defaults
	assert.Equal(t, DefaultValidationDataplaneHost, cfg.Validation.DataplaneHost)
	assert.Equal(t, DefaultValidationDataplanePort, cfg.Validation.DataplanePort)
}

func TestSetDefaults_AllSet(t *testing.T) {
	cfg := &Config{
		Controller: ControllerConfig{
			HealthzPort: 8081,
			MetricsPort: 9091,
		},
		Validation: ValidationConfig{
			DataplaneHost: "custom-host",
			DataplanePort: 5556,
		},
	}

	SetDefaults(cfg)

	// Verify existing values are not overwritten
	assert.Equal(t, 8081, cfg.Controller.HealthzPort)
	assert.Equal(t, 9091, cfg.Controller.MetricsPort)
	assert.Equal(t, "custom-host", cfg.Validation.DataplaneHost)
	assert.Equal(t, 5556, cfg.Validation.DataplanePort)
}

func TestSetDefaults_PartiallySet(t *testing.T) {
	cfg := &Config{
		Controller: ControllerConfig{
			HealthzPort: 8081, // Set
			// MetricsPort: 0 (unset)
		},
		Validation: ValidationConfig{
			DataplaneHost: "custom-host", // Set
			// DataplanePort: 0 (unset)
		},
	}

	SetDefaults(cfg)

	// Set values should remain
	assert.Equal(t, 8081, cfg.Controller.HealthzPort)
	assert.Equal(t, "custom-host", cfg.Validation.DataplaneHost)

	// Unset values should get defaults
	assert.Equal(t, DefaultMetricsPort, cfg.Controller.MetricsPort)
	assert.Equal(t, DefaultValidationDataplanePort, cfg.Validation.DataplanePort)
}

func TestSetDefaults_OperatorConfig(t *testing.T) {
	cfg := &Config{
		Controller: ControllerConfig{},
	}

	SetDefaults(cfg)

	assert.Equal(t, DefaultHealthzPort, cfg.Controller.HealthzPort)
	assert.Equal(t, DefaultMetricsPort, cfg.Controller.MetricsPort)
}

func TestSetDefaults_ValidationConfig(t *testing.T) {
	cfg := &Config{
		Validation: ValidationConfig{},
	}

	SetDefaults(cfg)

	assert.Equal(t, DefaultValidationDataplaneHost, cfg.Validation.DataplaneHost)
	assert.Equal(t, DefaultValidationDataplanePort, cfg.Validation.DataplanePort)
}

func TestSetDefaults_LoggingConfig(t *testing.T) {
	// Logging config has no defaults that override zero values
	// (Verbose 0 is valid = WARNING level)
	cfg := &Config{
		Logging: LoggingConfig{},
	}

	SetDefaults(cfg)

	// Zero value should remain (it is valid)
	assert.Equal(t, 0, cfg.Logging.Verbose)
}

func TestSetDefaults_Constants(t *testing.T) {
	// Verify default constants have expected values
	assert.Equal(t, 8080, DefaultHealthzPort)
	assert.Equal(t, 9090, DefaultMetricsPort)
	assert.Equal(t, 1, DefaultVerbose)
	assert.Equal(t, "localhost", DefaultValidationDataplaneHost)
	assert.Equal(t, 5555, DefaultValidationDataplanePort)
	assert.False(t, DefaultEnableValidationWebhook)
}

func TestSetDefaults_IntegrationWithParsing(t *testing.T) {
	// Test the typical workflow: Parse -> SetDefaults -> Validate
	yamlConfig := `
pod_selector:
  match_labels:
    app: haproxy

watched_resources:
  ingresses:
    api_version: networking.k8s.io/v1
    kind: Ingress
    index_by: ["metadata.namespace"]

haproxy_config:
  template: "global"
`

	cfg, err := ParseConfig(yamlConfig)
	assert.NoError(t, err)

	// Before SetDefaults, ports should be 0
	assert.Equal(t, 0, cfg.Controller.HealthzPort)
	assert.Equal(t, 0, cfg.Controller.MetricsPort)

	SetDefaults(cfg)

	// After SetDefaults, ports should have default values
	assert.Equal(t, DefaultHealthzPort, cfg.Controller.HealthzPort)
	assert.Equal(t, DefaultMetricsPort, cfg.Controller.MetricsPort)

	// After SetDefaults, validation should pass
	err = ValidateStructure(cfg)
	assert.NoError(t, err)
}

func TestSetDefaults_Idempotent(t *testing.T) {
	cfg := &Config{
		Controller: ControllerConfig{},
	}

	// Apply defaults twice
	SetDefaults(cfg)
	firstHealthz := cfg.Controller.HealthzPort
	firstMetrics := cfg.Controller.MetricsPort

	SetDefaults(cfg)
	secondHealthz := cfg.Controller.HealthzPort
	secondMetrics := cfg.Controller.MetricsPort

	// Should be idempotent
	assert.Equal(t, firstHealthz, secondHealthz)
	assert.Equal(t, firstMetrics, secondMetrics)
}
