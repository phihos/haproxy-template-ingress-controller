from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.certificate_load_action import CertificateLoadAction
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    certificate: str,
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
        "url": f"/services/haproxy/configuration/crt_loads/{certificate}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[CertificateLoadAction, Error]]:
    if response.status_code == 200:
        response_200 = CertificateLoadAction.from_dict(response.json())

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
) -> Response[Union[CertificateLoadAction, Error]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    certificate: str,
    *,
    client: Union[AuthenticatedClient, Client],
    crt_store: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[Union[CertificateLoadAction, Error]]:
    """Return one certificate load entry

     Returns one load entry by its certificate name in the specified crt_store

    Args:
        certificate (str):
        crt_store (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CertificateLoadAction, Error]]
    """

    kwargs = _get_kwargs(
        certificate=certificate,
        crt_store=crt_store,
        transaction_id=transaction_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    certificate: str,
    *,
    client: Union[AuthenticatedClient, Client],
    crt_store: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[Union[CertificateLoadAction, Error]]:
    """Return one certificate load entry

     Returns one load entry by its certificate name in the specified crt_store

    Args:
        certificate (str):
        crt_store (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CertificateLoadAction, Error]
    """

    return sync_detailed(
        certificate=certificate,
        client=client,
        crt_store=crt_store,
        transaction_id=transaction_id,
    ).parsed


async def asyncio_detailed(
    certificate: str,
    *,
    client: Union[AuthenticatedClient, Client],
    crt_store: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[Union[CertificateLoadAction, Error]]:
    """Return one certificate load entry

     Returns one load entry by its certificate name in the specified crt_store

    Args:
        certificate (str):
        crt_store (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CertificateLoadAction, Error]]
    """

    kwargs = _get_kwargs(
        certificate=certificate,
        crt_store=crt_store,
        transaction_id=transaction_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    certificate: str,
    *,
    client: Union[AuthenticatedClient, Client],
    crt_store: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[Union[CertificateLoadAction, Error]]:
    """Return one certificate load entry

     Returns one load entry by its certificate name in the specified crt_store

    Args:
        certificate (str):
        crt_store (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CertificateLoadAction, Error]
    """

    return (
        await asyncio_detailed(
            certificate=certificate,
            client=client,
            crt_store=crt_store,
            transaction_id=transaction_id,
        )
    ).parsed
