from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.ring_base_format import RingBaseFormat
from ..types import UNSET, Unset

T = TypeVar("T", bound="RingBase")


@_attrs_define
class RingBase:
    """HAProxy ring configuration

    Attributes:
        name (str):
        description (Union[Unset, str]):
        format_ (Union[Unset, RingBaseFormat]):
        maxlen (Union[None, Unset, int]):
        metadata (Union[Unset, Any]):
        size (Union[None, Unset, int]):
        timeout_connect (Union[None, Unset, int]):
        timeout_server (Union[None, Unset, int]):
    """

    name: str
    description: Union[Unset, str] = UNSET
    format_: Union[Unset, RingBaseFormat] = UNSET
    maxlen: Union[None, Unset, int] = UNSET
    metadata: Union[Unset, Any] = UNSET
    size: Union[None, Unset, int] = UNSET
    timeout_connect: Union[None, Unset, int] = UNSET
    timeout_server: Union[None, Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        format_: Union[Unset, str] = UNSET
        if not isinstance(self.format_, Unset):
            format_ = self.format_.value

        maxlen: Union[None, Unset, int]
        if isinstance(self.maxlen, Unset):
            maxlen = UNSET
        else:
            maxlen = self.maxlen

        metadata = self.metadata

        size: Union[None, Unset, int]
        if isinstance(self.size, Unset):
            size = UNSET
        else:
            size = self.size

        timeout_connect: Union[None, Unset, int]
        if isinstance(self.timeout_connect, Unset):
            timeout_connect = UNSET
        else:
            timeout_connect = self.timeout_connect

        timeout_server: Union[None, Unset, int]
        if isinstance(self.timeout_server, Unset):
            timeout_server = UNSET
        else:
            timeout_server = self.timeout_server

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if format_ is not UNSET:
            field_dict["format"] = format_
        if maxlen is not UNSET:
            field_dict["maxlen"] = maxlen
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if size is not UNSET:
            field_dict["size"] = size
        if timeout_connect is not UNSET:
            field_dict["timeout_connect"] = timeout_connect
        if timeout_server is not UNSET:
            field_dict["timeout_server"] = timeout_server

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description", UNSET)

        _format_ = d.pop("format", UNSET)
        format_: Union[Unset, RingBaseFormat]
        if isinstance(_format_, Unset):
            format_ = UNSET
        else:
            format_ = RingBaseFormat(_format_)

        def _parse_maxlen(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        maxlen = _parse_maxlen(d.pop("maxlen", UNSET))

        metadata = d.pop("metadata", UNSET)

        def _parse_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        size = _parse_size(d.pop("size", UNSET))

        def _parse_timeout_connect(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        timeout_connect = _parse_timeout_connect(d.pop("timeout_connect", UNSET))

        def _parse_timeout_server(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        timeout_server = _parse_timeout_server(d.pop("timeout_server", UNSET))

        ring_base = cls(
            name=name,
            description=description,
            format_=format_,
            maxlen=maxlen,
            metadata=metadata,
            size=size,
            timeout_connect=timeout_connect,
            timeout_server=timeout_server,
        )

        return ring_base
