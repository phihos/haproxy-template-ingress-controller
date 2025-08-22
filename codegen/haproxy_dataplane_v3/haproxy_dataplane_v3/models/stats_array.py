from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.stats import Stats


T = TypeVar("T", bound="StatsArray")


@_attrs_define
class StatsArray:
    """HAProxy stats array

    Attributes:
        error (Union[Unset, str]):
        runtime_api (Union[Unset, str]):
        stats (Union[Unset, list['Stats']]):
    """

    error: Union[Unset, str] = UNSET
    runtime_api: Union[Unset, str] = UNSET
    stats: Union[Unset, list["Stats"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        error = self.error

        runtime_api = self.runtime_api

        stats: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.stats, Unset):
            stats = []
            for stats_item_data in self.stats:
                stats_item = stats_item_data.to_dict()
                stats.append(stats_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if error is not UNSET:
            field_dict["error"] = error
        if runtime_api is not UNSET:
            field_dict["runtimeAPI"] = runtime_api
        if stats is not UNSET:
            field_dict["stats"] = stats

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.stats import Stats

        d = dict(src_dict)
        error = d.pop("error", UNSET)

        runtime_api = d.pop("runtimeAPI", UNSET)

        stats = []
        _stats = d.pop("stats", UNSET)
        for stats_item_data in _stats or []:
            stats_item = Stats.from_dict(stats_item_data)

            stats.append(stats_item)

        stats_array = cls(
            error=error,
            runtime_api=runtime_api,
            stats=stats,
        )

        stats_array.additional_properties = d
        return stats_array

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
