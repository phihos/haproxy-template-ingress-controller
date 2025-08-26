from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.replace_storage_general_file_body import ReplaceStorageGeneralFileBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    body: ReplaceStorageGeneralFileBody,
    skip_reload: Union[Unset, bool] = False,
    force_reload: Union[Unset, bool] = False,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["skip_reload"] = skip_reload

    params["force_reload"] = force_reload

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/services/haproxy/storage/general/{name}",
        "params": params,
    }

    _kwargs["files"] = body.to_multipart()

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Union[Any, Error]:
    if response.status_code == 202:
        response_202 = cast(Any, None)
        return response_202

    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404

    response_default = Error.from_dict(response.json())

    return response_default


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
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: ReplaceStorageGeneralFileBody,
    skip_reload: Union[Unset, bool] = False,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Any, Error]]:
    """Replace contents of a managed general use file on disk

     Replaces the contents of a managed general use file on disk

    Args:
        name (str):
        skip_reload (Union[Unset, bool]):  Default: False.
        force_reload (Union[Unset, bool]):  Default: False.
        body (ReplaceStorageGeneralFileBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Error]]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        skip_reload=skip_reload,
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
    body: ReplaceStorageGeneralFileBody,
    skip_reload: Union[Unset, bool] = False,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Any, Error]]:
    """Replace contents of a managed general use file on disk

     Replaces the contents of a managed general use file on disk

    Args:
        name (str):
        skip_reload (Union[Unset, bool]):  Default: False.
        force_reload (Union[Unset, bool]):  Default: False.
        body (ReplaceStorageGeneralFileBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Error]
    """

    return sync_detailed(
        name=name,
        client=client,
        body=body,
        skip_reload=skip_reload,
        force_reload=force_reload,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: ReplaceStorageGeneralFileBody,
    skip_reload: Union[Unset, bool] = False,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Any, Error]]:
    """Replace contents of a managed general use file on disk

     Replaces the contents of a managed general use file on disk

    Args:
        name (str):
        skip_reload (Union[Unset, bool]):  Default: False.
        force_reload (Union[Unset, bool]):  Default: False.
        body (ReplaceStorageGeneralFileBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Error]]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        skip_reload=skip_reload,
        force_reload=force_reload,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: ReplaceStorageGeneralFileBody,
    skip_reload: Union[Unset, bool] = False,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Any, Error]]:
    """Replace contents of a managed general use file on disk

     Replaces the contents of a managed general use file on disk

    Args:
        name (str):
        skip_reload (Union[Unset, bool]):  Default: False.
        force_reload (Union[Unset, bool]):  Default: False.
        body (ReplaceStorageGeneralFileBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Error]
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
            skip_reload=skip_reload,
            force_reload=force_reload,
        )
    ).parsed
