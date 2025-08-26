from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.mailers_section import MailersSection
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: MailersSection,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
    full_section: Union[Unset, bool] = False,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["transaction_id"] = transaction_id

    params["version"] = version

    params["force_reload"] = force_reload

    params["full_section"] = full_section

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/services/haproxy/configuration/mailers_section",
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[Error, MailersSection]:
    if response.status_code == 201:
        response_201 = MailersSection.from_dict(response.json())

        return response_201

    if response.status_code == 202:
        response_202 = MailersSection.from_dict(response.json())

        return response_202

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

    if response.status_code == 409:
        response_409 = Error.from_dict(response.json())

        return response_409

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, MailersSection]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: MailersSection,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
    full_section: Union[Unset, bool] = False,
) -> Response[Union[Error, MailersSection]]:
    """Add a new Mailers section

     Creates a new empty Mailers section

    Args:
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        full_section (Union[Unset, bool]):  Default: False.
        body (MailersSection): MailersSection with all it's children resources

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, MailersSection]]
    """

    kwargs = _get_kwargs(
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
        full_section=full_section,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: MailersSection,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
    full_section: Union[Unset, bool] = False,
) -> Optional[Union[Error, MailersSection]]:
    """Add a new Mailers section

     Creates a new empty Mailers section

    Args:
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        full_section (Union[Unset, bool]):  Default: False.
        body (MailersSection): MailersSection with all it's children resources

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, MailersSection]
    """

    return sync_detailed(
        client=client,
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
        full_section=full_section,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: MailersSection,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
    full_section: Union[Unset, bool] = False,
) -> Response[Union[Error, MailersSection]]:
    """Add a new Mailers section

     Creates a new empty Mailers section

    Args:
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        full_section (Union[Unset, bool]):  Default: False.
        body (MailersSection): MailersSection with all it's children resources

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, MailersSection]]
    """

    kwargs = _get_kwargs(
        body=body,
        transaction_id=transaction_id,
        version=version,
        force_reload=force_reload,
        full_section=full_section,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: MailersSection,
    transaction_id: Union[Unset, str] = UNSET,
    version: Union[Unset, int] = UNSET,
    force_reload: Union[Unset, bool] = False,
    full_section: Union[Unset, bool] = False,
) -> Optional[Union[Error, MailersSection]]:
    """Add a new Mailers section

     Creates a new empty Mailers section

    Args:
        transaction_id (Union[Unset, str]):
        version (Union[Unset, int]):
        force_reload (Union[Unset, bool]):  Default: False.
        full_section (Union[Unset, bool]):  Default: False.
        body (MailersSection): MailersSection with all it's children resources

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, MailersSection]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            transaction_id=transaction_id,
            version=version,
            force_reload=force_reload,
            full_section=full_section,
        )
    ).parsed
