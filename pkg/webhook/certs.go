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
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"fmt"
	"math/big"
	"time"
)

// CertificateManager handles generation and rotation of webhook certificates.
type CertificateManager struct {
	config CertConfig
}

// NewCertificateManager creates a new certificate manager with the given configuration.
func NewCertificateManager(config *CertConfig) *CertificateManager {
	// Apply defaults
	if config.CommonName == "" {
		config.CommonName = fmt.Sprintf("%s.%s.svc", config.ServiceName, config.Namespace)
	}
	if config.Organization == "" {
		config.Organization = "haproxy-template-ic"
	}
	if config.ValidityDuration == 0 {
		config.ValidityDuration = 365 * 24 * time.Hour // 1 year
	}
	if config.RotationThreshold == 0 {
		config.RotationThreshold = 30 * 24 * time.Hour // 30 days
	}

	return &CertificateManager{
		config: *config,
	}
}

// Generate creates a new CA certificate and server certificate.
//
// The CA certificate is self-signed and used to sign the server certificate.
// The server certificate includes DNS SANs for the webhook service in the cluster.
//
// Returns a Certificates struct containing the complete certificate chain.
func (cm *CertificateManager) Generate() (*Certificates, error) {
	now := time.Now()

	// Generate CA certificate
	caCert, caKey, err := cm.generateCACertificate(now)
	if err != nil {
		return nil, fmt.Errorf("failed to generate CA certificate: %w", err)
	}

	// Generate server certificate signed by CA
	serverCert, serverKey, err := cm.generateServerCertificate(now, caCert, caKey)
	if err != nil {
		return nil, fmt.Errorf("failed to generate server certificate: %w", err)
	}

	// Encode certificates to PEM
	caCertPEM := encodeCertificatePEM(caCert)
	caKeyPEM := encodePrivateKeyPEM(caKey)
	serverCertPEM := encodeCertificatePEM(serverCert)
	serverKeyPEM := encodePrivateKeyPEM(serverKey)

	return &Certificates{
		CACert:      caCertPEM,
		CAKey:       caKeyPEM,
		ServerCert:  serverCertPEM,
		ServerKey:   serverKeyPEM,
		ValidUntil:  serverCert.NotAfter,
		GeneratedAt: now,
	}, nil
}

// NeedsRotation returns true if the server certificate should be rotated.
//
// Rotation is triggered when the certificate expires within the rotation threshold
// (default 30 days).
func (cm *CertificateManager) NeedsRotation(certs *Certificates) bool {
	timeUntilExpiry := time.Until(certs.ValidUntil)
	return timeUntilExpiry < cm.config.RotationThreshold
}

// generateCACertificate creates a self-signed CA certificate.
func (cm *CertificateManager) generateCACertificate(now time.Time) (*x509.Certificate, *rsa.PrivateKey, error) {
	// Generate RSA private key
	key, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to generate RSA key: %w", err)
	}

	// Generate serial number
	serialNumber, err := generateSerialNumber()
	if err != nil {
		return nil, nil, err
	}

	// Create CA certificate template
	template := &x509.Certificate{
		SerialNumber: serialNumber,
		Subject: pkix.Name{
			CommonName:   fmt.Sprintf("%s CA", cm.config.Organization),
			Organization: []string{cm.config.Organization},
		},
		NotBefore:             now,
		NotAfter:              now.Add(cm.config.ValidityDuration),
		KeyUsage:              x509.KeyUsageCertSign | x509.KeyUsageCRLSign,
		BasicConstraintsValid: true,
		IsCA:                  true,
		MaxPathLen:            0,
		MaxPathLenZero:        true,
	}

	// Self-sign the certificate
	certDER, err := x509.CreateCertificate(rand.Reader, template, template, &key.PublicKey, key)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to create certificate: %w", err)
	}

	// Parse DER to x509.Certificate
	cert, err := x509.ParseCertificate(certDER)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to parse certificate: %w", err)
	}

	return cert, key, nil
}

