from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.fcgi_pass_header_cond import FcgiPassHeaderCond
from ..types import UNSET, Unset

T = TypeVar("T", bound="FcgiPassHeader")


@_attrs_define
class FcgiPassHeader:
    """Specifies the name of a request header to pass to the FastCGI application.
    Optionally, you can follow it with an ACL-based condition, in which case the FastCGI application evaluates it only
    if the condition is true.
    Most request headers are already available to the FastCGI application with the prefix "HTTP".
    Thus, you only need this directive to pass headers that are purposefully omitted.
    Currently, the headers "Authorization", "Proxy-Authorization", and hop-by-hop headers are omitted.
    Note that the headers "Content-type" and "Content-length" never pass to the FastCGI application because they are
    already converted into parameters.

        Attributes:
            cond (Union[Unset, FcgiPassHeaderCond]):
            cond_test (Union[Unset, str]):
            name (Union[Unset, str]):
    """

    cond: Union[Unset, FcgiPassHeaderCond] = UNSET
    cond_test: Union[Unset, str] = UNSET
    name: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cond: Union[Unset, str] = UNSET
        if not isinstance(self.cond, Unset):
            cond = self.cond.value

        cond_test = self.cond_test

        name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cond is not UNSET:
            field_dict["cond"] = cond
        if cond_test is not UNSET:
            field_dict["cond_test"] = cond_test
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _cond = d.pop("cond", UNSET)
        cond: Union[Unset, FcgiPassHeaderCond]
        if isinstance(_cond, Unset):
            cond = UNSET
        else:
            cond = FcgiPassHeaderCond(_cond)

        cond_test = d.pop("cond_test", UNSET)

        name = d.pop("name", UNSET)

        fcgi_pass_header = cls(
            cond=cond,
            cond_test=cond_test,
            name=name,
        )

        fcgi_pass_header.additional_properties = d
        return fcgi_pass_header

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
