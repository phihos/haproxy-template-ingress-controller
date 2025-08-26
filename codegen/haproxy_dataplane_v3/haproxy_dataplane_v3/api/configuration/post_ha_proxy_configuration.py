from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: str,
    skip_version: Union[Unset, bool] = False,
    skip_reload: Union[Unset, bool] = False,
    only_validate: Union[Unset, bool] = False,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
    x_runtime_actions: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_runtime_actions, Unset):
        headers["X-Runtime-Actions"] = x_runtime_actions

    params: dict[str, Any] = {}

    params["skip_version"] = skip_version

    params["skip_reload"] = skip_reload

    params["only_validate"] = only_validate

    params["version"] = version

    params["force_reload"] = force_reload

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/services/haproxy/configuration/raw",
        "params": params,
    }

    _kwargs["content"] = body

    headers["Content-Type"] = "text/plain"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> str:
    if response.status_code == 201:
        response_201 = response.text
        return response_201

    if response.status_code == 202:
        response_202 = response.text
        return response_202

    if response.status_code == 400:
        response_400 = response.text
        return response_400

    response_default = response.text
    return response_default


def _build_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Response[str]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: str,
    skip_version: Union[Unset, bool] = False,
    skip_reload: Union[Unset, bool] = False,
    only_validate: Union[Unset, bool] = False,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
    x_runtime_actions: Union[Unset, str] = UNSET,
) -> Response[str]:
    """Push new haproxy configuration

     Push a new haproxy configuration file in plain text

    Args:
        skip_version (Union[Unset, bool]):  Default: False.
        skip_reload (Union[Unset, bool]):  Default: False.
        only_validate (Union[Unset, bool]):  Default: False.
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        x_runtime_actions (Union[Unset, str]):
        body (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[str]
    """

    kwargs = _get_kwargs(
        body=body,
        skip_version=skip_version,
        skip_reload=skip_reload,
        only_validate=only_validate,
        version=version,
        force_reload=force_reload,
        x_runtime_actions=x_runtime_actions,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: str,
    skip_version: Union[Unset, bool] = False,
    skip_reload: Union[Unset, bool] = False,
    only_validate: Union[Unset, bool] = False,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
    x_runtime_actions: Union[Unset, str] = UNSET,
) -> Optional[str]:
    """Push new haproxy configuration

     Push a new haproxy configuration file in plain text

    Args:
        skip_version (Union[Unset, bool]):  Default: False.
        skip_reload (Union[Unset, bool]):  Default: False.
        only_validate (Union[Unset, bool]):  Default: False.
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        x_runtime_actions (Union[Unset, str]):
        body (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        str
    """

    return sync_detailed(
        client=client,
        body=body,
        skip_version=skip_version,
        skip_reload=skip_reload,
        only_validate=only_validate,
        version=version,
        force_reload=force_reload,
        x_runtime_actions=x_runtime_actions,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: str,
    skip_version: Union[Unset, bool] = False,
    skip_reload: Union[Unset, bool] = False,
    only_validate: Union[Unset, bool] = False,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
    x_runtime_actions: Union[Unset, str] = UNSET,
) -> Response[str]:
    """Push new haproxy configuration

     Push a new haproxy configuration file in plain text

    Args:
        skip_version (Union[Unset, bool]):  Default: False.
        skip_reload (Union[Unset, bool]):  Default: False.
        only_validate (Union[Unset, bool]):  Default: False.
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        x_runtime_actions (Union[Unset, str]):
        body (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[str]
    """

    kwargs = _get_kwargs(
        body=body,
        skip_version=skip_version,
        skip_reload=skip_reload,
        only_validate=only_validate,
        version=version,
        force_reload=force_reload,
        x_runtime_actions=x_runtime_actions,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: str,
    skip_version: Union[Unset, bool] = False,
    skip_reload: Union[Unset, bool] = False,
    only_validate: Union[Unset, bool] = False,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
    x_runtime_actions: Union[Unset, str] = UNSET,
) -> Optional[str]:
    """Push new haproxy configuration

     Push a new haproxy configuration file in plain text

    Args:
        skip_version (Union[Unset, bool]):  Default: False.
        skip_reload (Union[Unset, bool]):  Default: False.
        only_validate (Union[Unset, bool]):  Default: False.
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        x_runtime_actions (Union[Unset, str]):
        body (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        str
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            skip_version=skip_version,
            skip_reload=skip_reload,
            only_validate=only_validate,
            version=version,
            force_reload=force_reload,
            x_runtime_actions=x_runtime_actions,
        )
    ).parsed
