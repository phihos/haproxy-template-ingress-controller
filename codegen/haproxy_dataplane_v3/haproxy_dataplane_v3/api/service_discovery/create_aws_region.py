from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.aws_region import AWSRegion
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    *,
    body: AWSRegion,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/service_discovery/aws",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[AWSRegion, Error]]:
    if response.status_code == 201:
        response_201 = AWSRegion.from_dict(response.json())

        return response_201
    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400
    if response.status_code == 409:
        response_409 = Error.from_dict(response.json())

        return response_409
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[AWSRegion, Error]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AWSRegion,
) -> Response[Union[AWSRegion, Error]]:
    """Add a new AWS region

     Add a new AWS region.
    Credentials are not required in case Dataplane API is running in an EC2 instance with proper IAM
    role attached.

    Args:
        body (AWSRegion): AWS region configuration Example: {'access_key_id':
            '****************L7GT', 'allowlist': [{'key': 'tag-key', 'value':
            'Instance:Having:This:Tag'}], 'denylist': [{'key': 'tag:Environment', 'value':
            'development'}], 'enabled': True, 'id': '0', 'ipv4_address': 'private', 'name': 'frontend-
            service', 'region': 'us-east-1', 'retry_timeout': 1, 'secret_access_key':
            '****************soLl'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AWSRegion, Error]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AWSRegion,
) -> Optional[Union[AWSRegion, Error]]:
    """Add a new AWS region

     Add a new AWS region.
    Credentials are not required in case Dataplane API is running in an EC2 instance with proper IAM
    role attached.

    Args:
        body (AWSRegion): AWS region configuration Example: {'access_key_id':
            '****************L7GT', 'allowlist': [{'key': 'tag-key', 'value':
            'Instance:Having:This:Tag'}], 'denylist': [{'key': 'tag:Environment', 'value':
            'development'}], 'enabled': True, 'id': '0', 'ipv4_address': 'private', 'name': 'frontend-
            service', 'region': 'us-east-1', 'retry_timeout': 1, 'secret_access_key':
            '****************soLl'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AWSRegion, Error]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AWSRegion,
) -> Response[Union[AWSRegion, Error]]:
    """Add a new AWS region

     Add a new AWS region.
    Credentials are not required in case Dataplane API is running in an EC2 instance with proper IAM
    role attached.

    Args:
        body (AWSRegion): AWS region configuration Example: {'access_key_id':
            '****************L7GT', 'allowlist': [{'key': 'tag-key', 'value':
            'Instance:Having:This:Tag'}], 'denylist': [{'key': 'tag:Environment', 'value':
            'development'}], 'enabled': True, 'id': '0', 'ipv4_address': 'private', 'name': 'frontend-
            service', 'region': 'us-east-1', 'retry_timeout': 1, 'secret_access_key':
            '****************soLl'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AWSRegion, Error]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: AWSRegion,
) -> Optional[Union[AWSRegion, Error]]:
    """Add a new AWS region

     Add a new AWS region.
    Credentials are not required in case Dataplane API is running in an EC2 instance with proper IAM
    role attached.

    Args:
        body (AWSRegion): AWS region configuration Example: {'access_key_id':
            '****************L7GT', 'allowlist': [{'key': 'tag-key', 'value':
            'Instance:Having:This:Tag'}], 'denylist': [{'key': 'tag:Environment', 'value':
            'development'}], 'enabled': True, 'id': '0', 'ipv4_address': 'private', 'name': 'frontend-
            service', 'region': 'us-east-1', 'retry_timeout': 1, 'secret_access_key':
            '****************soLl'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AWSRegion, Error]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
