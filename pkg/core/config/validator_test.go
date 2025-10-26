package config

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestValidateStructure_Success(t *testing.T) {
	cfg := &Config{
		PodSelector: PodSelector{
			MatchLabels: map[string]string{"app": "haproxy"},
		},
		Controller: ControllerConfig{
			HealthzPort: 8080,
			MetricsPort: 9090,
		},
		Logging: LoggingConfig{
			Verbose: 1,
		},
		WatchedResources: map[string]WatchedResource{
			"ingresses": {
				APIVersion: "networking.k8s.io/v1",
				Resources:  "ingresses",
				IndexBy:    []string{"metadata.namespace"},
			},
		},
		HAProxyConfig: HAProxyConfig{
			Template: "global",
		},
	}

	err := ValidateStructure(cfg)
	assert.NoError(t, err)
}

func TestValidateStructure_NilConfig(t *testing.T) {
	err := ValidateStructure(nil)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "config is nil")
}

func TestValidatePodSelector_EmptyMatchLabels(t *testing.T) {
	cfg := &Config{
		PodSelector: PodSelector{
			MatchLabels: map[string]string{},
		},
	}

	err := ValidateStructure(cfg)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "match_labels cannot be empty")
}

func TestValidatePodSelector_EmptyLabelKey(t *testing.T) {
	cfg := &Config{
		PodSelector: PodSelector{
			MatchLabels: map[string]string{"": "value"},
		},
	}

	err := ValidateStructure(cfg)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "match_labels key cannot be empty")
}

func TestValidatePodSelector_EmptyLabelValue(t *testing.T) {
	cfg := &Config{
		PodSelector: PodSelector{
			MatchLabels: map[string]string{"app": ""},
		},
	}

	err := ValidateStructure(cfg)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "match_labels value")
}

func TestValidateOperatorConfig_InvalidHealthzPort(t *testing.T) {
	tests := []struct {
		name string
		port int
	}{
		{"zero", 0},
		{"negative", -1},
		{"too large", 65536},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cfg := &Config{
				PodSelector: PodSelector{
					MatchLabels: map[string]string{"app": "haproxy"},
				},
				Controller: ControllerConfig{
					HealthzPort: tt.port,
					MetricsPort: 9090,
				},
				WatchedResources: map[string]WatchedResource{
					"ingresses": {
						APIVersion: "networking.k8s.io/v1",
						Resources:  "ingresses",
						IndexBy:    []string{"metadata.namespace"},
					},
				},
				HAProxyConfig: HAProxyConfig{
					Template: "global",
				},
			}

			err := ValidateStructure(cfg)
			assert.Error(t, err)
			assert.Contains(t, err.Error(), "healthz_port")
		})
	}
}

func TestValidateOperatorConfig_InvalidMetricsPort(t *testing.T) {
	cfg := &Config{
		PodSelector: PodSelector{
			MatchLabels: map[string]string{"app": "haproxy"},
		},
		Controller: ControllerConfig{
			HealthzPort: 8080,
			MetricsPort: 0,
		},
		WatchedResources: map[string]WatchedResource{
			"ingresses": {
				APIVersion: "networking.k8s.io/v1",
				Resources:  "ingresses",
				IndexBy:    []string{"metadata.namespace"},
			},
		},
		HAProxyConfig: HAProxyConfig{
			Template: "global",
		},
	}

	err := ValidateStructure(cfg)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "metrics_port")
}

func TestValidateOperatorConfig_SamePort(t *testing.T) {
	cfg := &Config{
		PodSelector: PodSelector{
			MatchLabels: map[string]string{"app": "haproxy"},
		},
		Controller: ControllerConfig{
			HealthzPort: 8080,
			MetricsPort: 8080,
		},
		WatchedResources: map[string]WatchedResource{
			"ingresses": {
				APIVersion: "networking.k8s.io/v1",
				Resources:  "ingresses",
				IndexBy:    []string{"metadata.namespace"},
			},
		},
		HAProxyConfig: HAProxyConfig{
			Template: "global",
		},
	}

	err := ValidateStructure(cfg)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "cannot be the same")
}

func TestValidateLoggingConfig_InvalidVerbose(t *testing.T) {
	tests := []struct {
		name    string
		verbose int
	}{
		{"negative", -1},
		{"too large", 3},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cfg := &Config{
				PodSelector: PodSelector{
					MatchLabels: map[string]string{"app": "haproxy"},
				},
				Controller: ControllerConfig{
					HealthzPort: 8080,
					MetricsPort: 9090,
				},
				Logging: LoggingConfig{
					Verbose: tt.verbose,
				},
				WatchedResources: map[string]WatchedResource{
					"ingresses": {
						APIVersion: "networking.k8s.io/v1",
						Resources:  "ingresses",
						IndexBy:    []string{"metadata.namespace"},
					},
				},
				HAProxyConfig: HAProxyConfig{
					Template: "global",
				},
			}

			err := ValidateStructure(cfg)
			assert.Error(t, err)
			assert.Contains(t, err.Error(), "verbose")
		})
	}
}

