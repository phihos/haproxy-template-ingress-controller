from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.ha_proxy_reload_status import HAProxyReloadStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="HAProxyReload")


@_attrs_define
class HAProxyReload:
    """HAProxy reload

    Example:
        {'id': '2019-01-03-44', 'status': 'in_progress'}

    Attributes:
        id (Union[Unset, str]):
        reload_timestamp (Union[Unset, int]):
        response (Union[Unset, str]):
        status (Union[Unset, HAProxyReloadStatus]):
    """

    id: Union[Unset, str] = UNSET
    reload_timestamp: Union[Unset, int] = UNSET
    response: Union[Unset, str] = UNSET
    status: Union[Unset, HAProxyReloadStatus] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        reload_timestamp = self.reload_timestamp

        response = self.response

        status: Union[Unset, str] = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if reload_timestamp is not UNSET:
            field_dict["reload_timestamp"] = reload_timestamp
        if response is not UNSET:
            field_dict["response"] = response
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        reload_timestamp = d.pop("reload_timestamp", UNSET)

        response = d.pop("response", UNSET)

        _status = d.pop("status", UNSET)
        status: Union[Unset, HAProxyReloadStatus]
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = HAProxyReloadStatus(_status)

        ha_proxy_reload = cls(
            id=id,
            reload_timestamp=reload_timestamp,
            response=response,
            status=status,
        )

        ha_proxy_reload.additional_properties = d
        return ha_proxy_reload

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
