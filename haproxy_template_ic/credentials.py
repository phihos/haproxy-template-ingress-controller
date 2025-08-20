"""Credential management for HAProxy Template IC."""

import base64
import re
from typing import Any

import click
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
        fields = [
            "dataplane_username",
            "dataplane_password",
            "validation_username",
            "validation_password",
        ]

        # Decode all fields
        vals = [_decode_field(data.get(f)) for f in fields]

        # Check for missing/invalid fields
        if None in vals:
            missing = [fields[i] for i, v in enumerate(vals) if v is None]
            raise ValueError(f"Missing/invalid credential fields: {missing}")

        # Create auth objects - vals are guaranteed to be str after None check
        dataplane_auth = DataplaneAuth(username=vals[0], password=vals[1])  # type: ignore[arg-type]
        validation_auth = DataplaneAuth(username=vals[2], password=vals[3])  # type: ignore[arg-type]

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
        except Exception:
            return None

    return str(val).strip() if isinstance(val, str) else None


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
        or len(name) > 253
        or not re.match(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", name)
    ):
        raise click.BadParameter("Invalid K8s name format")
    return name
