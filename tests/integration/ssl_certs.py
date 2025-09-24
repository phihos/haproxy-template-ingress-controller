"""
SSL certificate generation utilities for HAProxy integration tests.

This module provides SSL certificate generation specifically for HAProxy
integration testing, creating combined PEM files (certificate + private key)
suitable for HAProxy SSL termination.
"""

import datetime
import ipaddress
from typing import NamedTuple

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


class SSLCertificate(NamedTuple):
    """Container for SSL certificate data."""

    combined_pem: str  # Certificate + private key combined (HAProxy format)
    cert_pem: str  # Certificate only
    key_pem: str  # Private key only


def generate_ssl_certificate(
    common_name: str = "localhost", san_names: list[str] | None = None
) -> SSLCertificate:
    """Generate self-signed SSL certificate for HAProxy testing.

    Args:
        common_name: Common name for the certificate (default: localhost)
        san_names: Additional Subject Alternative Names

    Returns:
        SSLCertificate with combined PEM format for HAProxy
    """
    if san_names is None:
        san_names = ["localhost", "127.0.0.1"]

    # Generate private key
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # Create certificate subject/issuer
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "HAProxy Test"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )

    # Create Subject Alternative Names
    san_list = []
    for san in san_names:
        try:
            # Try to parse as IP address
            ip_addr = ipaddress.ip_address(san)
            san_list.append(x509.IPAddress(ip_addr))
        except ValueError:
            # Not an IP address, treat as DNS name
            san_list.append(x509.DNSName(san))

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
        .add_extension(x509.SubjectAlternativeName(san_list), critical=False)
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
    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()
    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    # Create combined PEM for HAProxy (certificate first, then private key)
    combined_pem = cert_pem + key_pem

    return SSLCertificate(combined_pem=combined_pem, cert_pem=cert_pem, key_pem=key_pem)
