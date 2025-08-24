from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="FiftyOneDegreesOptions")


@_attrs_define
class FiftyOneDegreesOptions:
    """
    Attributes:
        cache_size (Union[Unset, int]):
        data_file (Union[Unset, str]):
        property_name_list (Union[Unset, str]):
        property_separator (Union[Unset, str]):
    """

    cache_size: Union[Unset, int] = UNSET
    data_file: Union[Unset, str] = UNSET
    property_name_list: Union[Unset, str] = UNSET
    property_separator: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cache_size = self.cache_size

        data_file = self.data_file

        property_name_list = self.property_name_list

        property_separator = self.property_separator

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cache_size is not UNSET:
            field_dict["cache_size"] = cache_size
        if data_file is not UNSET:
            field_dict["data_file"] = data_file
        if property_name_list is not UNSET:
            field_dict["property_name_list"] = property_name_list
        if property_separator is not UNSET:
            field_dict["property_separator"] = property_separator

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cache_size = d.pop("cache_size", UNSET)

        data_file = d.pop("data_file", UNSET)

        property_name_list = d.pop("property_name_list", UNSET)

        property_separator = d.pop("property_separator", UNSET)

        fifty_one_degrees_options = cls(
            cache_size=cache_size,
            data_file=data_file,
            property_name_list=property_name_list,
            property_separator=property_separator,
        )

        fifty_one_degrees_options.additional_properties = d
        return fifty_one_degrees_options

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
