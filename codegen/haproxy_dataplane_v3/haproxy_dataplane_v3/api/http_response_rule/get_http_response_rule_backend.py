from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.http_response_rule import HTTPResponseRule
from ...types import UNSET, Response, Unset


def _get_kwargs(
    parent_name: str,
    index: int,
    *,
    transaction_id: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["transaction_id"] = transaction_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/services/haproxy/configuration/backends/{parent_name}/http_response_rules/{index}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, HTTPResponseRule]]:
    if response.status_code == 200:
        response_200 = HTTPResponseRule.from_dict(response.json())

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
) -> Response[Union[Error, HTTPResponseRule]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    parent_name: str,
    index: int,
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[Union[Error, HTTPResponseRule]]:
    """Return one HTTP Response Rule

     Returns one HTTP Response Rule configuration by it's index in the specified parent.

    Args:
        parent_name (str):
        index (int):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, HTTPResponseRule]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        index=index,
        transaction_id=transaction_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    parent_name: str,
    index: int,
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[Union[Error, HTTPResponseRule]]:
    """Return one HTTP Response Rule

     Returns one HTTP Response Rule configuration by it's index in the specified parent.

    Args:
        parent_name (str):
        index (int):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, HTTPResponseRule]
    """

    return sync_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        transaction_id=transaction_id,
    ).parsed


async def asyncio_detailed(
    parent_name: str,
    index: int,
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[Union[Error, HTTPResponseRule]]:
    """Return one HTTP Response Rule

     Returns one HTTP Response Rule configuration by it's index in the specified parent.

    Args:
        parent_name (str):
        index (int):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, HTTPResponseRule]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        index=index,
        transaction_id=transaction_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    parent_name: str,
    index: int,
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[Union[Error, HTTPResponseRule]]:
    """Return one HTTP Response Rule

     Returns one HTTP Response Rule configuration by it's index in the specified parent.

    Args:
        parent_name (str):
        index (int):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, HTTPResponseRule]
    """

    return (
        await asyncio_detailed(
            parent_name=parent_name,
            index=index,
            client=client,
            transaction_id=transaction_id,
        )
    ).parsed
