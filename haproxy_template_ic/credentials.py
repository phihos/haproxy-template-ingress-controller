"""Credential management for HAProxy Template IC."""

import base64
import binascii
import re
from typing import Any

import click

from haproxy_template_ic.constants import ERROR_MISSING_CREDENTIALS, MAX_K8S_NAME_LENGTH
from pydantic import BaseModel, Field, SecretStr


class DataplaneAuth(BaseModel):
    """Authentication configuration for HAProxy Dataplane API."""

    username: str = Field(..., min_length=1, description="Username for Dataplane API")
    password: SecretStr = Field(
        ..., min_length=1, description="Password for Dataplane API"
    )


class Credentials(BaseModel):
    """Credentials for HAProxy instances loaded from Kubernetes Secret."""

    dataplane: DataplaneAuth = Field(
        ..., description="Production dataplane authentication"
    )
    validation: DataplaneAuth = Field(
        ..., description="Validation dataplane authentication"
    )

    @classmethod
    def from_secret(cls, data: dict) -> "Credentials":
        """Load credentials from Kubernetes Secret data.

        Args:
            data: Secret data dictionary containing credential fields

        Returns:
            Credentials instance with dataplane and validation auth

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Decode individual fields with descriptive names
        dataplane_username = _decode_field(data.get("dataplane_username"))
        dataplane_password = _decode_field(data.get("dataplane_password"))
        validation_username = _decode_field(data.get("validation_username"))
        validation_password = _decode_field(data.get("validation_password"))

        # Check for missing/invalid fields with early return
        missing_fields = []
        if dataplane_username is None:
            missing_fields.append("dataplane_username")
        if dataplane_password is None:
            missing_fields.append("dataplane_password")
        if validation_username is None:
            missing_fields.append("validation_username")
        if validation_password is None:
            missing_fields.append("validation_password")

        if missing_fields:
            raise ValueError(ERROR_MISSING_CREDENTIALS.format(fields=missing_fields))

        # Additional type safety check - these should not be None after validation
        assert dataplane_username is not None  # nosec B101
        assert dataplane_password is not None  # nosec B101
        assert validation_username is not None  # nosec B101
        assert validation_password is not None  # nosec B101

        # Create auth objects with validated fields
        dataplane_auth = DataplaneAuth(
            username=dataplane_username, password=SecretStr(dataplane_password)
        )
        validation_auth = DataplaneAuth(
            username=validation_username, password=SecretStr(validation_password)
        )

        return cls(dataplane=dataplane_auth, validation=validation_auth)


def _decode_field(val: Any) -> str | None:
    """Decode a secret field from string or base64 bytes.

    Args:
        val: Field value (string, bytes, or other)

    Returns:
        Decoded string value or None if invalid
    """
    if not val:
        return None

    if isinstance(val, bytes):
        try:
            return base64.b64decode(val).decode().strip()
        except (binascii.Error, UnicodeDecodeError, ValueError):
            return None

    if isinstance(val, str):
        # Kubernetes Secret values are always base64-encoded strings
        # We need to decode them to get the actual credential values
        try:
            return base64.b64decode(val.strip()).decode().strip()
        except (binascii.Error, UnicodeDecodeError, ValueError):
            # If base64 decoding fails, return the original string
            # This handles cases where the value might not be base64-encoded
            return val.strip()

    return None


def validate_k8s_name(ctx, param, name: str) -> str:
    """Validate Kubernetes resource name format.

    Args:
        ctx: Click context (unused)
        param: Click parameter (unused)
        name: Name to validate

    Returns:
        Validated name

    Raises:
        click.BadParameter: If name format is invalid
    """
    if (
        not name
        or len(name) > MAX_K8S_NAME_LENGTH
        or not re.match(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", name)
    ):
        raise click.BadParameter("Invalid K8s name format")
    return name
