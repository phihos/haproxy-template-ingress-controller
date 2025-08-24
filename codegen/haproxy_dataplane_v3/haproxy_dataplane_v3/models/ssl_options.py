from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.ssl_options_acme_scheduler import SslOptionsAcmeScheduler
from ..models.ssl_options_mode_async import SslOptionsModeAsync
from ..models.ssl_options_server_verify import SslOptionsServerVerify
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.ssl_options_engines_item import SslOptionsEnginesItem


T = TypeVar("T", bound="SslOptions")


@_attrs_define
class SslOptions:
    """
    Attributes:
        acme_scheduler (Union[Unset, SslOptionsAcmeScheduler]):
        ca_base (Union[Unset, str]):
        crt_base (Union[Unset, str]):
        default_bind_ciphers (Union[Unset, str]):
        default_bind_ciphersuites (Union[Unset, str]):
        default_bind_client_sigalgs (Union[Unset, str]):
        default_bind_curves (Union[Unset, str]):
        default_bind_options (Union[Unset, str]):
        default_bind_sigalgs (Union[Unset, str]):
        default_server_ciphers (Union[Unset, str]):
        default_server_ciphersuites (Union[Unset, str]):
        default_server_client_sigalgs (Union[Unset, str]):
        default_server_curves (Union[Unset, str]):
        default_server_options (Union[Unset, str]):
        default_server_sigalgs (Union[Unset, str]):
        dh_param_file (Union[Unset, str]):
        engines (Union[Unset, list['SslOptionsEnginesItem']]):
        issuers_chain_path (Union[Unset, str]):
        load_extra_files (Union[Unset, str]):
        maxsslconn (Union[Unset, int]):
        maxsslrate (Union[Unset, int]):
        mode_async (Union[Unset, SslOptionsModeAsync]):
        propquery (Union[Unset, str]):
        provider (Union[Unset, str]):
        provider_path (Union[Unset, str]):
        security_level (Union[None, Unset, int]):
        server_verify (Union[Unset, SslOptionsServerVerify]):
        skip_self_issued_ca (Union[Unset, bool]):
    """

    acme_scheduler: Union[Unset, SslOptionsAcmeScheduler] = UNSET
    ca_base: Union[Unset, str] = UNSET
    crt_base: Union[Unset, str] = UNSET
    default_bind_ciphers: Union[Unset, str] = UNSET
    default_bind_ciphersuites: Union[Unset, str] = UNSET
    default_bind_client_sigalgs: Union[Unset, str] = UNSET
    default_bind_curves: Union[Unset, str] = UNSET
    default_bind_options: Union[Unset, str] = UNSET
    default_bind_sigalgs: Union[Unset, str] = UNSET
    default_server_ciphers: Union[Unset, str] = UNSET
    default_server_ciphersuites: Union[Unset, str] = UNSET
    default_server_client_sigalgs: Union[Unset, str] = UNSET
    default_server_curves: Union[Unset, str] = UNSET
    default_server_options: Union[Unset, str] = UNSET
    default_server_sigalgs: Union[Unset, str] = UNSET
    dh_param_file: Union[Unset, str] = UNSET
    engines: Union[Unset, list["SslOptionsEnginesItem"]] = UNSET
    issuers_chain_path: Union[Unset, str] = UNSET
    load_extra_files: Union[Unset, str] = UNSET
    maxsslconn: Union[Unset, int] = UNSET
    maxsslrate: Union[Unset, int] = UNSET
    mode_async: Union[Unset, SslOptionsModeAsync] = UNSET
    propquery: Union[Unset, str] = UNSET
    provider: Union[Unset, str] = UNSET
    provider_path: Union[Unset, str] = UNSET
    security_level: Union[None, Unset, int] = UNSET
    server_verify: Union[Unset, SslOptionsServerVerify] = UNSET
    skip_self_issued_ca: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        acme_scheduler: Union[Unset, str] = UNSET
        if not isinstance(self.acme_scheduler, Unset):
            acme_scheduler = self.acme_scheduler.value

        ca_base = self.ca_base

        crt_base = self.crt_base

        default_bind_ciphers = self.default_bind_ciphers

        default_bind_ciphersuites = self.default_bind_ciphersuites

        default_bind_client_sigalgs = self.default_bind_client_sigalgs

        default_bind_curves = self.default_bind_curves

        default_bind_options = self.default_bind_options

        default_bind_sigalgs = self.default_bind_sigalgs

        default_server_ciphers = self.default_server_ciphers

        default_server_ciphersuites = self.default_server_ciphersuites

        default_server_client_sigalgs = self.default_server_client_sigalgs

        default_server_curves = self.default_server_curves

        default_server_options = self.default_server_options

        default_server_sigalgs = self.default_server_sigalgs

        dh_param_file = self.dh_param_file

        engines: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.engines, Unset):
            engines = []
            for engines_item_data in self.engines:
                engines_item = engines_item_data.to_dict()
                engines.append(engines_item)

        issuers_chain_path = self.issuers_chain_path

        load_extra_files = self.load_extra_files

        maxsslconn = self.maxsslconn

        maxsslrate = self.maxsslrate

        mode_async: Union[Unset, str] = UNSET
        if not isinstance(self.mode_async, Unset):
            mode_async = self.mode_async.value

        propquery = self.propquery

        provider = self.provider

        provider_path = self.provider_path

        security_level: Union[None, Unset, int]
        if isinstance(self.security_level, Unset):
            security_level = UNSET
        else:
            security_level = self.security_level

        server_verify: Union[Unset, str] = UNSET
        if not isinstance(self.server_verify, Unset):
            server_verify = self.server_verify.value

        skip_self_issued_ca = self.skip_self_issued_ca

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if acme_scheduler is not UNSET:
            field_dict["acme_scheduler"] = acme_scheduler
        if ca_base is not UNSET:
            field_dict["ca_base"] = ca_base
        if crt_base is not UNSET:
            field_dict["crt_base"] = crt_base
        if default_bind_ciphers is not UNSET:
            field_dict["default_bind_ciphers"] = default_bind_ciphers
        if default_bind_ciphersuites is not UNSET:
            field_dict["default_bind_ciphersuites"] = default_bind_ciphersuites
        if default_bind_client_sigalgs is not UNSET:
            field_dict["default_bind_client_sigalgs"] = default_bind_client_sigalgs
        if default_bind_curves is not UNSET:
            field_dict["default_bind_curves"] = default_bind_curves
        if default_bind_options is not UNSET:
            field_dict["default_bind_options"] = default_bind_options
        if default_bind_sigalgs is not UNSET:
            field_dict["default_bind_sigalgs"] = default_bind_sigalgs
        if default_server_ciphers is not UNSET:
            field_dict["default_server_ciphers"] = default_server_ciphers
        if default_server_ciphersuites is not UNSET:
            field_dict["default_server_ciphersuites"] = default_server_ciphersuites
        if default_server_client_sigalgs is not UNSET:
            field_dict["default_server_client_sigalgs"] = default_server_client_sigalgs
        if default_server_curves is not UNSET:
            field_dict["default_server_curves"] = default_server_curves
        if default_server_options is not UNSET:
            field_dict["default_server_options"] = default_server_options
        if default_server_sigalgs is not UNSET:
            field_dict["default_server_sigalgs"] = default_server_sigalgs
        if dh_param_file is not UNSET:
            field_dict["dh_param_file"] = dh_param_file
        if engines is not UNSET:
            field_dict["engines"] = engines
        if issuers_chain_path is not UNSET:
            field_dict["issuers_chain_path"] = issuers_chain_path
        if load_extra_files is not UNSET:
            field_dict["load_extra_files"] = load_extra_files
        if maxsslconn is not UNSET:
            field_dict["maxsslconn"] = maxsslconn
        if maxsslrate is not UNSET:
            field_dict["maxsslrate"] = maxsslrate
        if mode_async is not UNSET:
            field_dict["mode_async"] = mode_async
        if propquery is not UNSET:
            field_dict["propquery"] = propquery
        if provider is not UNSET:
            field_dict["provider"] = provider
        if provider_path is not UNSET:
            field_dict["provider_path"] = provider_path
        if security_level is not UNSET:
            field_dict["security_level"] = security_level
        if server_verify is not UNSET:
            field_dict["server_verify"] = server_verify
        if skip_self_issued_ca is not UNSET:
            field_dict["skip_self_issued_ca"] = skip_self_issued_ca

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.ssl_options_engines_item import SslOptionsEnginesItem

        d = dict(src_dict)
        _acme_scheduler = d.pop("acme_scheduler", UNSET)
        acme_scheduler: Union[Unset, SslOptionsAcmeScheduler]
        if isinstance(_acme_scheduler, Unset):
            acme_scheduler = UNSET
        else:
            acme_scheduler = SslOptionsAcmeScheduler(_acme_scheduler)

        ca_base = d.pop("ca_base", UNSET)

        crt_base = d.pop("crt_base", UNSET)

        default_bind_ciphers = d.pop("default_bind_ciphers", UNSET)

        default_bind_ciphersuites = d.pop("default_bind_ciphersuites", UNSET)

        default_bind_client_sigalgs = d.pop("default_bind_client_sigalgs", UNSET)

        default_bind_curves = d.pop("default_bind_curves", UNSET)

        default_bind_options = d.pop("default_bind_options", UNSET)

        default_bind_sigalgs = d.pop("default_bind_sigalgs", UNSET)

        default_server_ciphers = d.pop("default_server_ciphers", UNSET)

        default_server_ciphersuites = d.pop("default_server_ciphersuites", UNSET)

        default_server_client_sigalgs = d.pop("default_server_client_sigalgs", UNSET)

        default_server_curves = d.pop("default_server_curves", UNSET)

        default_server_options = d.pop("default_server_options", UNSET)

        default_server_sigalgs = d.pop("default_server_sigalgs", UNSET)

        dh_param_file = d.pop("dh_param_file", UNSET)

        engines = []
        _engines = d.pop("engines", UNSET)
        for engines_item_data in _engines or []:
            engines_item = SslOptionsEnginesItem.from_dict(engines_item_data)

            engines.append(engines_item)

        issuers_chain_path = d.pop("issuers_chain_path", UNSET)

        load_extra_files = d.pop("load_extra_files", UNSET)

        maxsslconn = d.pop("maxsslconn", UNSET)

        maxsslrate = d.pop("maxsslrate", UNSET)

        _mode_async = d.pop("mode_async", UNSET)
        mode_async: Union[Unset, SslOptionsModeAsync]
        if isinstance(_mode_async, Unset):
            mode_async = UNSET
        else:
            mode_async = SslOptionsModeAsync(_mode_async)

        propquery = d.pop("propquery", UNSET)

        provider = d.pop("provider", UNSET)

        provider_path = d.pop("provider_path", UNSET)

        def _parse_security_level(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        security_level = _parse_security_level(d.pop("security_level", UNSET))

        _server_verify = d.pop("server_verify", UNSET)
        server_verify: Union[Unset, SslOptionsServerVerify]
        if isinstance(_server_verify, Unset):
            server_verify = UNSET
        else:
            server_verify = SslOptionsServerVerify(_server_verify)

        skip_self_issued_ca = d.pop("skip_self_issued_ca", UNSET)

        ssl_options = cls(
            acme_scheduler=acme_scheduler,
            ca_base=ca_base,
            crt_base=crt_base,
            default_bind_ciphers=default_bind_ciphers,
            default_bind_ciphersuites=default_bind_ciphersuites,
            default_bind_client_sigalgs=default_bind_client_sigalgs,
            default_bind_curves=default_bind_curves,
            default_bind_options=default_bind_options,
            default_bind_sigalgs=default_bind_sigalgs,
            default_server_ciphers=default_server_ciphers,
            default_server_ciphersuites=default_server_ciphersuites,
            default_server_client_sigalgs=default_server_client_sigalgs,
            default_server_curves=default_server_curves,
            default_server_options=default_server_options,
            default_server_sigalgs=default_server_sigalgs,
            dh_param_file=dh_param_file,
            engines=engines,
            issuers_chain_path=issuers_chain_path,
            load_extra_files=load_extra_files,
            maxsslconn=maxsslconn,
            maxsslrate=maxsslrate,
            mode_async=mode_async,
            propquery=propquery,
            provider=provider,
            provider_path=provider_path,
            security_level=security_level,
            server_verify=server_verify,
            skip_self_issued_ca=skip_self_issued_ca,
        )

        ssl_options.additional_properties = d
        return ssl_options

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
