from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PeerEntry")


@_attrs_define
class PeerEntry:
    """Peer Entry from peers table

    Attributes:
        address (str):
        name (str):
        port (Union[None, int]):
        metadata (Union[Unset, Any]):
        shard (Union[Unset, int]):
    """

    address: str
    name: str
    port: Union[None, int]
    metadata: Union[Unset, Any] = UNSET
    shard: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        address = self.address

        name = self.name

        port: Union[None, int]
        port = self.port

        metadata = self.metadata

        shard = self.shard

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "address": address,
                "name": name,
                "port": port,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if shard is not UNSET:
            field_dict["shard"] = shard

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        address = d.pop("address")

        name = d.pop("name")

        def _parse_port(data: object) -> Union[None, int]:
            if data is None:
                return data
            return cast(Union[None, int], data)

        port = _parse_port(d.pop("port"))

        metadata = d.pop("metadata", UNSET)

        shard = d.pop("shard", UNSET)

        peer_entry = cls(
            address=address,
            name=name,
            port=port,
            metadata=metadata,
            shard=shard,
        )

        peer_entry.additional_properties = d
        return peer_entry

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
