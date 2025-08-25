from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..models.filter_type import FilterType
from ..types import UNSET, Unset

T = TypeVar("T", bound="Filter")


@_attrs_define
class Filter:
    """HAProxy filters

    Example:
        {'trace_name': 'name', 'trace_rnd_parsing': True, 'type': 'trace'}

    Attributes:
        type_ (FilterType):
        app_name (Union[Unset, str]): Name of the fcgi-app section this filter will use.
        bandwidth_limit_name (Union[Unset, str]): Filter name that will be used by 'set-bandwidth-limit' actions to
            reference a specific bandwidth limitation filter
        cache_name (Union[Unset, str]):
        default_limit (Union[Unset, int]): The max number of bytes that can be forwarded over the period.
            The value must be specified for per-stream and shared bandwidth limitation filters.
            It follows the HAProxy size format and is expressed in bytes.
        default_period (Union[Unset, int]): The default time period used to evaluate the bandwidth limitation rate.
            It can be specified for per-stream bandwidth limitation filters only.
            It follows the HAProxy time format and is expressed in milliseconds.
        key (Union[Unset, str]): A sample expression rule.
            It describes what elements will be analyzed, extracted, combined, and used to select which table entry to update
            the counters.
            It must be specified for shared bandwidth limitation filters only.
        limit (Union[Unset, int]): The max number of bytes that can be forwarded over the period.
            The value must be specified for per-stream and shared bandwidth limitation filters.
            It follows the HAProxy size format and is expressed in bytes.
        metadata (Union[Unset, Any]):
        min_size (Union[Unset, int]): The optional minimum number of bytes forwarded at a time by a stream excluding the
            last packet that may be smaller.
            This value can be specified for per-stream and shared bandwidth limitation filters.
            It follows the HAProxy size format and is expressed in bytes.
        spoe_config (Union[Unset, str]):
        spoe_engine (Union[Unset, str]):
        table (Union[Unset, str]): An optional table to be used instead of the default one, which is the stick-table
            declared in the current proxy.
            It can be specified for shared bandwidth limitation filters only.
        trace_hexdump (Union[Unset, bool]):
        trace_name (Union[Unset, str]):
        trace_rnd_forwarding (Union[Unset, bool]):
        trace_rnd_parsing (Union[Unset, bool]):
    """

    type_: FilterType
    app_name: Union[Unset, str] = UNSET
    bandwidth_limit_name: Union[Unset, str] = UNSET
    cache_name: Union[Unset, str] = UNSET
    default_limit: Union[Unset, int] = UNSET
    default_period: Union[Unset, int] = UNSET
    key: Union[Unset, str] = UNSET
    limit: Union[Unset, int] = UNSET
    metadata: Union[Unset, Any] = UNSET
    min_size: Union[Unset, int] = UNSET
    spoe_config: Union[Unset, str] = UNSET
    spoe_engine: Union[Unset, str] = UNSET
    table: Union[Unset, str] = UNSET
    trace_hexdump: Union[Unset, bool] = UNSET
    trace_name: Union[Unset, str] = UNSET
    trace_rnd_forwarding: Union[Unset, bool] = UNSET
    trace_rnd_parsing: Union[Unset, bool] = UNSET

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        app_name = self.app_name

        bandwidth_limit_name = self.bandwidth_limit_name

        cache_name = self.cache_name

        default_limit = self.default_limit

        default_period = self.default_period

        key = self.key

        limit = self.limit

        metadata = self.metadata

        min_size = self.min_size

        spoe_config = self.spoe_config

        spoe_engine = self.spoe_engine

        table = self.table

        trace_hexdump = self.trace_hexdump

        trace_name = self.trace_name

        trace_rnd_forwarding = self.trace_rnd_forwarding

        trace_rnd_parsing = self.trace_rnd_parsing

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "type": type_,
            }
        )
        if app_name is not UNSET:
            field_dict["app_name"] = app_name
        if bandwidth_limit_name is not UNSET:
            field_dict["bandwidth_limit_name"] = bandwidth_limit_name
        if cache_name is not UNSET:
            field_dict["cache_name"] = cache_name
        if default_limit is not UNSET:
            field_dict["default_limit"] = default_limit
        if default_period is not UNSET:
            field_dict["default_period"] = default_period
        if key is not UNSET:
            field_dict["key"] = key
        if limit is not UNSET:
            field_dict["limit"] = limit
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if min_size is not UNSET:
            field_dict["min_size"] = min_size
        if spoe_config is not UNSET:
            field_dict["spoe_config"] = spoe_config
        if spoe_engine is not UNSET:
            field_dict["spoe_engine"] = spoe_engine
        if table is not UNSET:
            field_dict["table"] = table
        if trace_hexdump is not UNSET:
            field_dict["trace_hexdump"] = trace_hexdump
        if trace_name is not UNSET:
            field_dict["trace_name"] = trace_name
        if trace_rnd_forwarding is not UNSET:
            field_dict["trace_rnd_forwarding"] = trace_rnd_forwarding
        if trace_rnd_parsing is not UNSET:
            field_dict["trace_rnd_parsing"] = trace_rnd_parsing

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = FilterType(d.pop("type"))

        app_name = d.pop("app_name", UNSET)

        bandwidth_limit_name = d.pop("bandwidth_limit_name", UNSET)

        cache_name = d.pop("cache_name", UNSET)

        default_limit = d.pop("default_limit", UNSET)

        default_period = d.pop("default_period", UNSET)

        key = d.pop("key", UNSET)

        limit = d.pop("limit", UNSET)

        metadata = d.pop("metadata", UNSET)

        min_size = d.pop("min_size", UNSET)

        spoe_config = d.pop("spoe_config", UNSET)

        spoe_engine = d.pop("spoe_engine", UNSET)

        table = d.pop("table", UNSET)

        trace_hexdump = d.pop("trace_hexdump", UNSET)

        trace_name = d.pop("trace_name", UNSET)

        trace_rnd_forwarding = d.pop("trace_rnd_forwarding", UNSET)

        trace_rnd_parsing = d.pop("trace_rnd_parsing", UNSET)

        filter_ = cls(
            type_=type_,
            app_name=app_name,
            bandwidth_limit_name=bandwidth_limit_name,
            cache_name=cache_name,
            default_limit=default_limit,
            default_period=default_period,
            key=key,
            limit=limit,
            metadata=metadata,
            min_size=min_size,
            spoe_config=spoe_config,
            spoe_engine=spoe_engine,
            table=table,
            trace_hexdump=trace_hexdump,
            trace_name=trace_name,
            trace_rnd_forwarding=trace_rnd_forwarding,
            trace_rnd_parsing=trace_rnd_parsing,
        )

        return filter_
