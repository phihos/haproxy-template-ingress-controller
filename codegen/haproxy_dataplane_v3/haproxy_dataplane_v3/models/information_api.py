import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="InformationApi")


@_attrs_define
class InformationApi:
    """
    Attributes:
        build_date (Union[Unset, datetime.datetime]): HAProxy Dataplane API build date
        version (Union[Unset, str]): HAProxy Dataplane API version string
    """

    build_date: Union[Unset, datetime.datetime] = UNSET
    version: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        build_date: Union[Unset, str] = UNSET
        if not isinstance(self.build_date, Unset):
            build_date = self.build_date.isoformat()

        version = self.version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if build_date is not UNSET:
            field_dict["build_date"] = build_date
        if version is not UNSET:
            field_dict["version"] = version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _build_date = d.pop("build_date", UNSET)
        build_date: Union[Unset, datetime.datetime]
        if isinstance(_build_date, Unset):
            build_date = UNSET
        else:
            build_date = isoparse(_build_date)

        version = d.pop("version", UNSET)

        information_api = cls(
            build_date=build_date,
            version=version,
        )

        information_api.additional_properties = d
        return information_api

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
