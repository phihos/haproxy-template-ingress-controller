from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="InformationSystemCpuInfo")


@_attrs_define
class InformationSystemCpuInfo:
    """
    Attributes:
        model (Union[Unset, str]):
        num_cpus (Union[Unset, int]): Number of logical CPUs
    """

    model: Union[Unset, str] = UNSET
    num_cpus: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        model = self.model

        num_cpus = self.num_cpus

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if model is not UNSET:
            field_dict["model"] = model
        if num_cpus is not UNSET:
            field_dict["num_cpus"] = num_cpus

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        model = d.pop("model", UNSET)

        num_cpus = d.pop("num_cpus", UNSET)

        information_system_cpu_info = cls(
            model=model,
            num_cpus=num_cpus,
        )

        information_system_cpu_info.additional_properties = d
        return information_system_cpu_info

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
