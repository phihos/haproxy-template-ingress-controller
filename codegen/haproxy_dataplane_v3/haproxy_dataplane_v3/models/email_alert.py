from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.email_alert_level import EmailAlertLevel
from ..types import UNSET, Unset

T = TypeVar("T", bound="EmailAlert")


@_attrs_define
class EmailAlert:
    """Send emails for important log messages.

    Attributes:
        from_ (str):
        mailers (str):
        to (str):
        level (Union[Unset, EmailAlertLevel]):
        metadata (Union[Unset, Any]):
        myhostname (Union[Unset, str]):
    """

    from_: str
    mailers: str
    to: str
    level: Union[Unset, EmailAlertLevel] = UNSET
    metadata: Union[Unset, Any] = UNSET
    myhostname: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from_ = self.from_

        mailers = self.mailers

        to = self.to

        level: Union[Unset, str] = UNSET
        if not isinstance(self.level, Unset):
            level = self.level.value

        metadata = self.metadata

        myhostname = self.myhostname

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "from": from_,
                "mailers": mailers,
                "to": to,
            }
        )
        if level is not UNSET:
            field_dict["level"] = level
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if myhostname is not UNSET:
            field_dict["myhostname"] = myhostname

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        from_ = d.pop("from")

        mailers = d.pop("mailers")

        to = d.pop("to")

        _level = d.pop("level", UNSET)
        level: Union[Unset, EmailAlertLevel]
        if isinstance(_level, Unset):
            level = UNSET
        else:
            level = EmailAlertLevel(_level)

        metadata = d.pop("metadata", UNSET)

        myhostname = d.pop("myhostname", UNSET)

        email_alert = cls(
            from_=from_,
            mailers=mailers,
            to=to,
            level=level,
            metadata=metadata,
            myhostname=myhostname,
        )

        email_alert.additional_properties = d
        return email_alert

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
