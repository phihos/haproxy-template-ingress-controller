from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.runtime_server import RuntimeServer
from ...types import Response


def _get_kwargs(
    parent_name: str,
    name: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/services/haproxy/runtime/backends/{parent_name}/servers/{name}",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, RuntimeServer]]:
    if response.status_code == 200:
        response_200 = RuntimeServer.from_dict(response.json())

        return response_200
    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, RuntimeServer]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    parent_name: str,
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[Error, RuntimeServer]]:
    """Return one server runtime settings

     Returns one server runtime settings by it's name in the specified backend.

    Args:
        parent_name (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, RuntimeServer]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        name=name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    parent_name: str,
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[Error, RuntimeServer]]:
    """Return one server runtime settings

     Returns one server runtime settings by it's name in the specified backend.

    Args:
        parent_name (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, RuntimeServer]
    """

    return sync_detailed(
        parent_name=parent_name,
        name=name,
        client=client,
    ).parsed


async def asyncio_detailed(
    parent_name: str,
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[Error, RuntimeServer]]:
    """Return one server runtime settings

     Returns one server runtime settings by it's name in the specified backend.

    Args:
        parent_name (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, RuntimeServer]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        name=name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    parent_name: str,
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[Error, RuntimeServer]]:
    """Return one server runtime settings

     Returns one server runtime settings by it's name in the specified backend.

    Args:
        parent_name (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, RuntimeServer]
    """

    return (
        await asyncio_detailed(
            parent_name=parent_name,
            name=name,
            client=client,
        )
    ).parsed
