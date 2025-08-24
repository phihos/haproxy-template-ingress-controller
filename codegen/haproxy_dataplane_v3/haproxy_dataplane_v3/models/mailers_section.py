from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="MailersSection")


@_attrs_define
class MailersSection:
    """MailersSection with all it's children resources

    Attributes:
        name (str):
        metadata (Union[Unset, Any]):
        timeout (Union[None, Unset, int]):
        mailer_entries (Union[Unset, Any]):
    """

    name: str
    metadata: Union[Unset, Any] = UNSET
    timeout: Union[None, Unset, int] = UNSET
    mailer_entries: Union[Unset, Any] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        metadata = self.metadata

        timeout: Union[None, Unset, int]
        if isinstance(self.timeout, Unset):
            timeout = UNSET
        else:
            timeout = self.timeout

        mailer_entries = self.mailer_entries

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if timeout is not UNSET:
            field_dict["timeout"] = timeout
        if mailer_entries is not UNSET:
            field_dict["mailer_entries"] = mailer_entries

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        metadata = d.pop("metadata", UNSET)

        def _parse_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        timeout = _parse_timeout(d.pop("timeout", UNSET))

        mailer_entries = d.pop("mailer_entries", UNSET)

        mailers_section = cls(
            name=name,
            metadata=metadata,
            timeout=timeout,
            mailer_entries=mailer_entries,
        )

        mailers_section.additional_properties = d
        return mailers_section

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
