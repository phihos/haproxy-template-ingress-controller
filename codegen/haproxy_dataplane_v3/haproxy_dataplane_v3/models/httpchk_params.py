from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.httpchk_params_method import HttpchkParamsMethod
from ..types import UNSET, Unset

T = TypeVar("T", bound="HttpchkParams")


@_attrs_define
class HttpchkParams:
    """
    Attributes:
        host (Union[Unset, str]):
        method (Union[Unset, HttpchkParamsMethod]):
        uri (Union[Unset, str]):
        version (Union[Unset, str]):
    """

    host: Union[Unset, str] = UNSET
    method: Union[Unset, HttpchkParamsMethod] = UNSET
    uri: Union[Unset, str] = UNSET
    version: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        host = self.host

        method: Union[Unset, str] = UNSET
        if not isinstance(self.method, Unset):
            method = self.method.value

        uri = self.uri

        version = self.version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if host is not UNSET:
            field_dict["host"] = host
        if method is not UNSET:
            field_dict["method"] = method
        if uri is not UNSET:
            field_dict["uri"] = uri
        if version is not UNSET:
            field_dict["version"] = version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        host = d.pop("host", UNSET)

        _method = d.pop("method", UNSET)
        method: Union[Unset, HttpchkParamsMethod]
        if isinstance(_method, Unset):
            method = UNSET
        else:
            method = HttpchkParamsMethod(_method)

        uri = d.pop("uri", UNSET)

        version = d.pop("version", UNSET)

        httpchk_params = cls(
            host=host,
            method=method,
            uri=uri,
            version=version,
        )

        httpchk_params.additional_properties = d
        return httpchk_params

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
