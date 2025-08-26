from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.set_stick_table_entries_body import SetStickTableEntriesBody
from ...types import Response


def _get_kwargs(
    parent_name: str,
    *,
    body: SetStickTableEntriesBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/services/haproxy/runtime/stick_tables/{parent_name}/entries",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Union[Any, Error]:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, Error]]:
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
    body: SetStickTableEntriesBody,
) -> Response[Union[Any, Error]]:
    """Set Entry to Stick Table

     Create or update a stick-table entry in the table.

    Args:
        parent_name (str):
        body (SetStickTableEntriesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Error]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: SetStickTableEntriesBody,
) -> Optional[Union[Any, Error]]:
    """Set Entry to Stick Table

     Create or update a stick-table entry in the table.

    Args:
        parent_name (str):
        body (SetStickTableEntriesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Error]
    """

    return sync_detailed(
        parent_name=parent_name,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: SetStickTableEntriesBody,
) -> Response[Union[Any, Error]]:
    """Set Entry to Stick Table

     Create or update a stick-table entry in the table.

    Args:
        parent_name (str):
        body (SetStickTableEntriesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Error]]
    """

    kwargs = _get_kwargs(
        parent_name=parent_name,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    parent_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    body: SetStickTableEntriesBody,
) -> Optional[Union[Any, Error]]:
    """Set Entry to Stick Table

     Create or update a stick-table entry in the table.

    Args:
        parent_name (str):
        body (SetStickTableEntriesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Error]
    """

    return (
        await asyncio_detailed(
            parent_name=parent_name,
            client=client,
            body=body,
        )
    ).parsed
