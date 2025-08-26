from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.stick_table_entry import StickTableEntry
from ...types import UNSET, Response, Unset


def _get_kwargs(
    parent_name: str,
    *,
    filter_: Union[Unset, str] = UNSET,
    key: Union[Unset, str] = UNSET,
    count: Union[Unset, int] = UNSET,
    offset: Union[Unset, int] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["filter"] = filter_

    params["key"] = key

    params["count"] = count

    params["offset"] = offset

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/services/haproxy/runtime/stick_tables/{parent_name}/entries",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[Error, list["StickTableEntry"]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for componentsschemasstick_table_entries_item_data in _response_200:
            componentsschemasstick_table_entries_item = StickTableEntry.from_dict(
                componentsschemasstick_table_entries_item_data
            )

            response_200.append(componentsschemasstick_table_entries_item)

        return response_200

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, list["StickTableEntry"]]]:
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
    filter_: Union[Unset, str] = UNSET,
    key: Union[Unset, str] = UNSET,
    count: Union[Unset, int] = UNSET,
    offset: Union[Unset, int] = UNSET,
) -> Response[Union[Error, list["StickTableEntry"]]]:
    """Return Stick Table Entries

     Returns an array of all entries in a given stick tables.

    Args:
        parent_name (str):
        filter_ (Union[Unset, str]):
        key (Union[Unset, str]):
        count (Union[Unset, int]):
        offset (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['StickTableEntry']]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        filter_=filter_,
        key=key,
        count=count,
        offset=offset,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    filter_: Union[Unset, str] = UNSET,
    key: Union[Unset, str] = UNSET,
    count: Union[Unset, int] = UNSET,
    offset: Union[Unset, int] = UNSET,
) -> Optional[Union[Error, list["StickTableEntry"]]]:
    """Return Stick Table Entries

     Returns an array of all entries in a given stick tables.

    Args:
        parent_name (str):
        filter_ (Union[Unset, str]):
        key (Union[Unset, str]):
        count (Union[Unset, int]):
        offset (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['StickTableEntry']]
    """

    return sync_detailed(
        parent_name=parent_name,
        client=client,
        filter_=filter_,
        key=key,
        count=count,
        offset=offset,
    ).parsed


async def asyncio_detailed(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    filter_: Union[Unset, str] = UNSET,
    key: Union[Unset, str] = UNSET,
    count: Union[Unset, int] = UNSET,
    offset: Union[Unset, int] = UNSET,
) -> Response[Union[Error, list["StickTableEntry"]]]:
    """Return Stick Table Entries

     Returns an array of all entries in a given stick tables.

    Args:
        parent_name (str):
        filter_ (Union[Unset, str]):
        key (Union[Unset, str]):
        count (Union[Unset, int]):
        offset (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['StickTableEntry']]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        filter_=filter_,
        key=key,
        count=count,
        offset=offset,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    filter_: Union[Unset, str] = UNSET,
    key: Union[Unset, str] = UNSET,
    count: Union[Unset, int] = UNSET,
    offset: Union[Unset, int] = UNSET,
) -> Optional[Union[Error, list["StickTableEntry"]]]:
    """Return Stick Table Entries

     Returns an array of all entries in a given stick tables.

    Args:
        parent_name (str):
        filter_ (Union[Unset, str]):
        key (Union[Unset, str]):
        count (Union[Unset, int]):
        offset (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['StickTableEntry']]
    """

    return (
        await asyncio_detailed(
            parent_name=parent_name,
            client=client,
            filter_=filter_,
            key=key,
            count=count,
            offset=offset,
        )
    ).parsed
