from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.stick_table_entry import StickTableEntry


T = TypeVar("T", bound="SetStickTableEntriesBody")


@_attrs_define
class SetStickTableEntriesBody:
    """
    Attributes:
        data_type (StickTableEntry): One entry in stick table
        key (str):
    """

    data_type: "StickTableEntry"
    key: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data_type = self.data_type.to_dict()

        key = self.key

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data_type": data_type,
                "key": key,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.stick_table_entry import StickTableEntry

        d = dict(src_dict)
        data_type = StickTableEntry.from_dict(d.pop("data_type"))

        key = d.pop("key")

        set_stick_table_entries_body = cls(
            data_type=data_type,
            key=key,
        )

        set_stick_table_entries_body.additional_properties = d
        return set_stick_table_entries_body

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
