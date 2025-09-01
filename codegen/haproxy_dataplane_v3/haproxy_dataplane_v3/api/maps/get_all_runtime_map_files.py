from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.map_file import MapFile
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    include_unmanaged: Union[Unset, bool] = False,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["include_unmanaged"] = include_unmanaged

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/services/haproxy/runtime/maps",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[Error, list["MapFile"]]:
    if response.status_code == 200:
        _response_200 = response.json()
        response_200 = []
        for componentsschemasmaps_item_data in _response_200:
            componentsschemasmaps_item = MapFile.from_dict(componentsschemasmaps_item_data)

            response_200.append(componentsschemasmaps_item)

        return response_200

    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, list["MapFile"]]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    include_unmanaged: Union[Unset, bool] = False,
) -> Response[Union[Error, list["MapFile"]]]:
    """Return runtime map files

     Returns runtime map files.

    Args:
        include_unmanaged (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['MapFile']]]
    """

    kwargs = _get_kwargs(
        include_unmanaged=include_unmanaged,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    include_unmanaged: Union[Unset, bool] = False,
) -> Optional[Union[Error, list["MapFile"]]]:
    """Return runtime map files

     Returns runtime map files.

    Args:
        include_unmanaged (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['MapFile']]
    """

    return sync_detailed(
        client=client,
        include_unmanaged=include_unmanaged,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    include_unmanaged: Union[Unset, bool] = False,
) -> Response[Union[Error, list["MapFile"]]]:
    """Return runtime map files

     Returns runtime map files.

    Args:
        include_unmanaged (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['MapFile']]]
    """

    kwargs = _get_kwargs(
        include_unmanaged=include_unmanaged,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    include_unmanaged: Union[Unset, bool] = False,
) -> Optional[Union[Error, list["MapFile"]]]:
    """Return runtime map files

     Returns runtime map files.

    Args:
        include_unmanaged (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['MapFile']]
    """

    return (
        await asyncio_detailed(
            client=client,
            include_unmanaged=include_unmanaged,
        )
    ).parsed
