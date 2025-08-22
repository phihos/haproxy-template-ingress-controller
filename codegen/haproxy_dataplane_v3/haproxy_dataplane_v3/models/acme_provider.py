from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.acme_provider_challenge import ACMEProviderChallenge
from ..models.acme_provider_keytype import ACMEProviderKeytype
from ..types import UNSET, Unset

T = TypeVar("T", bound="ACMEProvider")


@_attrs_define
class ACMEProvider:
    """Define an ACME provider to generate certificates automatically

    Attributes:
        directory (str): URL to the ACME provider's directory. For example:
            https://acme-staging-v02.api.letsencrypt.org/directory
        name (str): ACME provider's name
        account_key (Union[Unset, str]): Path where the the ACME account key is stored
        bits (Union[None, Unset, int]): Number of bits to generate an RSA certificate
        challenge (Union[Unset, ACMEProviderChallenge]): ACME challenge type. Only HTTP-01 and DNS-01 are supported.
        contact (Union[Unset, str]): Contact email for the ACME account
        curves (Union[Unset, str]): Curves used with the ECDSA key type
        keytype (Union[Unset, ACMEProviderKeytype]): Type of key to generate
        map_ (Union[Unset, str]): The map which will be used to store the ACME token (key) and thumbprint
        metadata (Union[Unset, Any]):
    """

    directory: str
    name: str
    account_key: Union[Unset, str] = UNSET
    bits: Union[None, Unset, int] = UNSET
    challenge: Union[Unset, ACMEProviderChallenge] = UNSET
    contact: Union[Unset, str] = UNSET
    curves: Union[Unset, str] = UNSET
    keytype: Union[Unset, ACMEProviderKeytype] = UNSET
    map_: Union[Unset, str] = UNSET
    metadata: Union[Unset, Any] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        directory = self.directory

        name = self.name

        account_key = self.account_key

        bits: Union[None, Unset, int]
        if isinstance(self.bits, Unset):
            bits = UNSET
        else:
            bits = self.bits

        challenge: Union[Unset, str] = UNSET
        if not isinstance(self.challenge, Unset):
            challenge = self.challenge.value

        contact = self.contact

        curves = self.curves

        keytype: Union[Unset, str] = UNSET
        if not isinstance(self.keytype, Unset):
            keytype = self.keytype.value

        map_ = self.map_

        metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "directory": directory,
                "name": name,
            }
        )
        if account_key is not UNSET:
            field_dict["account_key"] = account_key
        if bits is not UNSET:
            field_dict["bits"] = bits
        if challenge is not UNSET:
            field_dict["challenge"] = challenge
        if contact is not UNSET:
            field_dict["contact"] = contact
        if curves is not UNSET:
            field_dict["curves"] = curves
        if keytype is not UNSET:
            field_dict["keytype"] = keytype
        if map_ is not UNSET:
            field_dict["map"] = map_
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        directory = d.pop("directory")

        name = d.pop("name")

        account_key = d.pop("account_key", UNSET)

        def _parse_bits(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        bits = _parse_bits(d.pop("bits", UNSET))

        _challenge = d.pop("challenge", UNSET)
        challenge: Union[Unset, ACMEProviderChallenge]
        if isinstance(_challenge, Unset):
            challenge = UNSET
        else:
            challenge = ACMEProviderChallenge(_challenge)

        contact = d.pop("contact", UNSET)

        curves = d.pop("curves", UNSET)

        _keytype = d.pop("keytype", UNSET)
        keytype: Union[Unset, ACMEProviderKeytype]
        if isinstance(_keytype, Unset):
            keytype = UNSET
        else:
            keytype = ACMEProviderKeytype(_keytype)

        map_ = d.pop("map", UNSET)

        metadata = d.pop("metadata", UNSET)

        acme_provider = cls(
            directory=directory,
            name=name,
            account_key=account_key,
            bits=bits,
            challenge=challenge,
            contact=contact,
            curves=curves,
            keytype=keytype,
            map_=map_,
            metadata=metadata,
        )

        acme_provider.additional_properties = d
        return acme_provider

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
