package configloader

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"haproxy-template-ic/pkg/apis/haproxytemplate/v1alpha1"
	"haproxy-template-ic/pkg/core/config"
)

func TestConvertCRDToConfig(t *testing.T) {
	tests := []struct {
		name    string
		spec    v1alpha1.HAProxyTemplateConfigSpec
		want    *config.Config
		wantErr bool
	}{
		{
			name: "minimal valid config",
			spec: v1alpha1.HAProxyTemplateConfigSpec{
				CredentialsSecretRef: v1alpha1.SecretReference{
					Name: "haproxy-creds",
				},
				PodSelector: v1alpha1.PodSelector{
					MatchLabels: map[string]string{
						"app": "haproxy",
					},
				},
				HAProxyConfig: v1alpha1.HAProxyConfig{
					Template: "global\n  daemon",
				},
			},
			want: &config.Config{
				PodSelector: config.PodSelector{
					MatchLabels: map[string]string{
						"app": "haproxy",
					},
				},
				Controller: config.ControllerConfig{
					LeaderElection: config.LeaderElectionConfig{
						Enabled: true, // Default when not specified
					},
				},
				HAProxyConfig: config.HAProxyConfig{
					Template: "global\n  daemon",
				},
				WatchedResources: map[string]config.WatchedResource{},
				TemplateSnippets: map[string]config.TemplateSnippet{},
				Maps:             map[string]config.MapFile{},
				Files:            map[string]config.GeneralFile{},
				SSLCertificates:  map[string]config.SSLCertificate{},
			},
			wantErr: false,
		},
		{
			name: "complete config with all sections",
			spec: v1alpha1.HAProxyTemplateConfigSpec{
				CredentialsSecretRef: v1alpha1.SecretReference{
					Name:      "haproxy-creds",
					Namespace: "default",
				},
				PodSelector: v1alpha1.PodSelector{
					MatchLabels: map[string]string{
						"app":       "haproxy",
						"component": "loadbalancer",
					},
				},
				Controller: v1alpha1.ControllerConfig{
					HealthzPort: 8080,
					MetricsPort: 9090,
					LeaderElection: v1alpha1.LeaderElectionConfig{
						Enabled:       boolPtr(true),
						LeaseName:     "haproxy-leader",
						LeaseDuration: "15s",
						RenewDeadline: "10s",
						RetryPeriod:   "2s",
					},
				},
				Logging: v1alpha1.LoggingConfig{
					Verbose: 1,
				},
				Dataplane: v1alpha1.DataplaneConfig{
					Port:                    5555,
					MinDeploymentInterval:   "2s",
					DriftPreventionInterval: "5m",
				},
				WatchedResources: map[string]v1alpha1.WatchedResource{
					"ingresses": {
						APIVersion:    "networking.k8s.io/v1",
						Resources:     "ingresses",
						LabelSelector: "app=nginx,env=prod",
						IndexBy:       []string{"metadata.namespace", "metadata.name"},
					},
				},
				TemplateSnippets: map[string]v1alpha1.TemplateSnippet{
					"common_defaults": {
						Template: "timeout connect 5s",
					},
				},
				Maps: map[string]v1alpha1.MapFile{
					"backend_map": {
						Template: "{{ range .ingresses }}{{ .metadata.name }} backend_{{ .metadata.name }}\n{{ end }}",
					},
				},
				Files: map[string]v1alpha1.GeneralFile{
					"error_page": {
						Template: "<html><body>Error</body></html>",
					},
				},
				SSLCertificates: map[string]v1alpha1.SSLCertificate{
					"default_cert": {
						Template: "{{ .secret.data.cert }}",
					},
				},
				HAProxyConfig: v1alpha1.HAProxyConfig{
					Template: "global\n  daemon\n\ndefaults\n  {% include 'common_defaults' %}",
				},
			},
			want: &config.Config{
				PodSelector: config.PodSelector{
					MatchLabels: map[string]string{
						"app":       "haproxy",
						"component": "loadbalancer",
					},
				},
				Controller: config.ControllerConfig{
					HealthzPort: 8080,
					MetricsPort: 9090,
					LeaderElection: config.LeaderElectionConfig{
						Enabled:       true,
						LeaseName:     "haproxy-leader",
						LeaseDuration: "15s",
						RenewDeadline: "10s",
						RetryPeriod:   "2s",
					},
				},
				Logging: config.LoggingConfig{
					Verbose: 1,
				},
				Dataplane: config.DataplaneConfig{
					Port:                    5555,
					MinDeploymentInterval:   "2s",
					DriftPreventionInterval: "5m",
				},
				WatchedResources: map[string]config.WatchedResource{
					"ingresses": {
						APIVersion: "networking.k8s.io/v1",
						Resources:  "ingresses",
						LabelSelector: map[string]string{
							"app": "nginx",
							"env": "prod",
						},
						IndexBy: []string{"metadata.namespace", "metadata.name"},
					},
				},
				TemplateSnippets: map[string]config.TemplateSnippet{
					"common_defaults": {
						Name:     "common_defaults",
						Template: "timeout connect 5s",
						Priority: 500,
					},
				},
				Maps: map[string]config.MapFile{
					"backend_map": {
						Template: "{{ range .ingresses }}{{ .metadata.name }} backend_{{ .metadata.name }}\n{{ end }}",
					},
				},
				Files: map[string]config.GeneralFile{
					"error_page": {
						Template: "<html><body>Error</body></html>",
					},
				},
				SSLCertificates: map[string]config.SSLCertificate{
					"default_cert": {
						Template: "{{ .secret.data.cert }}",
					},
				},
				HAProxyConfig: config.HAProxyConfig{
					Template: "global\n  daemon\n\ndefaults\n  {% include 'common_defaults' %}",
				},
			},
			wantErr: false,
		},
		{
			name: "leader election disabled",
			spec: v1alpha1.HAProxyTemplateConfigSpec{
				CredentialsSecretRef: v1alpha1.SecretReference{
					Name: "haproxy-creds",
				},
				PodSelector: v1alpha1.PodSelector{
					MatchLabels: map[string]string{"app": "haproxy"},
				},
				Controller: v1alpha1.ControllerConfig{
					LeaderElection: v1alpha1.LeaderElectionConfig{
						Enabled: boolPtr(false),
					},
				},
				HAProxyConfig: v1alpha1.HAProxyConfig{
					Template: "global\n  daemon",
				},
			},
			want: &config.Config{
				PodSelector: config.PodSelector{
					MatchLabels: map[string]string{"app": "haproxy"},
				},
				Controller: config.ControllerConfig{
					LeaderElection: config.LeaderElectionConfig{
						Enabled: false,
					},
				},
				HAProxyConfig: config.HAProxyConfig{
					Template: "global\n  daemon",
				},
				WatchedResources: map[string]config.WatchedResource{},
				TemplateSnippets: map[string]config.TemplateSnippet{},
				Maps:             map[string]config.MapFile{},
				Files:            map[string]config.GeneralFile{},
				SSLCertificates:  map[string]config.SSLCertificate{},
			},
			wantErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := ConvertCRDToConfig(&tt.spec)

			if tt.wantErr {
				require.Error(t, err)
				return
			}

			require.NoError(t, err)
			assert.Equal(t, tt.want.PodSelector, got.PodSelector)
			assert.Equal(t, tt.want.Controller, got.Controller)
			assert.Equal(t, tt.want.Logging, got.Logging)
			assert.Equal(t, tt.want.Dataplane, got.Dataplane)
			assert.Equal(t, tt.want.WatchedResources, got.WatchedResources)
			assert.Equal(t, tt.want.TemplateSnippets, got.TemplateSnippets)
			assert.Equal(t, tt.want.Maps, got.Maps)
			assert.Equal(t, tt.want.Files, got.Files)
			assert.Equal(t, tt.want.SSLCertificates, got.SSLCertificates)
			assert.Equal(t, tt.want.HAProxyConfig, got.HAProxyConfig)
		})
	}
}

