from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.one_map_entry import OneMapEntry
from ...types import UNSET, Response, Unset


def _get_kwargs(
    parent_name: str,
    *,
    body: OneMapEntry,
    force_sync: Union[Unset, bool] = False,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["force_sync"] = force_sync

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/services/haproxy/runtime/maps/{parent_name}/entries",
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, OneMapEntry]]:
    if response.status_code == 201:
        response_201 = OneMapEntry.from_dict(response.json())

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
) -> Response[Union[Error, OneMapEntry]]:
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
    body: OneMapEntry,
    force_sync: Union[Unset, bool] = False,
) -> Response[Union[Error, OneMapEntry]]:
    """Adds an entry into the map file

     Adds an entry into the map file.

    Args:
        parent_name (str):
        force_sync (Union[Unset, bool]):  Default: False.
        body (OneMapEntry): One Map Entry

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, OneMapEntry]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        body=body,
        force_sync=force_sync,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: OneMapEntry,
    force_sync: Union[Unset, bool] = False,
) -> Optional[Union[Error, OneMapEntry]]:
    """Adds an entry into the map file

     Adds an entry into the map file.

    Args:
        parent_name (str):
        force_sync (Union[Unset, bool]):  Default: False.
        body (OneMapEntry): One Map Entry

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, OneMapEntry]
    """

    return sync_detailed(
        parent_name=parent_name,
        client=client,
        body=body,
        force_sync=force_sync,
    ).parsed


async def asyncio_detailed(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: OneMapEntry,
    force_sync: Union[Unset, bool] = False,
) -> Response[Union[Error, OneMapEntry]]:
    """Adds an entry into the map file

     Adds an entry into the map file.

    Args:
        parent_name (str):
        force_sync (Union[Unset, bool]):  Default: False.
        body (OneMapEntry): One Map Entry

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, OneMapEntry]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        body=body,
        force_sync=force_sync,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: OneMapEntry,
    force_sync: Union[Unset, bool] = False,
) -> Optional[Union[Error, OneMapEntry]]:
    """Adds an entry into the map file

     Adds an entry into the map file.

    Args:
        parent_name (str):
        force_sync (Union[Unset, bool]):  Default: False.
        body (OneMapEntry): One Map Entry

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, OneMapEntry]
    """

    return (
        await asyncio_detailed(
            parent_name=parent_name,
            client=client,
            body=body,
            force_sync=force_sync,
        )
    ).parsed
