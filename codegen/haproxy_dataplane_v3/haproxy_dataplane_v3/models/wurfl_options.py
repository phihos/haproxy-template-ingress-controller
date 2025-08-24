from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="WurflOptions")


@_attrs_define
class WurflOptions:
    """
    Attributes:
        cache_size (Union[Unset, int]):
        data_file (Union[Unset, str]):
        information_list (Union[Unset, str]):
        information_list_separator (Union[Unset, str]):
        patch_file (Union[Unset, str]):
    """

    cache_size: Union[Unset, int] = UNSET
    data_file: Union[Unset, str] = UNSET
    information_list: Union[Unset, str] = UNSET
    information_list_separator: Union[Unset, str] = UNSET
    patch_file: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cache_size = self.cache_size

        data_file = self.data_file

        information_list = self.information_list

        information_list_separator = self.information_list_separator

        patch_file = self.patch_file

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cache_size is not UNSET:
            field_dict["cache_size"] = cache_size
        if data_file is not UNSET:
            field_dict["data_file"] = data_file
        if information_list is not UNSET:
            field_dict["information_list"] = information_list
        if information_list_separator is not UNSET:
            field_dict["information_list_separator"] = information_list_separator
        if patch_file is not UNSET:
            field_dict["patch_file"] = patch_file

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cache_size = d.pop("cache_size", UNSET)

        data_file = d.pop("data_file", UNSET)

        information_list = d.pop("information_list", UNSET)

        information_list_separator = d.pop("information_list_separator", UNSET)

        patch_file = d.pop("patch_file", UNSET)

        wurfl_options = cls(
            cache_size=cache_size,
            data_file=data_file,
            information_list=information_list,
            information_list_separator=information_list_separator,
            patch_file=patch_file,
        )

        wurfl_options.additional_properties = d
        return wurfl_options

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
