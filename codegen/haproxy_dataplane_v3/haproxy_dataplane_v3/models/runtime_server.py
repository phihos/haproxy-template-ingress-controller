from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.runtime_server_admin_state import RuntimeServerAdminState
from ..models.runtime_server_operational_state import RuntimeServerOperationalState
from ..types import UNSET, Unset

T = TypeVar("T", bound="RuntimeServer")


@_attrs_define
class RuntimeServer:
    """Runtime transient server properties

    Example:
        {'address': '127.0.0.5', 'admin_state': 'ready', 'operational_state': 'up', 'port': 80, 'server_id': 1,
            'server_name': 'web_server'}

    Attributes:
        address (Union[Unset, str]):
        admin_state (Union[Unset, RuntimeServerAdminState]):
        id (Union[Unset, str]):
        name (Union[Unset, str]):
        operational_state (Union[Unset, RuntimeServerOperationalState]):
        port (Union[None, Unset, int]):
    """

    address: Union[Unset, str] = UNSET
    admin_state: Union[Unset, RuntimeServerAdminState] = UNSET
    id: Union[Unset, str] = UNSET
    name: Union[Unset, str] = UNSET
    operational_state: Union[Unset, RuntimeServerOperationalState] = UNSET
    port: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        address = self.address

        admin_state: Union[Unset, str] = UNSET
        if not isinstance(self.admin_state, Unset):
            admin_state = self.admin_state.value

        id = self.id

        name = self.name

        operational_state: Union[Unset, str] = UNSET
        if not isinstance(self.operational_state, Unset):
            operational_state = self.operational_state.value

        port: Union[None, Unset, int]
        if isinstance(self.port, Unset):
            port = UNSET
        else:
            port = self.port

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if address is not UNSET:
            field_dict["address"] = address
        if admin_state is not UNSET:
            field_dict["admin_state"] = admin_state
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if operational_state is not UNSET:
            field_dict["operational_state"] = operational_state
        if port is not UNSET:
            field_dict["port"] = port

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        address = d.pop("address", UNSET)

        _admin_state = d.pop("admin_state", UNSET)
        admin_state: Union[Unset, RuntimeServerAdminState]
        if isinstance(_admin_state, Unset):
            admin_state = UNSET
        else:
            admin_state = RuntimeServerAdminState(_admin_state)

        id = d.pop("id", UNSET)

        name = d.pop("name", UNSET)

        _operational_state = d.pop("operational_state", UNSET)
        operational_state: Union[Unset, RuntimeServerOperationalState]
        if isinstance(_operational_state, Unset):
            operational_state = UNSET
        else:
            operational_state = RuntimeServerOperationalState(_operational_state)

        def _parse_port(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        port = _parse_port(d.pop("port", UNSET))

        runtime_server = cls(
            address=address,
            admin_state=admin_state,
            id=id,
            name=name,
            operational_state=operational_state,
            port=port,
        )

        runtime_server.additional_properties = d
        return runtime_server

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
