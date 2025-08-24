from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.process_info_item import ProcessInfoItem


T = TypeVar("T", bound="HAProxyInformation")


@_attrs_define
class HAProxyInformation:
    """General HAProxy process information

    Attributes:
        error (Union[Unset, str]):
        info (Union[Unset, ProcessInfoItem]):
        runtime_api (Union[Unset, str]):
    """

    error: Union[Unset, str] = UNSET
    info: Union[Unset, "ProcessInfoItem"] = UNSET
    runtime_api: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        error = self.error

        info: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.info, Unset):
            info = self.info.to_dict()

        runtime_api = self.runtime_api

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if error is not UNSET:
            field_dict["error"] = error
        if info is not UNSET:
            field_dict["info"] = info
        if runtime_api is not UNSET:
            field_dict["runtimeAPI"] = runtime_api

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.process_info_item import ProcessInfoItem

        d = dict(src_dict)
        error = d.pop("error", UNSET)

        _info = d.pop("info", UNSET)
        info: Union[Unset, ProcessInfoItem]
        if isinstance(_info, Unset):
            info = UNSET
        else:
            info = ProcessInfoItem.from_dict(_info)

        runtime_api = d.pop("runtimeAPI", UNSET)

        ha_proxy_information = cls(
            error=error,
            info=info,
            runtime_api=runtime_api,
        )

        ha_proxy_information.additional_properties = d
        return ha_proxy_information

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
