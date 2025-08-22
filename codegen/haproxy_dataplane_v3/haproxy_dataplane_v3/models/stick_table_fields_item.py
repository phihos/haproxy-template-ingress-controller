from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.stick_table_fields_item_field import StickTableFieldsItemField
from ..models.stick_table_fields_item_type import StickTableFieldsItemType
from ..types import UNSET, Unset

T = TypeVar("T", bound="StickTableFieldsItem")


@_attrs_define
class StickTableFieldsItem:
    """
    Attributes:
        field (Union[Unset, StickTableFieldsItemField]):
        period (Union[Unset, int]):
        type_ (Union[Unset, StickTableFieldsItemType]):
    """

    field: Union[Unset, StickTableFieldsItemField] = UNSET
    period: Union[Unset, int] = UNSET
    type_: Union[Unset, StickTableFieldsItemType] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field: Union[Unset, str] = UNSET
        if not isinstance(self.field, Unset):
            field = self.field.value

        period = self.period

        type_: Union[Unset, str] = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if field is not UNSET:
            field_dict["field"] = field
        if period is not UNSET:
            field_dict["period"] = period
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _field = d.pop("field", UNSET)
        field: Union[Unset, StickTableFieldsItemField]
        if isinstance(_field, Unset):
            field = UNSET
        else:
            field = StickTableFieldsItemField(_field)

        period = d.pop("period", UNSET)

        _type_ = d.pop("type", UNSET)
        type_: Union[Unset, StickTableFieldsItemType]
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = StickTableFieldsItemType(_type_)

        stick_table_fields_item = cls(
            field=field,
            period=period,
            type_=type_,
        )

        stick_table_fields_item.additional_properties = d
        return stick_table_fields_item

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
