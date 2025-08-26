from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.mailers_section import MailersSection
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    transaction_id: Union[Unset, str] = UNSET,
    full_section: Union[Unset, bool] = False,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["transaction_id"] = transaction_id

    params["full_section"] = full_section

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/services/haproxy/configuration/mailers_section",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[Error, list["MailersSection"]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for componentsschemasmailers_sections_item_data in _response_200:
            componentsschemasmailers_sections_item = MailersSection.from_dict(
                componentsschemasmailers_sections_item_data
            )

            response_200.append(componentsschemasmailers_sections_item)

        return response_200

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, list["MailersSection"]]]:
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
    full_section: Union[Unset, bool] = False,
) -> Response[Union[Error, list["MailersSection"]]]:
    """Return an array of mailers sections

     Returns an array of all the configured mailers in HAProxy

    Args:
        transaction_id (Union[Unset, str]):
        full_section (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['MailersSection']]]
    """

    kwargs = _get_kwargs(
        transaction_id=transaction_id,
        full_section=full_section,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
    full_section: Union[Unset, bool] = False,
) -> Optional[Union[Error, list["MailersSection"]]]:
    """Return an array of mailers sections

     Returns an array of all the configured mailers in HAProxy

    Args:
        transaction_id (Union[Unset, str]):
        full_section (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['MailersSection']]
    """

    return sync_detailed(
        client=client,
        transaction_id=transaction_id,
        full_section=full_section,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
    full_section: Union[Unset, bool] = False,
) -> Response[Union[Error, list["MailersSection"]]]:
    """Return an array of mailers sections

     Returns an array of all the configured mailers in HAProxy

    Args:
        transaction_id (Union[Unset, str]):
        full_section (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['MailersSection']]]
    """

    kwargs = _get_kwargs(
        transaction_id=transaction_id,
        full_section=full_section,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    transaction_id: Union[Unset, str] = UNSET,
    full_section: Union[Unset, bool] = False,
) -> Optional[Union[Error, list["MailersSection"]]]:
    """Return an array of mailers sections

     Returns an array of all the configured mailers in HAProxy

    Args:
        transaction_id (Union[Unset, str]):
        full_section (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['MailersSection']]
    """

    return (
        await asyncio_detailed(
            client=client,
            transaction_id=transaction_id,
            full_section=full_section,
        )
    ).parsed
