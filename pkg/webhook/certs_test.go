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
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewCertificateManager(t *testing.T) {
	certMgr := NewCertificateManager(&CertConfig{
		Namespace:   "test-namespace",
		ServiceName: "test-service",
	})

	assert.Equal(t, "test-namespace", certMgr.config.Namespace)
	assert.Equal(t, "test-service", certMgr.config.ServiceName)
	assert.Equal(t, "test-service.test-namespace.svc", certMgr.config.CommonName)
	assert.Equal(t, "haproxy-template-ic", certMgr.config.Organization)
	assert.Equal(t, 365*24*time.Hour, certMgr.config.ValidityDuration)
	assert.Equal(t, 30*24*time.Hour, certMgr.config.RotationThreshold)
}

func TestNewCertificateManager_CustomConfig(t *testing.T) {
	certMgr := NewCertificateManager(&CertConfig{
		Namespace:         "custom-ns",
		ServiceName:       "custom-svc",
		CommonName:        "custom.example.com",
		Organization:      "Custom Org",
		ValidityDuration:  180 * 24 * time.Hour,
		RotationThreshold: 15 * 24 * time.Hour,
	})

	assert.Equal(t, "custom.example.com", certMgr.config.CommonName)
	assert.Equal(t, "Custom Org", certMgr.config.Organization)
	assert.Equal(t, 180*24*time.Hour, certMgr.config.ValidityDuration)
	assert.Equal(t, 15*24*time.Hour, certMgr.config.RotationThreshold)
}

func TestCertificateManager_Generate(t *testing.T) {
	certMgr := NewCertificateManager(&CertConfig{
		Namespace:   "test",
		ServiceName: "webhook",
	})

	certs, err := certMgr.Generate()

	require.NoError(t, err)
	assert.NotNil(t, certs)
	assert.NotEmpty(t, certs.CACert)
	assert.NotEmpty(t, certs.CAKey)
	assert.NotEmpty(t, certs.ServerCert)
	assert.NotEmpty(t, certs.ServerKey)
	assert.False(t, certs.ValidUntil.IsZero())
	assert.False(t, certs.GeneratedAt.IsZero())
}

func TestCertificateManager_GenerateCACert(t *testing.T) {
	certMgr := NewCertificateManager(&CertConfig{
		Namespace:   "test",
		ServiceName: "webhook",
	})

	certs, err := certMgr.Generate()
	require.NoError(t, err)

	// Parse CA certificate
	caCert, err := ParseCertificatePEM(certs.CACert)
	require.NoError(t, err)

	// Verify CA properties
	assert.True(t, caCert.IsCA, "CA certificate should have IsCA=true")
	assert.Contains(t, caCert.Subject.CommonName, "CA")
	assert.Contains(t, caCert.Subject.Organization, "haproxy-template-ic")

	// Verify validity period
	assert.True(t, caCert.NotBefore.Before(time.Now()))
	assert.True(t, caCert.NotAfter.After(time.Now()))
}

func TestCertificateManager_GenerateServerCert(t *testing.T) {
	certMgr := NewCertificateManager(&CertConfig{
		Namespace:   "my-namespace",
		ServiceName: "my-webhook",
	})

	certs, err := certMgr.Generate()
	require.NoError(t, err)

	// Parse server certificate
	serverCert, err := ParseCertificatePEM(certs.ServerCert)
	require.NoError(t, err)

	// Verify server properties
	assert.False(t, serverCert.IsCA, "Server certificate should have IsCA=false")
	assert.Equal(t, "my-webhook.my-namespace.svc", serverCert.Subject.CommonName)

	// Verify DNS SANs
	expectedDNSNames := []string{
		"my-webhook",
		"my-webhook.my-namespace",
		"my-webhook.my-namespace.svc",
		"my-webhook.my-namespace.svc.cluster.local",
	}
	assert.ElementsMatch(t, expectedDNSNames, serverCert.DNSNames)

	// Verify validity period
	assert.True(t, serverCert.NotBefore.Before(time.Now()))
	assert.True(t, serverCert.NotAfter.After(time.Now()))

	// Verify server cert is signed by CA
	caCert, err := ParseCertificatePEM(certs.CACert)
	require.NoError(t, err)

	err = serverCert.CheckSignatureFrom(caCert)
	assert.NoError(t, err, "Server certificate should be signed by CA")
}

func TestCertificateManager_NeedsRotation(t *testing.T) {
	certMgr := NewCertificateManager(&CertConfig{
		Namespace:         "test",
		ServiceName:       "webhook",
		RotationThreshold: 30 * 24 * time.Hour,
	})

	tests := []struct {
		name        string
		validUntil  time.Time
		needsRotate bool
	}{
		{
			name:        "expires in 60 days",
			validUntil:  time.Now().Add(60 * 24 * time.Hour),
			needsRotate: false,
		},
		{
			name:        "expires in 29 days",
			validUntil:  time.Now().Add(29 * 24 * time.Hour),
			needsRotate: true,
		},
		{
			name:        "expires in 1 day",
			validUntil:  time.Now().Add(24 * time.Hour),
			needsRotate: true,
		},
		{
			name:        "already expired",
			validUntil:  time.Now().Add(-24 * time.Hour),
			needsRotate: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			certs := &Certificates{
				ValidUntil: tt.validUntil,
			}

			needsRotate := certMgr.NeedsRotation(certs)
			assert.Equal(t, tt.needsRotate, needsRotate)
		})
	}
}

func TestGetCertificateExpiry(t *testing.T) {
	certMgr := NewCertificateManager(&CertConfig{
		Namespace:   "test",
		ServiceName: "webhook",
	})

	certs, err := certMgr.Generate()
	require.NoError(t, err)

	// Get expiry from PEM
	expiry, err := GetCertificateExpiry(certs.ServerCert)
	require.NoError(t, err)

	// Should match ValidUntil
	assert.Equal(t, certs.ValidUntil, expiry)

	// Should be in the future
	assert.True(t, expiry.After(time.Now()))
}

func TestParseCertificatePEM_Invalid(t *testing.T) {
	tests := []struct {
		name    string
		certPEM []byte
	}{
		{
			name:    "empty PEM",
			certPEM: []byte{},
		},
		{
			name:    "invalid PEM",
			certPEM: []byte("not a certificate"),
		},
		{
			name: "wrong PEM type",
			certPEM: []byte(`-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
-----END RSA PRIVATE KEY-----`),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := ParseCertificatePEM(tt.certPEM)
			assert.Error(t, err)
		})
	}
}

func TestCertificateManager_ConsistentGeneration(t *testing.T) {
	certMgr := NewCertificateManager(&CertConfig{
		Namespace:   "test",
		ServiceName: "webhook",
	})

	// Generate twice
	certs1, err := certMgr.Generate()
	require.NoError(t, err)

	certs2, err := certMgr.Generate()
	require.NoError(t, err)

	// Certificates should be different (different keys, serial numbers)
	assert.NotEqual(t, certs1.ServerCert, certs2.ServerCert)
	assert.NotEqual(t, certs1.ServerKey, certs2.ServerKey)

	// But both should be valid
	cert1, err := ParseCertificatePEM(certs1.ServerCert)
	require.NoError(t, err)

	cert2, err := ParseCertificatePEM(certs2.ServerCert)
	require.NoError(t, err)

	// Same DNS names
	assert.ElementsMatch(t, cert1.DNSNames, cert2.DNSNames)
}
