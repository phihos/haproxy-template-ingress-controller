"""
Webhook certificate generation utilities for acceptance tests.

This module provides secure, properly-scoped certificate generation
for admission webhook testing in Kubernetes environments.
"""

import base64
import datetime
from typing import NamedTuple

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


class WebhookCertificate(NamedTuple):
    """Container for webhook certificate data."""

    cert_pem: bytes
    key_pem: bytes
    ca_bundle: bytes


def generate_webhook_certificates(
    service_name: str, namespace: str
) -> WebhookCertificate:
    """Generate self-signed certificates for webhook server."""
    # Generate private key
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # Create certificate subject/issuer (keep CN under 64 chars)
    common_name = f"{service_name}.{namespace}.svc.cluster.local"
    if len(common_name) > 64:
        # Fallback to shorter name if too long
        common_name = f"webhook.{namespace[:20]}.svc"

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "test"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )

    # Subject Alternative Names for webhook service
    san_names = [
        x509.DNSName(service_name),
        x509.DNSName(f"{service_name}.{namespace}"),
        x509.DNSName(f"{service_name}.{namespace}.svc"),
        x509.DNSName(f"{service_name}.{namespace}.svc.cluster.local"),
    ]

    # Create certificate (valid for 1 hour for tests)
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(hours=1))
        .add_extension(x509.SubjectAlternativeName(san_names), critical=False)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                content_commitment=False,
                data_encipherment=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=True,
        )
        .sign(private_key, hashes.SHA256())
    )

    # Serialize to PEM format
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return WebhookCertificate(cert_pem=cert_pem, key_pem=key_pem, ca_bundle=cert_pem)


def create_cert_secret_manifest(
    cert: WebhookCertificate, secret_name: str, namespace: str
) -> dict:
    """Create Kubernetes Secret manifest for webhook certificates."""
    return {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": secret_name, "namespace": namespace},
        "type": "kubernetes.io/tls",
        "data": {
            "tls.crt": base64.b64encode(cert.cert_pem).decode(),
            "tls.key": base64.b64encode(cert.key_pem).decode(),
            "ca.crt": base64.b64encode(cert.ca_bundle).decode(),
        },
    }


def create_validating_webhook_config(
    webhook_name: str,
    service_name: str,
    service_namespace: str,
    ca_bundle: bytes,
    target_namespace: str | None = None,
) -> dict:
    """Create ValidatingAdmissionWebhook manifest."""
    ca_bundle_b64 = base64.b64encode(ca_bundle).decode()
    namespace_selector = (
        {"matchLabels": {"name": target_namespace}} if target_namespace else {}
    )

    webhooks = []
    for resource_type, (api_group, path) in [
        ("ingresses", ("networking.k8s.io", "/validate/ingresses")),
        ("secrets", ("", "/validate/secrets")),
    ]:
        webhooks.append(
            {
                "name": f"{resource_type}.validation.haproxy-template-ic.io",
                "clientConfig": {
                    "service": {
                        "name": service_name,
                        "namespace": service_namespace,
                        "path": path,
                    },
                    "caBundle": ca_bundle_b64,
                },
                "rules": [
                    {
                        "operations": ["CREATE", "UPDATE"],
                        "apiGroups": [api_group],
                        "apiVersions": ["v1"],
                        "resources": [resource_type],
                    }
                ],
                "admissionReviewVersions": ["v1", "v1beta1"],
                "sideEffects": "None",
                "failurePolicy": "Ignore",
                "namespaceSelector": namespace_selector,
            }
        )

    return {
        "apiVersion": "admissionregistration.k8s.io/v1",
        "kind": "ValidatingAdmissionWebhook",
        "metadata": {"name": webhook_name},
        "webhooks": webhooks,
    }
