from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.acl_lines import ACLLines
    from ..models.spoe_message_event import SPOEMessageEvent


T = TypeVar("T", bound="SPOEMessage")


@_attrs_define
class SPOEMessage:
    """SPOE message section configuration

    Attributes:
        name (str):
        acl (Union[Unset, list['ACLLines']]): HAProxy ACL lines array (corresponds to acl directives)
        args (Union[Unset, str]):
        event (Union[Unset, SPOEMessageEvent]):
    """

    name: str
    acl: Union[Unset, list["ACLLines"]] = UNSET
    args: Union[Unset, str] = UNSET
    event: Union[Unset, "SPOEMessageEvent"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        acl: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.acl, Unset):
            acl = []
            for componentsschemasacls_item_data in self.acl:
                componentsschemasacls_item = componentsschemasacls_item_data.to_dict()
                acl.append(componentsschemasacls_item)

        args = self.args

        event: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.event, Unset):
            event = self.event.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if acl is not UNSET:
            field_dict["acl"] = acl
        if args is not UNSET:
            field_dict["args"] = args
        if event is not UNSET:
            field_dict["event"] = event

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.acl_lines import ACLLines
        from ..models.spoe_message_event import SPOEMessageEvent

        d = dict(src_dict)
        name = d.pop("name")

        acl = []
        _acl = d.pop("acl", UNSET)
        for componentsschemasacls_item_data in _acl or []:
            componentsschemasacls_item = ACLLines.from_dict(componentsschemasacls_item_data)

            acl.append(componentsschemasacls_item)

        args = d.pop("args", UNSET)

        _event = d.pop("event", UNSET)
        event: Union[Unset, SPOEMessageEvent]
        if isinstance(_event, Unset):
            event = UNSET
        else:
            event = SPOEMessageEvent.from_dict(_event)

        spoe_message = cls(
            name=name,
            acl=acl,
            args=args,
            event=event,
        )

        spoe_message.additional_properties = d
        return spoe_message

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
