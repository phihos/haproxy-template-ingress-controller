from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    parent_name: str,
    name: str,
    *,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["transaction_id"] = transaction_id

    params["version"] = version

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": f"/services/haproxy/spoe/spoe_files/{parent_name}/scopes/{name}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, Error]]:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204
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
    parent_name: str,
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> Response[Union[Any, Error]]:
    """Delete a SPOE scope

     Deletes a SPOE scope from the configuration file.

    Args:
        parent_name (str):
        name (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Error]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        name=name,
        transaction_id=transaction_id,
        version=version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    parent_name: str,
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> Optional[Union[Any, Error]]:
    """Delete a SPOE scope

     Deletes a SPOE scope from the configuration file.

    Args:
        parent_name (str):
        name (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Error]
    """

    return sync_detailed(
        parent_name=parent_name,
        name=name,
        client=client,
        transaction_id=transaction_id,
        version=version,
    ).parsed


async def asyncio_detailed(
    parent_name: str,
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> Response[Union[Any, Error]]:
    """Delete a SPOE scope

     Deletes a SPOE scope from the configuration file.

    Args:
        parent_name (str):
        name (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Error]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        name=name,
        transaction_id=transaction_id,
        version=version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    parent_name: str,
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> Optional[Union[Any, Error]]:
    """Delete a SPOE scope

     Deletes a SPOE scope from the configuration file.

    Args:
        parent_name (str):
        name (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Error]
    """

    return (
        await asyncio_detailed(
            parent_name=parent_name,
            name=name,
            client=client,
            transaction_id=transaction_id,
            version=version,
        )
    ).parsed
