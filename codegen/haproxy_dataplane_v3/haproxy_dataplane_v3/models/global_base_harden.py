from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.global_base_harden_reject_privileged_ports import GlobalBaseHardenRejectPrivilegedPorts


T = TypeVar("T", bound="GlobalBaseHarden")


@_attrs_define
class GlobalBaseHarden:
    """
    Attributes:
        reject_privileged_ports (Union[Unset, GlobalBaseHardenRejectPrivilegedPorts]):
    """

    reject_privileged_ports: Union[Unset, "GlobalBaseHardenRejectPrivilegedPorts"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        reject_privileged_ports: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.reject_privileged_ports, Unset):
            reject_privileged_ports = self.reject_privileged_ports.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if reject_privileged_ports is not UNSET:
            field_dict["reject_privileged_ports"] = reject_privileged_ports

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.global_base_harden_reject_privileged_ports import GlobalBaseHardenRejectPrivilegedPorts

        d = dict(src_dict)
        _reject_privileged_ports = d.pop("reject_privileged_ports", UNSET)
        reject_privileged_ports: Union[Unset, GlobalBaseHardenRejectPrivilegedPorts]
        if isinstance(_reject_privileged_ports, Unset):
            reject_privileged_ports = UNSET
        else:
            reject_privileged_ports = GlobalBaseHardenRejectPrivilegedPorts.from_dict(_reject_privileged_ports)

        global_base_harden = cls(
            reject_privileged_ports=reject_privileged_ports,
        )

        global_base_harden.additional_properties = d
        return global_base_harden

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
