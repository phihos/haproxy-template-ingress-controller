from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.configuration_transaction import ConfigurationTransaction
from ...models.error import Error
from ...models.start_transaction_response_429 import StartTransactionResponse429
from ...types import UNSET, Response


def _get_kwargs(
    *,
    version: int,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["version"] = version

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/services/haproxy/transactions",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[ConfigurationTransaction, Error, StartTransactionResponse429]:
    if response.status_code == 201:
        response_201 = ConfigurationTransaction.from_dict(response.json())

        return response_201

    if response.status_code == 429:
        response_429 = StartTransactionResponse429.from_dict(response.json())

        return response_429

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ConfigurationTransaction, Error, StartTransactionResponse429]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    version: int,
) -> Response[Union[ConfigurationTransaction, Error, StartTransactionResponse429]]:
    """Start a new transaction

     Starts a new transaction and returns it's id

    Args:
        version (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ConfigurationTransaction, Error, StartTransactionResponse429]]
    """

    kwargs = _get_kwargs(
        version=version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    version: int,
) -> Optional[Union[ConfigurationTransaction, Error, StartTransactionResponse429]]:
    """Start a new transaction

     Starts a new transaction and returns it's id

    Args:
        version (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ConfigurationTransaction, Error, StartTransactionResponse429]
    """

    return sync_detailed(
        client=client,
        version=version,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    version: int,
) -> Response[Union[ConfigurationTransaction, Error, StartTransactionResponse429]]:
    """Start a new transaction

     Starts a new transaction and returns it's id

    Args:
        version (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ConfigurationTransaction, Error, StartTransactionResponse429]]
    """

    kwargs = _get_kwargs(
        version=version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    version: int,
) -> Optional[Union[ConfigurationTransaction, Error, StartTransactionResponse429]]:
    """Start a new transaction

     Starts a new transaction and returns it's id

    Args:
        version (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ConfigurationTransaction, Error, StartTransactionResponse429]
    """

    return (
        await asyncio_detailed(
            client=client,
            version=version,
        )
    ).parsed
