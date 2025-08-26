from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.consul_server import ConsulServer
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    *,
    body: ConsulServer,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/service_discovery/consul",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[ConsulServer, Error]:
    if response.status_code == 201:
        response_201 = ConsulServer.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

    if response.status_code == 409:
        response_409 = Error.from_dict(response.json())

        return response_409

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ConsulServer, Error]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ConsulServer,
) -> Response[Union[ConsulServer, Error]]:
    """Add a new Consul server

     Adds a new Consul server.

    Args:
        body (ConsulServer): Consul server configuration Example: {'address': '127.0.0.1',
            'enabled': True, 'id': '0', 'port': 90, 'retry_timeout': 10}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ConsulServer, Error]]
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
    body: ConsulServer,
) -> Optional[Union[ConsulServer, Error]]:
    """Add a new Consul server

     Adds a new Consul server.

    Args:
        body (ConsulServer): Consul server configuration Example: {'address': '127.0.0.1',
            'enabled': True, 'id': '0', 'port': 90, 'retry_timeout': 10}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ConsulServer, Error]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ConsulServer,
) -> Response[Union[ConsulServer, Error]]:
    """Add a new Consul server

     Adds a new Consul server.

    Args:
        body (ConsulServer): Consul server configuration Example: {'address': '127.0.0.1',
            'enabled': True, 'id': '0', 'port': 90, 'retry_timeout': 10}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ConsulServer, Error]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ConsulServer,
) -> Optional[Union[ConsulServer, Error]]:
    """Add a new Consul server

     Adds a new Consul server.

    Args:
        body (ConsulServer): Consul server configuration Example: {'address': '127.0.0.1',
            'enabled': True, 'id': '0', 'port': 90, 'retry_timeout': 10}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ConsulServer, Error]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
