from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.consul_server_health_check_policy import ConsulServerHealthCheckPolicy
from ..models.consul_server_mode import ConsulServerMode
from ..models.consul_server_server_slots_growth_type import ConsulServerServerSlotsGrowthType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ConsulServer")


@_attrs_define
class ConsulServer:
    """Consul server configuration

    Example:
        {'address': '127.0.0.1', 'enabled': True, 'id': '0', 'port': 90, 'retry_timeout': 10}

    Attributes:
        address (str):
        enabled (bool):
        port (int):
        retry_timeout (int): Duration in seconds in-between data pulling requests to the consul server
        defaults (Union[Unset, str]): Name of the defaults section to be used in backends created by this service
        description (Union[Unset, str]):
        health_check_policy (Union[Unset, ConsulServerHealthCheckPolicy]): Defines the health check conditions required
            for each node to be considered valid for the service.
              none: all nodes are considered valid
              any: a node is considered valid if any one health check is 'passing'
              all: a node is considered valid if all health checks are 'passing'
              min: a node is considered valid if the number of 'passing' checks is greater or equal to the
            'health_check_policy_min' value.
                If the node has less health checks configured then 'health_check_policy_min' it is considered invalid.
            Default: ConsulServerHealthCheckPolicy.NONE.
        health_check_policy_min (Union[Unset, int]):
        id (Union[None, Unset, str]): Auto generated ID.
        mode (Union[Unset, ConsulServerMode]):  Default: ConsulServerMode.HTTP.
        name (Union[Unset, str]):
        namespace (Union[Unset, str]):
        server_slots_base (Union[Unset, int]):  Default: 10.
        server_slots_growth_increment (Union[Unset, int]):
        server_slots_growth_type (Union[Unset, ConsulServerServerSlotsGrowthType]):  Default:
            ConsulServerServerSlotsGrowthType.EXPONENTIAL.
        service_allowlist (Union[Unset, list[str]]):
        service_denylist (Union[Unset, list[str]]):
        service_name_regexp (Union[Unset, str]): Regular expression used to filter services by name.
        token (Union[Unset, str]):
    """

    address: str
    enabled: bool
    port: int
    retry_timeout: int
    defaults: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    health_check_policy: Union[Unset, ConsulServerHealthCheckPolicy] = ConsulServerHealthCheckPolicy.NONE
    health_check_policy_min: Union[Unset, int] = UNSET
    id: Union[None, Unset, str] = UNSET
    mode: Union[Unset, ConsulServerMode] = ConsulServerMode.HTTP
    name: Union[Unset, str] = UNSET
    namespace: Union[Unset, str] = UNSET
    server_slots_base: Union[Unset, int] = 10
    server_slots_growth_increment: Union[Unset, int] = UNSET
    server_slots_growth_type: Union[Unset, ConsulServerServerSlotsGrowthType] = (
        ConsulServerServerSlotsGrowthType.EXPONENTIAL
    )
    service_allowlist: Union[Unset, list[str]] = UNSET
    service_denylist: Union[Unset, list[str]] = UNSET
    service_name_regexp: Union[Unset, str] = UNSET
    token: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        address = self.address

        enabled = self.enabled

        port = self.port

        retry_timeout = self.retry_timeout

        defaults = self.defaults

        description = self.description

        health_check_policy: Union[Unset, str] = UNSET
        if not isinstance(self.health_check_policy, Unset):
            health_check_policy = self.health_check_policy.value

        health_check_policy_min = self.health_check_policy_min

        id: Union[None, Unset, str]
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        mode: Union[Unset, str] = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        name = self.name

        namespace = self.namespace

        server_slots_base = self.server_slots_base

        server_slots_growth_increment = self.server_slots_growth_increment

        server_slots_growth_type: Union[Unset, str] = UNSET
        if not isinstance(self.server_slots_growth_type, Unset):
            server_slots_growth_type = self.server_slots_growth_type.value

        service_allowlist: Union[Unset, list[str]] = UNSET
        if not isinstance(self.service_allowlist, Unset):
            service_allowlist = self.service_allowlist

        service_denylist: Union[Unset, list[str]] = UNSET
        if not isinstance(self.service_denylist, Unset):
            service_denylist = self.service_denylist

        service_name_regexp = self.service_name_regexp

        token = self.token

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "address": address,
                "enabled": enabled,
                "port": port,
                "retry_timeout": retry_timeout,
            }
        )
        if defaults is not UNSET:
            field_dict["defaults"] = defaults
        if description is not UNSET:
            field_dict["description"] = description
        if health_check_policy is not UNSET:
            field_dict["health_check_policy"] = health_check_policy
        if health_check_policy_min is not UNSET:
            field_dict["health_check_policy_min"] = health_check_policy_min
        if id is not UNSET:
            field_dict["id"] = id
        if mode is not UNSET:
            field_dict["mode"] = mode
        if name is not UNSET:
            field_dict["name"] = name
        if namespace is not UNSET:
            field_dict["namespace"] = namespace
        if server_slots_base is not UNSET:
            field_dict["server_slots_base"] = server_slots_base
        if server_slots_growth_increment is not UNSET:
            field_dict["server_slots_growth_increment"] = server_slots_growth_increment
        if server_slots_growth_type is not UNSET:
            field_dict["server_slots_growth_type"] = server_slots_growth_type
        if service_allowlist is not UNSET:
            field_dict["service_allowlist"] = service_allowlist
        if service_denylist is not UNSET:
            field_dict["service_denylist"] = service_denylist
        if service_name_regexp is not UNSET:
            field_dict["service_name_regexp"] = service_name_regexp
        if token is not UNSET:
            field_dict["token"] = token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        address = d.pop("address")

        enabled = d.pop("enabled")

        port = d.pop("port")

        retry_timeout = d.pop("retry_timeout")

        defaults = d.pop("defaults", UNSET)

        description = d.pop("description", UNSET)

        _health_check_policy = d.pop("health_check_policy", UNSET)
        health_check_policy: Union[Unset, ConsulServerHealthCheckPolicy]
        if isinstance(_health_check_policy, Unset):
            health_check_policy = UNSET
        else:
            health_check_policy = ConsulServerHealthCheckPolicy(_health_check_policy)

        health_check_policy_min = d.pop("health_check_policy_min", UNSET)

        def _parse_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        id = _parse_id(d.pop("id", UNSET))

        _mode = d.pop("mode", UNSET)
        mode: Union[Unset, ConsulServerMode]
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = ConsulServerMode(_mode)

        name = d.pop("name", UNSET)

        namespace = d.pop("namespace", UNSET)

        server_slots_base = d.pop("server_slots_base", UNSET)

        server_slots_growth_increment = d.pop("server_slots_growth_increment", UNSET)

        _server_slots_growth_type = d.pop("server_slots_growth_type", UNSET)
        server_slots_growth_type: Union[Unset, ConsulServerServerSlotsGrowthType]
        if isinstance(_server_slots_growth_type, Unset):
            server_slots_growth_type = UNSET
        else:
            server_slots_growth_type = ConsulServerServerSlotsGrowthType(_server_slots_growth_type)

        service_allowlist = cast(list[str], d.pop("service_allowlist", UNSET))

        service_denylist = cast(list[str], d.pop("service_denylist", UNSET))

        service_name_regexp = d.pop("service_name_regexp", UNSET)

        token = d.pop("token", UNSET)

        consul_server = cls(
            address=address,
            enabled=enabled,
            port=port,
            retry_timeout=retry_timeout,
            defaults=defaults,
            description=description,
            health_check_policy=health_check_policy,
            health_check_policy_min=health_check_policy_min,
            id=id,
            mode=mode,
            name=name,
            namespace=namespace,
            server_slots_base=server_slots_base,
            server_slots_growth_increment=server_slots_growth_increment,
            server_slots_growth_type=server_slots_growth_type,
            service_allowlist=service_allowlist,
            service_denylist=service_denylist,
            service_name_regexp=service_name_regexp,
            token=token,
        )

        return consul_server
