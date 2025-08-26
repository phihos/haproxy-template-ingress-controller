from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...models.delete_cluster_configuration import DeleteClusterConfiguration
from ...models.error import Error
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
    *,
    client: Union[AuthenticatedClient, Client],
    configuration: Union[Unset, DeleteClusterConfiguration] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> Response[Union[Any, Error]]:
    """Delete cluster settings

     Delete cluster settings and move the node back to single mode

    Args:
        configuration (Union[Unset, DeleteClusterConfiguration]):
        version (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Error]]
    """

    kwargs = _get_kwargs(
        configuration=configuration,
        version=version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    configuration: Union[Unset, DeleteClusterConfiguration] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> Optional[Union[Any, Error]]:
    """Delete cluster settings

     Delete cluster settings and move the node back to single mode

    Args:
        configuration (Union[Unset, DeleteClusterConfiguration]):
        version (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Error]
    """

    return sync_detailed(
        client=client,
        configuration=configuration,
        version=version,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    configuration: Union[Unset, DeleteClusterConfiguration] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> Response[Union[Any, Error]]:
    """Delete cluster settings

     Delete cluster settings and move the node back to single mode

    Args:
        configuration (Union[Unset, DeleteClusterConfiguration]):
        version (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, Error]]
    """

    kwargs = _get_kwargs(
        configuration=configuration,
        version=version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    configuration: Union[Unset, DeleteClusterConfiguration] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> Optional[Union[Any, Error]]:
    """Delete cluster settings

     Delete cluster settings and move the node back to single mode

    Args:
        configuration (Union[Unset, DeleteClusterConfiguration]):
        version (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, Error]
    """

    return (
        await asyncio_detailed(
            client=client,
            configuration=configuration,
            version=version,
        )
    ).parsed
