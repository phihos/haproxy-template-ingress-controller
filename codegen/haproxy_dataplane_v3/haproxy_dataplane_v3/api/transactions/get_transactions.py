from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.configuration_transaction import ConfigurationTransaction
from ...models.error import Error
from ...models.get_transactions_status import GetTransactionsStatus
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    status: Union[Unset, GetTransactionsStatus] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_status: Union[Unset, str] = UNSET
    if not isinstance(status, Unset):
        json_status = status.value

    params["status"] = json_status

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/services/haproxy/transactions",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[Error, list["ConfigurationTransaction"]]:
    if response.status_code == 200:
        _response_200 = response.json()
        response_200 = []
        for componentsschemastransactions_item_data in _response_200:
            componentsschemastransactions_item = ConfigurationTransaction.from_dict(
                componentsschemastransactions_item_data
            )

            response_200.append(componentsschemastransactions_item)

        return response_200

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, list["ConfigurationTransaction"]]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    status: Union[Unset, GetTransactionsStatus] = UNSET,
) -> Response[Union[Error, list["ConfigurationTransaction"]]]:
    """Return list of HAProxy configuration transactions.

     Returns a list of HAProxy configuration transactions. Transactions can be filtered by their status.

    Args:
        status (Union[Unset, GetTransactionsStatus]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['ConfigurationTransaction']]]
    """

    kwargs = _get_kwargs(
        status=status,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    status: Union[Unset, GetTransactionsStatus] = UNSET,
) -> Optional[Union[Error, list["ConfigurationTransaction"]]]:
    """Return list of HAProxy configuration transactions.

     Returns a list of HAProxy configuration transactions. Transactions can be filtered by their status.

    Args:
        status (Union[Unset, GetTransactionsStatus]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['ConfigurationTransaction']]
    """

    return sync_detailed(
        client=client,
        status=status,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    status: Union[Unset, GetTransactionsStatus] = UNSET,
) -> Response[Union[Error, list["ConfigurationTransaction"]]]:
    """Return list of HAProxy configuration transactions.

     Returns a list of HAProxy configuration transactions. Transactions can be filtered by their status.

    Args:
        status (Union[Unset, GetTransactionsStatus]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['ConfigurationTransaction']]]
    """

    kwargs = _get_kwargs(
        status=status,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    status: Union[Unset, GetTransactionsStatus] = UNSET,
) -> Optional[Union[Error, list["ConfigurationTransaction"]]]:
    """Return list of HAProxy configuration transactions.

     Returns a list of HAProxy configuration transactions. Transactions can be filtered by their status.

    Args:
        status (Union[Unset, GetTransactionsStatus]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['ConfigurationTransaction']]
    """

    return (
        await asyncio_detailed(
            client=client,
            status=status,
        )
    ).parsed
