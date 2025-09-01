from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.http_check import HTTPCheck
from ...types import UNSET, Response, Unset


def _get_kwargs(
    parent_name: str,
    *,
    body: list["HTTPCheck"],
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
        "url": f"/services/haproxy/configuration/backends/{parent_name}/http_checks",
        "params": params,
    }

    _kwargs["json"] = []
    for componentsschemashttp_checks_item_data in body:
        componentsschemashttp_checks_item = componentsschemashttp_checks_item_data.to_dict()
        _kwargs["json"].append(componentsschemashttp_checks_item)

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[Error, list["HTTPCheck"]]:
    if response.status_code == 200:
        _response_200 = response.json()
        response_200 = []
        for componentsschemashttp_checks_item_data in _response_200:
            componentsschemashttp_checks_item = HTTPCheck.from_dict(componentsschemashttp_checks_item_data)

            response_200.append(componentsschemashttp_checks_item)

        return response_200

    if response.status_code == 202:
        _response_202 = response.json()
        response_202 = []
        for componentsschemashttp_checks_item_data in _response_202:
            componentsschemashttp_checks_item = HTTPCheck.from_dict(componentsschemashttp_checks_item_data)

            response_202.append(componentsschemashttp_checks_item)

        return response_202

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, list["HTTPCheck"]]]:
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
    body: list["HTTPCheck"],
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Error, list["HTTPCheck"]]]:
    """Replace an HTTP checks list

     Replaces a whole list of HTTP checks with the list given in parameter

    Args:
        parent_name (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (list['HTTPCheck']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['HTTPCheck']]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
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
    *,
    client: Union[AuthenticatedClient, Client],
    body: list["HTTPCheck"],
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Error, list["HTTPCheck"]]]:
    """Replace an HTTP checks list

     Replaces a whole list of HTTP checks with the list given in parameter

    Args:
        parent_name (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (list['HTTPCheck']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['HTTPCheck']]
    """

    return sync_detailed(
        parent_name=parent_name,
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    ).parsed


async def asyncio_detailed(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: list["HTTPCheck"],
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Error, list["HTTPCheck"]]]:
    """Replace an HTTP checks list

     Replaces a whole list of HTTP checks with the list given in parameter

    Args:
        parent_name (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (list['HTTPCheck']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['HTTPCheck']]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: list["HTTPCheck"],
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Error, list["HTTPCheck"]]]:
    """Replace an HTTP checks list

     Replaces a whole list of HTTP checks with the list given in parameter

    Args:
        parent_name (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (list['HTTPCheck']):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['HTTPCheck']]
    """

    return (
        await asyncio_detailed(
            parent_name=parent_name,
            client=client,
            body=body,
            transaction_id=transaction_id,
            version=version,
            force_reload=force_reload,
        )
    ).parsed
