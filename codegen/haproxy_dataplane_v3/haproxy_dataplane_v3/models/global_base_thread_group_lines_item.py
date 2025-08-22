from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="GlobalBaseThreadGroupLinesItem")


@_attrs_define
class GlobalBaseThreadGroupLinesItem:
    """
    Attributes:
        group (str):
        num_or_range (str):
    """

    group: str
    num_or_range: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        group = self.group

        num_or_range = self.num_or_range

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "group": group,
                "num_or_range": num_or_range,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        group = d.pop("group")

        num_or_range = d.pop("num_or_range")

        global_base_thread_group_lines_item = cls(
            group=group,
            num_or_range=num_or_range,
        )

        global_base_thread_group_lines_item.additional_properties = d
        return global_base_thread_group_lines_item

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
