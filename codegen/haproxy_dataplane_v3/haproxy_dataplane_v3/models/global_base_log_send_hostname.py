from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.global_base_log_send_hostname_enabled import GlobalBaseLogSendHostnameEnabled
from ..types import UNSET, Unset

T = TypeVar("T", bound="GlobalBaseLogSendHostname")


@_attrs_define
class GlobalBaseLogSendHostname:
    """
    Attributes:
        enabled (GlobalBaseLogSendHostnameEnabled):
        param (Union[Unset, str]):
    """

    enabled: GlobalBaseLogSendHostnameEnabled
    param: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        enabled = self.enabled.value

        param = self.param

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "enabled": enabled,
            }
        )
        if param is not UNSET:
            field_dict["param"] = param

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        enabled = GlobalBaseLogSendHostnameEnabled(d.pop("enabled"))

        param = d.pop("param", UNSET)

        global_base_log_send_hostname = cls(
            enabled=enabled,
            param=param,
        )

        global_base_log_send_hostname.additional_properties = d
        return global_base_log_send_hostname

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
