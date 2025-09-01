from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.error import Error
from ...models.one_acl_file_entry import OneACLFileEntry
from ...types import Response


def _get_kwargs(
    parent_name: str,
    *,
    body: list["OneACLFileEntry"],
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/services/haproxy/runtime/acls/{parent_name}/entries",
    }

    _kwargs["json"] = []
    for componentsschemasacl_files_entries_item_data in body:
        componentsschemasacl_files_entries_item = componentsschemasacl_files_entries_item_data.to_dict()
        _kwargs["json"].append(componentsschemasacl_files_entries_item)

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[Error, list["OneACLFileEntry"]]:
    if response.status_code == 201:
        _response_201 = response.json()
        response_201 = []
        for componentsschemasacl_files_entries_item_data in _response_201:
            componentsschemasacl_files_entries_item = OneACLFileEntry.from_dict(
                componentsschemasacl_files_entries_item_data
            )

            response_201.append(componentsschemasacl_files_entries_item)

        return response_201

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Error, list["OneACLFileEntry"]]]:
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
    body: list["OneACLFileEntry"],
) -> Response[Union[Error, list["OneACLFileEntry"]]]:
    """Add a new ACL payload

     Adds a new ACL payload.

    Args:
        parent_name (str):
        body (list['OneACLFileEntry']): Array of entries of one runtime acl file

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['OneACLFileEntry']]]
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
    body: list["OneACLFileEntry"],
) -> Optional[Union[Error, list["OneACLFileEntry"]]]:
    """Add a new ACL payload

     Adds a new ACL payload.

    Args:
        parent_name (str):
        body (list['OneACLFileEntry']): Array of entries of one runtime acl file

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['OneACLFileEntry']]
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
    body: list["OneACLFileEntry"],
) -> Response[Union[Error, list["OneACLFileEntry"]]]:
    """Add a new ACL payload

     Adds a new ACL payload.

    Args:
        parent_name (str):
        body (list['OneACLFileEntry']): Array of entries of one runtime acl file

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Error, list['OneACLFileEntry']]]
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
    body: list["OneACLFileEntry"],
) -> Optional[Union[Error, list["OneACLFileEntry"]]]:
    """Add a new ACL payload

     Adds a new ACL payload.

    Args:
        parent_name (str):
        body (list['OneACLFileEntry']): Array of entries of one runtime acl file

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Error, list['OneACLFileEntry']]
    """

    return (
        await asyncio_detailed(
            parent_name=parent_name,
            client=client,
            body=body,
        )
    ).parsed
