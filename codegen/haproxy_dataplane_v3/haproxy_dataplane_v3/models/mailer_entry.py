from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="MailerEntry")


@_attrs_define
class MailerEntry:
    """Mailer entry of a Mailers section

    Attributes:
        address (str):
        name (str):
        port (int):
        metadata (Union[Unset, Any]):
    """

    address: str
    name: str
    port: int
    metadata: Union[Unset, Any] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        address = self.address

        name = self.name

        port = self.port

        metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "address": address,
                "name": name,
                "port": port,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        address = d.pop("address")

        name = d.pop("name")

        port = d.pop("port")

        metadata = d.pop("metadata", UNSET)

        mailer_entry = cls(
            address=address,
            name=name,
            port=port,
            metadata=metadata,
        )

        mailer_entry.additional_properties = d
        return mailer_entry

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
