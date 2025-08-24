from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="User")


@_attrs_define
class User:
    """HAProxy userlist user

    Attributes:
        password (str):
        secure_password (bool):
        username (str):
        groups (Union[Unset, str]):
        metadata (Union[Unset, Any]):
    """

    password: str
    secure_password: bool
    username: str
    groups: Union[Unset, str] = UNSET
    metadata: Union[Unset, Any] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        password = self.password

        secure_password = self.secure_password

        username = self.username

        groups = self.groups

        metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "password": password,
                "secure_password": secure_password,
                "username": username,
            }
        )
        if groups is not UNSET:
            field_dict["groups"] = groups
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        password = d.pop("password")

        secure_password = d.pop("secure_password")

        username = d.pop("username")

        groups = d.pop("groups", UNSET)

        metadata = d.pop("metadata", UNSET)

        user = cls(
            password=password,
            secure_password=secure_password,
            username=username,
            groups=groups,
            metadata=metadata,
        )

        user.additional_properties = d
        return user

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
