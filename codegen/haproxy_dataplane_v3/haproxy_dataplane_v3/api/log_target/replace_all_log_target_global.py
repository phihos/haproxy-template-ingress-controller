from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.log_target import LogTarget
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: list["LogTarget"],
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
        "url": "/services/haproxy/configuration/global/log_targets",
        "params": params,
    }

    _kwargs["json"] = []
    for componentsschemaslog_targets_item_data in body:
        componentsschemaslog_targets_item = componentsschemaslog_targets_item_data.to_dict()
        _kwargs["json"].append(componentsschemaslog_targets_item)

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[Error, list["LogTarget"]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for componentsschemaslog_targets_item_data in _response_200:
            componentsschemaslog_targets_item = LogTarget.from_dict(componentsschemaslog_targets_item_data)

            response_200.append(componentsschemaslog_targets_item)

        return response_200

    if response.status_code == 202:
        response_202 = []
        _response_202 = response.json()
        for componentsschemaslog_targets_item_data in _response_202:
            componentsschemaslog_targets_item = LogTarget.from_dict(componentsschemaslog_targets_item_data)

            response_202.append(componentsschemaslog_targets_item)

        return response_202

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, list["LogTarget"]]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: list["LogTarget"],
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Error, list["LogTarget"]]]:
    """Replace a Log Target list

     Replaces a whole list of Log Targets with the list given in parameter

    Args:
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (list['LogTarget']): HAProxy log target array (corresponds to log directives)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['LogTarget']]]
    """

    kwargs = _get_kwargs(
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
    *,
    client: Union[AuthenticatedClient, Client],
    body: list["LogTarget"],
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Error, list["LogTarget"]]]:
    """Replace a Log Target list

     Replaces a whole list of Log Targets with the list given in parameter

    Args:
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (list['LogTarget']): HAProxy log target array (corresponds to log directives)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['LogTarget']]
    """

    return sync_detailed(
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: list["LogTarget"],
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Error, list["LogTarget"]]]:
    """Replace a Log Target list

     Replaces a whole list of Log Targets with the list given in parameter

    Args:
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (list['LogTarget']): HAProxy log target array (corresponds to log directives)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['LogTarget']]]
    """

    kwargs = _get_kwargs(
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: list["LogTarget"],
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Error, list["LogTarget"]]]:
    """Replace a Log Target list

     Replaces a whole list of Log Targets with the list given in parameter

    Args:
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (list['LogTarget']): HAProxy log target array (corresponds to log directives)

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['LogTarget']]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            transaction_id=transaction_id,
            version=version,
            force_reload=force_reload,
        )
    ).parsed
