from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.group import Group
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    userlist: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["userlist"] = userlist

    params["transaction_id"] = transaction_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/services/haproxy/configuration/groups",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Optional[list["Group"]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for componentsschemasgroups_item_data in _response_200:
            componentsschemasgroups_item = Group.from_dict(componentsschemasgroups_item_data)

            response_200.append(componentsschemasgroups_item)

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Response[list["Group"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    userlist: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[list["Group"]]:
    """Return an array of userlist groups

    Args:
        userlist (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['Group']]
    """

    kwargs = _get_kwargs(
        userlist=userlist,
        transaction_id=transaction_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    userlist: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[list["Group"]]:
    """Return an array of userlist groups

    Args:
        userlist (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['Group']
    """

    return sync_detailed(
        client=client,
        userlist=userlist,
        transaction_id=transaction_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    userlist: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[list["Group"]]:
    """Return an array of userlist groups

    Args:
        userlist (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['Group']]
    """

    kwargs = _get_kwargs(
        userlist=userlist,
        transaction_id=transaction_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    userlist: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[list["Group"]]:
    """Return an array of userlist groups

    Args:
        userlist (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['Group']
    """

    return (
        await asyncio_detailed(
            client=client,
            userlist=userlist,
            transaction_id=transaction_id,
        )
    ).parsed
