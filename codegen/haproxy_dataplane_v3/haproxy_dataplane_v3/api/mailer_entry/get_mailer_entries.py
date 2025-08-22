from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.mailer_entry import MailerEntry
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    mailers_section: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["mailers_section"] = mailers_section

    params["transaction_id"] = transaction_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/services/haproxy/configuration/mailer_entries",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[list["MailerEntry"]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for componentsschemasmailer_entries_item_data in _response_200:
            componentsschemasmailer_entries_item = MailerEntry.from_dict(componentsschemasmailer_entries_item_data)

            response_200.append(componentsschemasmailer_entries_item)

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[list["MailerEntry"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    mailers_section: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[list["MailerEntry"]]:
    """Return an array of mailer_entries

     Returns an array of all the mailer_entries configured in the specified mailers section.

    Args:
        mailers_section (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['MailerEntry']]
    """

    kwargs = _get_kwargs(
        mailers_section=mailers_section,
        transaction_id=transaction_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    mailers_section: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[list["MailerEntry"]]:
    """Return an array of mailer_entries

     Returns an array of all the mailer_entries configured in the specified mailers section.

    Args:
        mailers_section (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['MailerEntry']
    """

    return sync_detailed(
        client=client,
        mailers_section=mailers_section,
        transaction_id=transaction_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    mailers_section: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[list["MailerEntry"]]:
    """Return an array of mailer_entries

     Returns an array of all the mailer_entries configured in the specified mailers section.

    Args:
        mailers_section (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['MailerEntry']]
    """

    kwargs = _get_kwargs(
        mailers_section=mailers_section,
        transaction_id=transaction_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    mailers_section: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[list["MailerEntry"]]:
    """Return an array of mailer_entries

     Returns an array of all the mailer_entries configured in the specified mailers section.

    Args:
        mailers_section (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['MailerEntry']
    """

    return (
        await asyncio_detailed(
            client=client,
            mailers_section=mailers_section,
            transaction_id=transaction_id,
        )
    ).parsed
