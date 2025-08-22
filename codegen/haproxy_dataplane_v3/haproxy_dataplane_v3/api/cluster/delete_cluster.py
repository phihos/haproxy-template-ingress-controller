from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_cluster_configuration import DeleteClusterConfiguration
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    configuration: Union[Unset, DeleteClusterConfiguration] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_configuration: Union[Unset, str] = UNSET
    if not isinstance(configuration, Unset):
        json_configuration = configuration.value

    params["configuration"] = json_configuration

    params["version"] = version

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/cluster",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Optional[Any]:
    if response.status_code == 204:
        return None
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Response[Any]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    configuration: Union[Unset, DeleteClusterConfiguration] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> Response[Any]:
    """Delete cluster settings

     Delete cluster settings and move the node back to single mode

    Args:
        configuration (Union[Unset, DeleteClusterConfiguration]):
        version (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        configuration=configuration,
        version=version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    configuration: Union[Unset, DeleteClusterConfiguration] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> Response[Any]:
    """Delete cluster settings

     Delete cluster settings and move the node back to single mode

    Args:
        configuration (Union[Unset, DeleteClusterConfiguration]):
        version (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        configuration=configuration,
        version=version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
