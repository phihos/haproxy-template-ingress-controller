from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.runtime_add_server import RuntimeAddServer
from ...types import Response


def _get_kwargs(
    parent_name: str,
    *,
    body: RuntimeAddServer,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/services/haproxy/runtime/backends/{parent_name}/servers",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[Error, RuntimeAddServer]:
    if response.status_code == 201:
        response_201 = RuntimeAddServer.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = Error.from_dict(response.json())

        return response_409

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, RuntimeAddServer]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: RuntimeAddServer,
) -> Response[Union[Error, RuntimeAddServer]]:
    """Adds a new server to a backend

     Adds a new server to the specified backend

    Args:
        parent_name (str):
        body (RuntimeAddServer): Settable properties when adding a new server using HAProxy's
            runtime.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, RuntimeAddServer]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: RuntimeAddServer,
) -> Optional[Union[Error, RuntimeAddServer]]:
    """Adds a new server to a backend

     Adds a new server to the specified backend

    Args:
        parent_name (str):
        body (RuntimeAddServer): Settable properties when adding a new server using HAProxy's
            runtime.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, RuntimeAddServer]
    """

    return sync_detailed(
        parent_name=parent_name,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: RuntimeAddServer,
) -> Response[Union[Error, RuntimeAddServer]]:
    """Adds a new server to a backend

     Adds a new server to the specified backend

    Args:
        parent_name (str):
        body (RuntimeAddServer): Settable properties when adding a new server using HAProxy's
            runtime.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, RuntimeAddServer]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: RuntimeAddServer,
) -> Optional[Union[Error, RuntimeAddServer]]:
    """Adds a new server to a backend

     Adds a new server to the specified backend

    Args:
        parent_name (str):
        body (RuntimeAddServer): Settable properties when adding a new server using HAProxy's
            runtime.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, RuntimeAddServer]
    """

    return (
        await asyncio_detailed(
            parent_name=parent_name,
            client=client,
            body=body,
        )
    ).parsed
