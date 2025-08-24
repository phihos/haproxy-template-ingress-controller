import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="ACMECertificateStatus")


@_attrs_define
class ACMECertificateStatus:
    """Status of a single ACME certificate from runtime.

    Attributes:
        acme_section (Union[Unset, str]): ACME section which generated the certificate.
        certificate (Union[Unset, str]): Certificate name
        expiries_in (Union[Unset, str]): Duration until certificate expiry.
        expiry_date (Union[Unset, datetime.datetime]): Certificate expiration date.
        renewal_in (Union[Unset, str]): Duration until the next planned renewal.
        scheduled_renewal (Union[Unset, datetime.datetime]): Planned date for certificate renewal.
        state (Union[Unset, str]): State of the ACME task, either "Running" or "Scheduled".
    """

    acme_section: Union[Unset, str] = UNSET
    certificate: Union[Unset, str] = UNSET
    expiries_in: Union[Unset, str] = UNSET
    expiry_date: Union[Unset, datetime.datetime] = UNSET
    renewal_in: Union[Unset, str] = UNSET
    scheduled_renewal: Union[Unset, datetime.datetime] = UNSET
    state: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        acme_section = self.acme_section

        certificate = self.certificate

        expiries_in = self.expiries_in

        expiry_date: Union[Unset, str] = UNSET
        if not isinstance(self.expiry_date, Unset):
            expiry_date = self.expiry_date.isoformat()

        renewal_in = self.renewal_in

        scheduled_renewal: Union[Unset, str] = UNSET
        if not isinstance(self.scheduled_renewal, Unset):
            scheduled_renewal = self.scheduled_renewal.isoformat()

        state = self.state

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if acme_section is not UNSET:
            field_dict["acme_section"] = acme_section
        if certificate is not UNSET:
            field_dict["certificate"] = certificate
        if expiries_in is not UNSET:
            field_dict["expiries_in"] = expiries_in
        if expiry_date is not UNSET:
            field_dict["expiry_date"] = expiry_date
        if renewal_in is not UNSET:
            field_dict["renewal_in"] = renewal_in
        if scheduled_renewal is not UNSET:
            field_dict["scheduled_renewal"] = scheduled_renewal
        if state is not UNSET:
            field_dict["state"] = state

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        acme_section = d.pop("acme_section", UNSET)

        certificate = d.pop("certificate", UNSET)

        expiries_in = d.pop("expiries_in", UNSET)

        _expiry_date = d.pop("expiry_date", UNSET)
        expiry_date: Union[Unset, datetime.datetime]
        if isinstance(_expiry_date, Unset):
            expiry_date = UNSET
        else:
            expiry_date = isoparse(_expiry_date)

        renewal_in = d.pop("renewal_in", UNSET)

        _scheduled_renewal = d.pop("scheduled_renewal", UNSET)
        scheduled_renewal: Union[Unset, datetime.datetime]
        if isinstance(_scheduled_renewal, Unset):
            scheduled_renewal = UNSET
        else:
            scheduled_renewal = isoparse(_scheduled_renewal)

        state = d.pop("state", UNSET)

        acme_certificate_status = cls(
            acme_section=acme_section,
            certificate=certificate,
            expiries_in=expiries_in,
            expiry_date=expiry_date,
            renewal_in=renewal_in,
            scheduled_renewal=scheduled_renewal,
            state=state,
        )

        acme_certificate_status.additional_properties = d
        return acme_certificate_status

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
