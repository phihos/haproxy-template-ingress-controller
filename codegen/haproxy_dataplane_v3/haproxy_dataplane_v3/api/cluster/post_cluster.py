from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.cluster_settings import ClusterSettings
from ...models.error import Error
from ...models.post_cluster_configuration import PostClusterConfiguration
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: ClusterSettings,
    configuration: Union[Unset, PostClusterConfiguration] = UNSET,
    advertised_address: Union[Unset, str] = UNSET,
    advertised_port: Union[Unset, int] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    json_configuration: Union[Unset, str] = UNSET
    if not isinstance(configuration, Unset):
        json_configuration = configuration.value

    params["configuration"] = json_configuration

    params["advertised_address"] = advertised_address

    params["advertised_port"] = advertised_port

    params["version"] = version

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/cluster",
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ClusterSettings, Error]]:
    if response.status_code == 200:
        response_200 = ClusterSettings.from_dict(response.json())

        return response_200
    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ClusterSettings, Error]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ClusterSettings,
    configuration: Union[Unset, PostClusterConfiguration] = UNSET,
    advertised_address: Union[Unset, str] = UNSET,
    advertised_port: Union[Unset, int] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> Response[Union[ClusterSettings, Error]]:
    """Post cluster settings

     Post cluster settings

    Args:
        configuration (Union[Unset, PostClusterConfiguration]):
        advertised_address (Union[Unset, str]):
        advertised_port (Union[Unset, int]):
        version (Union[Unset, int]):
        body (ClusterSettings): Settings related to a cluster.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ClusterSettings, Error]]
    """

    kwargs = _get_kwargs(
        body=body,
        configuration=configuration,
        advertised_address=advertised_address,
        advertised_port=advertised_port,
        version=version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ClusterSettings,
    configuration: Union[Unset, PostClusterConfiguration] = UNSET,
    advertised_address: Union[Unset, str] = UNSET,
    advertised_port: Union[Unset, int] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> Optional[Union[ClusterSettings, Error]]:
    """Post cluster settings

     Post cluster settings

    Args:
        configuration (Union[Unset, PostClusterConfiguration]):
        advertised_address (Union[Unset, str]):
        advertised_port (Union[Unset, int]):
        version (Union[Unset, int]):
        body (ClusterSettings): Settings related to a cluster.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ClusterSettings, Error]
    """

    return sync_detailed(
        client=client,
        body=body,
        configuration=configuration,
        advertised_address=advertised_address,
        advertised_port=advertised_port,
        version=version,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ClusterSettings,
    configuration: Union[Unset, PostClusterConfiguration] = UNSET,
    advertised_address: Union[Unset, str] = UNSET,
    advertised_port: Union[Unset, int] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> Response[Union[ClusterSettings, Error]]:
    """Post cluster settings

     Post cluster settings

    Args:
        configuration (Union[Unset, PostClusterConfiguration]):
        advertised_address (Union[Unset, str]):
        advertised_port (Union[Unset, int]):
        version (Union[Unset, int]):
        body (ClusterSettings): Settings related to a cluster.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ClusterSettings, Error]]
    """

    kwargs = _get_kwargs(
        body=body,
        configuration=configuration,
        advertised_address=advertised_address,
        advertised_port=advertised_port,
        version=version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ClusterSettings,
    configuration: Union[Unset, PostClusterConfiguration] = UNSET,
    advertised_address: Union[Unset, str] = UNSET,
    advertised_port: Union[Unset, int] = UNSET,
    version: Union[Unset, int] = UNSET,
) -> Optional[Union[ClusterSettings, Error]]:
    """Post cluster settings

     Post cluster settings

    Args:
        configuration (Union[Unset, PostClusterConfiguration]):
        advertised_address (Union[Unset, str]):
        advertised_port (Union[Unset, int]):
        version (Union[Unset, int]):
        body (ClusterSettings): Settings related to a cluster.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ClusterSettings, Error]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            configuration=configuration,
            advertised_address=advertised_address,
            advertised_port=advertised_port,
            version=version,
        )
    ).parsed
