from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.ssl_frontend_use_certificate import SSLFrontendUseCertificate
from ...types import UNSET, Response, Unset


def _get_kwargs(
    parent_name: str,
    *,
    transaction_id: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["transaction_id"] = transaction_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/services/haproxy/configuration/frontends/{parent_name}/ssl_front_uses",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[list["SSLFrontendUseCertificate"]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for componentsschemasssl_front_uses_item_data in _response_200:
            componentsschemasssl_front_uses_item = SSLFrontendUseCertificate.from_dict(
                componentsschemasssl_front_uses_item_data
            )

            response_200.append(componentsschemasssl_front_uses_item)

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[list["SSLFrontendUseCertificate"]]:
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
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[list["SSLFrontendUseCertificate"]]:
    """Return an array of SSLFrontUses

     Returns an array of all SSLFrontUses that are configured in specified frontend.

    Args:
        parent_name (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['SSLFrontendUseCertificate']]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        transaction_id=transaction_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[list["SSLFrontendUseCertificate"]]:
    """Return an array of SSLFrontUses

     Returns an array of all SSLFrontUses that are configured in specified frontend.

    Args:
        parent_name (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['SSLFrontendUseCertificate']
    """

    return sync_detailed(
        parent_name=parent_name,
        client=client,
        transaction_id=transaction_id,
    ).parsed


async def asyncio_detailed(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[list["SSLFrontendUseCertificate"]]:
    """Return an array of SSLFrontUses

     Returns an array of all SSLFrontUses that are configured in specified frontend.

    Args:
        parent_name (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['SSLFrontendUseCertificate']]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        transaction_id=transaction_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[list["SSLFrontendUseCertificate"]]:
    """Return an array of SSLFrontUses

     Returns an array of all SSLFrontUses that are configured in specified frontend.

    Args:
        parent_name (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['SSLFrontendUseCertificate']
    """

    return (
        await asyncio_detailed(
            parent_name=parent_name,
            client=client,
            transaction_id=transaction_id,
        )
    ).parsed
