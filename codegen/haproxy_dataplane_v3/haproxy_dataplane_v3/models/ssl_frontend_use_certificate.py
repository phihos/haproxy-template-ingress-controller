from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.ssl_frontend_use_certificate_ocsp_update import SSLFrontendUseCertificateOcspUpdate
from ..models.ssl_frontend_use_certificate_ssl_max_ver import SSLFrontendUseCertificateSslMaxVer
from ..models.ssl_frontend_use_certificate_ssl_min_ver import SSLFrontendUseCertificateSslMinVer
from ..models.ssl_frontend_use_certificate_verify import SSLFrontendUseCertificateVerify
from ..types import UNSET, Unset

T = TypeVar("T", bound="SSLFrontendUseCertificate")


@_attrs_define
class SSLFrontendUseCertificate:
    """Assign a certificate to the current frontend

    Attributes:
        certificate (str): Certificate filename
        allow_0rtt (Union[Unset, bool]):
        alpn (Union[Unset, str]):
        ca_file (Union[Unset, str]):
        ciphers (Union[Unset, str]):
        ciphersuites (Union[Unset, str]):
        client_sigalgs (Union[Unset, str]):
        crl_file (Union[Unset, str]):
        curves (Union[Unset, str]):
        ecdhe (Union[Unset, str]):
        issuer (Union[Unset, str]): OCSP issuer filename
        key (Union[Unset, str]): Private key filename
        metadata (Union[Unset, Any]):
        no_alpn (Union[Unset, bool]):
        no_ca_names (Union[Unset, bool]):
        npn (Union[Unset, str]):
        ocsp (Union[Unset, str]): OCSP response filename
        ocsp_update (Union[Unset, SSLFrontendUseCertificateOcspUpdate]): Automatic OCSP response update
        sctl (Union[Unset, str]): Signed Certificate Timestamp List filename
        sigalgs (Union[Unset, str]):
        ssl_max_ver (Union[Unset, SSLFrontendUseCertificateSslMaxVer]):
        ssl_min_ver (Union[Unset, SSLFrontendUseCertificateSslMinVer]):
        verify (Union[Unset, SSLFrontendUseCertificateVerify]):
    """

    certificate: str
    allow_0rtt: Union[Unset, bool] = UNSET
    alpn: Union[Unset, str] = UNSET
    ca_file: Union[Unset, str] = UNSET
    ciphers: Union[Unset, str] = UNSET
    ciphersuites: Union[Unset, str] = UNSET
    client_sigalgs: Union[Unset, str] = UNSET
    crl_file: Union[Unset, str] = UNSET
    curves: Union[Unset, str] = UNSET
    ecdhe: Union[Unset, str] = UNSET
    issuer: Union[Unset, str] = UNSET
    key: Union[Unset, str] = UNSET
    metadata: Union[Unset, Any] = UNSET
    no_alpn: Union[Unset, bool] = UNSET
    no_ca_names: Union[Unset, bool] = UNSET
    npn: Union[Unset, str] = UNSET
    ocsp: Union[Unset, str] = UNSET
    ocsp_update: Union[Unset, SSLFrontendUseCertificateOcspUpdate] = UNSET
    sctl: Union[Unset, str] = UNSET
    sigalgs: Union[Unset, str] = UNSET
    ssl_max_ver: Union[Unset, SSLFrontendUseCertificateSslMaxVer] = UNSET
    ssl_min_ver: Union[Unset, SSLFrontendUseCertificateSslMinVer] = UNSET
    verify: Union[Unset, SSLFrontendUseCertificateVerify] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        certificate = self.certificate

        allow_0rtt = self.allow_0rtt

        alpn = self.alpn

        ca_file = self.ca_file

        ciphers = self.ciphers

        ciphersuites = self.ciphersuites

        client_sigalgs = self.client_sigalgs

        crl_file = self.crl_file

        curves = self.curves

        ecdhe = self.ecdhe

        issuer = self.issuer

        key = self.key

        metadata = self.metadata

        no_alpn = self.no_alpn

        no_ca_names = self.no_ca_names

        npn = self.npn

        ocsp = self.ocsp

        ocsp_update: Union[Unset, str] = UNSET
        if not isinstance(self.ocsp_update, Unset):
            ocsp_update = self.ocsp_update.value

        sctl = self.sctl

        sigalgs = self.sigalgs

        ssl_max_ver: Union[Unset, str] = UNSET
        if not isinstance(self.ssl_max_ver, Unset):
            ssl_max_ver = self.ssl_max_ver.value

        ssl_min_ver: Union[Unset, str] = UNSET
        if not isinstance(self.ssl_min_ver, Unset):
            ssl_min_ver = self.ssl_min_ver.value

        verify: Union[Unset, str] = UNSET
        if not isinstance(self.verify, Unset):
            verify = self.verify.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "certificate": certificate,
            }
        )
        if allow_0rtt is not UNSET:
            field_dict["allow_0rtt"] = allow_0rtt
        if alpn is not UNSET:
            field_dict["alpn"] = alpn
        if ca_file is not UNSET:
            field_dict["ca_file"] = ca_file
        if ciphers is not UNSET:
            field_dict["ciphers"] = ciphers
        if ciphersuites is not UNSET:
            field_dict["ciphersuites"] = ciphersuites
        if client_sigalgs is not UNSET:
            field_dict["client_sigalgs"] = client_sigalgs
        if crl_file is not UNSET:
            field_dict["crl_file"] = crl_file
        if curves is not UNSET:
            field_dict["curves"] = curves
        if ecdhe is not UNSET:
            field_dict["ecdhe"] = ecdhe
        if issuer is not UNSET:
            field_dict["issuer"] = issuer
        if key is not UNSET:
            field_dict["key"] = key
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if no_alpn is not UNSET:
            field_dict["no_alpn"] = no_alpn
        if no_ca_names is not UNSET:
            field_dict["no_ca_names"] = no_ca_names
        if npn is not UNSET:
            field_dict["npn"] = npn
        if ocsp is not UNSET:
            field_dict["ocsp"] = ocsp
        if ocsp_update is not UNSET:
            field_dict["ocsp_update"] = ocsp_update
        if sctl is not UNSET:
            field_dict["sctl"] = sctl
        if sigalgs is not UNSET:
            field_dict["sigalgs"] = sigalgs
        if ssl_max_ver is not UNSET:
            field_dict["ssl_max_ver"] = ssl_max_ver
        if ssl_min_ver is not UNSET:
            field_dict["ssl_min_ver"] = ssl_min_ver
        if verify is not UNSET:
            field_dict["verify"] = verify

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        certificate = d.pop("certificate")

        allow_0rtt = d.pop("allow_0rtt", UNSET)

        alpn = d.pop("alpn", UNSET)

        ca_file = d.pop("ca_file", UNSET)

        ciphers = d.pop("ciphers", UNSET)

        ciphersuites = d.pop("ciphersuites", UNSET)

        client_sigalgs = d.pop("client_sigalgs", UNSET)

        crl_file = d.pop("crl_file", UNSET)

        curves = d.pop("curves", UNSET)

        ecdhe = d.pop("ecdhe", UNSET)

        issuer = d.pop("issuer", UNSET)

        key = d.pop("key", UNSET)

        metadata = d.pop("metadata", UNSET)

        no_alpn = d.pop("no_alpn", UNSET)

        no_ca_names = d.pop("no_ca_names", UNSET)

        npn = d.pop("npn", UNSET)

        ocsp = d.pop("ocsp", UNSET)

        _ocsp_update = d.pop("ocsp_update", UNSET)
        ocsp_update: Union[Unset, SSLFrontendUseCertificateOcspUpdate]
        if isinstance(_ocsp_update, Unset):
            ocsp_update = UNSET
        else:
            ocsp_update = SSLFrontendUseCertificateOcspUpdate(_ocsp_update)

        sctl = d.pop("sctl", UNSET)

        sigalgs = d.pop("sigalgs", UNSET)

        _ssl_max_ver = d.pop("ssl_max_ver", UNSET)
        ssl_max_ver: Union[Unset, SSLFrontendUseCertificateSslMaxVer]
        if isinstance(_ssl_max_ver, Unset):
            ssl_max_ver = UNSET
        else:
            ssl_max_ver = SSLFrontendUseCertificateSslMaxVer(_ssl_max_ver)

        _ssl_min_ver = d.pop("ssl_min_ver", UNSET)
        ssl_min_ver: Union[Unset, SSLFrontendUseCertificateSslMinVer]
        if isinstance(_ssl_min_ver, Unset):
            ssl_min_ver = UNSET
        else:
            ssl_min_ver = SSLFrontendUseCertificateSslMinVer(_ssl_min_ver)

        _verify = d.pop("verify", UNSET)
        verify: Union[Unset, SSLFrontendUseCertificateVerify]
        if isinstance(_verify, Unset):
            verify = UNSET
        else:
            verify = SSLFrontendUseCertificateVerify(_verify)

        ssl_frontend_use_certificate = cls(
            certificate=certificate,
            allow_0rtt=allow_0rtt,
            alpn=alpn,
            ca_file=ca_file,
            ciphers=ciphers,
            ciphersuites=ciphersuites,
            client_sigalgs=client_sigalgs,
            crl_file=crl_file,
            curves=curves,
            ecdhe=ecdhe,
            issuer=issuer,
            key=key,
            metadata=metadata,
            no_alpn=no_alpn,
            no_ca_names=no_ca_names,
            npn=npn,
            ocsp=ocsp,
            ocsp_update=ocsp_update,
            sctl=sctl,
            sigalgs=sigalgs,
            ssl_max_ver=ssl_max_ver,
            ssl_min_ver=ssl_min_ver,
            verify=verify,
        )

        ssl_frontend_use_certificate.additional_properties = d
        return ssl_frontend_use_certificate

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
