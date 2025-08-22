from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.cluster_settings_mode import ClusterSettingsMode
from ..models.cluster_settings_status import ClusterSettingsStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cluster_settings_cluster_controller_information import ClusterSettingsClusterControllerInformation


T = TypeVar("T", bound="ClusterSettings")


@_attrs_define
class ClusterSettings:
    """Settings related to a cluster.

    Attributes:
        bootstrap_key (Union[Unset, str]):
        cluster (Union[Unset, ClusterSettingsClusterControllerInformation]):
        mode (Union[Unset, ClusterSettingsMode]):
        status (Union[Unset, ClusterSettingsStatus]):
    """

    bootstrap_key: Union[Unset, str] = UNSET
    cluster: Union[Unset, "ClusterSettingsClusterControllerInformation"] = UNSET
    mode: Union[Unset, ClusterSettingsMode] = UNSET
    status: Union[Unset, ClusterSettingsStatus] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        bootstrap_key = self.bootstrap_key

        cluster: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.cluster, Unset):
            cluster = self.cluster.to_dict()

        mode: Union[Unset, str] = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        status: Union[Unset, str] = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if bootstrap_key is not UNSET:
            field_dict["bootstrap_key"] = bootstrap_key
        if cluster is not UNSET:
            field_dict["cluster"] = cluster
        if mode is not UNSET:
            field_dict["mode"] = mode
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cluster_settings_cluster_controller_information import ClusterSettingsClusterControllerInformation

        d = dict(src_dict)
        bootstrap_key = d.pop("bootstrap_key", UNSET)

        _cluster = d.pop("cluster", UNSET)
        cluster: Union[Unset, ClusterSettingsClusterControllerInformation]
        if isinstance(_cluster, Unset):
            cluster = UNSET
        else:
            cluster = ClusterSettingsClusterControllerInformation.from_dict(_cluster)

        _mode = d.pop("mode", UNSET)
        mode: Union[Unset, ClusterSettingsMode]
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = ClusterSettingsMode(_mode)

        _status = d.pop("status", UNSET)
        status: Union[Unset, ClusterSettingsStatus]
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = ClusterSettingsStatus(_status)

        cluster_settings = cls(
            bootstrap_key=bootstrap_key,
            cluster=cluster,
            mode=mode,
            status=status,
        )

        cluster_settings.additional_properties = d
        return cluster_settings

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
