from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeviceAtlasOptions")


@_attrs_define
class DeviceAtlasOptions:
    """
    Attributes:
        json_file (Union[Unset, str]):
        log_level (Union[Unset, str]):
        properties_cookie (Union[Unset, str]):
        separator (Union[Unset, str]):
    """

    json_file: Union[Unset, str] = UNSET
    log_level: Union[Unset, str] = UNSET
    properties_cookie: Union[Unset, str] = UNSET
    separator: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        json_file = self.json_file

        log_level = self.log_level

        properties_cookie = self.properties_cookie

        separator = self.separator

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if json_file is not UNSET:
            field_dict["json_file"] = json_file
        if log_level is not UNSET:
            field_dict["log_level"] = log_level
        if properties_cookie is not UNSET:
            field_dict["properties_cookie"] = properties_cookie
        if separator is not UNSET:
            field_dict["separator"] = separator

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        json_file = d.pop("json_file", UNSET)

        log_level = d.pop("log_level", UNSET)

        properties_cookie = d.pop("properties_cookie", UNSET)

        separator = d.pop("separator", UNSET)

        device_atlas_options = cls(
            json_file=json_file,
            log_level=log_level,
            properties_cookie=properties_cookie,
            separator=separator,
        )

        device_atlas_options.additional_properties = d
        return device_atlas_options

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
