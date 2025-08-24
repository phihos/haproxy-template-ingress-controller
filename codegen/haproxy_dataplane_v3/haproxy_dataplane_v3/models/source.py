from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.source_usesrc import SourceUsesrc
from ..types import UNSET, Unset

T = TypeVar("T", bound="Source")


@_attrs_define
class Source:
    """
    Attributes:
        address (str):
        address_second (Union[Unset, str]):
        hdr (Union[Unset, str]):
        interface (Union[Unset, str]):
        occ (Union[Unset, str]):
        port (Union[Unset, int]):
        port_second (Union[Unset, int]):
        usesrc (Union[Unset, SourceUsesrc]):
    """

    address: str
    address_second: Union[Unset, str] = UNSET
    hdr: Union[Unset, str] = UNSET
    interface: Union[Unset, str] = UNSET
    occ: Union[Unset, str] = UNSET
    port: Union[Unset, int] = UNSET
    port_second: Union[Unset, int] = UNSET
    usesrc: Union[Unset, SourceUsesrc] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        address = self.address

        address_second = self.address_second

        hdr = self.hdr

        interface = self.interface

        occ = self.occ

        port = self.port

        port_second = self.port_second

        usesrc: Union[Unset, str] = UNSET
        if not isinstance(self.usesrc, Unset):
            usesrc = self.usesrc.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "address": address,
            }
        )
        if address_second is not UNSET:
            field_dict["address_second"] = address_second
        if hdr is not UNSET:
            field_dict["hdr"] = hdr
        if interface is not UNSET:
            field_dict["interface"] = interface
        if occ is not UNSET:
            field_dict["occ"] = occ
        if port is not UNSET:
            field_dict["port"] = port
        if port_second is not UNSET:
            field_dict["port_second"] = port_second
        if usesrc is not UNSET:
            field_dict["usesrc"] = usesrc

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        address = d.pop("address")

        address_second = d.pop("address_second", UNSET)

        hdr = d.pop("hdr", UNSET)

        interface = d.pop("interface", UNSET)

        occ = d.pop("occ", UNSET)

        port = d.pop("port", UNSET)

        port_second = d.pop("port_second", UNSET)

        _usesrc = d.pop("usesrc", UNSET)
        usesrc: Union[Unset, SourceUsesrc]
        if isinstance(_usesrc, Unset):
            usesrc = UNSET
        else:
            usesrc = SourceUsesrc(_usesrc)

        source = cls(
            address=address,
            address_second=address_second,
            hdr=hdr,
            interface=interface,
            occ=occ,
            port=port,
            port_second=port_second,
            usesrc=usesrc,
        )

        source.additional_properties = d
        return source

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
