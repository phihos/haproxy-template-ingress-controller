// Package config provides configuration loading and validation.
package config

import (
	"fmt"

	"gopkg.in/yaml.v3"
)

// ParseConfig parses YAML configuration into a Config struct.
// This is a pure function that only parses YAML - it does not load from
// Kubernetes, apply defaults, or perform validation.
func ParseConfig(configYAML string) (*Config, error) {
	if configYAML == "" {
		return nil, fmt.Errorf("config YAML is empty")
	}

	var cfg Config
	if err := yaml.Unmarshal([]byte(configYAML), &cfg); err != nil {
		return nil, fmt.Errorf("failed to unmarshal YAML: %w", err)
	}

	return &cfg, nil
}

// LoadCredentials parses Secret data into a Credentials struct.
// This is a pure function that extracts credentials from Secret data.
// It does not load from Kubernetes or perform validation.
//
// Expected Secret keys: dataplane_username, dataplane_password,
// validation_username, validation_password.
func LoadCredentials(secretData map[string][]byte) (*Credentials, error) {
	if secretData == nil {
		return nil, fmt.Errorf("secret data is nil")
	}

	// Extract required fields
	dataplaneUsername, ok := secretData["dataplane_username"]
	if !ok || len(dataplaneUsername) == 0 {
		return nil, fmt.Errorf("missing required secret key: dataplane_username")
	}

	dataplanePassword, ok := secretData["dataplane_password"]
	if !ok || len(dataplanePassword) == 0 {
		return nil, fmt.Errorf("missing required secret key: dataplane_password")
	}

	validationUsername, ok := secretData["validation_username"]
	if !ok || len(validationUsername) == 0 {
		return nil, fmt.Errorf("missing required secret key: validation_username")
	}

	validationPassword, ok := secretData["validation_password"]
	if !ok || len(validationPassword) == 0 {
		return nil, fmt.Errorf("missing required secret key: validation_password")
	}

	return &Credentials{
		DataplaneUsername:  string(dataplaneUsername),
		DataplanePassword:  string(dataplanePassword),
		ValidationUsername: string(validationUsername),
		ValidationPassword: string(validationPassword),
	}, nil
}
