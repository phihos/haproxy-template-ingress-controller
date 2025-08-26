from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.consul_server import ConsulServer
from ...models.error import Error
from ...types import Response


def _get_kwargs(
    id: str,
    *,
    body: ConsulServer,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/service_discovery/consul/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[ConsulServer, Error]:
    if response.status_code == 200:
        response_200 = ConsulServer.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404

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
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: ConsulServer,
) -> Response[Union[ConsulServer, Error]]:
    """Replace a Consul server

     Replaces a Consul server configuration by it's id.

    Args:
        id (str):
        body (ConsulServer): Consul server configuration Example: {'address': '127.0.0.1',
            'enabled': True, 'id': '0', 'port': 90, 'retry_timeout': 10}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ConsulServer, Error]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: ConsulServer,
) -> Optional[Union[ConsulServer, Error]]:
    """Replace a Consul server

     Replaces a Consul server configuration by it's id.

    Args:
        id (str):
        body (ConsulServer): Consul server configuration Example: {'address': '127.0.0.1',
            'enabled': True, 'id': '0', 'port': 90, 'retry_timeout': 10}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ConsulServer, Error]
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: ConsulServer,
) -> Response[Union[ConsulServer, Error]]:
    """Replace a Consul server

     Replaces a Consul server configuration by it's id.

    Args:
        id (str):
        body (ConsulServer): Consul server configuration Example: {'address': '127.0.0.1',
            'enabled': True, 'id': '0', 'port': 90, 'retry_timeout': 10}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ConsulServer, Error]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: ConsulServer,
) -> Optional[Union[ConsulServer, Error]]:
    """Replace a Consul server

     Replaces a Consul server configuration by it's id.

    Args:
        id (str):
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
            id=id,
            client=client,
            body=body,
        )
    ).parsed
