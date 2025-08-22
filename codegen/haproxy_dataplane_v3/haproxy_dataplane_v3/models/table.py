from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.table_type import TableType
from ..types import UNSET, Unset

T = TypeVar("T", bound="Table")


@_attrs_define
class Table:
    """
    Attributes:
        expire (Union[None, Unset, str]):
        metadata (Union[Unset, Any]):
        name (Union[Unset, str]):
        no_purge (Union[Unset, bool]):
        recv_only (Union[Unset, bool]):
        size (Union[Unset, str]):
        store (Union[Unset, str]):
        type_ (Union[Unset, TableType]):
        type_len (Union[None, Unset, int]):
        write_to (Union[None, Unset, str]):
    """

    expire: Union[None, Unset, str] = UNSET
    metadata: Union[Unset, Any] = UNSET
    name: Union[Unset, str] = UNSET
    no_purge: Union[Unset, bool] = UNSET
    recv_only: Union[Unset, bool] = UNSET
    size: Union[Unset, str] = UNSET
    store: Union[Unset, str] = UNSET
    type_: Union[Unset, TableType] = UNSET
    type_len: Union[None, Unset, int] = UNSET
    write_to: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        expire: Union[None, Unset, str]
        if isinstance(self.expire, Unset):
            expire = UNSET
        else:
            expire = self.expire

        metadata = self.metadata

        name = self.name

        no_purge = self.no_purge

        recv_only = self.recv_only

        size = self.size

        store = self.store

        type_: Union[Unset, str] = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        type_len: Union[None, Unset, int]
        if isinstance(self.type_len, Unset):
            type_len = UNSET
        else:
            type_len = self.type_len

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
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if name is not UNSET:
            field_dict["name"] = name
        if no_purge is not UNSET:
            field_dict["no_purge"] = no_purge
        if recv_only is not UNSET:
            field_dict["recv_only"] = recv_only
        if size is not UNSET:
            field_dict["size"] = size
        if store is not UNSET:
            field_dict["store"] = store
        if type_ is not UNSET:
            field_dict["type"] = type_
        if type_len is not UNSET:
            field_dict["type_len"] = type_len
        if write_to is not UNSET:
            field_dict["write_to"] = write_to

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_expire(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        expire = _parse_expire(d.pop("expire", UNSET))

        metadata = d.pop("metadata", UNSET)

        name = d.pop("name", UNSET)

        no_purge = d.pop("no_purge", UNSET)

        recv_only = d.pop("recv_only", UNSET)

        size = d.pop("size", UNSET)

        store = d.pop("store", UNSET)

        _type_ = d.pop("type", UNSET)
        type_: Union[Unset, TableType]
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = TableType(_type_)

        def _parse_type_len(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        type_len = _parse_type_len(d.pop("type_len", UNSET))

        def _parse_write_to(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        write_to = _parse_write_to(d.pop("write_to", UNSET))

        table = cls(
            expire=expire,
            metadata=metadata,
            name=name,
            no_purge=no_purge,
            recv_only=recv_only,
            size=size,
            store=store,
            type_=type_,
            type_len=type_len,
            write_to=write_to,
        )

        table.additional_properties = d
        return table

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
