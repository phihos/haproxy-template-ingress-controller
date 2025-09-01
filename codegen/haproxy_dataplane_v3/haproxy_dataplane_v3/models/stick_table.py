from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.stick_table_type import StickTableType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.stick_table_fields_item import StickTableFieldsItem


T = TypeVar("T", bound="StickTable")


@_attrs_define
class StickTable:
    """Stick Table Information

    Attributes:
        fields (Union[Unset, list['StickTableFieldsItem']]):
        name (Union[Unset, str]):
        size (Union[None, Unset, int]):
        type_ (Union[Unset, StickTableType]):
        used (Union[None, Unset, int]):
    """

    fields: Union[Unset, list["StickTableFieldsItem"]] = UNSET
    name: Union[Unset, str] = UNSET
    size: Union[None, Unset, int] = UNSET
    type_: Union[Unset, StickTableType] = UNSET
    used: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        fields: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.fields, Unset):
            fields = []
            for fields_item_data in self.fields:
                fields_item = fields_item_data.to_dict()
                fields.append(fields_item)

        name = self.name

        size: Union[None, Unset, int]
        if isinstance(self.size, Unset):
            size = UNSET
        else:
            size = self.size

        type_: Union[Unset, str] = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        used: Union[None, Unset, int]
        if isinstance(self.used, Unset):
            used = UNSET
        else:
            used = self.used

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if fields is not UNSET:
            field_dict["fields"] = fields
        if name is not UNSET:
            field_dict["name"] = name
        if size is not UNSET:
            field_dict["size"] = size
        if type_ is not UNSET:
            field_dict["type"] = type_
        if used is not UNSET:
            field_dict["used"] = used

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.stick_table_fields_item import StickTableFieldsItem

        d = dict(src_dict)
        _fields = d.pop("fields", UNSET)
        fields: Union[Unset, list[StickTableFieldsItem]] = UNSET
        if not isinstance(_fields, Unset):
            fields = []
            for fields_item_data in _fields:
                fields_item = StickTableFieldsItem.from_dict(fields_item_data)

                fields.append(fields_item)

        name = d.pop("name", UNSET)

        def _parse_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        size = _parse_size(d.pop("size", UNSET))

        _type_ = d.pop("type", UNSET)
        type_: Union[Unset, StickTableType]
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = StickTableType(_type_)

        def _parse_used(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        used = _parse_used(d.pop("used", UNSET))

        stick_table = cls(
            fields=fields,
            name=name,
            size=size,
            type_=type_,
            used=used,
        )

        stick_table.additional_properties = d
        return stick_table

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
