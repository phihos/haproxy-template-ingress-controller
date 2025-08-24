from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.information_system_cpu_info import InformationSystemCpuInfo
    from ..models.information_system_mem_info import InformationSystemMemInfo


T = TypeVar("T", bound="InformationSystem")


@_attrs_define
class InformationSystem:
    """
    Attributes:
        cpu_info (Union[Unset, InformationSystemCpuInfo]):
        hostname (Union[Unset, str]): Hostname where the HAProxy is running
        mem_info (Union[Unset, InformationSystemMemInfo]):
        os_string (Union[Unset, str]): OS string
        time (Union[Unset, int]): Current time in milliseconds since Epoch.
        uptime (Union[None, Unset, int]): System uptime
    """

    cpu_info: Union[Unset, "InformationSystemCpuInfo"] = UNSET
    hostname: Union[Unset, str] = UNSET
    mem_info: Union[Unset, "InformationSystemMemInfo"] = UNSET
    os_string: Union[Unset, str] = UNSET
    time: Union[Unset, int] = UNSET
    uptime: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cpu_info: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.cpu_info, Unset):
            cpu_info = self.cpu_info.to_dict()

        hostname = self.hostname

        mem_info: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.mem_info, Unset):
            mem_info = self.mem_info.to_dict()

        os_string = self.os_string

        time = self.time

        uptime: Union[None, Unset, int]
        if isinstance(self.uptime, Unset):
            uptime = UNSET
        else:
            uptime = self.uptime

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cpu_info is not UNSET:
            field_dict["cpu_info"] = cpu_info
        if hostname is not UNSET:
            field_dict["hostname"] = hostname
        if mem_info is not UNSET:
            field_dict["mem_info"] = mem_info
        if os_string is not UNSET:
            field_dict["os_string"] = os_string
        if time is not UNSET:
            field_dict["time"] = time
        if uptime is not UNSET:
            field_dict["uptime"] = uptime

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.information_system_cpu_info import InformationSystemCpuInfo
        from ..models.information_system_mem_info import InformationSystemMemInfo

        d = dict(src_dict)
        _cpu_info = d.pop("cpu_info", UNSET)
        cpu_info: Union[Unset, InformationSystemCpuInfo]
        if isinstance(_cpu_info, Unset):
            cpu_info = UNSET
        else:
            cpu_info = InformationSystemCpuInfo.from_dict(_cpu_info)

        hostname = d.pop("hostname", UNSET)

        _mem_info = d.pop("mem_info", UNSET)
        mem_info: Union[Unset, InformationSystemMemInfo]
        if isinstance(_mem_info, Unset):
            mem_info = UNSET
        else:
            mem_info = InformationSystemMemInfo.from_dict(_mem_info)

        os_string = d.pop("os_string", UNSET)

        time = d.pop("time", UNSET)

        def _parse_uptime(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        uptime = _parse_uptime(d.pop("uptime", UNSET))

        information_system = cls(
            cpu_info=cpu_info,
            hostname=hostname,
            mem_info=mem_info,
            os_string=os_string,
            time=time,
            uptime=uptime,
        )

        information_system.additional_properties = d
        return information_system

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
