from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.lua_options_loads_item import LuaOptionsLoadsItem
    from ..models.lua_options_prepend_path_item import LuaOptionsPrependPathItem


T = TypeVar("T", bound="LuaOptions")


@_attrs_define
class LuaOptions:
    """
    Attributes:
        load_per_thread (Union[Unset, str]):
        loads (Union[Unset, list['LuaOptionsLoadsItem']]):
        prepend_path (Union[Unset, list['LuaOptionsPrependPathItem']]):
    """

    load_per_thread: Union[Unset, str] = UNSET
    loads: Union[Unset, list["LuaOptionsLoadsItem"]] = UNSET
    prepend_path: Union[Unset, list["LuaOptionsPrependPathItem"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        load_per_thread = self.load_per_thread

        loads: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.loads, Unset):
            loads = []
            for loads_item_data in self.loads:
                loads_item = loads_item_data.to_dict()
                loads.append(loads_item)

        prepend_path: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.prepend_path, Unset):
            prepend_path = []
            for prepend_path_item_data in self.prepend_path:
                prepend_path_item = prepend_path_item_data.to_dict()
                prepend_path.append(prepend_path_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if load_per_thread is not UNSET:
            field_dict["load_per_thread"] = load_per_thread
        if loads is not UNSET:
            field_dict["loads"] = loads
        if prepend_path is not UNSET:
            field_dict["prepend_path"] = prepend_path

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.lua_options_loads_item import LuaOptionsLoadsItem
        from ..models.lua_options_prepend_path_item import LuaOptionsPrependPathItem

        d = dict(src_dict)
        load_per_thread = d.pop("load_per_thread", UNSET)

        loads = []
        _loads = d.pop("loads", UNSET)
        for loads_item_data in _loads or []:
            loads_item = LuaOptionsLoadsItem.from_dict(loads_item_data)

            loads.append(loads_item)

        prepend_path = []
        _prepend_path = d.pop("prepend_path", UNSET)
        for prepend_path_item_data in _prepend_path or []:
            prepend_path_item = LuaOptionsPrependPathItem.from_dict(prepend_path_item_data)

            prepend_path.append(prepend_path_item)

        lua_options = cls(
            load_per_thread=load_per_thread,
            loads=loads,
            prepend_path=prepend_path,
        )

        lua_options.additional_properties = d
        return lua_options

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
