from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DgramBind")


@_attrs_define
class DgramBind:
    """HAProxy log forward dgram bind configuration

    Attributes:
        address (Union[Unset, str]):
        interface (Union[Unset, str]):
        metadata (Union[Unset, Any]):
        name (Union[Unset, str]):
        namespace (Union[Unset, str]):
        port (Union[None, Unset, int]):
        port_range_end (Union[None, Unset, int]):
        transparent (Union[Unset, bool]):
    """

    address: Union[Unset, str] = UNSET
    interface: Union[Unset, str] = UNSET
    metadata: Union[Unset, Any] = UNSET
    name: Union[Unset, str] = UNSET
    namespace: Union[Unset, str] = UNSET
    port: Union[None, Unset, int] = UNSET
    port_range_end: Union[None, Unset, int] = UNSET
    transparent: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        address = self.address

        interface = self.interface

        metadata = self.metadata

        name = self.name

        namespace = self.namespace

        port: Union[None, Unset, int]
        if isinstance(self.port, Unset):
            port = UNSET
        else:
            port = self.port

        port_range_end: Union[None, Unset, int]
        if isinstance(self.port_range_end, Unset):
            port_range_end = UNSET
        else:
            port_range_end = self.port_range_end

        transparent = self.transparent

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if address is not UNSET:
            field_dict["address"] = address
        if interface is not UNSET:
            field_dict["interface"] = interface
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if name is not UNSET:
            field_dict["name"] = name
        if namespace is not UNSET:
            field_dict["namespace"] = namespace
        if port is not UNSET:
            field_dict["port"] = port
        if port_range_end is not UNSET:
            field_dict["port-range-end"] = port_range_end
        if transparent is not UNSET:
            field_dict["transparent"] = transparent

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        address = d.pop("address", UNSET)

        interface = d.pop("interface", UNSET)

        metadata = d.pop("metadata", UNSET)

        name = d.pop("name", UNSET)

        namespace = d.pop("namespace", UNSET)

        def _parse_port(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        port = _parse_port(d.pop("port", UNSET))

        def _parse_port_range_end(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        port_range_end = _parse_port_range_end(d.pop("port-range-end", UNSET))

        transparent = d.pop("transparent", UNSET)

        dgram_bind = cls(
            address=address,
            interface=interface,
            metadata=metadata,
            name=name,
            namespace=namespace,
            port=port,
            port_range_end=port_range_end,
            transparent=transparent,
        )

        dgram_bind.additional_properties = d
        return dgram_bind

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
