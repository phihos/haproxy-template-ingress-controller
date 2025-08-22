from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_storage_ssl_crt_list_file_body import CreateStorageSSLCrtListFileBody
from ...models.error import Error
from ...models.sslcrt_list_file import SSLCRTListFile
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: CreateStorageSSLCrtListFileBody,
    force_reload: Union[Unset, bool] = False,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["force_reload"] = force_reload

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/services/haproxy/storage/ssl_crt_lists",
        "params": params,
    }

    _kwargs["files"] = body.to_multipart()

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, SSLCRTListFile]]:
    if response.status_code == 201:
        response_201 = SSLCRTListFile.from_dict(response.json())

        return response_201
    if response.status_code == 202:
        response_202 = SSLCRTListFile.from_dict(response.json())

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
) -> Response[Union[Error, SSLCRTListFile]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: CreateStorageSSLCrtListFileBody,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Error, SSLCRTListFile]]:
    """Create a certificate list

     Creates a certificate list.

    Args:
        force_reload (Union[Unset, bool]):  Default: False.
        body (CreateStorageSSLCrtListFileBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, SSLCRTListFile]]
    """

    kwargs = _get_kwargs(
        body=body,
        force_reload=force_reload,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: CreateStorageSSLCrtListFileBody,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Error, SSLCRTListFile]]:
    """Create a certificate list

     Creates a certificate list.

    Args:
        force_reload (Union[Unset, bool]):  Default: False.
        body (CreateStorageSSLCrtListFileBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, SSLCRTListFile]
    """

    return sync_detailed(
        client=client,
        body=body,
        force_reload=force_reload,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: CreateStorageSSLCrtListFileBody,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Error, SSLCRTListFile]]:
    """Create a certificate list

     Creates a certificate list.

    Args:
        force_reload (Union[Unset, bool]):  Default: False.
        body (CreateStorageSSLCrtListFileBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, SSLCRTListFile]]
    """

    kwargs = _get_kwargs(
        body=body,
        force_reload=force_reload,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: CreateStorageSSLCrtListFileBody,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Error, SSLCRTListFile]]:
    """Create a certificate list

     Creates a certificate list.

    Args:
        force_reload (Union[Unset, bool]):  Default: False.
        body (CreateStorageSSLCrtListFileBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, SSLCRTListFile]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            force_reload=force_reload,
        )
    ).parsed
