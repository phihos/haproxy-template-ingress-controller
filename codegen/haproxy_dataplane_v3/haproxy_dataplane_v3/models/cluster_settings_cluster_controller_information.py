from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cluster_settings_cluster_controller_information_log_targets_item import (
        ClusterSettingsClusterControllerInformationLogTargetsItem,
    )


T = TypeVar("T", bound="ClusterSettingsClusterControllerInformation")


@_attrs_define
class ClusterSettingsClusterControllerInformation:
    """
    Attributes:
        address (Union[Unset, str]):
        api_base_path (Union[Unset, str]):
        cluster_id (Union[Unset, str]):
        description (Union[Unset, str]):
        log_targets (Union[Unset, list['ClusterSettingsClusterControllerInformationLogTargetsItem']]):
        name (Union[Unset, str]):
        port (Union[None, Unset, int]):
    """

    address: Union[Unset, str] = UNSET
    api_base_path: Union[Unset, str] = UNSET
    cluster_id: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    log_targets: Union[Unset, list["ClusterSettingsClusterControllerInformationLogTargetsItem"]] = UNSET
    name: Union[Unset, str] = UNSET
    port: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        address = self.address

        api_base_path = self.api_base_path

        cluster_id = self.cluster_id

        description = self.description

        log_targets: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.log_targets, Unset):
            log_targets = []
            for log_targets_item_data in self.log_targets:
                log_targets_item = log_targets_item_data.to_dict()
                log_targets.append(log_targets_item)

        name = self.name

        port: Union[None, Unset, int]
        if isinstance(self.port, Unset):
            port = UNSET
        else:
            port = self.port

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if address is not UNSET:
            field_dict["address"] = address
        if api_base_path is not UNSET:
            field_dict["api_base_path"] = api_base_path
        if cluster_id is not UNSET:
            field_dict["cluster_id"] = cluster_id
        if description is not UNSET:
            field_dict["description"] = description
        if log_targets is not UNSET:
            field_dict["log_targets"] = log_targets
        if name is not UNSET:
            field_dict["name"] = name
        if port is not UNSET:
            field_dict["port"] = port

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cluster_settings_cluster_controller_information_log_targets_item import (
            ClusterSettingsClusterControllerInformationLogTargetsItem,
        )

        d = dict(src_dict)
        address = d.pop("address", UNSET)

        api_base_path = d.pop("api_base_path", UNSET)

        cluster_id = d.pop("cluster_id", UNSET)

        description = d.pop("description", UNSET)

        _log_targets = d.pop("log_targets", UNSET)
        log_targets: Union[Unset, list[ClusterSettingsClusterControllerInformationLogTargetsItem]] = UNSET
        if not isinstance(_log_targets, Unset):
            log_targets = []
            for log_targets_item_data in _log_targets:
                log_targets_item = ClusterSettingsClusterControllerInformationLogTargetsItem.from_dict(
                    log_targets_item_data
                )

                log_targets.append(log_targets_item)

        name = d.pop("name", UNSET)

        def _parse_port(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        port = _parse_port(d.pop("port", UNSET))

        cluster_settings_cluster_controller_information = cls(
            address=address,
            api_base_path=api_base_path,
            cluster_id=cluster_id,
            description=description,
            log_targets=log_targets,
            name=name,
            port=port,
        )

        cluster_settings_cluster_controller_information.additional_properties = d
        return cluster_settings_cluster_controller_information

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
