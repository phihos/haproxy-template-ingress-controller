from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SSLCrtListEntry")


@_attrs_define
class SSLCrtListEntry:
    """SSL Crt List Entry

    Attributes:
        file (Union[Unset, str]):
        line_number (Union[Unset, int]):
        sni_filter (Union[Unset, list[str]]):
        ssl_bind_config (Union[Unset, str]):
    """

    file: Union[Unset, str] = UNSET
    line_number: Union[Unset, int] = UNSET
    sni_filter: Union[Unset, list[str]] = UNSET
    ssl_bind_config: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file = self.file

        line_number = self.line_number

        sni_filter: Union[Unset, list[str]] = UNSET
        if not isinstance(self.sni_filter, Unset):
            sni_filter = self.sni_filter

        ssl_bind_config = self.ssl_bind_config

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if file is not UNSET:
            field_dict["file"] = file
        if line_number is not UNSET:
            field_dict["line_number"] = line_number
        if sni_filter is not UNSET:
            field_dict["sni_filter"] = sni_filter
        if ssl_bind_config is not UNSET:
            field_dict["ssl_bind_config"] = ssl_bind_config

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file = d.pop("file", UNSET)

        line_number = d.pop("line_number", UNSET)

        sni_filter = cast(list[str], d.pop("sni_filter", UNSET))

        ssl_bind_config = d.pop("ssl_bind_config", UNSET)

        ssl_crt_list_entry = cls(
            file=file,
            line_number=line_number,
            sni_filter=sni_filter,
            ssl_bind_config=ssl_bind_config,
        )

        ssl_crt_list_entry.additional_properties = d
        return ssl_crt_list_entry

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
