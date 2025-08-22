from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.ssl_crt_list_entry import SSLCrtListEntry
from ...types import UNSET, Response


def _get_kwargs(
    *,
    name: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["name"] = name

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/services/haproxy/runtime/ssl_crt_lists/entries",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[list["SSLCrtListEntry"]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for componentsschemasssl_crt_list_entries_item_data in _response_200:
            componentsschemasssl_crt_list_entries_item = SSLCrtListEntry.from_dict(
                componentsschemasssl_crt_list_entries_item_data
            )

            response_200.append(componentsschemasssl_crt_list_entries_item)

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[list["SSLCrtListEntry"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    name: str,
) -> Response[list["SSLCrtListEntry"]]:
    """Get all the entries inside a crt-list

     Returns an array of entries present inside the given crt-list file. Their index can be used to
    delete them.

    Args:
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['SSLCrtListEntry']]
    """

    kwargs = _get_kwargs(
        name=name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    name: str,
) -> Optional[list["SSLCrtListEntry"]]:
    """Get all the entries inside a crt-list

     Returns an array of entries present inside the given crt-list file. Their index can be used to
    delete them.

    Args:
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['SSLCrtListEntry']
    """

    return sync_detailed(
        client=client,
        name=name,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    name: str,
) -> Response[list["SSLCrtListEntry"]]:
    """Get all the entries inside a crt-list

     Returns an array of entries present inside the given crt-list file. Their index can be used to
    delete them.

    Args:
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['SSLCrtListEntry']]
    """

    kwargs = _get_kwargs(
        name=name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    name: str,
) -> Optional[list["SSLCrtListEntry"]]:
    """Get all the entries inside a crt-list

     Returns an array of entries present inside the given crt-list file. Their index can be used to
    delete them.

    Args:
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['SSLCrtListEntry']
    """

    return (
        await asyncio_detailed(
            client=client,
            name=name,
        )
    ).parsed
