import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="OneCRLEntryRevokedCertificatesItem")


@_attrs_define
class OneCRLEntryRevokedCertificatesItem:
    """
    Attributes:
        revocation_date (Union[Unset, datetime.date]):
        serial_number (Union[Unset, str]):
    """

    revocation_date: Union[Unset, datetime.date] = UNSET
    serial_number: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        revocation_date: Union[Unset, str] = UNSET
        if not isinstance(self.revocation_date, Unset):
            revocation_date = self.revocation_date.isoformat()

        serial_number = self.serial_number

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if revocation_date is not UNSET:
            field_dict["revocation_date"] = revocation_date
        if serial_number is not UNSET:
            field_dict["serial_number"] = serial_number

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _revocation_date = d.pop("revocation_date", UNSET)
        revocation_date: Union[Unset, datetime.date]
        if isinstance(_revocation_date, Unset):
            revocation_date = UNSET
        else:
            revocation_date = isoparse(_revocation_date).date()

        serial_number = d.pop("serial_number", UNSET)

        one_crl_entry_revoked_certificates_item = cls(
            revocation_date=revocation_date,
            serial_number=serial_number,
        )

        one_crl_entry_revoked_certificates_item.additional_properties = d
        return one_crl_entry_revoked_certificates_item

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
