from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.spoe_message_event_cond import SPOEMessageEventCond
from ..models.spoe_message_event_name import SPOEMessageEventName
from ..types import UNSET, Unset

T = TypeVar("T", bound="SPOEMessageEvent")


@_attrs_define
class SPOEMessageEvent:
    """
    Attributes:
        name (SPOEMessageEventName):
        cond (Union[Unset, SPOEMessageEventCond]):
        cond_test (Union[Unset, str]):
    """

    name: SPOEMessageEventName
    cond: Union[Unset, SPOEMessageEventCond] = UNSET
    cond_test: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name.value

        cond: Union[Unset, str] = UNSET
        if not isinstance(self.cond, Unset):
            cond = self.cond.value

        cond_test = self.cond_test

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if cond is not UNSET:
            field_dict["cond"] = cond
        if cond_test is not UNSET:
            field_dict["cond_test"] = cond_test

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = SPOEMessageEventName(d.pop("name"))

        _cond = d.pop("cond", UNSET)
        cond: Union[Unset, SPOEMessageEventCond]
        if isinstance(_cond, Unset):
            cond = UNSET
        else:
            cond = SPOEMessageEventCond(_cond)

        cond_test = d.pop("cond_test", UNSET)

        spoe_message_event = cls(
            name=name,
            cond=cond,
            cond_test=cond_test,
        )

        spoe_message_event.additional_properties = d
        return spoe_message_event

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
