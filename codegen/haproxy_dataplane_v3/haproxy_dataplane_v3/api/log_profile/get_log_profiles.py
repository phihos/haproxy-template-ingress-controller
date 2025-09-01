from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.log_profile import LogProfile
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    transaction_id: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["transaction_id"] = transaction_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/services/haproxy/configuration/log_profiles",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[Error, list["LogProfile"]]:
    if response.status_code == 200:
        _response_200 = response.json()
        response_200 = []
        for componentsschemaslog_profiles_item_data in _response_200:
            componentsschemaslog_profiles_item = LogProfile.from_dict(componentsschemaslog_profiles_item_data)

            response_200.append(componentsschemaslog_profiles_item)

        return response_200

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, list["LogProfile"]]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[Union[Error, list["LogProfile"]]]:
    """Return all the Log Profiles

     Returns an array of all the configured log_profile sections in HAProxy

    Args:
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['LogProfile']]]
    """

    kwargs = _get_kwargs(
        transaction_id=transaction_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[Union[Error, list["LogProfile"]]]:
    """Return all the Log Profiles

     Returns an array of all the configured log_profile sections in HAProxy

    Args:
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['LogProfile']]
    """

    return sync_detailed(
        client=client,
        transaction_id=transaction_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[Union[Error, list["LogProfile"]]]:
    """Return all the Log Profiles

     Returns an array of all the configured log_profile sections in HAProxy

    Args:
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['LogProfile']]]
    """

    kwargs = _get_kwargs(
        transaction_id=transaction_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[Union[Error, list["LogProfile"]]]:
    """Return all the Log Profiles

     Returns an array of all the configured log_profile sections in HAProxy

    Args:
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['LogProfile']]
    """

    return (
        await asyncio_detailed(
            client=client,
            transaction_id=transaction_id,
        )
    ).parsed
