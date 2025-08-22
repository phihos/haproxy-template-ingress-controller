from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.cluster_settings_cluster_controller_information_log_targets_item_protocol import (
    ClusterSettingsClusterControllerInformationLogTargetsItemProtocol,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="ClusterSettingsClusterControllerInformationLogTargetsItem")


@_attrs_define
class ClusterSettingsClusterControllerInformationLogTargetsItem:
    """
    Attributes:
        address (str):
        port (int):
        protocol (ClusterSettingsClusterControllerInformationLogTargetsItemProtocol):
        log_format (Union[Unset, str]):
    """

    address: str
    port: int
    protocol: ClusterSettingsClusterControllerInformationLogTargetsItemProtocol
    log_format: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        address = self.address

        port = self.port

        protocol = self.protocol.value

        log_format = self.log_format

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "address": address,
                "port": port,
                "protocol": protocol,
            }
        )
        if log_format is not UNSET:
            field_dict["log_format"] = log_format

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        address = d.pop("address")

        port = d.pop("port")

        protocol = ClusterSettingsClusterControllerInformationLogTargetsItemProtocol(d.pop("protocol"))

        log_format = d.pop("log_format", UNSET)

        cluster_settings_cluster_controller_information_log_targets_item = cls(
            address=address,
            port=port,
            protocol=protocol,
            log_format=log_format,
        )

        cluster_settings_cluster_controller_information_log_targets_item.additional_properties = d
        return cluster_settings_cluster_controller_information_log_targets_item

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
