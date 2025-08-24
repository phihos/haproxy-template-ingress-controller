from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.backend_switching_rule import BackendSwitchingRule
from ...models.error import Error
from ...types import UNSET, Response, Unset


def _get_kwargs(
    parent_name: str,
    index: int,
    *,
    body: BackendSwitchingRule,
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
        "url": f"/services/haproxy/configuration/frontends/{parent_name}/backend_switching_rules/{index}",
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[BackendSwitchingRule, Error]]:
    if response.status_code == 200:
        response_200 = BackendSwitchingRule.from_dict(response.json())

        return response_200
    if response.status_code == 202:
        response_202 = BackendSwitchingRule.from_dict(response.json())

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
) -> Response[Union[BackendSwitchingRule, Error]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    parent_name: str,
    index: int,
    *,
    client: Union[AuthenticatedClient, Client],
    body: BackendSwitchingRule,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[BackendSwitchingRule, Error]]:
    """Replace a Backend Switching Rule

     Replaces a Backend Switching Rule configuration by it's index in the specified frontend.

    Args:
        parent_name (str):
        index (int):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (BackendSwitchingRule): HAProxy backend switching rule configuration (corresponds to
            use_backend directive) Example: {'cond': 'if', 'cond_test': '{ req_ssl_sni -i
            www.example.com }', 'index': 0, 'name': 'test_backend'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[BackendSwitchingRule, Error]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        index=index,
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
    parent_name: str,
    index: int,
    *,
    client: Union[AuthenticatedClient, Client],
    body: BackendSwitchingRule,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[BackendSwitchingRule, Error]]:
    """Replace a Backend Switching Rule

     Replaces a Backend Switching Rule configuration by it's index in the specified frontend.

    Args:
        parent_name (str):
        index (int):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (BackendSwitchingRule): HAProxy backend switching rule configuration (corresponds to
            use_backend directive) Example: {'cond': 'if', 'cond_test': '{ req_ssl_sni -i
            www.example.com }', 'index': 0, 'name': 'test_backend'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[BackendSwitchingRule, Error]
    """

    return sync_detailed(
        parent_name=parent_name,
        index=index,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    ).parsed


async def asyncio_detailed(
    parent_name: str,
    index: int,
    *,
    client: Union[AuthenticatedClient, Client],
    body: BackendSwitchingRule,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[BackendSwitchingRule, Error]]:
    """Replace a Backend Switching Rule

     Replaces a Backend Switching Rule configuration by it's index in the specified frontend.

    Args:
        parent_name (str):
        index (int):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (BackendSwitchingRule): HAProxy backend switching rule configuration (corresponds to
            use_backend directive) Example: {'cond': 'if', 'cond_test': '{ req_ssl_sni -i
            www.example.com }', 'index': 0, 'name': 'test_backend'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[BackendSwitchingRule, Error]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        index=index,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    parent_name: str,
    index: int,
    *,
    client: Union[AuthenticatedClient, Client],
    body: BackendSwitchingRule,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[BackendSwitchingRule, Error]]:
    """Replace a Backend Switching Rule

     Replaces a Backend Switching Rule configuration by it's index in the specified frontend.

    Args:
        parent_name (str):
        index (int):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (BackendSwitchingRule): HAProxy backend switching rule configuration (corresponds to
            use_backend directive) Example: {'cond': 'if', 'cond_test': '{ req_ssl_sni -i
            www.example.com }', 'index': 0, 'name': 'test_backend'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[BackendSwitchingRule, Error]
    """

    return (
        await asyncio_detailed(
            parent_name=parent_name,
            index=index,
            client=client,
            body=body,
            transaction_id=transaction_id,
            version=version,
            force_reload=force_reload,
        )
    ).parsed
