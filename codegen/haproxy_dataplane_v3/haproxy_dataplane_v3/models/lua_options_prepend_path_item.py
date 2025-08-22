from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.lua_options_prepend_path_item_type import LuaOptionsPrependPathItemType
from ..types import UNSET, Unset

T = TypeVar("T", bound="LuaOptionsPrependPathItem")


@_attrs_define
class LuaOptionsPrependPathItem:
    """
    Attributes:
        path (str):
        type_ (Union[Unset, LuaOptionsPrependPathItemType]):
    """

    path: str
    type_: Union[Unset, LuaOptionsPrependPathItemType] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        type_: Union[Unset, str] = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
            }
        )
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        path = d.pop("path")

        _type_ = d.pop("type", UNSET)
        type_: Union[Unset, LuaOptionsPrependPathItemType]
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = LuaOptionsPrependPathItemType(_type_)

        lua_options_prepend_path_item = cls(
            path=path,
            type_=type_,
        )

        lua_options_prepend_path_item.additional_properties = d
        return lua_options_prepend_path_item

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
