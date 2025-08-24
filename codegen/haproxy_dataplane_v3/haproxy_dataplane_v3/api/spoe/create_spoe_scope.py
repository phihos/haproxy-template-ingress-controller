from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    parent_name: str,
    *,
    body: str,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["transaction_id"] = transaction_id

    params["version"] = version

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/services/haproxy/spoe/spoe_files/{parent_name}/scopes",
        "params": params,
    }

    _kwargs["json"] = body

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, str]]:
    if response.status_code == 201:
        response_201 = cast(str, response.json())
        return response_201
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
) -> Response[Union[Error, str]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: str,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> Response[Union[Error, str]]:
    """Add a new spoe scope

     Adds a new spoe scope.

    Args:
        parent_name (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        body (str): SPOE scope name

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, str]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        body=body,
        transaction_id=transaction_id,
        version=version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: str,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> Optional[Union[Error, str]]:
    """Add a new spoe scope

     Adds a new spoe scope.

    Args:
        parent_name (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        body (str): SPOE scope name

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, str]
    """

    return sync_detailed(
        parent_name=parent_name,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
    ).parsed


async def asyncio_detailed(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: str,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> Response[Union[Error, str]]:
    """Add a new spoe scope

     Adds a new spoe scope.

    Args:
        parent_name (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        body (str): SPOE scope name

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, str]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        body=body,
        transaction_id=transaction_id,
        version=version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: str,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> Optional[Union[Error, str]]:
    """Add a new spoe scope

     Adds a new spoe scope.

    Args:
        parent_name (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        body (str): SPOE scope name

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, str]
    """

    return (
        await asyncio_detailed(
            parent_name=parent_name,
            client=client,
            body=body,
            transaction_id=transaction_id,
            version=version,
        )
    ).parsed
