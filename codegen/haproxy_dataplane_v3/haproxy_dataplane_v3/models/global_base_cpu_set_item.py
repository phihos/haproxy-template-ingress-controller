from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.global_base_cpu_set_item_directive import GlobalBaseCpuSetItemDirective
from ..types import UNSET, Unset

T = TypeVar("T", bound="GlobalBaseCpuSetItem")


@_attrs_define
class GlobalBaseCpuSetItem:
    """
    Attributes:
        directive (GlobalBaseCpuSetItemDirective):
        set_ (Union[Unset, str]):
    """

    directive: GlobalBaseCpuSetItemDirective
    set_: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        directive = self.directive.value

        set_ = self.set_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "directive": directive,
            }
        )
        if set_ is not UNSET:
            field_dict["set"] = set_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        directive = GlobalBaseCpuSetItemDirective(d.pop("directive"))

        set_ = d.pop("set", UNSET)

        global_base_cpu_set_item = cls(
            directive=directive,
            set_=set_,
        )

        global_base_cpu_set_item.additional_properties = d
        return global_base_cpu_set_item

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
