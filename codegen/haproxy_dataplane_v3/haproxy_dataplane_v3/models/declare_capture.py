from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.declare_capture_type import DeclareCaptureType
from ..types import UNSET, Unset

T = TypeVar("T", bound="DeclareCapture")


@_attrs_define
class DeclareCapture:
    """
    Attributes:
        length (int):
        type_ (DeclareCaptureType):
        metadata (Union[Unset, Any]):
    """

    length: int
    type_: DeclareCaptureType
    metadata: Union[Unset, Any] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        length = self.length

        type_ = self.type_.value

        metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "length": length,
                "type": type_,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        length = d.pop("length")

        type_ = DeclareCaptureType(d.pop("type"))

        metadata = d.pop("metadata", UNSET)

        declare_capture = cls(
            length=length,
            type_=type_,
            metadata=metadata,
        )

        declare_capture.additional_properties = d
        return declare_capture

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
