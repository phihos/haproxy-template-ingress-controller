from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.config_stick_table_srvkey import ConfigStickTableSrvkey
from ..models.config_stick_table_type import ConfigStickTableType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ConfigStickTable")


@_attrs_define
class ConfigStickTable:
    """
    Attributes:
        expire (Union[None, Unset, int]):
        keylen (Union[None, Unset, int]):
        metadata (Union[Unset, Any]):
        nopurge (Union[Unset, bool]):
        peers (Union[Unset, str]):
        recv_only (Union[Unset, bool]):
        size (Union[None, Unset, int]):
        srvkey (Union[Unset, ConfigStickTableSrvkey]):
        store (Union[Unset, str]):
        type_ (Union[Unset, ConfigStickTableType]):
        write_to (Union[None, Unset, str]):
    """

    expire: Union[None, Unset, int] = UNSET
    keylen: Union[None, Unset, int] = UNSET
    metadata: Union[Unset, Any] = UNSET
    nopurge: Union[Unset, bool] = UNSET
    peers: Union[Unset, str] = UNSET
    recv_only: Union[Unset, bool] = UNSET
    size: Union[None, Unset, int] = UNSET
    srvkey: Union[Unset, ConfigStickTableSrvkey] = UNSET
    store: Union[Unset, str] = UNSET
    type_: Union[Unset, ConfigStickTableType] = UNSET
    write_to: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        expire: Union[None, Unset, int]
        if isinstance(self.expire, Unset):
            expire = UNSET
        else:
            expire = self.expire

        keylen: Union[None, Unset, int]
        if isinstance(self.keylen, Unset):
            keylen = UNSET
        else:
            keylen = self.keylen

        metadata = self.metadata

        nopurge = self.nopurge

        peers = self.peers

        recv_only = self.recv_only

        size: Union[None, Unset, int]
        if isinstance(self.size, Unset):
            size = UNSET
        else:
            size = self.size

        srvkey: Union[Unset, str] = UNSET
        if not isinstance(self.srvkey, Unset):
            srvkey = self.srvkey.value

        store = self.store

        type_: Union[Unset, str] = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        write_to: Union[None, Unset, str]
        if isinstance(self.write_to, Unset):
            write_to = UNSET
        else:
            write_to = self.write_to

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if expire is not UNSET:
            field_dict["expire"] = expire
        if keylen is not UNSET:
            field_dict["keylen"] = keylen
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if nopurge is not UNSET:
            field_dict["nopurge"] = nopurge
        if peers is not UNSET:
            field_dict["peers"] = peers
        if recv_only is not UNSET:
            field_dict["recv_only"] = recv_only
        if size is not UNSET:
            field_dict["size"] = size
        if srvkey is not UNSET:
            field_dict["srvkey"] = srvkey
        if store is not UNSET:
            field_dict["store"] = store
        if type_ is not UNSET:
            field_dict["type"] = type_
        if write_to is not UNSET:
            field_dict["write_to"] = write_to

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_expire(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        expire = _parse_expire(d.pop("expire", UNSET))

        def _parse_keylen(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        keylen = _parse_keylen(d.pop("keylen", UNSET))

        metadata = d.pop("metadata", UNSET)

        nopurge = d.pop("nopurge", UNSET)

        peers = d.pop("peers", UNSET)

        recv_only = d.pop("recv_only", UNSET)

        def _parse_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        size = _parse_size(d.pop("size", UNSET))

        _srvkey = d.pop("srvkey", UNSET)
        srvkey: Union[Unset, ConfigStickTableSrvkey]
        if isinstance(_srvkey, Unset):
            srvkey = UNSET
        else:
            srvkey = ConfigStickTableSrvkey(_srvkey)

        store = d.pop("store", UNSET)

        _type_ = d.pop("type", UNSET)
        type_: Union[Unset, ConfigStickTableType]
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = ConfigStickTableType(_type_)

        def _parse_write_to(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        write_to = _parse_write_to(d.pop("write_to", UNSET))

        config_stick_table = cls(
            expire=expire,
            keylen=keylen,
            metadata=metadata,
            nopurge=nopurge,
            peers=peers,
            recv_only=recv_only,
            size=size,
            srvkey=srvkey,
            store=store,
            type_=type_,
            write_to=write_to,
        )

        config_stick_table.additional_properties = d
        return config_stick_table

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
