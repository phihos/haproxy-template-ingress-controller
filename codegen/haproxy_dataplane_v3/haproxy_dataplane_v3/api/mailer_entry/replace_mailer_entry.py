from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.mailer_entry import MailerEntry
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    body: MailerEntry,
    mailers_section: str,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["mailers_section"] = mailers_section

    params["transaction_id"] = transaction_id

    params["version"] = version

    params["force_reload"] = force_reload

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/services/haproxy/configuration/mailer_entries/{name}",
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[Error, MailerEntry]:
    if response.status_code == 200:
        response_200 = MailerEntry.from_dict(response.json())

        return response_200

    if response.status_code == 202:
        response_202 = MailerEntry.from_dict(response.json())

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
    body: MailerEntry,
    mailers_section: str,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Error, MailerEntry]]:
    """Replace a mailer_entry

     Replaces a mailer entry configuration by it's name in the specified mailers section.

    Args:
        name (str):
        mailers_section (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (MailerEntry): Mailer entry of a Mailers section

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, MailerEntry]]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        mailers_section=mailers_section,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: MailerEntry,
    mailers_section: str,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Error, MailerEntry]]:
    """Replace a mailer_entry

     Replaces a mailer entry configuration by it's name in the specified mailers section.

    Args:
        name (str):
        mailers_section (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (MailerEntry): Mailer entry of a Mailers section

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, MailerEntry]
    """

    return sync_detailed(
        name=name,
        client=client,
        body=body,
        mailers_section=mailers_section,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: MailerEntry,
    mailers_section: str,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Response[Union[Error, MailerEntry]]:
    """Replace a mailer_entry

     Replaces a mailer entry configuration by it's name in the specified mailers section.

    Args:
        name (str):
        mailers_section (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (MailerEntry): Mailer entry of a Mailers section

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, MailerEntry]]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        mailers_section=mailers_section,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: MailerEntry,
    mailers_section: str,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
) -> Optional[Union[Error, MailerEntry]]:
    """Replace a mailer_entry

     Replaces a mailer entry configuration by it's name in the specified mailers section.

    Args:
        name (str):
        mailers_section (str):
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        body (MailerEntry): Mailer entry of a Mailers section

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
            body=body,
            mailers_section=mailers_section,
            transaction_id=transaction_id,
            version=version,
            force_reload=force_reload,
        )
    ).parsed
