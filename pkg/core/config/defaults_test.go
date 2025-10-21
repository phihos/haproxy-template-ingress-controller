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

	setDefaults(cfg)

	// Controller defaults
	assert.Equal(t, DefaultHealthzPort, cfg.Controller.HealthzPort)
	assert.Equal(t, DefaultMetricsPort, cfg.Controller.MetricsPort)

	// Dataplane defaults
	assert.Equal(t, DefaultDataplanePort, cfg.Dataplane.Port)
}

func TestSetDefaults_AllSet(t *testing.T) {
	cfg := &Config{
		Controller: ControllerConfig{
			HealthzPort: 8081,
			MetricsPort: 9091,
		},
		Dataplane: DataplaneConfig{
			Port: 5556,
		},
	}

	setDefaults(cfg)

	// Verify existing values are not overwritten
	assert.Equal(t, 8081, cfg.Controller.HealthzPort)
	assert.Equal(t, 9091, cfg.Controller.MetricsPort)
	assert.Equal(t, 5556, cfg.Dataplane.Port)
}

func TestSetDefaults_PartiallySet(t *testing.T) {
	cfg := &Config{
		Controller: ControllerConfig{
			HealthzPort: 8081, // Set
			// MetricsPort: 0 (unset)
		},
		Dataplane: DataplaneConfig{
			// Port: 0 (unset)
		},
	}

	setDefaults(cfg)

	// Set values should remain
	assert.Equal(t, 8081, cfg.Controller.HealthzPort)

	// Unset values should get defaults
	assert.Equal(t, DefaultMetricsPort, cfg.Controller.MetricsPort)
	assert.Equal(t, DefaultDataplanePort, cfg.Dataplane.Port)
}

func TestSetDefaults_OperatorConfig(t *testing.T) {
	cfg := &Config{
		Controller: ControllerConfig{},
	}

	setDefaults(cfg)

	assert.Equal(t, DefaultHealthzPort, cfg.Controller.HealthzPort)
	assert.Equal(t, DefaultMetricsPort, cfg.Controller.MetricsPort)
}

func TestSetDefaults_LoggingConfig(t *testing.T) {
	// Logging config has no defaults that override zero values
	// (Verbose 0 is valid = WARNING level)
	cfg := &Config{
		Logging: LoggingConfig{},
	}

	setDefaults(cfg)

	// Zero value should remain (it is valid)
	assert.Equal(t, 0, cfg.Logging.Verbose)
}

func TestSetDefaults_Constants(t *testing.T) {
	// Verify default constants have expected values
	assert.Equal(t, 8080, DefaultHealthzPort)
	assert.Equal(t, 9090, DefaultMetricsPort)
	assert.Equal(t, 1, DefaultVerbose)
	assert.Equal(t, 5555, DefaultDataplanePort)
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

	cfg, err := parseConfig(yamlConfig)
	assert.NoError(t, err)

	// Before SetDefaults, ports should be 0
	assert.Equal(t, 0, cfg.Controller.HealthzPort)
	assert.Equal(t, 0, cfg.Controller.MetricsPort)

	setDefaults(cfg)

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
	setDefaults(cfg)
	firstHealthz := cfg.Controller.HealthzPort
	firstMetrics := cfg.Controller.MetricsPort

	setDefaults(cfg)
	secondHealthz := cfg.Controller.HealthzPort
	secondMetrics := cfg.Controller.MetricsPort

	// Should be idempotent
	assert.Equal(t, firstHealthz, secondHealthz)
	assert.Equal(t, firstMetrics, secondMetrics)
}
