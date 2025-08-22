import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="SSLFile")


@_attrs_define
class SSLFile:
    """A file containing one or more SSL/TLS certificates and keys

    Attributes:
        algorithm (Union[Unset, str]):
        authority_key_id (Union[Unset, str]):
        chain_issuer (Union[Unset, str]):
        chain_subject (Union[Unset, str]):
        description (Union[Unset, str]):
        domains (Union[Unset, str]):
        file (Union[Unset, str]):
        ip_addresses (Union[Unset, str]):
        issuers (Union[Unset, str]):
        not_after (Union[None, Unset, datetime.datetime]):
        not_before (Union[None, Unset, datetime.datetime]):
        serial (Union[Unset, str]):
        sha1_finger_print (Union[Unset, str]):
        sha256_finger_print (Union[Unset, str]):
        size (Union[None, Unset, int]): File size in bytes.
        status (Union[Unset, str]): Only set when using the runtime API.
        storage_name (Union[Unset, str]):
        subject (Union[Unset, str]):
        subject_alternative_names (Union[Unset, str]):
        subject_key_id (Union[Unset, str]):
    """

    algorithm: Union[Unset, str] = UNSET
    authority_key_id: Union[Unset, str] = UNSET
    chain_issuer: Union[Unset, str] = UNSET
    chain_subject: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    domains: Union[Unset, str] = UNSET
    file: Union[Unset, str] = UNSET
    ip_addresses: Union[Unset, str] = UNSET
    issuers: Union[Unset, str] = UNSET
    not_after: Union[None, Unset, datetime.datetime] = UNSET
    not_before: Union[None, Unset, datetime.datetime] = UNSET
    serial: Union[Unset, str] = UNSET
    sha1_finger_print: Union[Unset, str] = UNSET
    sha256_finger_print: Union[Unset, str] = UNSET
    size: Union[None, Unset, int] = UNSET
    status: Union[Unset, str] = UNSET
    storage_name: Union[Unset, str] = UNSET
    subject: Union[Unset, str] = UNSET
    subject_alternative_names: Union[Unset, str] = UNSET
    subject_key_id: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        algorithm = self.algorithm

        authority_key_id = self.authority_key_id

        chain_issuer = self.chain_issuer

        chain_subject = self.chain_subject

        description = self.description

        domains = self.domains

        file = self.file

        ip_addresses = self.ip_addresses

        issuers = self.issuers

        not_after: Union[None, Unset, str]
        if isinstance(self.not_after, Unset):
            not_after = UNSET
        elif isinstance(self.not_after, datetime.datetime):
            not_after = self.not_after.isoformat()
        else:
            not_after = self.not_after

        not_before: Union[None, Unset, str]
        if isinstance(self.not_before, Unset):
            not_before = UNSET
        elif isinstance(self.not_before, datetime.datetime):
            not_before = self.not_before.isoformat()
        else:
            not_before = self.not_before

        serial = self.serial

        sha1_finger_print = self.sha1_finger_print

        sha256_finger_print = self.sha256_finger_print

        size: Union[None, Unset, int]
        if isinstance(self.size, Unset):
            size = UNSET
        else:
            size = self.size

        status = self.status

        storage_name = self.storage_name

        subject = self.subject

        subject_alternative_names = self.subject_alternative_names

        subject_key_id = self.subject_key_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if algorithm is not UNSET:
            field_dict["algorithm"] = algorithm
        if authority_key_id is not UNSET:
            field_dict["authority_key_id"] = authority_key_id
        if chain_issuer is not UNSET:
            field_dict["chain_issuer"] = chain_issuer
        if chain_subject is not UNSET:
            field_dict["chain_subject"] = chain_subject
        if description is not UNSET:
            field_dict["description"] = description
        if domains is not UNSET:
            field_dict["domains"] = domains
        if file is not UNSET:
            field_dict["file"] = file
        if ip_addresses is not UNSET:
            field_dict["ip_addresses"] = ip_addresses
        if issuers is not UNSET:
            field_dict["issuers"] = issuers
        if not_after is not UNSET:
            field_dict["not_after"] = not_after
        if not_before is not UNSET:
            field_dict["not_before"] = not_before
        if serial is not UNSET:
            field_dict["serial"] = serial
        if sha1_finger_print is not UNSET:
            field_dict["sha1_finger_print"] = sha1_finger_print
        if sha256_finger_print is not UNSET:
            field_dict["sha256_finger_print"] = sha256_finger_print
        if size is not UNSET:
            field_dict["size"] = size
        if status is not UNSET:
            field_dict["status"] = status
        if storage_name is not UNSET:
            field_dict["storage_name"] = storage_name
        if subject is not UNSET:
            field_dict["subject"] = subject
        if subject_alternative_names is not UNSET:
            field_dict["subject_alternative_names"] = subject_alternative_names
        if subject_key_id is not UNSET:
            field_dict["subject_key_id"] = subject_key_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        algorithm = d.pop("algorithm", UNSET)

        authority_key_id = d.pop("authority_key_id", UNSET)

        chain_issuer = d.pop("chain_issuer", UNSET)

        chain_subject = d.pop("chain_subject", UNSET)

        description = d.pop("description", UNSET)

        domains = d.pop("domains", UNSET)

        file = d.pop("file", UNSET)

        ip_addresses = d.pop("ip_addresses", UNSET)

        issuers = d.pop("issuers", UNSET)

        def _parse_not_after(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                not_after_type_0 = isoparse(data)

                return not_after_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        not_after = _parse_not_after(d.pop("not_after", UNSET))

        def _parse_not_before(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                not_before_type_0 = isoparse(data)

                return not_before_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        not_before = _parse_not_before(d.pop("not_before", UNSET))

        serial = d.pop("serial", UNSET)

        sha1_finger_print = d.pop("sha1_finger_print", UNSET)

        sha256_finger_print = d.pop("sha256_finger_print", UNSET)

        def _parse_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        size = _parse_size(d.pop("size", UNSET))

        status = d.pop("status", UNSET)

        storage_name = d.pop("storage_name", UNSET)

        subject = d.pop("subject", UNSET)

        subject_alternative_names = d.pop("subject_alternative_names", UNSET)

        subject_key_id = d.pop("subject_key_id", UNSET)

        ssl_file = cls(
            algorithm=algorithm,
            authority_key_id=authority_key_id,
            chain_issuer=chain_issuer,
            chain_subject=chain_subject,
            description=description,
            domains=domains,
            file=file,
            ip_addresses=ip_addresses,
            issuers=issuers,
            not_after=not_after,
            not_before=not_before,
            serial=serial,
            sha1_finger_print=sha1_finger_print,
            sha256_finger_print=sha256_finger_print,
            size=size,
            status=status,
            storage_name=storage_name,
            subject=subject,
            subject_alternative_names=subject_alternative_names,
            subject_key_id=subject_key_id,
        )

        ssl_file.additional_properties = d
        return ssl_file

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
