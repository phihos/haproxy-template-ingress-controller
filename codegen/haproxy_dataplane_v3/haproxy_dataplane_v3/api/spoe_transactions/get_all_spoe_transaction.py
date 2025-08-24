from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_spoe_transaction_status import GetAllSpoeTransactionStatus
from ...models.spoe_configuration_transaction import SPOEConfigurationTransaction
from ...types import UNSET, Response, Unset


def _get_kwargs(
    parent_name: str,
    *,
    status: Union[Unset, GetAllSpoeTransactionStatus] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_status: Union[Unset, str] = UNSET
    if not isinstance(status, Unset):
        json_status = status.value

    params["status"] = json_status

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/services/haproxy/spoe/spoe_files/{parent_name}/transactions",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[list["SPOEConfigurationTransaction"]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for componentsschemasspoe_transactions_item_data in _response_200:
            componentsschemasspoe_transactions_item = SPOEConfigurationTransaction.from_dict(
                componentsschemasspoe_transactions_item_data
            )

            response_200.append(componentsschemasspoe_transactions_item)

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[list["SPOEConfigurationTransaction"]]:
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
    status: Union[Unset, GetAllSpoeTransactionStatus] = UNSET,
) -> Response[list["SPOEConfigurationTransaction"]]:
    """Return list of SPOE configuration transactions.

     Returns a list of SPOE configuration transactions. Transactions can be filtered by their status.

    Args:
        parent_name (str):
        status (Union[Unset, GetAllSpoeTransactionStatus]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['SPOEConfigurationTransaction']]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        status=status,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    status: Union[Unset, GetAllSpoeTransactionStatus] = UNSET,
) -> Optional[list["SPOEConfigurationTransaction"]]:
    """Return list of SPOE configuration transactions.

     Returns a list of SPOE configuration transactions. Transactions can be filtered by their status.

    Args:
        parent_name (str):
        status (Union[Unset, GetAllSpoeTransactionStatus]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['SPOEConfigurationTransaction']
    """

    return sync_detailed(
        parent_name=parent_name,
        client=client,
        status=status,
    ).parsed


async def asyncio_detailed(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    status: Union[Unset, GetAllSpoeTransactionStatus] = UNSET,
) -> Response[list["SPOEConfigurationTransaction"]]:
    """Return list of SPOE configuration transactions.

     Returns a list of SPOE configuration transactions. Transactions can be filtered by their status.

    Args:
        parent_name (str):
        status (Union[Unset, GetAllSpoeTransactionStatus]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['SPOEConfigurationTransaction']]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        status=status,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    status: Union[Unset, GetAllSpoeTransactionStatus] = UNSET,
) -> Optional[list["SPOEConfigurationTransaction"]]:
    """Return list of SPOE configuration transactions.

     Returns a list of SPOE configuration transactions. Transactions can be filtered by their status.

    Args:
        parent_name (str):
        status (Union[Unset, GetAllSpoeTransactionStatus]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['SPOEConfigurationTransaction']
    """

    return (
        await asyncio_detailed(
            parent_name=parent_name,
            client=client,
            status=status,
        )
    ).parsed
