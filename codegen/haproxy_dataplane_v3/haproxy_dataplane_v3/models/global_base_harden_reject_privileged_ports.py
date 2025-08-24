from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.global_base_harden_reject_privileged_ports_quic import GlobalBaseHardenRejectPrivilegedPortsQuic
from ..models.global_base_harden_reject_privileged_ports_tcp import GlobalBaseHardenRejectPrivilegedPortsTcp
from ..types import UNSET, Unset

T = TypeVar("T", bound="GlobalBaseHardenRejectPrivilegedPorts")


@_attrs_define
class GlobalBaseHardenRejectPrivilegedPorts:
    """
    Attributes:
        quic (Union[Unset, GlobalBaseHardenRejectPrivilegedPortsQuic]):
        tcp (Union[Unset, GlobalBaseHardenRejectPrivilegedPortsTcp]):
    """

    quic: Union[Unset, GlobalBaseHardenRejectPrivilegedPortsQuic] = UNSET
    tcp: Union[Unset, GlobalBaseHardenRejectPrivilegedPortsTcp] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        quic: Union[Unset, str] = UNSET
        if not isinstance(self.quic, Unset):
            quic = self.quic.value

        tcp: Union[Unset, str] = UNSET
        if not isinstance(self.tcp, Unset):
            tcp = self.tcp.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if quic is not UNSET:
            field_dict["quic"] = quic
        if tcp is not UNSET:
            field_dict["tcp"] = tcp

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _quic = d.pop("quic", UNSET)
        quic: Union[Unset, GlobalBaseHardenRejectPrivilegedPortsQuic]
        if isinstance(_quic, Unset):
            quic = UNSET
        else:
            quic = GlobalBaseHardenRejectPrivilegedPortsQuic(_quic)

        _tcp = d.pop("tcp", UNSET)
        tcp: Union[Unset, GlobalBaseHardenRejectPrivilegedPortsTcp]
        if isinstance(_tcp, Unset):
            tcp = UNSET
        else:
            tcp = GlobalBaseHardenRejectPrivilegedPortsTcp(_tcp)

        global_base_harden_reject_privileged_ports = cls(
            quic=quic,
            tcp=tcp,
        )

        global_base_harden_reject_privileged_ports.additional_properties = d
        return global_base_harden_reject_privileged_ports

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
