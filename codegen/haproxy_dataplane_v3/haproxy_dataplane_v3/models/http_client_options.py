from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.http_client_options_resolvers_disabled import HttpClientOptionsResolversDisabled
from ..models.http_client_options_resolvers_prefer import HttpClientOptionsResolversPrefer
from ..models.http_client_options_ssl_verify import HttpClientOptionsSslVerify
from ..types import UNSET, Unset

T = TypeVar("T", bound="HttpClientOptions")


@_attrs_define
class HttpClientOptions:
    """
    Attributes:
        resolvers_disabled (Union[Unset, HttpClientOptionsResolversDisabled]):
        resolvers_id (Union[Unset, str]):
        resolvers_prefer (Union[Unset, HttpClientOptionsResolversPrefer]):
        retries (Union[Unset, int]):
        ssl_ca_file (Union[Unset, str]):
        ssl_verify (Union[Unset, HttpClientOptionsSslVerify]):
        timeout_connect (Union[None, Unset, int]):
    """

    resolvers_disabled: Union[Unset, HttpClientOptionsResolversDisabled] = UNSET
    resolvers_id: Union[Unset, str] = UNSET
    resolvers_prefer: Union[Unset, HttpClientOptionsResolversPrefer] = UNSET
    retries: Union[Unset, int] = UNSET
    ssl_ca_file: Union[Unset, str] = UNSET
    ssl_verify: Union[Unset, HttpClientOptionsSslVerify] = UNSET
    timeout_connect: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        resolvers_disabled: Union[Unset, str] = UNSET
        if not isinstance(self.resolvers_disabled, Unset):
            resolvers_disabled = self.resolvers_disabled.value

        resolvers_id = self.resolvers_id

        resolvers_prefer: Union[Unset, str] = UNSET
        if not isinstance(self.resolvers_prefer, Unset):
            resolvers_prefer = self.resolvers_prefer.value

        retries = self.retries

        ssl_ca_file = self.ssl_ca_file

        ssl_verify: Union[Unset, str] = UNSET
        if not isinstance(self.ssl_verify, Unset):
            ssl_verify = self.ssl_verify.value

        timeout_connect: Union[None, Unset, int]
        if isinstance(self.timeout_connect, Unset):
            timeout_connect = UNSET
        else:
            timeout_connect = self.timeout_connect

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if resolvers_disabled is not UNSET:
            field_dict["resolvers_disabled"] = resolvers_disabled
        if resolvers_id is not UNSET:
            field_dict["resolvers_id"] = resolvers_id
        if resolvers_prefer is not UNSET:
            field_dict["resolvers_prefer"] = resolvers_prefer
        if retries is not UNSET:
            field_dict["retries"] = retries
        if ssl_ca_file is not UNSET:
            field_dict["ssl_ca_file"] = ssl_ca_file
        if ssl_verify is not UNSET:
            field_dict["ssl_verify"] = ssl_verify
        if timeout_connect is not UNSET:
            field_dict["timeout_connect"] = timeout_connect

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _resolvers_disabled = d.pop("resolvers_disabled", UNSET)
        resolvers_disabled: Union[Unset, HttpClientOptionsResolversDisabled]
        if isinstance(_resolvers_disabled, Unset):
            resolvers_disabled = UNSET
        else:
            resolvers_disabled = HttpClientOptionsResolversDisabled(_resolvers_disabled)

        resolvers_id = d.pop("resolvers_id", UNSET)

        _resolvers_prefer = d.pop("resolvers_prefer", UNSET)
        resolvers_prefer: Union[Unset, HttpClientOptionsResolversPrefer]
        if isinstance(_resolvers_prefer, Unset):
            resolvers_prefer = UNSET
        else:
            resolvers_prefer = HttpClientOptionsResolversPrefer(_resolvers_prefer)

        retries = d.pop("retries", UNSET)

        ssl_ca_file = d.pop("ssl_ca_file", UNSET)

        _ssl_verify = d.pop("ssl_verify", UNSET)
        ssl_verify: Union[Unset, HttpClientOptionsSslVerify]
        if isinstance(_ssl_verify, Unset):
            ssl_verify = UNSET
        else:
            ssl_verify = HttpClientOptionsSslVerify(_ssl_verify)

        def _parse_timeout_connect(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        timeout_connect = _parse_timeout_connect(d.pop("timeout_connect", UNSET))

        http_client_options = cls(
            resolvers_disabled=resolvers_disabled,
            resolvers_id=resolvers_id,
            resolvers_prefer=resolvers_prefer,
            retries=retries,
            ssl_ca_file=ssl_ca_file,
            ssl_verify=ssl_verify,
            timeout_connect=timeout_connect,
        )

        http_client_options.additional_properties = d
        return http_client_options

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
