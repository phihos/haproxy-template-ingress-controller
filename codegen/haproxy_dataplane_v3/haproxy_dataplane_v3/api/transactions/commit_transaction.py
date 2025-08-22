from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.configuration_transaction import ConfigurationTransaction
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: str,
    *,
    force_reload: Union[Unset, bool] = False,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["force_reload"] = force_reload

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/services/haproxy/transactions/{id}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ConfigurationTransaction, Error]]:
    if response.status_code == 200:
        response_200 = ConfigurationTransaction.from_dict(response.json())

        return response_200
    if response.status_code == 202:
        response_202 = ConfigurationTransaction.from_dict(response.json())

        return response_202
    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400
    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404
    if response.status_code == 406:
        response_406 = Error.from_dict(response.json())

        return response_406
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ConfigurationTransaction, Error]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[ConfigurationTransaction, Error]]:
    """Commit transaction

     Commit transaction, execute all operations in transaction and return msg

    Args:
        id (str):
        force_reload (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ConfigurationTransaction, Error]]
    """

    kwargs = _get_kwargs(
        id=id,
        force_reload=force_reload,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[ConfigurationTransaction, Error]]:
    """Commit transaction

     Commit transaction, execute all operations in transaction and return msg

    Args:
        id (str):
        force_reload (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ConfigurationTransaction, Error]
    """

    return sync_detailed(
        id=id,
        client=client,
        force_reload=force_reload,
    ).parsed


async def asyncio_detailed(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[ConfigurationTransaction, Error]]:
    """Commit transaction

     Commit transaction, execute all operations in transaction and return msg

    Args:
        id (str):
        force_reload (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ConfigurationTransaction, Error]]
    """

    kwargs = _get_kwargs(
        id=id,
        force_reload=force_reload,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[ConfigurationTransaction, Error]]:
    """Commit transaction

     Commit transaction, execute all operations in transaction and return msg

    Args:
        id (str):
        force_reload (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ConfigurationTransaction, Error]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            force_reload=force_reload,
        )
    ).parsed
