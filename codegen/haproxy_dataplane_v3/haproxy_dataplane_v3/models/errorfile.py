from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.errorfile_code import ErrorfileCode
from ..types import UNSET, Unset

T = TypeVar("T", bound="Errorfile")


@_attrs_define
class Errorfile:
    """
    Attributes:
        code (Union[Unset, ErrorfileCode]):
        file (Union[Unset, str]):
    """

    code: Union[Unset, ErrorfileCode] = UNSET
    file: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        code: Union[Unset, int] = UNSET
        if not isinstance(self.code, Unset):
            code = self.code.value

        file = self.file

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if code is not UNSET:
            field_dict["code"] = code
        if file is not UNSET:
            field_dict["file"] = file

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _code = d.pop("code", UNSET)
        code: Union[Unset, ErrorfileCode]
        if isinstance(_code, Unset):
            code = UNSET
        else:
            code = ErrorfileCode(_code)

        file = d.pop("file", UNSET)

        errorfile = cls(
            code=code,
            file=file,
        )

        errorfile.additional_properties = d
        return errorfile

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
