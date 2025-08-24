from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SSLCertificateIDCertificateId")


@_attrs_define
class SSLCertificateIDCertificateId:
    """
    Attributes:
        hash_algorithm (Union[Unset, str]):
        issuer_key_hash (Union[Unset, str]):
        issuer_name_hash (Union[Unset, str]):
        serial_number (Union[Unset, str]):
    """

    hash_algorithm: Union[Unset, str] = UNSET
    issuer_key_hash: Union[Unset, str] = UNSET
    issuer_name_hash: Union[Unset, str] = UNSET
    serial_number: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        hash_algorithm = self.hash_algorithm

        issuer_key_hash = self.issuer_key_hash

        issuer_name_hash = self.issuer_name_hash

        serial_number = self.serial_number

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if hash_algorithm is not UNSET:
            field_dict["hash_algorithm"] = hash_algorithm
        if issuer_key_hash is not UNSET:
            field_dict["issuer_key_hash"] = issuer_key_hash
        if issuer_name_hash is not UNSET:
            field_dict["issuer_name_hash"] = issuer_name_hash
        if serial_number is not UNSET:
            field_dict["serial_number"] = serial_number

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        hash_algorithm = d.pop("hash_algorithm", UNSET)

        issuer_key_hash = d.pop("issuer_key_hash", UNSET)

        issuer_name_hash = d.pop("issuer_name_hash", UNSET)

        serial_number = d.pop("serial_number", UNSET)

        ssl_certificate_id_certificate_id = cls(
            hash_algorithm=hash_algorithm,
            issuer_key_hash=issuer_key_hash,
            issuer_name_hash=issuer_name_hash,
            serial_number=serial_number,
        )

        ssl_certificate_id_certificate_id.additional_properties = d
        return ssl_certificate_id_certificate_id

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
