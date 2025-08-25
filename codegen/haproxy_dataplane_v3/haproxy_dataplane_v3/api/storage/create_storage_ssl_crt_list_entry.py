from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.ssl_crt_list_entry import SSLCrtListEntry
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    body: SSLCrtListEntry,
    force_reload: Union[Unset, bool] = False,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["force_reload"] = force_reload

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/services/haproxy/storage/ssl_crt_lists/{name}/entries",
        "params": params,
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, Error, SSLCrtListEntry]]:
    if response.status_code == 201:
        response_201 = SSLCrtListEntry.from_dict(response.json())

        return response_201
    if response.status_code == 202:
        response_202 = cast(Any, None)
        return response_202
    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400
    if response.status_code == 409:
        response_409 = Error.from_dict(response.json())

        return response_409
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, Error, SSLCrtListEntry]]:
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
    body: SSLCrtListEntry,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Any, Error, SSLCrtListEntry]]:
    """Creates a new entry in a CrtList

     Creates a new entry in a certificate list.

    Args:
        name (str):
        force_reload (Union[Unset, bool]):  Default: False.
        body (SSLCrtListEntry): SSL Crt List Entry

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Error, SSLCrtListEntry]]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        force_reload=force_reload,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: SSLCrtListEntry,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Any, Error, SSLCrtListEntry]]:
    """Creates a new entry in a CrtList

     Creates a new entry in a certificate list.

    Args:
        name (str):
        force_reload (Union[Unset, bool]):  Default: False.
        body (SSLCrtListEntry): SSL Crt List Entry

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Error, SSLCrtListEntry]
    """

    return sync_detailed(
        name=name,
        client=client,
        body=body,
        force_reload=force_reload,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: SSLCrtListEntry,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Any, Error, SSLCrtListEntry]]:
    """Creates a new entry in a CrtList

     Creates a new entry in a certificate list.

    Args:
        name (str):
        force_reload (Union[Unset, bool]):  Default: False.
        body (SSLCrtListEntry): SSL Crt List Entry

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Error, SSLCrtListEntry]]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        force_reload=force_reload,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: SSLCrtListEntry,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Any, Error, SSLCrtListEntry]]:
    """Creates a new entry in a CrtList

     Creates a new entry in a certificate list.

    Args:
        name (str):
        force_reload (Union[Unset, bool]):  Default: False.
        body (SSLCrtListEntry): SSL Crt List Entry

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Error, SSLCrtListEntry]
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
            force_reload=force_reload,
        )
    ).parsed
