from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_errors_section import HttpErrorsSection
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    transaction_id: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["transaction_id"] = transaction_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/services/haproxy/configuration/http_errors_sections",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[list["HttpErrorsSection"]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for componentsschemashttp_errors_sections_item_data in _response_200:
            componentsschemashttp_errors_sections_item = HttpErrorsSection.from_dict(
                componentsschemashttp_errors_sections_item_data
            )

            response_200.append(componentsschemashttp_errors_sections_item)

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[list["HttpErrorsSection"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[list["HttpErrorsSection"]]:
    """Return an array of http-error sections

     Returns an array of all configured http-error sections.

    Args:
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['HttpErrorsSection']]
    """

    kwargs = _get_kwargs(
        transaction_id=transaction_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[list["HttpErrorsSection"]]:
    """Return an array of http-error sections

     Returns an array of all configured http-error sections.

    Args:
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['HttpErrorsSection']
    """

    return sync_detailed(
        client=client,
        transaction_id=transaction_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[list["HttpErrorsSection"]]:
    """Return an array of http-error sections

     Returns an array of all configured http-error sections.

    Args:
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['HttpErrorsSection']]
    """

    kwargs = _get_kwargs(
        transaction_id=transaction_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[list["HttpErrorsSection"]]:
    """Return an array of http-error sections

     Returns an array of all configured http-error sections.

    Args:
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['HttpErrorsSection']
    """

    return (
        await asyncio_detailed(
            client=client,
            transaction_id=transaction_id,
        )
    ).parsed
