from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.monitor_fail_cond import MonitorFailCond

T = TypeVar("T", bound="MonitorFail")


@_attrs_define
class MonitorFail:
    """
    Attributes:
        cond (MonitorFailCond):
        cond_test (str):
    """

    cond: MonitorFailCond
    cond_test: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cond = self.cond.value

        cond_test = self.cond_test

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "cond": cond,
                "cond_test": cond_test,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cond = MonitorFailCond(d.pop("cond"))

        cond_test = d.pop("cond_test")

        monitor_fail = cls(
            cond=cond,
            cond_test=cond_test,
        )

        monitor_fail.additional_properties = d
        return monitor_fail

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
