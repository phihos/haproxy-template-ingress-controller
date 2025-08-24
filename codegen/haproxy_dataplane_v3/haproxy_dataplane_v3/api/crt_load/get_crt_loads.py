from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.certificate_load_action import CertificateLoadAction
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    crt_store: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["crt_store"] = crt_store

    params["transaction_id"] = transaction_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/services/haproxy/configuration/crt_loads",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[list["CertificateLoadAction"]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for componentsschemascrt_loads_item_data in _response_200:
            componentsschemascrt_loads_item = CertificateLoadAction.from_dict(componentsschemascrt_loads_item_data)

            response_200.append(componentsschemascrt_loads_item)

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[list["CertificateLoadAction"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    crt_store: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[list["CertificateLoadAction"]]:
    """Return an array of loaded certificates

     Returns the list of loaded certificates from the specified crt_store

    Args:
        crt_store (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['CertificateLoadAction']]
    """

    kwargs = _get_kwargs(
        crt_store=crt_store,
        transaction_id=transaction_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    crt_store: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[list["CertificateLoadAction"]]:
    """Return an array of loaded certificates

     Returns the list of loaded certificates from the specified crt_store

    Args:
        crt_store (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['CertificateLoadAction']
    """

    return sync_detailed(
        client=client,
        crt_store=crt_store,
        transaction_id=transaction_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    crt_store: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[list["CertificateLoadAction"]]:
    """Return an array of loaded certificates

     Returns the list of loaded certificates from the specified crt_store

    Args:
        crt_store (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['CertificateLoadAction']]
    """

    kwargs = _get_kwargs(
        crt_store=crt_store,
        transaction_id=transaction_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    crt_store: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[list["CertificateLoadAction"]]:
    """Return an array of loaded certificates

     Returns the list of loaded certificates from the specified crt_store

    Args:
        crt_store (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['CertificateLoadAction']
    """

    return (
        await asyncio_detailed(
            client=client,
            crt_store=crt_store,
            transaction_id=transaction_id,
        )
    ).parsed
