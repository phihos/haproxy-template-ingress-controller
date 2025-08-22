import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.one_crl_entry_revoked_certificates_item import OneCRLEntryRevokedCertificatesItem


T = TypeVar("T", bound="OneCRLEntry")


@_attrs_define
class OneCRLEntry:
    """A certificate revocation list entry.

    Attributes:
        issuer (Union[Unset, str]):
        last_update (Union[Unset, datetime.date]):
        next_update (Union[Unset, datetime.date]):
        revoked_certificates (Union[Unset, list['OneCRLEntryRevokedCertificatesItem']]):
        signature_algorithm (Union[Unset, str]):
        status (Union[Unset, str]):
        storage_name (Union[Unset, str]):
        version (Union[Unset, str]):
    """

    issuer: Union[Unset, str] = UNSET
    last_update: Union[Unset, datetime.date] = UNSET
    next_update: Union[Unset, datetime.date] = UNSET
    revoked_certificates: Union[Unset, list["OneCRLEntryRevokedCertificatesItem"]] = UNSET
    signature_algorithm: Union[Unset, str] = UNSET
    status: Union[Unset, str] = UNSET
    storage_name: Union[Unset, str] = UNSET
    version: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        issuer = self.issuer

        last_update: Union[Unset, str] = UNSET
        if not isinstance(self.last_update, Unset):
            last_update = self.last_update.isoformat()

        next_update: Union[Unset, str] = UNSET
        if not isinstance(self.next_update, Unset):
            next_update = self.next_update.isoformat()

        revoked_certificates: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.revoked_certificates, Unset):
            revoked_certificates = []
            for revoked_certificates_item_data in self.revoked_certificates:
                revoked_certificates_item = revoked_certificates_item_data.to_dict()
                revoked_certificates.append(revoked_certificates_item)

        signature_algorithm = self.signature_algorithm

        status = self.status

        storage_name = self.storage_name

        version = self.version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if issuer is not UNSET:
            field_dict["issuer"] = issuer
        if last_update is not UNSET:
            field_dict["last_update"] = last_update
        if next_update is not UNSET:
            field_dict["next_update"] = next_update
        if revoked_certificates is not UNSET:
            field_dict["revoked_certificates"] = revoked_certificates
        if signature_algorithm is not UNSET:
            field_dict["signature_algorithm"] = signature_algorithm
        if status is not UNSET:
            field_dict["status"] = status
        if storage_name is not UNSET:
            field_dict["storage_name"] = storage_name
        if version is not UNSET:
            field_dict["version"] = version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.one_crl_entry_revoked_certificates_item import OneCRLEntryRevokedCertificatesItem

        d = dict(src_dict)
        issuer = d.pop("issuer", UNSET)

        _last_update = d.pop("last_update", UNSET)
        last_update: Union[Unset, datetime.date]
        if isinstance(_last_update, Unset):
            last_update = UNSET
        else:
            last_update = isoparse(_last_update).date()

        _next_update = d.pop("next_update", UNSET)
        next_update: Union[Unset, datetime.date]
        if isinstance(_next_update, Unset):
            next_update = UNSET
        else:
            next_update = isoparse(_next_update).date()

        revoked_certificates = []
        _revoked_certificates = d.pop("revoked_certificates", UNSET)
        for revoked_certificates_item_data in _revoked_certificates or []:
            revoked_certificates_item = OneCRLEntryRevokedCertificatesItem.from_dict(revoked_certificates_item_data)

            revoked_certificates.append(revoked_certificates_item)

        signature_algorithm = d.pop("signature_algorithm", UNSET)

        status = d.pop("status", UNSET)

        storage_name = d.pop("storage_name", UNSET)

        version = d.pop("version", UNSET)

        one_crl_entry = cls(
            issuer=issuer,
            last_update=last_update,
            next_update=next_update,
            revoked_certificates=revoked_certificates,
            signature_algorithm=signature_algorithm,
            status=status,
            storage_name=storage_name,
            version=version,
        )

        one_crl_entry.additional_properties = d
        return one_crl_entry

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
