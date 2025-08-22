from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.one_map_entry import OneMapEntry
from ...types import Response


def _get_kwargs(
    parent_name: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/services/haproxy/runtime/maps/{parent_name}/entries",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, list["OneMapEntry"]]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for componentsschemasmap_entries_item_data in _response_200:
            componentsschemasmap_entries_item = OneMapEntry.from_dict(componentsschemasmap_entries_item_data)

            response_200.append(componentsschemasmap_entries_item)

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
) -> Response[Union[Error, list["OneMapEntry"]]]:
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
) -> Response[Union[Error, list["OneMapEntry"]]]:
    """Return one map runtime entries

     Returns an array of all entries in a given runtime map file.

    Args:
        parent_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['OneMapEntry']]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[Error, list["OneMapEntry"]]]:
    """Return one map runtime entries

     Returns an array of all entries in a given runtime map file.

    Args:
        parent_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['OneMapEntry']]
    """

    return sync_detailed(
        parent_name=parent_name,
        client=client,
    ).parsed


async def asyncio_detailed(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[Error, list["OneMapEntry"]]]:
    """Return one map runtime entries

     Returns an array of all entries in a given runtime map file.

    Args:
        parent_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['OneMapEntry']]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[Error, list["OneMapEntry"]]]:
    """Return one map runtime entries

     Returns an array of all entries in a given runtime map file.

    Args:
        parent_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['OneMapEntry']]
    """

    return (
        await asyncio_detailed(
            parent_name=parent_name,
            client=client,
        )
    ).parsed