func TestParseLabelSelector(t *testing.T) {
	tests := []struct {
		name     string
		selector string
		want     map[string]string
	}{
		{
			name:     "empty string",
			selector: "",
			want:     nil,
		},
		{
			name:     "single label",
			selector: "app=nginx",
			want: map[string]string{
				"app": "nginx",
			},
		},
		{
			name:     "multiple labels",
			selector: "app=nginx,env=prod,version=v1",
			want: map[string]string{
				"app":     "nginx",
				"env":     "prod",
				"version": "v1",
			},
		},
		{
			name:     "labels with spaces",
			selector: "app = nginx , env = prod",
			want: map[string]string{
				"app": "nginx",
				"env": "prod",
			},
		},
		{
			name:     "label with empty value",
			selector: "app=nginx,env=",
			want: map[string]string{
				"app": "nginx",
				"env": "",
			},
		},
		{
			name:     "trailing comma",
			selector: "app=nginx,env=prod,",
			want: map[string]string{
				"app": "nginx",
				"env": "prod",
			},
		},
		{
			name:     "malformed - no equals",
			selector: "app,env=prod",
			want: map[string]string{
				"env": "prod",
			},
		},
		{
			name:     "kubernetes style labels",
			selector: "app.kubernetes.io/name=haproxy,app.kubernetes.io/component=loadbalancer",
			want: map[string]string{
				"app.kubernetes.io/name":      "haproxy",
				"app.kubernetes.io/component": "loadbalancer",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := parseLabelSelector(tt.selector)
			assert.Equal(t, tt.want, got)
		})
	}
}

// boolPtr returns a pointer to a bool value (helper for tests).
func boolPtr(b bool) *bool {
	return &b
}