func TestValidateWatchedResources_Empty(t *testing.T) {
	cfg := &Config{
		PodSelector: PodSelector{
			MatchLabels: map[string]string{"app": "haproxy"},
		},
		Controller: ControllerConfig{
			HealthzPort: 8080,
			MetricsPort: 9090,
		},
		WatchedResources: map[string]WatchedResource{},
		HAProxyConfig: HAProxyConfig{
			Template: "global",
		},
	}

	err := ValidateStructure(cfg)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "at least one resource must be configured")
}

func TestValidateWatchedResource_MissingAPIVersion(t *testing.T) {
	cfg := &Config{
		PodSelector: PodSelector{
			MatchLabels: map[string]string{"app": "haproxy"},
		},
		Controller: ControllerConfig{
			HealthzPort: 8080,
			MetricsPort: 9090,
		},
		WatchedResources: map[string]WatchedResource{
			"ingresses": {
				APIVersion: "",
				Resources:  "ingresses",
				IndexBy:    []string{"metadata.namespace"},
			},
		},
		HAProxyConfig: HAProxyConfig{
			Template: "global",
		},
	}

	err := ValidateStructure(cfg)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "api_version")
}

func TestValidateWatchedResource_MissingKind(t *testing.T) {
	cfg := &Config{
		PodSelector: PodSelector{
			MatchLabels: map[string]string{"app": "haproxy"},
		},
		Controller: ControllerConfig{
			HealthzPort: 8080,
			MetricsPort: 9090,
		},
		WatchedResources: map[string]WatchedResource{
			"ingresses": {
				APIVersion: "networking.k8s.io/v1",
				Resources:  "",
				IndexBy:    []string{"metadata.namespace"},
			},
		},
		HAProxyConfig: HAProxyConfig{
			Template: "global",
		},
	}

	err := ValidateStructure(cfg)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "kind")
}

func TestValidateWatchedResource_EmptyIndexBy(t *testing.T) {
	cfg := &Config{
		PodSelector: PodSelector{
			MatchLabels: map[string]string{"app": "haproxy"},
		},
		Controller: ControllerConfig{
			HealthzPort: 8080,
			MetricsPort: 9090,
		},
		WatchedResources: map[string]WatchedResource{
			"ingresses": {
				APIVersion: "networking.k8s.io/v1",
				Resources:  "ingresses",
				IndexBy:    []string{},
			},
		},
		HAProxyConfig: HAProxyConfig{
			Template: "global",
		},
	}

	err := ValidateStructure(cfg)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "index_by")
}

func TestValidateWatchedResource_EmptyIndexByElement(t *testing.T) {
	cfg := &Config{
		PodSelector: PodSelector{
			MatchLabels: map[string]string{"app": "haproxy"},
		},
		Controller: ControllerConfig{
			HealthzPort: 8080,
			MetricsPort: 9090,
		},
		WatchedResources: map[string]WatchedResource{
			"ingresses": {
				APIVersion: "networking.k8s.io/v1",
				Resources:  "ingresses",
				IndexBy:    []string{"metadata.namespace", ""},
			},
		},
		HAProxyConfig: HAProxyConfig{
			Template: "global",
		},
	}

	err := ValidateStructure(cfg)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "index_by[1] cannot be empty")
}

func TestValidateHAProxyConfig_EmptyTemplate(t *testing.T) {
	cfg := &Config{
		PodSelector: PodSelector{
			MatchLabels: map[string]string{"app": "haproxy"},
		},
		Controller: ControllerConfig{
			HealthzPort: 8080,
			MetricsPort: 9090,
		},
		WatchedResources: map[string]WatchedResource{
			"ingresses": {
				APIVersion: "networking.k8s.io/v1",
				Resources:  "ingresses",
				IndexBy:    []string{"metadata.namespace"},
			},
		},
		HAProxyConfig: HAProxyConfig{
			Template: "",
		},
	}

	err := ValidateStructure(cfg)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "template cannot be empty")
}

func TestValidateCredentials_Success(t *testing.T) {
	creds := &Credentials{
		DataplaneUsername: "admin",
		DataplanePassword: "pass",
	}

	err := ValidateCredentials(creds)
	assert.NoError(t, err)
}

func TestValidateCredentials_Nil(t *testing.T) {
	err := ValidateCredentials(nil)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "credentials are nil")
}

func TestValidateCredentials_MissingFields(t *testing.T) {
	tests := []struct {
		name     string
		creds    *Credentials
		errField string
	}{
		{
			name: "missing dataplane_username",
			creds: &Credentials{
				DataplaneUsername: "",
				DataplanePassword: "pass",
			},
			errField: "dataplane_username",
		},
		{
			name: "missing dataplane_password",
			creds: &Credentials{
				DataplaneUsername: "admin",
				DataplanePassword: "",
			},
			errField: "dataplane_password",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidateCredentials(tt.creds)
			assert.Error(t, err)
			assert.Contains(t, err.Error(), tt.errField)
		})
	}
}
