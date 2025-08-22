from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.stats_options_stats_admin_cond import StatsOptionsStatsAdminCond
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.stats_auth import StatsAuth
    from ..models.stats_http_request import StatsHttpRequest


T = TypeVar("T", bound="StatsOptions")


@_attrs_define
class StatsOptions:
    """
    Attributes:
        stats_admin (Union[Unset, bool]):
        stats_admin_cond (Union[Unset, StatsOptionsStatsAdminCond]):
        stats_admin_cond_test (Union[Unset, str]):
        stats_auths (Union[Unset, list['StatsAuth']]):
        stats_enable (Union[Unset, bool]):
        stats_hide_version (Union[Unset, bool]):
        stats_http_requests (Union[Unset, list['StatsHttpRequest']]):
        stats_maxconn (Union[Unset, int]):
        stats_realm (Union[Unset, bool]):
        stats_realm_realm (Union[None, Unset, str]):
        stats_refresh_delay (Union[None, Unset, int]):
        stats_show_desc (Union[None, Unset, str]):
        stats_show_legends (Union[Unset, bool]):
        stats_show_modules (Union[Unset, bool]):
        stats_show_node_name (Union[None, Unset, str]):
        stats_uri_prefix (Union[Unset, str]):
    """

    stats_admin: Union[Unset, bool] = UNSET
    stats_admin_cond: Union[Unset, StatsOptionsStatsAdminCond] = UNSET
    stats_admin_cond_test: Union[Unset, str] = UNSET
    stats_auths: Union[Unset, list["StatsAuth"]] = UNSET
    stats_enable: Union[Unset, bool] = UNSET
    stats_hide_version: Union[Unset, bool] = UNSET
    stats_http_requests: Union[Unset, list["StatsHttpRequest"]] = UNSET
    stats_maxconn: Union[Unset, int] = UNSET
    stats_realm: Union[Unset, bool] = UNSET
    stats_realm_realm: Union[None, Unset, str] = UNSET
    stats_refresh_delay: Union[None, Unset, int] = UNSET
    stats_show_desc: Union[None, Unset, str] = UNSET
    stats_show_legends: Union[Unset, bool] = UNSET
    stats_show_modules: Union[Unset, bool] = UNSET
    stats_show_node_name: Union[None, Unset, str] = UNSET
    stats_uri_prefix: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        stats_admin = self.stats_admin

        stats_admin_cond: Union[Unset, str] = UNSET
        if not isinstance(self.stats_admin_cond, Unset):
            stats_admin_cond = self.stats_admin_cond.value

        stats_admin_cond_test = self.stats_admin_cond_test

        stats_auths: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.stats_auths, Unset):
            stats_auths = []
            for stats_auths_item_data in self.stats_auths:
                stats_auths_item = stats_auths_item_data.to_dict()
                stats_auths.append(stats_auths_item)

        stats_enable = self.stats_enable

        stats_hide_version = self.stats_hide_version

        stats_http_requests: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.stats_http_requests, Unset):
            stats_http_requests = []
            for stats_http_requests_item_data in self.stats_http_requests:
                stats_http_requests_item = stats_http_requests_item_data.to_dict()
                stats_http_requests.append(stats_http_requests_item)

        stats_maxconn = self.stats_maxconn

        stats_realm = self.stats_realm

        stats_realm_realm: Union[None, Unset, str]
        if isinstance(self.stats_realm_realm, Unset):
            stats_realm_realm = UNSET
        else:
            stats_realm_realm = self.stats_realm_realm

        stats_refresh_delay: Union[None, Unset, int]
        if isinstance(self.stats_refresh_delay, Unset):
            stats_refresh_delay = UNSET
        else:
            stats_refresh_delay = self.stats_refresh_delay

        stats_show_desc: Union[None, Unset, str]
        if isinstance(self.stats_show_desc, Unset):
            stats_show_desc = UNSET
        else:
            stats_show_desc = self.stats_show_desc

        stats_show_legends = self.stats_show_legends

        stats_show_modules = self.stats_show_modules

        stats_show_node_name: Union[None, Unset, str]
        if isinstance(self.stats_show_node_name, Unset):
            stats_show_node_name = UNSET
        else:
            stats_show_node_name = self.stats_show_node_name

        stats_uri_prefix = self.stats_uri_prefix

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if stats_admin is not UNSET:
            field_dict["stats_admin"] = stats_admin
        if stats_admin_cond is not UNSET:
            field_dict["stats_admin_cond"] = stats_admin_cond
        if stats_admin_cond_test is not UNSET:
            field_dict["stats_admin_cond_test"] = stats_admin_cond_test
        if stats_auths is not UNSET:
            field_dict["stats_auths"] = stats_auths
        if stats_enable is not UNSET:
            field_dict["stats_enable"] = stats_enable
        if stats_hide_version is not UNSET:
            field_dict["stats_hide_version"] = stats_hide_version
        if stats_http_requests is not UNSET:
            field_dict["stats_http_requests"] = stats_http_requests
        if stats_maxconn is not UNSET:
            field_dict["stats_maxconn"] = stats_maxconn
        if stats_realm is not UNSET:
            field_dict["stats_realm"] = stats_realm
        if stats_realm_realm is not UNSET:
            field_dict["stats_realm_realm"] = stats_realm_realm
        if stats_refresh_delay is not UNSET:
            field_dict["stats_refresh_delay"] = stats_refresh_delay
        if stats_show_desc is not UNSET:
            field_dict["stats_show_desc"] = stats_show_desc
        if stats_show_legends is not UNSET:
            field_dict["stats_show_legends"] = stats_show_legends
        if stats_show_modules is not UNSET:
            field_dict["stats_show_modules"] = stats_show_modules
        if stats_show_node_name is not UNSET:
            field_dict["stats_show_node_name"] = stats_show_node_name
        if stats_uri_prefix is not UNSET:
            field_dict["stats_uri_prefix"] = stats_uri_prefix

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.stats_auth import StatsAuth
        from ..models.stats_http_request import StatsHttpRequest

        d = dict(src_dict)
        stats_admin = d.pop("stats_admin", UNSET)

        _stats_admin_cond = d.pop("stats_admin_cond", UNSET)
        stats_admin_cond: Union[Unset, StatsOptionsStatsAdminCond]
        if isinstance(_stats_admin_cond, Unset):
            stats_admin_cond = UNSET
        else:
            stats_admin_cond = StatsOptionsStatsAdminCond(_stats_admin_cond)

        stats_admin_cond_test = d.pop("stats_admin_cond_test", UNSET)

        stats_auths = []
        _stats_auths = d.pop("stats_auths", UNSET)
        for stats_auths_item_data in _stats_auths or []:
            stats_auths_item = StatsAuth.from_dict(stats_auths_item_data)

            stats_auths.append(stats_auths_item)

        stats_enable = d.pop("stats_enable", UNSET)

        stats_hide_version = d.pop("stats_hide_version", UNSET)

        stats_http_requests = []
        _stats_http_requests = d.pop("stats_http_requests", UNSET)
        for stats_http_requests_item_data in _stats_http_requests or []:
            stats_http_requests_item = StatsHttpRequest.from_dict(stats_http_requests_item_data)

            stats_http_requests.append(stats_http_requests_item)

        stats_maxconn = d.pop("stats_maxconn", UNSET)

        stats_realm = d.pop("stats_realm", UNSET)

        def _parse_stats_realm_realm(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        stats_realm_realm = _parse_stats_realm_realm(d.pop("stats_realm_realm", UNSET))

        def _parse_stats_refresh_delay(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        stats_refresh_delay = _parse_stats_refresh_delay(d.pop("stats_refresh_delay", UNSET))

        def _parse_stats_show_desc(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        stats_show_desc = _parse_stats_show_desc(d.pop("stats_show_desc", UNSET))

        stats_show_legends = d.pop("stats_show_legends", UNSET)

        stats_show_modules = d.pop("stats_show_modules", UNSET)

        def _parse_stats_show_node_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        stats_show_node_name = _parse_stats_show_node_name(d.pop("stats_show_node_name", UNSET))

        stats_uri_prefix = d.pop("stats_uri_prefix", UNSET)

        stats_options = cls(
            stats_admin=stats_admin,
            stats_admin_cond=stats_admin_cond,
            stats_admin_cond_test=stats_admin_cond_test,
            stats_auths=stats_auths,
            stats_enable=stats_enable,
            stats_hide_version=stats_hide_version,
            stats_http_requests=stats_http_requests,
            stats_maxconn=stats_maxconn,
            stats_realm=stats_realm,
            stats_realm_realm=stats_realm_realm,
            stats_refresh_delay=stats_refresh_delay,
            stats_show_desc=stats_show_desc,
            stats_show_legends=stats_show_legends,
            stats_show_modules=stats_show_modules,
            stats_show_node_name=stats_show_node_name,
            stats_uri_prefix=stats_uri_prefix,
        )

        stats_options.additional_properties = d
        return stats_options

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
