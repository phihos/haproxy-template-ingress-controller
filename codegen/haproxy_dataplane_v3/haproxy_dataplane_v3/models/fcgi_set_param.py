from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.fcgi_set_param_cond import FcgiSetParamCond
from ..types import UNSET, Unset

T = TypeVar("T", bound="FcgiSetParam")


@_attrs_define
class FcgiSetParam:
    """Sets a FastCGI parameter to pass to this application.
    Its value, defined by <format> can take a formatted string, the same as the log directive.
    Optionally, you can follow it with an ACL-based condition, in which case the FastCGI application evaluates it only
    if the condition is true.

        Attributes:
            cond (Union[Unset, FcgiSetParamCond]):
            cond_test (Union[Unset, str]):
            format_ (Union[Unset, str]):
            name (Union[Unset, str]):
    """

    cond: Union[Unset, FcgiSetParamCond] = UNSET
    cond_test: Union[Unset, str] = UNSET
    format_: Union[Unset, str] = UNSET
    name: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cond: Union[Unset, str] = UNSET
        if not isinstance(self.cond, Unset):
            cond = self.cond.value

        cond_test = self.cond_test

        format_ = self.format_

        name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cond is not UNSET:
            field_dict["cond"] = cond
        if cond_test is not UNSET:
            field_dict["cond_test"] = cond_test
        if format_ is not UNSET:
            field_dict["format"] = format_
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _cond = d.pop("cond", UNSET)
        cond: Union[Unset, FcgiSetParamCond]
        if isinstance(_cond, Unset):
            cond = UNSET
        else:
            cond = FcgiSetParamCond(_cond)

        cond_test = d.pop("cond_test", UNSET)

        format_ = d.pop("format", UNSET)

        name = d.pop("name", UNSET)

        fcgi_set_param = cls(
            cond=cond,
            cond_test=cond_test,
            format_=format_,
            name=name,
        )

        fcgi_set_param.additional_properties = d
        return fcgi_set_param

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
