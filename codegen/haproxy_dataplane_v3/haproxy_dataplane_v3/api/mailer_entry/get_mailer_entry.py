from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.mailer_entry import MailerEntry
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
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
        "url": f"/services/haproxy/configuration/mailer_entries/{name}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Error, MailerEntry]]:
    if response.status_code == 200:
        response_200 = MailerEntry.from_dict(response.json())

        return response_200
    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, MailerEntry]]:
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
    mailers_section: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[Union[Error, MailerEntry]]:
    """Return one mailer_entry

     Returns one mailer_entry configuration by it's name in the specified mailers section.

    Args:
        name (str):
        mailers_section (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, MailerEntry]]
    """

    kwargs = _get_kwargs(
        name=name,
        mailers_section=mailers_section,
        transaction_id=transaction_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    mailers_section: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[Union[Error, MailerEntry]]:
    """Return one mailer_entry

     Returns one mailer_entry configuration by it's name in the specified mailers section.

    Args:
        name (str):
        mailers_section (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, MailerEntry]
    """

    return sync_detailed(
        name=name,
        client=client,
        mailers_section=mailers_section,
        transaction_id=transaction_id,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    mailers_section: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[Union[Error, MailerEntry]]:
    """Return one mailer_entry

     Returns one mailer_entry configuration by it's name in the specified mailers section.

    Args:
        name (str):
        mailers_section (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, MailerEntry]]
    """

    kwargs = _get_kwargs(
        name=name,
        mailers_section=mailers_section,
        transaction_id=transaction_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    mailers_section: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[Union[Error, MailerEntry]]:
    """Return one mailer_entry

     Returns one mailer_entry configuration by it's name in the specified mailers section.

    Args:
        name (str):
        mailers_section (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, MailerEntry]
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            mailers_section=mailers_section,
            transaction_id=transaction_id,
        )
    ).parsed
