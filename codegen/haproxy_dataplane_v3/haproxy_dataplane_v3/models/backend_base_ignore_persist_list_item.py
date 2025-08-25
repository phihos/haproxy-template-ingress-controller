from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.backend_base_ignore_persist_list_item_cond import BackendBaseIgnorePersistListItemCond

T = TypeVar("T", bound="BackendBaseIgnorePersistListItem")


@_attrs_define
class BackendBaseIgnorePersistListItem:
    """
    Attributes:
        cond (BackendBaseIgnorePersistListItemCond):
        cond_test (str):
    """

    cond: BackendBaseIgnorePersistListItemCond
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
        cond = BackendBaseIgnorePersistListItemCond(d.pop("cond"))

        cond_test = d.pop("cond_test")

        backend_base_ignore_persist_list_item = cls(
            cond=cond,
            cond_test=cond_test,
        )

        backend_base_ignore_persist_list_item.additional_properties = d
        return backend_base_ignore_persist_list_item

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
