from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="GlobalBaseCpuMapsItem")


@_attrs_define
class GlobalBaseCpuMapsItem:
    """
    Attributes:
        cpu_set (str):
        process (str):
    """

    cpu_set: str
    process: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cpu_set = self.cpu_set

        process = self.process

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "cpu_set": cpu_set,
                "process": process,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cpu_set = d.pop("cpu_set")

        process = d.pop("process")

        global_base_cpu_maps_item = cls(
            cpu_set=cpu_set,
            process=process,
        )

        global_base_cpu_maps_item.additional_properties = d
        return global_base_cpu_maps_item

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
