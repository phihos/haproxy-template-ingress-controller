from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.one_map_entry import OneMapEntry
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    body: list["OneMapEntry"],
    force_sync: Union[Unset, bool] = False,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["force_sync"] = force_sync

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/services/haproxy/runtime/maps/{name}",
        "params": params,
    }

    _body = []
    for componentsschemasmap_entries_item_data in body:
        componentsschemasmap_entries_item = componentsschemasmap_entries_item_data.to_dict()
        _body.append(componentsschemasmap_entries_item)

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, list["OneMapEntry"]]]:
    if response.status_code == 201:
        response_201 = []
        _response_201 = response.json()
        for componentsschemasmap_entries_item_data in _response_201:
            componentsschemasmap_entries_item = OneMapEntry.from_dict(componentsschemasmap_entries_item_data)

            response_201.append(componentsschemasmap_entries_item)

        return response_201
    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, list["OneMapEntry"]]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: list["OneMapEntry"],
    force_sync: Union[Unset, bool] = False,
) -> Response[Union[Error, list["OneMapEntry"]]]:
    """Add a new map payload

     Adds a new map payload.

    Args:
        name (str):
        force_sync (Union[Unset, bool]):  Default: False.
        body (list['OneMapEntry']): Entries of one runtime map

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['OneMapEntry']]]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        force_sync=force_sync,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: list["OneMapEntry"],
    force_sync: Union[Unset, bool] = False,
) -> Optional[Union[Error, list["OneMapEntry"]]]:
    """Add a new map payload

     Adds a new map payload.

    Args:
        name (str):
        force_sync (Union[Unset, bool]):  Default: False.
        body (list['OneMapEntry']): Entries of one runtime map

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['OneMapEntry']]
    """

    return sync_detailed(
        name=name,
        client=client,
        body=body,
        force_sync=force_sync,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: list["OneMapEntry"],
    force_sync: Union[Unset, bool] = False,
) -> Response[Union[Error, list["OneMapEntry"]]]:
    """Add a new map payload

     Adds a new map payload.

    Args:
        name (str):
        force_sync (Union[Unset, bool]):  Default: False.
        body (list['OneMapEntry']): Entries of one runtime map

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['OneMapEntry']]]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        force_sync=force_sync,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: list["OneMapEntry"],
    force_sync: Union[Unset, bool] = False,
) -> Optional[Union[Error, list["OneMapEntry"]]]:
    """Add a new map payload

     Adds a new map payload.

    Args:
        name (str):
        force_sync (Union[Unset, bool]):  Default: False.
        body (list['OneMapEntry']): Entries of one runtime map

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['OneMapEntry']]
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
            force_sync=force_sync,
        )
    ).parsed
