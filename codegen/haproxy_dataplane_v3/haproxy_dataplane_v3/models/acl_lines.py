from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ACLLines")


@_attrs_define
class ACLLines:
    """The use of Access Control Lists (ACL) provides a flexible solution to perform
    content switching and generally to take decisions based on content extracted
    from the request, the response or any environmental status.

        Attributes:
            acl_name (str):
            criterion (str):
            metadata (Union[Unset, Any]):
            value (Union[Unset, str]):
    """

    acl_name: str
    criterion: str
    metadata: Union[Unset, Any] = UNSET
    value: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        acl_name = self.acl_name

        criterion = self.criterion

        metadata = self.metadata

        value = self.value

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "acl_name": acl_name,
                "criterion": criterion,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if value is not UNSET:
            field_dict["value"] = value

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        acl_name = d.pop("acl_name")

        criterion = d.pop("criterion")

        metadata = d.pop("metadata", UNSET)

        value = d.pop("value", UNSET)

        acl_lines = cls(
            acl_name=acl_name,
            criterion=criterion,
            metadata=metadata,
            value=value,
        )

        return acl_lines
