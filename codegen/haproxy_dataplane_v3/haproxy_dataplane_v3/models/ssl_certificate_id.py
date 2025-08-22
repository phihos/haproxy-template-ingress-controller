from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.ssl_certificate_id_certificate_id import SSLCertificateIDCertificateId


T = TypeVar("T", bound="SSLCertificateID")


@_attrs_define
class SSLCertificateID:
    """SSL Certificate ID

    Attributes:
        certificate_id (Union[Unset, SSLCertificateIDCertificateId]):
        certificate_id_key (Union[Unset, str]):
        certificate_path (Union[Unset, str]):
    """

    certificate_id: Union[Unset, "SSLCertificateIDCertificateId"] = UNSET
    certificate_id_key: Union[Unset, str] = UNSET
    certificate_path: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        certificate_id: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.certificate_id, Unset):
            certificate_id = self.certificate_id.to_dict()

        certificate_id_key = self.certificate_id_key

        certificate_path = self.certificate_path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if certificate_id is not UNSET:
            field_dict["certificate_id"] = certificate_id
        if certificate_id_key is not UNSET:
            field_dict["certificate_id_key"] = certificate_id_key
        if certificate_path is not UNSET:
            field_dict["certificate_path"] = certificate_path

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.ssl_certificate_id_certificate_id import SSLCertificateIDCertificateId

        d = dict(src_dict)
        _certificate_id = d.pop("certificate_id", UNSET)
        certificate_id: Union[Unset, SSLCertificateIDCertificateId]
        if isinstance(_certificate_id, Unset):
            certificate_id = UNSET
        else:
            certificate_id = SSLCertificateIDCertificateId.from_dict(_certificate_id)

        certificate_id_key = d.pop("certificate_id_key", UNSET)

        certificate_path = d.pop("certificate_path", UNSET)

        ssl_certificate_id = cls(
            certificate_id=certificate_id,
            certificate_id_key=certificate_id_key,
            certificate_path=certificate_path,
        )

        ssl_certificate_id.additional_properties = d
        return ssl_certificate_id

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
