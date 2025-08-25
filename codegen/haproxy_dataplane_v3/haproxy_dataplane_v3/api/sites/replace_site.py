from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.site import Site
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    body: Site,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["transaction_id"] = transaction_id

    params["version"] = version

    params["force_reload"] = force_reload

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/services/haproxy/sites/{name}",
        "params": params,
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, Site]]:
    if response.status_code == 200:
        response_200 = Site.from_dict(response.json())

        return response_200
    if response.status_code == 202:
        response_202 = Site.from_dict(response.json())

        return response_202
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
) -> Response[Union[Error, Site]]:
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
    body: Site,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Error, Site]]:
    """Replace a site

     Replaces a site configuration by it's name.

    Args:
        name (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (Site): Site configuration. Sites are considered as one service and all farms
            connected to that service.
            Farms are connected to service using use-backend and default_backend directives. Sites let
            you
            configure simple HAProxy configurations, for more advanced options use
            /haproxy/configuration
            endpoints.
             Example: {'farms': [{'balance': {'algorithm': 'roundrobin'}, 'mode': 'http', 'name':
            'www_backend', 'servers': [{'address': '127.0.1.1', 'name': 'www_server', 'port': 4567},
            {'address': '127.0.1.2', 'name': 'www_server_new', 'port': 4567}], 'use_as': 'default'}],
            'name': 'test_site', 'service': {'http_connection_mode': 'httpclose', 'maxconn': 2000,
            'mode': 'http'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Site]]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        transaction_id=transaction_id,
        version=version,
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
    body: Site,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Error, Site]]:
    """Replace a site

     Replaces a site configuration by it's name.

    Args:
        name (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (Site): Site configuration. Sites are considered as one service and all farms
            connected to that service.
            Farms are connected to service using use-backend and default_backend directives. Sites let
            you
            configure simple HAProxy configurations, for more advanced options use
            /haproxy/configuration
            endpoints.
             Example: {'farms': [{'balance': {'algorithm': 'roundrobin'}, 'mode': 'http', 'name':
            'www_backend', 'servers': [{'address': '127.0.1.1', 'name': 'www_server', 'port': 4567},
            {'address': '127.0.1.2', 'name': 'www_server_new', 'port': 4567}], 'use_as': 'default'}],
            'name': 'test_site', 'service': {'http_connection_mode': 'httpclose', 'maxconn': 2000,
            'mode': 'http'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Site]
    """

    return sync_detailed(
        name=name,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: Site,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Error, Site]]:
    """Replace a site

     Replaces a site configuration by it's name.

    Args:
        name (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (Site): Site configuration. Sites are considered as one service and all farms
            connected to that service.
            Farms are connected to service using use-backend and default_backend directives. Sites let
            you
            configure simple HAProxy configurations, for more advanced options use
            /haproxy/configuration
            endpoints.
             Example: {'farms': [{'balance': {'algorithm': 'roundrobin'}, 'mode': 'http', 'name':
            'www_backend', 'servers': [{'address': '127.0.1.1', 'name': 'www_server', 'port': 4567},
            {'address': '127.0.1.2', 'name': 'www_server_new', 'port': 4567}], 'use_as': 'default'}],
            'name': 'test_site', 'service': {'http_connection_mode': 'httpclose', 'maxconn': 2000,
            'mode': 'http'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, Site]]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: Site,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Error, Site]]:
    """Replace a site

     Replaces a site configuration by it's name.

    Args:
        name (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (Site): Site configuration. Sites are considered as one service and all farms
            connected to that service.
            Farms are connected to service using use-backend and default_backend directives. Sites let
            you
            configure simple HAProxy configurations, for more advanced options use
            /haproxy/configuration
            endpoints.
             Example: {'farms': [{'balance': {'algorithm': 'roundrobin'}, 'mode': 'http', 'name':
            'www_backend', 'servers': [{'address': '127.0.1.1', 'name': 'www_server', 'port': 4567},
            {'address': '127.0.1.2', 'name': 'www_server_new', 'port': 4567}], 'use_as': 'default'}],
            'name': 'test_site', 'service': {'http_connection_mode': 'httpclose', 'maxconn': 2000,
            'mode': 'http'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, Site]
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
            transaction_id=transaction_id,
            version=version,
            force_reload=force_reload,
        )
    ).parsed
