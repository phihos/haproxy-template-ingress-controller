from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.fcgi_app import FcgiApp
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    transaction_id: Union[Unset, str] = UNSET,
    full_section: Union[Unset, bool] = False,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["transaction_id"] = transaction_id

    params["full_section"] = full_section

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/services/haproxy/configuration/fcgi_apps/{name}",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Union[Error, FcgiApp]:
    if response.status_code == 200:
        response_200 = FcgiApp.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, FcgiApp]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
    full_section: Union[Unset, bool] = False,
) -> Response[Union[Error, FcgiApp]]:
    """Return a FCGI app

     Returns one FCGI application configuration by its name.

    Args:
        name (str):
        transaction_id (Union[Unset, str]):
        full_section (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, FcgiApp]]
    """

    kwargs = _get_kwargs(
        name=name,
        transaction_id=transaction_id,
        full_section=full_section,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
    full_section: Union[Unset, bool] = False,
) -> Optional[Union[Error, FcgiApp]]:
    """Return a FCGI app

     Returns one FCGI application configuration by its name.

    Args:
        name (str):
        transaction_id (Union[Unset, str]):
        full_section (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, FcgiApp]
    """

    return sync_detailed(
        name=name,
        client=client,
        transaction_id=transaction_id,
        full_section=full_section,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
    full_section: Union[Unset, bool] = False,
) -> Response[Union[Error, FcgiApp]]:
    """Return a FCGI app

     Returns one FCGI application configuration by its name.

    Args:
        name (str):
        transaction_id (Union[Unset, str]):
        full_section (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, FcgiApp]]
    """

    kwargs = _get_kwargs(
        name=name,
        transaction_id=transaction_id,
        full_section=full_section,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
    full_section: Union[Unset, bool] = False,
) -> Optional[Union[Error, FcgiApp]]:
    """Return a FCGI app

     Returns one FCGI application configuration by its name.

    Args:
        name (str):
        transaction_id (Union[Unset, str]):
        full_section (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, FcgiApp]
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            transaction_id=transaction_id,
            full_section=full_section,
        )
    ).parsed
