from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.nameserver import Nameserver
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: Nameserver,
    resolver: str,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["resolver"] = resolver

    params["transaction_id"] = transaction_id

    params["version"] = version

    params["force_reload"] = force_reload

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/services/haproxy/configuration/nameservers",
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[Error, Nameserver]:
    if response.status_code == 201:
        response_201 = Nameserver.from_dict(response.json())

        return response_201

    if response.status_code == 202:
        response_202 = Nameserver.from_dict(response.json())

        return response_202

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

    if response.status_code == 409:
        response_409 = Error.from_dict(response.json())

        return response_409

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, Nameserver]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Nameserver,
    resolver: str,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Error, Nameserver]]:
    """Add a nameserver

     Adds a new nameserver to the resolvers section.

    Args:
        resolver (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (Nameserver): Nameserver used in Runtime DNS configuration Example: {'address':
            '10.0.0.1', 'name': 'ns1', 'port': 53}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Nameserver]]
    """

    kwargs = _get_kwargs(
        body=body,
        resolver=resolver,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Nameserver,
    resolver: str,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Error, Nameserver]]:
    """Add a nameserver

     Adds a new nameserver to the resolvers section.

    Args:
        resolver (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (Nameserver): Nameserver used in Runtime DNS configuration Example: {'address':
            '10.0.0.1', 'name': 'ns1', 'port': 53}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Nameserver]
    """

    return sync_detailed(
        client=client,
        body=body,
        resolver=resolver,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Nameserver,
    resolver: str,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Error, Nameserver]]:
    """Add a nameserver

     Adds a new nameserver to the resolvers section.

    Args:
        resolver (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (Nameserver): Nameserver used in Runtime DNS configuration Example: {'address':
            '10.0.0.1', 'name': 'ns1', 'port': 53}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Nameserver]]
    """

    kwargs = _get_kwargs(
        body=body,
        resolver=resolver,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: Nameserver,
    resolver: str,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Error, Nameserver]]:
    """Add a nameserver

     Adds a new nameserver to the resolvers section.

    Args:
        resolver (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (Nameserver): Nameserver used in Runtime DNS configuration Example: {'address':
            '10.0.0.1', 'name': 'ns1', 'port': 53}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Nameserver]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            resolver=resolver,
            transaction_id=transaction_id,
            version=version,
            force_reload=force_reload,
        )
    ).parsed
