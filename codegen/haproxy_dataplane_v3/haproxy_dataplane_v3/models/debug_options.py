from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DebugOptions")


@_attrs_define
class DebugOptions:
    """
    Attributes:
        anonkey (Union[None, Unset, int]):
        quiet (Union[Unset, bool]):
        stress_level (Union[None, Unset, int]):
        zero_warning (Union[Unset, bool]):
    """

    anonkey: Union[None, Unset, int] = UNSET
    quiet: Union[Unset, bool] = UNSET
    stress_level: Union[None, Unset, int] = UNSET
    zero_warning: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        anonkey: Union[None, Unset, int]
        if isinstance(self.anonkey, Unset):
            anonkey = UNSET
        else:
            anonkey = self.anonkey

        quiet = self.quiet

        stress_level: Union[None, Unset, int]
        if isinstance(self.stress_level, Unset):
            stress_level = UNSET
        else:
            stress_level = self.stress_level

        zero_warning = self.zero_warning

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if anonkey is not UNSET:
            field_dict["anonkey"] = anonkey
        if quiet is not UNSET:
            field_dict["quiet"] = quiet
        if stress_level is not UNSET:
            field_dict["stress_level"] = stress_level
        if zero_warning is not UNSET:
            field_dict["zero_warning"] = zero_warning

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_anonkey(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        anonkey = _parse_anonkey(d.pop("anonkey", UNSET))

        quiet = d.pop("quiet", UNSET)

        def _parse_stress_level(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        stress_level = _parse_stress_level(d.pop("stress_level", UNSET))

        zero_warning = d.pop("zero_warning", UNSET)

        debug_options = cls(
            anonkey=anonkey,
            quiet=quiet,
            stress_level=stress_level,
            zero_warning=zero_warning,
        )

        debug_options.additional_properties = d
        return debug_options

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
