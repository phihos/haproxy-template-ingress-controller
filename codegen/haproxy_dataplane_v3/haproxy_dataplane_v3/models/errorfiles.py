from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.errorfiles_codes_item import ErrorfilesCodesItem
from ..types import UNSET, Unset

T = TypeVar("T", bound="Errorfiles")


@_attrs_define
class Errorfiles:
    """
    Attributes:
        codes (Union[Unset, list[ErrorfilesCodesItem]]):
        metadata (Union[Unset, Any]):
        name (Union[Unset, str]):
    """

    codes: Union[Unset, list[ErrorfilesCodesItem]] = UNSET
    metadata: Union[Unset, Any] = UNSET
    name: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        codes: Union[Unset, list[int]] = UNSET
        if not isinstance(self.codes, Unset):
            codes = []
            for codes_item_data in self.codes:
                codes_item = codes_item_data.value
                codes.append(codes_item)

        metadata = self.metadata

        name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if codes is not UNSET:
            field_dict["codes"] = codes
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _codes = d.pop("codes", UNSET)
        codes: Union[Unset, list[ErrorfilesCodesItem]] = UNSET
        if not isinstance(_codes, Unset):
            codes = []
            for codes_item_data in _codes:
                codes_item = ErrorfilesCodesItem(codes_item_data)

                codes.append(codes_item)

        metadata = d.pop("metadata", UNSET)

        name = d.pop("name", UNSET)

        errorfiles = cls(
            codes=codes,
            metadata=metadata,
            name=name,
        )

        errorfiles.additional_properties = d
        return errorfiles

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
