from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TuneBufferOptions")


@_attrs_define
class TuneBufferOptions:
    """
    Attributes:
        buffers_limit (Union[None, Unset, int]):
        buffers_reserve (Union[Unset, int]):
        bufsize (Union[Unset, int]):
        bufsize_small (Union[None, Unset, int]):
        pipesize (Union[Unset, int]):
        rcvbuf_backend (Union[None, Unset, int]):
        rcvbuf_client (Union[None, Unset, int]):
        rcvbuf_frontend (Union[None, Unset, int]):
        rcvbuf_server (Union[None, Unset, int]):
        recv_enough (Union[Unset, int]):
        sndbuf_backend (Union[None, Unset, int]):
        sndbuf_client (Union[None, Unset, int]):
        sndbuf_frontend (Union[None, Unset, int]):
        sndbuf_server (Union[None, Unset, int]):
    """

    buffers_limit: Union[None, Unset, int] = UNSET
    buffers_reserve: Union[Unset, int] = UNSET
    bufsize: Union[Unset, int] = UNSET
    bufsize_small: Union[None, Unset, int] = UNSET
    pipesize: Union[Unset, int] = UNSET
    rcvbuf_backend: Union[None, Unset, int] = UNSET
    rcvbuf_client: Union[None, Unset, int] = UNSET
    rcvbuf_frontend: Union[None, Unset, int] = UNSET
    rcvbuf_server: Union[None, Unset, int] = UNSET
    recv_enough: Union[Unset, int] = UNSET
    sndbuf_backend: Union[None, Unset, int] = UNSET
    sndbuf_client: Union[None, Unset, int] = UNSET
    sndbuf_frontend: Union[None, Unset, int] = UNSET
    sndbuf_server: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        buffers_limit: Union[None, Unset, int]
        if isinstance(self.buffers_limit, Unset):
            buffers_limit = UNSET
        else:
            buffers_limit = self.buffers_limit

        buffers_reserve = self.buffers_reserve

        bufsize = self.bufsize

        bufsize_small: Union[None, Unset, int]
        if isinstance(self.bufsize_small, Unset):
            bufsize_small = UNSET
        else:
            bufsize_small = self.bufsize_small

        pipesize = self.pipesize

        rcvbuf_backend: Union[None, Unset, int]
        if isinstance(self.rcvbuf_backend, Unset):
            rcvbuf_backend = UNSET
        else:
            rcvbuf_backend = self.rcvbuf_backend

        rcvbuf_client: Union[None, Unset, int]
        if isinstance(self.rcvbuf_client, Unset):
            rcvbuf_client = UNSET
        else:
            rcvbuf_client = self.rcvbuf_client

        rcvbuf_frontend: Union[None, Unset, int]
        if isinstance(self.rcvbuf_frontend, Unset):
            rcvbuf_frontend = UNSET
        else:
            rcvbuf_frontend = self.rcvbuf_frontend

        rcvbuf_server: Union[None, Unset, int]
        if isinstance(self.rcvbuf_server, Unset):
            rcvbuf_server = UNSET
        else:
            rcvbuf_server = self.rcvbuf_server

        recv_enough = self.recv_enough

        sndbuf_backend: Union[None, Unset, int]
        if isinstance(self.sndbuf_backend, Unset):
            sndbuf_backend = UNSET
        else:
            sndbuf_backend = self.sndbuf_backend

        sndbuf_client: Union[None, Unset, int]
        if isinstance(self.sndbuf_client, Unset):
            sndbuf_client = UNSET
        else:
            sndbuf_client = self.sndbuf_client

        sndbuf_frontend: Union[None, Unset, int]
        if isinstance(self.sndbuf_frontend, Unset):
            sndbuf_frontend = UNSET
        else:
            sndbuf_frontend = self.sndbuf_frontend

        sndbuf_server: Union[None, Unset, int]
        if isinstance(self.sndbuf_server, Unset):
            sndbuf_server = UNSET
        else:
            sndbuf_server = self.sndbuf_server

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if buffers_limit is not UNSET:
            field_dict["buffers_limit"] = buffers_limit
        if buffers_reserve is not UNSET:
            field_dict["buffers_reserve"] = buffers_reserve
        if bufsize is not UNSET:
            field_dict["bufsize"] = bufsize
        if bufsize_small is not UNSET:
            field_dict["bufsize_small"] = bufsize_small
        if pipesize is not UNSET:
            field_dict["pipesize"] = pipesize
        if rcvbuf_backend is not UNSET:
            field_dict["rcvbuf_backend"] = rcvbuf_backend
        if rcvbuf_client is not UNSET:
            field_dict["rcvbuf_client"] = rcvbuf_client
        if rcvbuf_frontend is not UNSET:
            field_dict["rcvbuf_frontend"] = rcvbuf_frontend
        if rcvbuf_server is not UNSET:
            field_dict["rcvbuf_server"] = rcvbuf_server
        if recv_enough is not UNSET:
            field_dict["recv_enough"] = recv_enough
        if sndbuf_backend is not UNSET:
            field_dict["sndbuf_backend"] = sndbuf_backend
        if sndbuf_client is not UNSET:
            field_dict["sndbuf_client"] = sndbuf_client
        if sndbuf_frontend is not UNSET:
            field_dict["sndbuf_frontend"] = sndbuf_frontend
        if sndbuf_server is not UNSET:
            field_dict["sndbuf_server"] = sndbuf_server

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_buffers_limit(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        buffers_limit = _parse_buffers_limit(d.pop("buffers_limit", UNSET))

        buffers_reserve = d.pop("buffers_reserve", UNSET)

        bufsize = d.pop("bufsize", UNSET)

        def _parse_bufsize_small(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        bufsize_small = _parse_bufsize_small(d.pop("bufsize_small", UNSET))

        pipesize = d.pop("pipesize", UNSET)

        def _parse_rcvbuf_backend(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        rcvbuf_backend = _parse_rcvbuf_backend(d.pop("rcvbuf_backend", UNSET))

        def _parse_rcvbuf_client(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        rcvbuf_client = _parse_rcvbuf_client(d.pop("rcvbuf_client", UNSET))

        def _parse_rcvbuf_frontend(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        rcvbuf_frontend = _parse_rcvbuf_frontend(d.pop("rcvbuf_frontend", UNSET))

        def _parse_rcvbuf_server(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        rcvbuf_server = _parse_rcvbuf_server(d.pop("rcvbuf_server", UNSET))

        recv_enough = d.pop("recv_enough", UNSET)

        def _parse_sndbuf_backend(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        sndbuf_backend = _parse_sndbuf_backend(d.pop("sndbuf_backend", UNSET))

        def _parse_sndbuf_client(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        sndbuf_client = _parse_sndbuf_client(d.pop("sndbuf_client", UNSET))

        def _parse_sndbuf_frontend(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        sndbuf_frontend = _parse_sndbuf_frontend(d.pop("sndbuf_frontend", UNSET))

        def _parse_sndbuf_server(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        sndbuf_server = _parse_sndbuf_server(d.pop("sndbuf_server", UNSET))

        tune_buffer_options = cls(
            buffers_limit=buffers_limit,
            buffers_reserve=buffers_reserve,
            bufsize=bufsize,
            bufsize_small=bufsize_small,
            pipesize=pipesize,
            rcvbuf_backend=rcvbuf_backend,
            rcvbuf_client=rcvbuf_client,
            rcvbuf_frontend=rcvbuf_frontend,
            rcvbuf_server=rcvbuf_server,
            recv_enough=recv_enough,
            sndbuf_backend=sndbuf_backend,
            sndbuf_client=sndbuf_client,
            sndbuf_frontend=sndbuf_frontend,
            sndbuf_server=sndbuf_server,
        )

        tune_buffer_options.additional_properties = d
        return tune_buffer_options

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
