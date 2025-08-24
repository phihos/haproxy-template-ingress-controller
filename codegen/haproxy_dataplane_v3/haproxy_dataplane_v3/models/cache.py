from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Cache")


@_attrs_define
class Cache:
    """HAPRoxy Cache section

    Attributes:
        name (str):
        max_age (Union[Unset, int]):
        max_object_size (Union[Unset, int]):
        max_secondary_entries (Union[Unset, int]):
        metadata (Union[Unset, Any]):
        process_vary (Union[None, Unset, bool]):
        total_max_size (Union[Unset, int]):
    """

    name: str
    max_age: Union[Unset, int] = UNSET
    max_object_size: Union[Unset, int] = UNSET
    max_secondary_entries: Union[Unset, int] = UNSET
    metadata: Union[Unset, Any] = UNSET
    process_vary: Union[None, Unset, bool] = UNSET
    total_max_size: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        max_age = self.max_age

        max_object_size = self.max_object_size

        max_secondary_entries = self.max_secondary_entries

        metadata = self.metadata

        process_vary: Union[None, Unset, bool]
        if isinstance(self.process_vary, Unset):
            process_vary = UNSET
        else:
            process_vary = self.process_vary

        total_max_size = self.total_max_size

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if max_age is not UNSET:
            field_dict["max_age"] = max_age
        if max_object_size is not UNSET:
            field_dict["max_object_size"] = max_object_size
        if max_secondary_entries is not UNSET:
            field_dict["max_secondary_entries"] = max_secondary_entries
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if process_vary is not UNSET:
            field_dict["process_vary"] = process_vary
        if total_max_size is not UNSET:
            field_dict["total_max_size"] = total_max_size

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        max_age = d.pop("max_age", UNSET)

        max_object_size = d.pop("max_object_size", UNSET)

        max_secondary_entries = d.pop("max_secondary_entries", UNSET)

        metadata = d.pop("metadata", UNSET)

        def _parse_process_vary(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        process_vary = _parse_process_vary(d.pop("process_vary", UNSET))

        total_max_size = d.pop("total_max_size", UNSET)

        cache = cls(
            name=name,
            max_age=max_age,
            max_object_size=max_object_size,
            max_secondary_entries=max_secondary_entries,
            metadata=metadata,
            process_vary=process_vary,
            total_max_size=total_max_size,
        )

        cache.additional_properties = d
        return cache

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
