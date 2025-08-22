from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.certificate_load_action_ocsp_update import CertificateLoadActionOcspUpdate
from ..types import UNSET, Unset

T = TypeVar("T", bound="CertificateLoadAction")


@_attrs_define
class CertificateLoadAction:
    """Loads a certificate from a store with options

    Attributes:
        certificate (str): Certificate filename
        acme (Union[Unset, str]): ACME section name to use
        alias (Union[Unset, str]): Certificate alias
        domains (Union[Unset, list[str]]): List of domains used to generate the certificate with ACME
        issuer (Union[Unset, str]): OCSP issuer filename
        key (Union[Unset, str]): Private key filename
        metadata (Union[Unset, Any]):
        ocsp (Union[Unset, str]): OCSP response filename
        ocsp_update (Union[Unset, CertificateLoadActionOcspUpdate]): Automatic OCSP response update
        sctl (Union[Unset, str]): Signed Certificate Timestamp List filename
    """

    certificate: str
    acme: Union[Unset, str] = UNSET
    alias: Union[Unset, str] = UNSET
    domains: Union[Unset, list[str]] = UNSET
    issuer: Union[Unset, str] = UNSET
    key: Union[Unset, str] = UNSET
    metadata: Union[Unset, Any] = UNSET
    ocsp: Union[Unset, str] = UNSET
    ocsp_update: Union[Unset, CertificateLoadActionOcspUpdate] = UNSET
    sctl: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        certificate = self.certificate

        acme = self.acme

        alias = self.alias

        domains: Union[Unset, list[str]] = UNSET
        if not isinstance(self.domains, Unset):
            domains = self.domains

        issuer = self.issuer

        key = self.key

        metadata = self.metadata

        ocsp = self.ocsp

        ocsp_update: Union[Unset, str] = UNSET
        if not isinstance(self.ocsp_update, Unset):
            ocsp_update = self.ocsp_update.value

        sctl = self.sctl

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "certificate": certificate,
            }
        )
        if acme is not UNSET:
            field_dict["acme"] = acme
        if alias is not UNSET:
            field_dict["alias"] = alias
        if domains is not UNSET:
            field_dict["domains"] = domains
        if issuer is not UNSET:
            field_dict["issuer"] = issuer
        if key is not UNSET:
            field_dict["key"] = key
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if ocsp is not UNSET:
            field_dict["ocsp"] = ocsp
        if ocsp_update is not UNSET:
            field_dict["ocsp_update"] = ocsp_update
        if sctl is not UNSET:
            field_dict["sctl"] = sctl

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        certificate = d.pop("certificate")

        acme = d.pop("acme", UNSET)

        alias = d.pop("alias", UNSET)

        domains = cast(list[str], d.pop("domains", UNSET))

        issuer = d.pop("issuer", UNSET)

        key = d.pop("key", UNSET)

        metadata = d.pop("metadata", UNSET)

        ocsp = d.pop("ocsp", UNSET)

        _ocsp_update = d.pop("ocsp_update", UNSET)
        ocsp_update: Union[Unset, CertificateLoadActionOcspUpdate]
        if isinstance(_ocsp_update, Unset):
            ocsp_update = UNSET
        else:
            ocsp_update = CertificateLoadActionOcspUpdate(_ocsp_update)

        sctl = d.pop("sctl", UNSET)

        certificate_load_action = cls(
            certificate=certificate,
            acme=acme,
            alias=alias,
            domains=domains,
            issuer=issuer,
            key=key,
            metadata=metadata,
            ocsp=ocsp,
            ocsp_update=ocsp_update,
            sctl=sctl,
        )

        certificate_load_action.additional_properties = d
        return certificate_load_action

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
