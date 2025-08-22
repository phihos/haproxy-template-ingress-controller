from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_stats_type import GetStatsType
from ...models.stats_array import StatsArray
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    type_: Union[Unset, GetStatsType] = UNSET,
    name: Union[Unset, str] = UNSET,
    parent: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_type_: Union[Unset, str] = UNSET
    if not isinstance(type_, Unset):
        json_type_ = type_.value

    params["type"] = json_type_

    params["name"] = name

    params["parent"] = parent

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/services/haproxy/stats/native",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Optional[StatsArray]:
    if response.status_code == 200:
        response_200 = StatsArray.from_dict(response.json())

        return response_200
    if response.status_code == 500:
        response_500 = StatsArray.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Response[StatsArray]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    type_: Union[Unset, GetStatsType] = UNSET,
    name: Union[Unset, str] = UNSET,
    parent: Union[Unset, str] = UNSET,
) -> Response[StatsArray]:
    """Gets stats

     Getting stats from the HAProxy.

    Args:
        type_ (Union[Unset, GetStatsType]):
        name (Union[Unset, str]):
        parent (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[StatsArray]
    """

    kwargs = _get_kwargs(
        type_=type_,
        name=name,
        parent=parent,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    type_: Union[Unset, GetStatsType] = UNSET,
    name: Union[Unset, str] = UNSET,
    parent: Union[Unset, str] = UNSET,
) -> Optional[StatsArray]:
    """Gets stats

     Getting stats from the HAProxy.

    Args:
        type_ (Union[Unset, GetStatsType]):
        name (Union[Unset, str]):
        parent (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        StatsArray
    """

    return sync_detailed(
        client=client,
        type_=type_,
        name=name,
        parent=parent,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    type_: Union[Unset, GetStatsType] = UNSET,
    name: Union[Unset, str] = UNSET,
    parent: Union[Unset, str] = UNSET,
) -> Response[StatsArray]:
    """Gets stats

     Getting stats from the HAProxy.

    Args:
        type_ (Union[Unset, GetStatsType]):
        name (Union[Unset, str]):
        parent (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[StatsArray]
    """

    kwargs = _get_kwargs(
        type_=type_,
        name=name,
        parent=parent,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    type_: Union[Unset, GetStatsType] = UNSET,
    name: Union[Unset, str] = UNSET,
    parent: Union[Unset, str] = UNSET,
) -> Optional[StatsArray]:
    """Gets stats

     Getting stats from the HAProxy.

    Args:
        type_ (Union[Unset, GetStatsType]):
        name (Union[Unset, str]):
        parent (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        StatsArray
    """

    return (
        await asyncio_detailed(
            client=client,
            type_=type_,
            name=name,
            parent=parent,
        )
    ).parsed
