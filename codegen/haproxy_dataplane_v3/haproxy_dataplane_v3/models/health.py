from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.health_haproxy import HealthHaproxy
from ..types import UNSET, Unset

T = TypeVar("T", bound="Health")


@_attrs_define
class Health:
    """
    Attributes:
        haproxy (Union[Unset, HealthHaproxy]):
    """

    haproxy: Union[Unset, HealthHaproxy] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        haproxy: Union[Unset, str] = UNSET
        if not isinstance(self.haproxy, Unset):
            haproxy = self.haproxy.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if haproxy is not UNSET:
            field_dict["haproxy"] = haproxy

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _haproxy = d.pop("haproxy", UNSET)
        haproxy: Union[Unset, HealthHaproxy]
        if isinstance(_haproxy, Unset):
            haproxy = UNSET
        else:
            haproxy = HealthHaproxy(_haproxy)

        health = cls(
            haproxy=haproxy,
        )

        health.additional_properties = d
        return health

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