// generateServerCertificate creates a server certificate signed by the CA.
func (cm *CertificateManager) generateServerCertificate(now time.Time, caCert *x509.Certificate, caKey *rsa.PrivateKey) (*x509.Certificate, *rsa.PrivateKey, error) {
	// Generate RSA private key
	key, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to generate RSA key: %w", err)
	}

	// Generate serial number
	serialNumber, err := generateSerialNumber()
	if err != nil {
		return nil, nil, err
	}

	// DNS names for the webhook service
	dnsNames := []string{
		cm.config.ServiceName, // service
		fmt.Sprintf("%s.%s", cm.config.ServiceName, cm.config.Namespace),                   // service.namespace
		fmt.Sprintf("%s.%s.svc", cm.config.ServiceName, cm.config.Namespace),               // service.namespace.svc
		fmt.Sprintf("%s.%s.svc.cluster.local", cm.config.ServiceName, cm.config.Namespace), // FQDN
	}

	// Create server certificate template
	template := &x509.Certificate{
		SerialNumber: serialNumber,
		Subject: pkix.Name{
			CommonName:   cm.config.CommonName,
			Organization: []string{cm.config.Organization},
		},
		DNSNames:    dnsNames,
		NotBefore:   now,
		NotAfter:    now.Add(cm.config.ValidityDuration),
		KeyUsage:    x509.KeyUsageDigitalSignature | x509.KeyUsageKeyEncipherment,
		ExtKeyUsage: []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
	}

	// Sign with CA certificate
	certDER, err := x509.CreateCertificate(rand.Reader, template, caCert, &key.PublicKey, caKey)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to create certificate: %w", err)
	}

	// Parse DER to x509.Certificate
	cert, err := x509.ParseCertificate(certDER)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to parse certificate: %w", err)
	}

	return cert, key, nil
}

// generateSerialNumber generates a cryptographically secure random serial number.
func generateSerialNumber() (*big.Int, error) {
	serialNumberLimit := new(big.Int).Lsh(big.NewInt(1), 128)
	serialNumber, err := rand.Int(rand.Reader, serialNumberLimit)
	if err != nil {
		return nil, fmt.Errorf("failed to generate serial number: %w", err)
	}
	return serialNumber, nil
}

// encodeCertificatePEM encodes an x509 certificate to PEM format.
func encodeCertificatePEM(cert *x509.Certificate) []byte {
	block := &pem.Block{
		Type:  "CERTIFICATE",
		Bytes: cert.Raw,
	}
	return pem.EncodeToMemory(block)
}

// encodePrivateKeyPEM encodes an RSA private key to PEM format.
func encodePrivateKeyPEM(key *rsa.PrivateKey) []byte {
	block := &pem.Block{
		Type:  "RSA PRIVATE KEY",
		Bytes: x509.MarshalPKCS1PrivateKey(key),
	}
	return pem.EncodeToMemory(block)
}

// ParseCertificatePEM parses a PEM-encoded certificate.
//
// This is useful for loading previously generated certificates from storage.
func ParseCertificatePEM(certPEM []byte) (*x509.Certificate, error) {
	block, _ := pem.Decode(certPEM)
	if block == nil {
		return nil, fmt.Errorf("failed to decode PEM block")
	}

	if block.Type != "CERTIFICATE" {
		return nil, fmt.Errorf("expected CERTIFICATE block, got %s", block.Type)
	}

	cert, err := x509.ParseCertificate(block.Bytes)
	if err != nil {
		return nil, fmt.Errorf("failed to parse certificate: %w", err)
	}

	return cert, nil
}

// GetCertificateExpiry returns when a PEM-encoded certificate expires.
//
// This is a convenience function for checking certificate validity without
// parsing the full certificate.
func GetCertificateExpiry(certPEM []byte) (time.Time, error) {
	cert, err := ParseCertificatePEM(certPEM)
	if err != nil {
		return time.Time{}, err
	}
	return cert.NotAfter, nil
}
