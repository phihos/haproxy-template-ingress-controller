from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.one_crl_entry import OneCRLEntry
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    index: Union[Unset, int] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["index"] = index

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/services/haproxy/runtime/ssl_crl_files/{name}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[Error, list["OneCRLEntry"]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for componentsschemasssl_crl_entries_item_data in _response_200:
            componentsschemasssl_crl_entries_item = OneCRLEntry.from_dict(componentsschemasssl_crl_entries_item_data)

            response_200.append(componentsschemasssl_crl_entries_item)

        return response_200

    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, list["OneCRLEntry"]]]:
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
    index: Union[Unset, int] = UNSET,
) -> Response[Union[Error, list["OneCRLEntry"]]]:
    """Get the contents of a CRL file

     Returns one or all entries in a CRL file using the runtime socket.

    Args:
        name (str):
        index (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['OneCRLEntry']]]
    """

    kwargs = _get_kwargs(
        name=name,
        index=index,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    index: Union[Unset, int] = UNSET,
) -> Optional[Union[Error, list["OneCRLEntry"]]]:
    """Get the contents of a CRL file

     Returns one or all entries in a CRL file using the runtime socket.

    Args:
        name (str):
        index (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['OneCRLEntry']]
    """

    return sync_detailed(
        name=name,
        client=client,
        index=index,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    index: Union[Unset, int] = UNSET,
) -> Response[Union[Error, list["OneCRLEntry"]]]:
    """Get the contents of a CRL file

     Returns one or all entries in a CRL file using the runtime socket.

    Args:
        name (str):
        index (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['OneCRLEntry']]]
    """

    kwargs = _get_kwargs(
        name=name,
        index=index,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    index: Union[Unset, int] = UNSET,
) -> Optional[Union[Error, list["OneCRLEntry"]]]:
    """Get the contents of a CRL file

     Returns one or all entries in a CRL file using the runtime socket.

    Args:
        name (str):
        index (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['OneCRLEntry']]
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            index=index,
        )
    ).parsed
