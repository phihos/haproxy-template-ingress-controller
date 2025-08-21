"""Tests for credential management with Pydantic models."""

import pytest
import click
from pydantic import ValidationError

from haproxy_template_ic.credentials import (
    Credentials,
    DataplaneAuth,
    validate_k8s_name,
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
