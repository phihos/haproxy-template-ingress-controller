from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    name: str,
    cert_file: str,
    line_number: Union[Unset, int] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["name"] = name

    params["cert_file"] = cert_file

    params["line_number"] = line_number

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/services/haproxy/runtime/ssl_crt_lists/entries",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, Error]]:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204
    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400
    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, Error]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    name: str,
    cert_file: str,
    line_number: Union[Unset, int] = UNSET,
) -> Response[Union[Any, Error]]:
    """Delete an entry from a crt-list

     Deletes a single entry from the given crt-list using the runtime socket.

    Args:
        name (str):
        cert_file (str):
        line_number (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Error]]
    """

    kwargs = _get_kwargs(
        name=name,
        cert_file=cert_file,
        line_number=line_number,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    name: str,
    cert_file: str,
    line_number: Union[Unset, int] = UNSET,
) -> Optional[Union[Any, Error]]:
    """Delete an entry from a crt-list

     Deletes a single entry from the given crt-list using the runtime socket.

    Args:
        name (str):
        cert_file (str):
        line_number (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Error]
    """

    return sync_detailed(
        client=client,
        name=name,
        cert_file=cert_file,
        line_number=line_number,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    name: str,
    cert_file: str,
    line_number: Union[Unset, int] = UNSET,
) -> Response[Union[Any, Error]]:
    """Delete an entry from a crt-list

     Deletes a single entry from the given crt-list using the runtime socket.

    Args:
        name (str):
        cert_file (str):
        line_number (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Error]]
    """

    kwargs = _get_kwargs(
        name=name,
        cert_file=cert_file,
        line_number=line_number,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    name: str,
    cert_file: str,
    line_number: Union[Unset, int] = UNSET,
) -> Optional[Union[Any, Error]]:
    """Delete an entry from a crt-list

     Deletes a single entry from the given crt-list using the runtime socket.

    Args:
        name (str):
        cert_file (str):
        line_number (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Error]
    """

    return (
        await asyncio_detailed(
            client=client,
            name=name,
            cert_file=cert_file,
            line_number=line_number,
        )
    ).parsed
