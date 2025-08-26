from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.spoe_configuration_transaction import SPOEConfigurationTransaction
from ...types import UNSET, Response, Unset


def _get_kwargs(
    parent_name: str,
    id: str,
    *,
    force_reload: Union[Unset, bool] = False,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["force_reload"] = force_reload

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/services/haproxy/spoe/spoe_files/{parent_name}/transactions/{id}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[Error, SPOEConfigurationTransaction]:
    if response.status_code == 200:
        response_200 = SPOEConfigurationTransaction.from_dict(response.json())

        return response_200

    if response.status_code == 202:
        response_202 = SPOEConfigurationTransaction.from_dict(response.json())

        return response_202

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, SPOEConfigurationTransaction]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    parent_name: str,
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Error, SPOEConfigurationTransaction]]:
    """Commit transaction

     Commit transaction, execute all operations in transaction and return msg

    Args:
        parent_name (str):
        id (str):
        force_reload (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, SPOEConfigurationTransaction]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        id=id,
        force_reload=force_reload,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    parent_name: str,
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Error, SPOEConfigurationTransaction]]:
    """Commit transaction

     Commit transaction, execute all operations in transaction and return msg

    Args:
        parent_name (str):
        id (str):
        force_reload (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, SPOEConfigurationTransaction]
    """

    return sync_detailed(
        parent_name=parent_name,
        id=id,
        client=client,
        force_reload=force_reload,
    ).parsed


async def asyncio_detailed(
    parent_name: str,
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Error, SPOEConfigurationTransaction]]:
    """Commit transaction

     Commit transaction, execute all operations in transaction and return msg

    Args:
        parent_name (str):
        id (str):
        force_reload (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, SPOEConfigurationTransaction]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        id=id,
        force_reload=force_reload,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    parent_name: str,
    id: str,
    *,
    client: Union[AuthenticatedClient, Client],
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Error, SPOEConfigurationTransaction]]:
    """Commit transaction

     Commit transaction, execute all operations in transaction and return msg

    Args:
        parent_name (str):
        id (str):
        force_reload (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, SPOEConfigurationTransaction]
    """

    return (
        await asyncio_detailed(
            parent_name=parent_name,
            id=id,
            client=client,
            force_reload=force_reload,
        )
    ).parsed
