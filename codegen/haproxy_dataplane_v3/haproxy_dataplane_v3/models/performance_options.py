from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.performance_options_profiling_memory import PerformanceOptionsProfilingMemory
from ..models.performance_options_profiling_tasks import PerformanceOptionsProfilingTasks
from ..types import UNSET, Unset

T = TypeVar("T", bound="PerformanceOptions")


@_attrs_define
class PerformanceOptions:
    """
    Attributes:
        busy_polling (Union[Unset, bool]):
        max_spread_checks (Union[None, Unset, int]):
        maxcompcpuusage (Union[Unset, int]):
        maxcomprate (Union[Unset, int]):
        maxconn (Union[Unset, int]):
        maxconnrate (Union[Unset, int]):
        maxpipes (Union[Unset, int]):
        maxsessrate (Union[Unset, int]):
        maxzlibmem (Union[Unset, int]):
        noepoll (Union[Unset, bool]):
        noevports (Union[Unset, bool]):
        nogetaddrinfo (Union[Unset, bool]):
        nokqueue (Union[Unset, bool]):
        nopoll (Union[Unset, bool]):
        noreuseport (Union[Unset, bool]):
        nosplice (Union[Unset, bool]):
        profiling_memory (Union[Unset, PerformanceOptionsProfilingMemory]):
        profiling_tasks (Union[Unset, PerformanceOptionsProfilingTasks]):
        server_state_base (Union[Unset, str]):
        server_state_file (Union[Unset, str]):
        spread_checks (Union[Unset, int]):
        thread_hard_limit (Union[None, Unset, int]):
    """

    busy_polling: Union[Unset, bool] = UNSET
    max_spread_checks: Union[None, Unset, int] = UNSET
    maxcompcpuusage: Union[Unset, int] = UNSET
    maxcomprate: Union[Unset, int] = UNSET
    maxconn: Union[Unset, int] = UNSET
    maxconnrate: Union[Unset, int] = UNSET
    maxpipes: Union[Unset, int] = UNSET
    maxsessrate: Union[Unset, int] = UNSET
    maxzlibmem: Union[Unset, int] = UNSET
    noepoll: Union[Unset, bool] = UNSET
    noevports: Union[Unset, bool] = UNSET
    nogetaddrinfo: Union[Unset, bool] = UNSET
    nokqueue: Union[Unset, bool] = UNSET
    nopoll: Union[Unset, bool] = UNSET
    noreuseport: Union[Unset, bool] = UNSET
    nosplice: Union[Unset, bool] = UNSET
    profiling_memory: Union[Unset, PerformanceOptionsProfilingMemory] = UNSET
    profiling_tasks: Union[Unset, PerformanceOptionsProfilingTasks] = UNSET
    server_state_base: Union[Unset, str] = UNSET
    server_state_file: Union[Unset, str] = UNSET
    spread_checks: Union[Unset, int] = UNSET
    thread_hard_limit: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        busy_polling = self.busy_polling

        max_spread_checks: Union[None, Unset, int]
        if isinstance(self.max_spread_checks, Unset):
            max_spread_checks = UNSET
        else:
            max_spread_checks = self.max_spread_checks

        maxcompcpuusage = self.maxcompcpuusage

        maxcomprate = self.maxcomprate

        maxconn = self.maxconn

        maxconnrate = self.maxconnrate

        maxpipes = self.maxpipes

        maxsessrate = self.maxsessrate

        maxzlibmem = self.maxzlibmem

        noepoll = self.noepoll

        noevports = self.noevports

        nogetaddrinfo = self.nogetaddrinfo

        nokqueue = self.nokqueue

        nopoll = self.nopoll

        noreuseport = self.noreuseport

        nosplice = self.nosplice

        profiling_memory: Union[Unset, str] = UNSET
        if not isinstance(self.profiling_memory, Unset):
            profiling_memory = self.profiling_memory.value

        profiling_tasks: Union[Unset, str] = UNSET
        if not isinstance(self.profiling_tasks, Unset):
            profiling_tasks = self.profiling_tasks.value

        server_state_base = self.server_state_base

        server_state_file = self.server_state_file

        spread_checks = self.spread_checks

        thread_hard_limit: Union[None, Unset, int]
        if isinstance(self.thread_hard_limit, Unset):
            thread_hard_limit = UNSET
        else:
            thread_hard_limit = self.thread_hard_limit

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if busy_polling is not UNSET:
            field_dict["busy_polling"] = busy_polling
        if max_spread_checks is not UNSET:
            field_dict["max_spread_checks"] = max_spread_checks
        if maxcompcpuusage is not UNSET:
            field_dict["maxcompcpuusage"] = maxcompcpuusage
        if maxcomprate is not UNSET:
            field_dict["maxcomprate"] = maxcomprate
        if maxconn is not UNSET:
            field_dict["maxconn"] = maxconn
        if maxconnrate is not UNSET:
            field_dict["maxconnrate"] = maxconnrate
        if maxpipes is not UNSET:
            field_dict["maxpipes"] = maxpipes
        if maxsessrate is not UNSET:
            field_dict["maxsessrate"] = maxsessrate
        if maxzlibmem is not UNSET:
            field_dict["maxzlibmem"] = maxzlibmem
        if noepoll is not UNSET:
            field_dict["noepoll"] = noepoll
        if noevports is not UNSET:
            field_dict["noevports"] = noevports
        if nogetaddrinfo is not UNSET:
            field_dict["nogetaddrinfo"] = nogetaddrinfo
        if nokqueue is not UNSET:
            field_dict["nokqueue"] = nokqueue
        if nopoll is not UNSET:
            field_dict["nopoll"] = nopoll
        if noreuseport is not UNSET:
            field_dict["noreuseport"] = noreuseport
        if nosplice is not UNSET:
            field_dict["nosplice"] = nosplice
        if profiling_memory is not UNSET:
            field_dict["profiling_memory"] = profiling_memory
        if profiling_tasks is not UNSET:
            field_dict["profiling_tasks"] = profiling_tasks
        if server_state_base is not UNSET:
            field_dict["server_state_base"] = server_state_base
        if server_state_file is not UNSET:
            field_dict["server_state_file"] = server_state_file
        if spread_checks is not UNSET:
            field_dict["spread_checks"] = spread_checks
        if thread_hard_limit is not UNSET:
            field_dict["thread_hard_limit"] = thread_hard_limit

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        busy_polling = d.pop("busy_polling", UNSET)

        def _parse_max_spread_checks(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_spread_checks = _parse_max_spread_checks(d.pop("max_spread_checks", UNSET))

        maxcompcpuusage = d.pop("maxcompcpuusage", UNSET)

        maxcomprate = d.pop("maxcomprate", UNSET)

        maxconn = d.pop("maxconn", UNSET)

        maxconnrate = d.pop("maxconnrate", UNSET)

        maxpipes = d.pop("maxpipes", UNSET)

        maxsessrate = d.pop("maxsessrate", UNSET)

        maxzlibmem = d.pop("maxzlibmem", UNSET)

        noepoll = d.pop("noepoll", UNSET)

        noevports = d.pop("noevports", UNSET)

        nogetaddrinfo = d.pop("nogetaddrinfo", UNSET)

        nokqueue = d.pop("nokqueue", UNSET)

        nopoll = d.pop("nopoll", UNSET)

        noreuseport = d.pop("noreuseport", UNSET)

        nosplice = d.pop("nosplice", UNSET)

        _profiling_memory = d.pop("profiling_memory", UNSET)
        profiling_memory: Union[Unset, PerformanceOptionsProfilingMemory]
        if isinstance(_profiling_memory, Unset):
            profiling_memory = UNSET
        else:
            profiling_memory = PerformanceOptionsProfilingMemory(_profiling_memory)

        _profiling_tasks = d.pop("profiling_tasks", UNSET)
        profiling_tasks: Union[Unset, PerformanceOptionsProfilingTasks]
        if isinstance(_profiling_tasks, Unset):
            profiling_tasks = UNSET
        else:
            profiling_tasks = PerformanceOptionsProfilingTasks(_profiling_tasks)

        server_state_base = d.pop("server_state_base", UNSET)

        server_state_file = d.pop("server_state_file", UNSET)

        spread_checks = d.pop("spread_checks", UNSET)

        def _parse_thread_hard_limit(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        thread_hard_limit = _parse_thread_hard_limit(d.pop("thread_hard_limit", UNSET))

        performance_options = cls(
            busy_polling=busy_polling,
            max_spread_checks=max_spread_checks,
            maxcompcpuusage=maxcompcpuusage,
            maxcomprate=maxcomprate,
            maxconn=maxconn,
            maxconnrate=maxconnrate,
            maxpipes=maxpipes,
            maxsessrate=maxsessrate,
            maxzlibmem=maxzlibmem,
            noepoll=noepoll,
            noevports=noevports,
            nogetaddrinfo=nogetaddrinfo,
            nokqueue=nokqueue,
            nopoll=nopoll,
            noreuseport=noreuseport,
            nosplice=nosplice,
            profiling_memory=profiling_memory,
            profiling_tasks=profiling_tasks,
            server_state_base=server_state_base,
            server_state_file=server_state_file,
            spread_checks=spread_checks,
            thread_hard_limit=thread_hard_limit,
        )

        performance_options.additional_properties = d
        return performance_options

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
