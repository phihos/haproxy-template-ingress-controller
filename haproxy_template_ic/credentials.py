"""Credential management for HAProxy Template IC."""

import base64
import binascii
import logging
import re
from typing import Any, cast

import click
from pydantic import BaseModel, Field, SecretStr, ConfigDict

from haproxy_template_ic.constants import MAX_K8S_NAME_LENGTH

logger = logging.getLogger(__name__)


class DataplaneAuth(BaseModel):
    """Authentication configuration for HAProxy Dataplane API."""

    username: str = Field(..., min_length=1, description="Username for Dataplane API")
    password: SecretStr = Field(
        ..., min_length=1, description="Password for Dataplane API"
    )

    model_config = ConfigDict(frozen=True)


class Credentials(BaseModel):
    """Credentials for HAProxy instances loaded from Kubernetes Secret."""

    dataplane: DataplaneAuth = Field(
        ..., description="Production dataplane authentication"
    )
    validation: DataplaneAuth = Field(
        ..., description="Validation dataplane authentication"
    )

    model_config = ConfigDict(frozen=True)

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
            raise ValueError(f"Missing/invalid credential fields: {missing_fields}")

        # Create auth objects with validated fields
        # Type safety: These fields are guaranteed non-None after validation above
        if not all(
            [
                dataplane_username,
                dataplane_password,
                validation_username,
                validation_password,
            ]
        ):
            raise RuntimeError("Internal error: validated fields should not be None")

        dataplane_auth = DataplaneAuth(
            username=cast(str, dataplane_username),
            password=SecretStr(cast(str, dataplane_password)),
        )
        validation_auth = DataplaneAuth(
            username=cast(str, validation_username),
            password=SecretStr(cast(str, validation_password)),
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
        except binascii.Error as e:
            logger.debug(f"Base64 decode error for bytes value: {e}")
            return None
        except UnicodeDecodeError as e:
            logger.debug(f"Unicode decode error for bytes value: {e}")
            return None
        except ValueError as e:
            logger.debug(f"Value error decoding bytes: {e}")
            return None

    if isinstance(val, str):
        # Kubernetes Secret values are always base64-encoded strings
        # We need to decode them to get the actual credential values
        try:
            return base64.b64decode(val.strip()).decode().strip()
        except binascii.Error as e:
            logger.debug(f"Base64 decode error for string value, using original: {e}")
            return val.strip()
        except UnicodeDecodeError as e:
            logger.debug(f"Unicode decode error for string value, using original: {e}")
            return val.strip()
        except ValueError as e:
            logger.debug(f"Value error decoding string, using original: {e}")
            return val.strip()

    return None


def validate_k8s_name(_ctx, _param, name: str) -> str:
    """Validate Kubernetes resource name format.

    Args:
        _ctx: Click context (unused)
        _param: Click parameter (unused)
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
