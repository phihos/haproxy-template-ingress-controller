from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.stats_http_request_type import StatsHttpRequestType
from ..types import UNSET, Unset

T = TypeVar("T", bound="StatsHttpRequest")


@_attrs_define
class StatsHttpRequest:
    """
    Attributes:
        type_ (StatsHttpRequestType):
        cond (Union[Unset, str]):
        cond_test (Union[Unset, str]):
        realm (Union[Unset, str]):
    """

    type_: StatsHttpRequestType
    cond: Union[Unset, str] = UNSET
    cond_test: Union[Unset, str] = UNSET
    realm: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        cond = self.cond

        cond_test = self.cond_test

        realm = self.realm

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if cond is not UNSET:
            field_dict["cond"] = cond
        if cond_test is not UNSET:
            field_dict["cond_test"] = cond_test
        if realm is not UNSET:
            field_dict["realm"] = realm

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = StatsHttpRequestType(d.pop("type"))

        cond = d.pop("cond", UNSET)

        cond_test = d.pop("cond_test", UNSET)

        realm = d.pop("realm", UNSET)

        stats_http_request = cls(
            type_=type_,
            cond=cond,
            cond_test=cond_test,
            realm=realm,
        )

        stats_http_request.additional_properties = d
        return stats_http_request

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
