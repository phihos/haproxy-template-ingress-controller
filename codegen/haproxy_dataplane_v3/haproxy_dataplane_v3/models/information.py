from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.information_api import InformationApi
    from ..models.information_system import InformationSystem


T = TypeVar("T", bound="Information")


@_attrs_define
class Information:
    """General API, OS and hardware information

    Example:
        {'api': {'build_date': datetime.datetime(2019, 8, 21, 17, 31, 56,
            tzinfo=datetime.timezone(datetime.timedelta(0), 'Z')), 'version': 'v1.2.1 45a3288.dev'}, 'system': {'cpu_info':
            {'model': 'Intel(R) Core(TM) i7-7500U CPU @ 2.70GHz', 'num_cpus': 4}, 'hostname': 'test', 'mem_info':
            {'dataplaneapi_memory': 44755536, 'free_memory': 5790642176, 'total_memory': 16681517056}, 'os_string': 'Linux
            4.15.0-58-generic #64-Ubuntu SMP Tue Aug 6 11:12:41 UTC 2019', 'time': 1566401525, 'uptime': 87340}}

    Attributes:
        api (Union[Unset, InformationApi]):
        system (Union[Unset, InformationSystem]):
    """

    api: Union[Unset, "InformationApi"] = UNSET
    system: Union[Unset, "InformationSystem"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        api: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.api, Unset):
            api = self.api.to_dict()

        system: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.system, Unset):
            system = self.system.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if api is not UNSET:
            field_dict["api"] = api
        if system is not UNSET:
            field_dict["system"] = system

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.information_api import InformationApi
        from ..models.information_system import InformationSystem

        d = dict(src_dict)
        _api = d.pop("api", UNSET)
        api: Union[Unset, InformationApi]
        if isinstance(_api, Unset):
            api = UNSET
        else:
            api = InformationApi.from_dict(_api)

        _system = d.pop("system", UNSET)
        system: Union[Unset, InformationSystem]
        if isinstance(_system, Unset):
            system = UNSET
        else:
            system = InformationSystem.from_dict(_system)

        information = cls(
            api=api,
            system=system,
        )

        information.additional_properties = d
        return information

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
