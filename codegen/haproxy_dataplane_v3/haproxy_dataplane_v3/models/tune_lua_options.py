from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.tune_lua_options_bool_sample_conversion import TuneLuaOptionsBoolSampleConversion
from ..models.tune_lua_options_log_loggers import TuneLuaOptionsLogLoggers
from ..models.tune_lua_options_log_stderr import TuneLuaOptionsLogStderr
from ..types import UNSET, Unset

T = TypeVar("T", bound="TuneLuaOptions")


@_attrs_define
class TuneLuaOptions:
    """
    Attributes:
        bool_sample_conversion (Union[Unset, TuneLuaOptionsBoolSampleConversion]):
        burst_timeout (Union[None, Unset, int]):
        forced_yield (Union[Unset, int]):
        log_loggers (Union[Unset, TuneLuaOptionsLogLoggers]):
        log_stderr (Union[Unset, TuneLuaOptionsLogStderr]):
        maxmem (Union[None, Unset, int]):
        service_timeout (Union[None, Unset, int]):
        session_timeout (Union[None, Unset, int]):
        task_timeout (Union[None, Unset, int]):
    """

    bool_sample_conversion: Union[Unset, TuneLuaOptionsBoolSampleConversion] = UNSET
    burst_timeout: Union[None, Unset, int] = UNSET
    forced_yield: Union[Unset, int] = UNSET
    log_loggers: Union[Unset, TuneLuaOptionsLogLoggers] = UNSET
    log_stderr: Union[Unset, TuneLuaOptionsLogStderr] = UNSET
    maxmem: Union[None, Unset, int] = UNSET
    service_timeout: Union[None, Unset, int] = UNSET
    session_timeout: Union[None, Unset, int] = UNSET
    task_timeout: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        bool_sample_conversion: Union[Unset, str] = UNSET
        if not isinstance(self.bool_sample_conversion, Unset):
            bool_sample_conversion = self.bool_sample_conversion.value

        burst_timeout: Union[None, Unset, int]
        if isinstance(self.burst_timeout, Unset):
            burst_timeout = UNSET
        else:
            burst_timeout = self.burst_timeout

        forced_yield = self.forced_yield

        log_loggers: Union[Unset, str] = UNSET
        if not isinstance(self.log_loggers, Unset):
            log_loggers = self.log_loggers.value

        log_stderr: Union[Unset, str] = UNSET
        if not isinstance(self.log_stderr, Unset):
            log_stderr = self.log_stderr.value

        maxmem: Union[None, Unset, int]
        if isinstance(self.maxmem, Unset):
            maxmem = UNSET
        else:
            maxmem = self.maxmem

        service_timeout: Union[None, Unset, int]
        if isinstance(self.service_timeout, Unset):
            service_timeout = UNSET
        else:
            service_timeout = self.service_timeout

        session_timeout: Union[None, Unset, int]
        if isinstance(self.session_timeout, Unset):
            session_timeout = UNSET
        else:
            session_timeout = self.session_timeout

        task_timeout: Union[None, Unset, int]
        if isinstance(self.task_timeout, Unset):
            task_timeout = UNSET
        else:
            task_timeout = self.task_timeout

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if bool_sample_conversion is not UNSET:
            field_dict["bool_sample_conversion"] = bool_sample_conversion
        if burst_timeout is not UNSET:
            field_dict["burst_timeout"] = burst_timeout
        if forced_yield is not UNSET:
            field_dict["forced_yield"] = forced_yield
        if log_loggers is not UNSET:
            field_dict["log_loggers"] = log_loggers
        if log_stderr is not UNSET:
            field_dict["log_stderr"] = log_stderr
        if maxmem is not UNSET:
            field_dict["maxmem"] = maxmem
        if service_timeout is not UNSET:
            field_dict["service_timeout"] = service_timeout
        if session_timeout is not UNSET:
            field_dict["session_timeout"] = session_timeout
        if task_timeout is not UNSET:
            field_dict["task_timeout"] = task_timeout

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _bool_sample_conversion = d.pop("bool_sample_conversion", UNSET)
        bool_sample_conversion: Union[Unset, TuneLuaOptionsBoolSampleConversion]
        if isinstance(_bool_sample_conversion, Unset):
            bool_sample_conversion = UNSET
        else:
            bool_sample_conversion = TuneLuaOptionsBoolSampleConversion(_bool_sample_conversion)

        def _parse_burst_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        burst_timeout = _parse_burst_timeout(d.pop("burst_timeout", UNSET))

        forced_yield = d.pop("forced_yield", UNSET)

        _log_loggers = d.pop("log_loggers", UNSET)
        log_loggers: Union[Unset, TuneLuaOptionsLogLoggers]
        if isinstance(_log_loggers, Unset):
            log_loggers = UNSET
        else:
            log_loggers = TuneLuaOptionsLogLoggers(_log_loggers)

        _log_stderr = d.pop("log_stderr", UNSET)
        log_stderr: Union[Unset, TuneLuaOptionsLogStderr]
        if isinstance(_log_stderr, Unset):
            log_stderr = UNSET
        else:
            log_stderr = TuneLuaOptionsLogStderr(_log_stderr)

        def _parse_maxmem(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        maxmem = _parse_maxmem(d.pop("maxmem", UNSET))

        def _parse_service_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        service_timeout = _parse_service_timeout(d.pop("service_timeout", UNSET))

        def _parse_session_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        session_timeout = _parse_session_timeout(d.pop("session_timeout", UNSET))

        def _parse_task_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        task_timeout = _parse_task_timeout(d.pop("task_timeout", UNSET))

        tune_lua_options = cls(
            bool_sample_conversion=bool_sample_conversion,
            burst_timeout=burst_timeout,
            forced_yield=forced_yield,
            log_loggers=log_loggers,
            log_stderr=log_stderr,
            maxmem=maxmem,
            service_timeout=service_timeout,
            session_timeout=session_timeout,
            task_timeout=task_timeout,
        )

        tune_lua_options.additional_properties = d
        return tune_lua_options

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
