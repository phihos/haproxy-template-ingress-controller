from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.stats_type import StatsType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.native_stat_stats import NativeStatStats


T = TypeVar("T", bound="Stats")


@_attrs_define
class Stats:
    """Current stats for one object.

    Attributes:
        backend_name (Union[Unset, str]):
        name (Union[Unset, str]):
        stats (Union[Unset, NativeStatStats]):  Example: {'bin': 4326578, 'bout': 889901290, 'comp_byp': 0, 'comp_in':
            0, 'comp_out': 0, 'comp_rsp': 0, 'conn_rate': 12, 'conn_rate_max': 456, 'conn_tot': 45682, 'dcon': 0, 'dreq': 4,
            'dresp': 1, 'dses': 0, 'ereq': 54, 'hrsp_1xx': 0, 'hrsp_2xx': 165, 'hrsp_3xx': 12, 'hrsp_4xx': 50, 'hrsp_5xx':
            4, 'hrsp_other': 0, 'iid': 0, 'intercepted': 346, 'last_chk': 'L4OK in 0ms', 'mode': 'http', 'pid': 3204,
            'rate': 64, 'rate_lim': 20000, 'rate_max': 4000, 'req_rate': 49, 'req_rate_max': 3965, 'req_total': 1254786,
            'scur': 129, 'slim': 2000, 'smax': 2000, 'status': 'UP', 'stot': 12902}.
        type_ (Union[Unset, StatsType]):
    """

    backend_name: Union[Unset, str] = UNSET
    name: Union[Unset, str] = UNSET
    stats: Union[Unset, "NativeStatStats"] = UNSET
    type_: Union[Unset, StatsType] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        backend_name = self.backend_name

        name = self.name

        stats: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.stats, Unset):
            stats = self.stats.to_dict()

        type_: Union[Unset, str] = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if backend_name is not UNSET:
            field_dict["backend_name"] = backend_name
        if name is not UNSET:
            field_dict["name"] = name
        if stats is not UNSET:
            field_dict["stats"] = stats
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.native_stat_stats import NativeStatStats

        d = dict(src_dict)
        backend_name = d.pop("backend_name", UNSET)

        name = d.pop("name", UNSET)

        _stats = d.pop("stats", UNSET)
        stats: Union[Unset, NativeStatStats]
        if isinstance(_stats, Unset):
            stats = UNSET
        else:
            stats = NativeStatStats.from_dict(_stats)

        _type_ = d.pop("type", UNSET)
        type_: Union[Unset, StatsType]
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = StatsType(_type_)

        stats = cls(
            backend_name=backend_name,
            name=name,
            stats=stats,
            type_=type_,
        )

        stats.additional_properties = d
        return stats

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
