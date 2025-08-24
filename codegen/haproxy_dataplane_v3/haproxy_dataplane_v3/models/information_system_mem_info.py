from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="InformationSystemMemInfo")


@_attrs_define
class InformationSystemMemInfo:
    """
    Attributes:
        dataplaneapi_memory (Union[Unset, int]):
        free_memory (Union[Unset, int]):
        total_memory (Union[Unset, int]):
    """

    dataplaneapi_memory: Union[Unset, int] = UNSET
    free_memory: Union[Unset, int] = UNSET
    total_memory: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataplaneapi_memory = self.dataplaneapi_memory

        free_memory = self.free_memory

        total_memory = self.total_memory

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if dataplaneapi_memory is not UNSET:
            field_dict["dataplaneapi_memory"] = dataplaneapi_memory
        if free_memory is not UNSET:
            field_dict["free_memory"] = free_memory
        if total_memory is not UNSET:
            field_dict["total_memory"] = total_memory

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        dataplaneapi_memory = d.pop("dataplaneapi_memory", UNSET)

        free_memory = d.pop("free_memory", UNSET)

        total_memory = d.pop("total_memory", UNSET)

        information_system_mem_info = cls(
            dataplaneapi_memory=dataplaneapi_memory,
            free_memory=free_memory,
            total_memory=total_memory,
        )

        information_system_mem_info.additional_properties = d
        return information_system_mem_info

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
