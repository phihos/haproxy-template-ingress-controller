"""Tests for credential management with Pydantic models."""

import base64
import pytest
import click
from pydantic import ValidationError

from haproxy_template_ic.credentials import (
    Credentials,
    DataplaneAuth,
    validate_k8s_name,
    _decode_field,
)

# Test cases: (input_data, expected_success, expected_error_substring_or_None)
CREDENTIALS_TEST_CASES = [
    # Valid cases
    (
        {
            "dataplane_username": "admin",
            "dataplane_password": "pass1",
            "validation_username": "admin",
            "validation_password": "pass2",
        },
        True,
        None,
    ),
    # Base64 bytes
    (
        {
            "dataplane_username": b"YWRtaW4=",
            "dataplane_password": b"cGFzczE=",
            "validation_username": b"YWRtaW4=",
            "validation_password": b"cGFzczI=",
        },
        True,
        None,
    ),
    # Whitespace trimming in values
    (
        {
            "dataplane_username": " admin ",
            "dataplane_password": "pass1 ",
            "validation_username": "admin",
            "validation_password": " pass2 ",
        },
        True,
        None,
    ),
    # Error cases
    ({"dataplane_username": "admin"}, False, "Missing/invalid"),
    (
        {
            "dataplane_username": "admin",
            "dataplane_password": "",
            "validation_username": "admin",
            "validation_password": "pass",
        },
        False,
        "Missing/invalid",
    ),
    (
        {
            "dataplane_username": "admin",
            "dataplane_password": 123,
            "validation_username": "admin",
            "validation_password": "pass",
        },
        False,
        "Missing/invalid",
    ),
    (
        {
            "dataplane_username": b"invalid!",
            "dataplane_password": "pass",
            "validation_username": "admin",
            "validation_password": "pass",
        },
        False,
        "Missing/invalid",
    ),
]

K8S_NAME_CASES = [
    # Valid names
    ("valid-name", True),
    ("valid123", True),
    ("v", True),
    # Invalid names
    ("", False),
    ("toolong" * 50, False),
    ("Invalid", False),
    ("-invalid", False),
]


@pytest.mark.parametrize("data,success,error", CREDENTIALS_TEST_CASES)
def test_credentials_from_secret(data, success, error):
    """Test credential loading with various inputs."""
    if not success:
        with pytest.raises(ValueError, match=error):
            Credentials.from_secret(data)
    else:
        creds = Credentials.from_secret(data)
        assert isinstance(creds, Credentials)
        assert isinstance(creds.dataplane, DataplaneAuth)
        assert isinstance(creds.validation, DataplaneAuth)
        assert creds.dataplane.username == "admin"
        assert creds.dataplane.password.get_secret_value() == "pass1"
        assert creds.validation.username == "admin"
        assert creds.validation.password.get_secret_value() == "pass2"


def test_dataplane_auth_validation():
    """Test DataplaneAuth validation."""
    # Valid auth
    auth = DataplaneAuth(username="admin", password="secret")
    assert auth.username == "admin"
    assert auth.password.get_secret_value() == "secret"

    # Empty username should fail
    with pytest.raises(ValidationError):
        DataplaneAuth(username="", password="secret")

    # Empty password should fail
    with pytest.raises(ValidationError):
        DataplaneAuth(username="admin", password="")


def test_credentials_model_validation():
    """Test Credentials model validation."""
    dataplane_auth = DataplaneAuth(username="admin", password="adminpass")
    validation_auth = DataplaneAuth(username="validator", password="validpass")

    creds = Credentials(dataplane=dataplane_auth, validation=validation_auth)

    assert creds.dataplane == dataplane_auth
    assert creds.validation == validation_auth


def test_credentials_equality():
    """Test Credentials equality comparison."""
    creds1 = Credentials(
        dataplane=DataplaneAuth(username="admin", password="pass1"),
        validation=DataplaneAuth(username="admin", password="pass2"),
    )
    creds2 = Credentials(
        dataplane=DataplaneAuth(username="admin", password="pass1"),
        validation=DataplaneAuth(username="admin", password="pass2"),
    )
    creds3 = Credentials(
        dataplane=DataplaneAuth(username="admin", password="different"),
        validation=DataplaneAuth(username="admin", password="pass2"),
    )

    assert creds1 == creds2
    assert creds1 != creds3


@pytest.mark.parametrize("name,valid", K8S_NAME_CASES)
def test_k8s_name_validation(name, valid):
    """Test Kubernetes name validation."""
    if valid:
        assert validate_k8s_name(None, None, name) == name
    else:
        with pytest.raises(click.BadParameter):
            validate_k8s_name(None, None, name)


# Tests for _decode_field function to improve coverage


def test_decode_field_empty_values():
    """Test _decode_field with empty/None values."""
    assert _decode_field(None) is None
    assert _decode_field("") is None
    assert _decode_field(b"") is None


def test_decode_field_bytes_invalid_base64():
    """Test _decode_field with bytes that are not valid base64."""
    # Invalid base64 bytes
    invalid_base64 = b"not-valid-base64!!!"
    result = _decode_field(invalid_base64)
    assert result is None


def test_decode_field_bytes_invalid_unicode():
    """Test _decode_field with bytes that decode to invalid unicode."""
    # This creates bytes that are valid base64 but decode to invalid unicode

    invalid_unicode_bytes = base64.b64encode(b"\xff\xfe\xfd")
    result = _decode_field(invalid_unicode_bytes)
    assert result is None


def test_decode_field_bytes_value_error():
    """Test _decode_field with bytes that cause ValueError in base64 decode."""
    # Use invalid base64 length to trigger Error (which is subclass of ValueError)
    malformed_bytes = b"A"  # Single character - invalid base64 length
    result = _decode_field(malformed_bytes)
    assert result is None


def test_decode_field_string_fallback():
    """Test _decode_field string fallback when base64 decode fails."""
    # String that's not valid base64 - should return original
    non_base64_string = "plain-text-credential"
    result = _decode_field(non_base64_string)
    assert result == "plain-text-credential"


def test_decode_field_string_unicode_error_fallback():
    """Test _decode_field string unicode error fallback."""
    # Create a base64 string that decodes to invalid unicode

    invalid_unicode_b64 = base64.b64encode(b"\xff\xfe\xfd").decode("ascii")
    result = _decode_field(invalid_unicode_b64)
    # Should fall back to original string
    assert result == invalid_unicode_b64


def test_decode_field_string_value_error_fallback():
    """Test _decode_field string ValueError fallback."""
    # String with invalid base64 padding
    invalid_padding = "YWRtaW4"  # Missing padding
    result = _decode_field(invalid_padding)
    # Should fall back to original string
    assert result == "YWRtaW4"


def test_decode_field_non_string_non_bytes():
    """Test _decode_field with non-string, non-bytes input."""
    assert _decode_field(123) is None
    assert _decode_field([]) is None
    assert _decode_field({}) is None
    assert _decode_field(object()) is None
