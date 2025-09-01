from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.peer_entry import PeerEntry
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    peer_section: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["peer_section"] = peer_section

    params["transaction_id"] = transaction_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/services/haproxy/configuration/peer_entries",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[Error, list["PeerEntry"]]:
    if response.status_code == 200:
        _response_200 = response.json()
        response_200 = []
        for componentsschemaspeer_entries_item_data in _response_200:
            componentsschemaspeer_entries_item = PeerEntry.from_dict(componentsschemaspeer_entries_item_data)

            response_200.append(componentsschemaspeer_entries_item)

        return response_200

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, list["PeerEntry"]]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    peer_section: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[Union[Error, list["PeerEntry"]]]:
    """Return an array of peer_entries

     Returns an array of all peer_entries that are configured in specified peer section.

    Args:
        peer_section (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['PeerEntry']]]
    """

    kwargs = _get_kwargs(
        peer_section=peer_section,
        transaction_id=transaction_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    peer_section: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[Union[Error, list["PeerEntry"]]]:
    """Return an array of peer_entries

     Returns an array of all peer_entries that are configured in specified peer section.

    Args:
        peer_section (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['PeerEntry']]
    """

    return sync_detailed(
        client=client,
        peer_section=peer_section,
        transaction_id=transaction_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    peer_section: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Response[Union[Error, list["PeerEntry"]]]:
    """Return an array of peer_entries

     Returns an array of all peer_entries that are configured in specified peer section.

    Args:
        peer_section (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['PeerEntry']]]
    """

    kwargs = _get_kwargs(
        peer_section=peer_section,
        transaction_id=transaction_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    peer_section: str,
    transaction_id: Union[Unset, str] = UNSET,
) -> Optional[Union[Error, list["PeerEntry"]]]:
    """Return an array of peer_entries

     Returns an array of all peer_entries that are configured in specified peer section.

    Args:
        peer_section (str):
        transaction_id (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['PeerEntry']]
    """

    return (
        await asyncio_detailed(
            client=client,
            peer_section=peer_section,
            transaction_id=transaction_id,
        )
    ).parsed
