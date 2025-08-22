from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.mysql_check_params_client_version import MysqlCheckParamsClientVersion
from ..types import UNSET, Unset

T = TypeVar("T", bound="MysqlCheckParams")


@_attrs_define
class MysqlCheckParams:
    """
    Attributes:
        client_version (Union[Unset, MysqlCheckParamsClientVersion]):
        username (Union[Unset, str]):
    """

    client_version: Union[Unset, MysqlCheckParamsClientVersion] = UNSET
    username: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        client_version: Union[Unset, str] = UNSET
        if not isinstance(self.client_version, Unset):
            client_version = self.client_version.value

        username = self.username

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if client_version is not UNSET:
            field_dict["client_version"] = client_version
        if username is not UNSET:
            field_dict["username"] = username

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _client_version = d.pop("client_version", UNSET)
        client_version: Union[Unset, MysqlCheckParamsClientVersion]
        if isinstance(_client_version, Unset):
            client_version = UNSET
        else:
            client_version = MysqlCheckParamsClientVersion(_client_version)

        username = d.pop("username", UNSET)

        mysql_check_params = cls(
            client_version=client_version,
            username=username,
        )

        mysql_check_params.additional_properties = d
        return mysql_check_params

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
