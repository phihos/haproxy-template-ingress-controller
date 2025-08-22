from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ResolverBase")


@_attrs_define
class ResolverBase:
    """Runtime DNS configuration

    Attributes:
        name (str):
        accepted_payload_size (Union[Unset, int]):
        hold_nx (Union[None, Unset, int]):
        hold_obsolete (Union[None, Unset, int]):
        hold_other (Union[None, Unset, int]):
        hold_refused (Union[None, Unset, int]):
        hold_timeout (Union[None, Unset, int]):
        hold_valid (Union[None, Unset, int]):
        metadata (Union[Unset, Any]):
        parse_resolv_conf (Union[Unset, bool]):
        resolve_retries (Union[Unset, int]):
        timeout_resolve (Union[Unset, int]):
        timeout_retry (Union[Unset, int]):
    """

    name: str
    accepted_payload_size: Union[Unset, int] = UNSET
    hold_nx: Union[None, Unset, int] = UNSET
    hold_obsolete: Union[None, Unset, int] = UNSET
    hold_other: Union[None, Unset, int] = UNSET
    hold_refused: Union[None, Unset, int] = UNSET
    hold_timeout: Union[None, Unset, int] = UNSET
    hold_valid: Union[None, Unset, int] = UNSET
    metadata: Union[Unset, Any] = UNSET
    parse_resolv_conf: Union[Unset, bool] = UNSET
    resolve_retries: Union[Unset, int] = UNSET
    timeout_resolve: Union[Unset, int] = UNSET
    timeout_retry: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        accepted_payload_size = self.accepted_payload_size

        hold_nx: Union[None, Unset, int]
        if isinstance(self.hold_nx, Unset):
            hold_nx = UNSET
        else:
            hold_nx = self.hold_nx

        hold_obsolete: Union[None, Unset, int]
        if isinstance(self.hold_obsolete, Unset):
            hold_obsolete = UNSET
        else:
            hold_obsolete = self.hold_obsolete

        hold_other: Union[None, Unset, int]
        if isinstance(self.hold_other, Unset):
            hold_other = UNSET
        else:
            hold_other = self.hold_other

        hold_refused: Union[None, Unset, int]
        if isinstance(self.hold_refused, Unset):
            hold_refused = UNSET
        else:
            hold_refused = self.hold_refused

        hold_timeout: Union[None, Unset, int]
        if isinstance(self.hold_timeout, Unset):
            hold_timeout = UNSET
        else:
            hold_timeout = self.hold_timeout

        hold_valid: Union[None, Unset, int]
        if isinstance(self.hold_valid, Unset):
            hold_valid = UNSET
        else:
            hold_valid = self.hold_valid

        metadata = self.metadata

        parse_resolv_conf = self.parse_resolv_conf

        resolve_retries = self.resolve_retries

        timeout_resolve = self.timeout_resolve

        timeout_retry = self.timeout_retry

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if accepted_payload_size is not UNSET:
            field_dict["accepted_payload_size"] = accepted_payload_size
        if hold_nx is not UNSET:
            field_dict["hold_nx"] = hold_nx
        if hold_obsolete is not UNSET:
            field_dict["hold_obsolete"] = hold_obsolete
        if hold_other is not UNSET:
            field_dict["hold_other"] = hold_other
        if hold_refused is not UNSET:
            field_dict["hold_refused"] = hold_refused
        if hold_timeout is not UNSET:
            field_dict["hold_timeout"] = hold_timeout
        if hold_valid is not UNSET:
            field_dict["hold_valid"] = hold_valid
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if parse_resolv_conf is not UNSET:
            field_dict["parse-resolv-conf"] = parse_resolv_conf
        if resolve_retries is not UNSET:
            field_dict["resolve_retries"] = resolve_retries
        if timeout_resolve is not UNSET:
            field_dict["timeout_resolve"] = timeout_resolve
        if timeout_retry is not UNSET:
            field_dict["timeout_retry"] = timeout_retry

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        accepted_payload_size = d.pop("accepted_payload_size", UNSET)

        def _parse_hold_nx(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        hold_nx = _parse_hold_nx(d.pop("hold_nx", UNSET))

        def _parse_hold_obsolete(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        hold_obsolete = _parse_hold_obsolete(d.pop("hold_obsolete", UNSET))

        def _parse_hold_other(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        hold_other = _parse_hold_other(d.pop("hold_other", UNSET))

        def _parse_hold_refused(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        hold_refused = _parse_hold_refused(d.pop("hold_refused", UNSET))

        def _parse_hold_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        hold_timeout = _parse_hold_timeout(d.pop("hold_timeout", UNSET))

        def _parse_hold_valid(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        hold_valid = _parse_hold_valid(d.pop("hold_valid", UNSET))

        metadata = d.pop("metadata", UNSET)

        parse_resolv_conf = d.pop("parse-resolv-conf", UNSET)

        resolve_retries = d.pop("resolve_retries", UNSET)

        timeout_resolve = d.pop("timeout_resolve", UNSET)

        timeout_retry = d.pop("timeout_retry", UNSET)

        resolver_base = cls(
            name=name,
            accepted_payload_size=accepted_payload_size,
            hold_nx=hold_nx,
            hold_obsolete=hold_obsolete,
            hold_other=hold_other,
            hold_refused=hold_refused,
            hold_timeout=hold_timeout,
            hold_valid=hold_valid,
            metadata=metadata,
            parse_resolv_conf=parse_resolv_conf,
            resolve_retries=resolve_retries,
            timeout_resolve=timeout_resolve,
            timeout_retry=timeout_retry,
        )

        resolver_base.additional_properties = d
        return resolver_base

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
