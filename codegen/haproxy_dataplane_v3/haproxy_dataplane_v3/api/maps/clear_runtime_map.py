from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    force_delete: Union[Unset, bool] = UNSET,
    force_sync: Union[Unset, bool] = False,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["forceDelete"] = force_delete

    params["force_sync"] = force_sync

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": f"/services/haproxy/runtime/maps/{name}",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Union[Any, Error]:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

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
    force_delete: Union[Unset, bool] = UNSET,
    force_sync: Union[Unset, bool] = False,
) -> Response[Union[Any, Error]]:
    """Remove all map entries from the map file

     Remove all map entries from the map file.

    Args:
        name (str):
        force_delete (Union[Unset, bool]):
        force_sync (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Error]]
    """

    kwargs = _get_kwargs(
        name=name,
        force_delete=force_delete,
        force_sync=force_sync,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    force_delete: Union[Unset, bool] = UNSET,
    force_sync: Union[Unset, bool] = False,
) -> Optional[Union[Any, Error]]:
    """Remove all map entries from the map file

     Remove all map entries from the map file.

    Args:
        name (str):
        force_delete (Union[Unset, bool]):
        force_sync (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Error]
    """

    return sync_detailed(
        name=name,
        client=client,
        force_delete=force_delete,
        force_sync=force_sync,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    force_delete: Union[Unset, bool] = UNSET,
    force_sync: Union[Unset, bool] = False,
) -> Response[Union[Any, Error]]:
    """Remove all map entries from the map file

     Remove all map entries from the map file.

    Args:
        name (str):
        force_delete (Union[Unset, bool]):
        force_sync (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Error]]
    """

    kwargs = _get_kwargs(
        name=name,
        force_delete=force_delete,
        force_sync=force_sync,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    force_delete: Union[Unset, bool] = UNSET,
    force_sync: Union[Unset, bool] = False,
) -> Optional[Union[Any, Error]]:
    """Remove all map entries from the map file

     Remove all map entries from the map file.

    Args:
        name (str):
        force_delete (Union[Unset, bool]):
        force_sync (Union[Unset, bool]):  Default: False.

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
            force_delete=force_delete,
            force_sync=force_sync,
        )
    ).parsed
