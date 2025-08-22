from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.tcp_response_rule import TCPResponseRule
from ...types import UNSET, Response, Unset


def _get_kwargs(
    parent_name: str,
    index: int,
    *,
    body: TCPResponseRule,
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
        "method": "post",
        "url": f"/services/haproxy/configuration/backends/{parent_name}/tcp_response_rules/{index}",
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, TCPResponseRule]]:
    if response.status_code == 201:
        response_201 = TCPResponseRule.from_dict(response.json())

        return response_201
    if response.status_code == 202:
        response_202 = TCPResponseRule.from_dict(response.json())

        return response_202
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
) -> Response[Union[Error, TCPResponseRule]]:
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
    body: TCPResponseRule,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Error, TCPResponseRule]]:
    """Add a new TCP Response Rule

     Adds a new TCP Response Rule of the specified type in the specified backend.

    Args:
        parent_name (str):
        index (int):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (TCPResponseRule): HAProxy TCP Response Rule configuration (corresponds to tcp-
            response) Example: {'cond': 'if', 'cond_test': '{ src 192.168.0.0/16 }', 'index': 0,
            'type': 'content'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, TCPResponseRule]]
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
    body: TCPResponseRule,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Error, TCPResponseRule]]:
    """Add a new TCP Response Rule

     Adds a new TCP Response Rule of the specified type in the specified backend.

    Args:
        parent_name (str):
        index (int):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (TCPResponseRule): HAProxy TCP Response Rule configuration (corresponds to tcp-
            response) Example: {'cond': 'if', 'cond_test': '{ src 192.168.0.0/16 }', 'index': 0,
            'type': 'content'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, TCPResponseRule]
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
    body: TCPResponseRule,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Error, TCPResponseRule]]:
    """Add a new TCP Response Rule

     Adds a new TCP Response Rule of the specified type in the specified backend.

    Args:
        parent_name (str):
        index (int):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (TCPResponseRule): HAProxy TCP Response Rule configuration (corresponds to tcp-
            response) Example: {'cond': 'if', 'cond_test': '{ src 192.168.0.0/16 }', 'index': 0,
            'type': 'content'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, TCPResponseRule]]
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
    body: TCPResponseRule,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Error, TCPResponseRule]]:
    """Add a new TCP Response Rule

     Adds a new TCP Response Rule of the specified type in the specified backend.

    Args:
        parent_name (str):
        index (int):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (TCPResponseRule): HAProxy TCP Response Rule configuration (corresponds to tcp-
            response) Example: {'cond': 'if', 'cond_test': '{ src 192.168.0.0/16 }', 'index': 0,
            'type': 'content'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, TCPResponseRule]
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
