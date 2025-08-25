from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="MailersSectionBase")


@_attrs_define
class MailersSectionBase:
    """A list of SMTP servers used by HAProxy to send emails.

    Attributes:
        name (str):
        metadata (Union[Unset, Any]):
        timeout (Union[None, Unset, int]):
    """

    name: str
    metadata: Union[Unset, Any] = UNSET
    timeout: Union[None, Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        metadata = self.metadata

        timeout: Union[None, Unset, int]
        if isinstance(self.timeout, Unset):
            timeout = UNSET
        else:
            timeout = self.timeout

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if timeout is not UNSET:
            field_dict["timeout"] = timeout

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

        mailers_section_base = cls(
            name=name,
            metadata=metadata,
            timeout=timeout,
        )

        return mailers_section_base
