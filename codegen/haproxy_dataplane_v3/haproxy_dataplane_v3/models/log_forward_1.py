from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="LogForward1")


@_attrs_define
class LogForward1:
    """HAProxy log forward configuration

    Attributes:
        name (str):
        assume_rfc6587_ntf (Union[Unset, bool]):
        backlog (Union[None, Unset, int]):
        dont_parse_log (Union[Unset, bool]):
        maxconn (Union[None, Unset, int]):
        metadata (Union[Unset, Any]):
        timeout_client (Union[None, Unset, int]):
    """

    name: str
    assume_rfc6587_ntf: Union[Unset, bool] = UNSET
    backlog: Union[None, Unset, int] = UNSET
    dont_parse_log: Union[Unset, bool] = UNSET
    maxconn: Union[None, Unset, int] = UNSET
    metadata: Union[Unset, Any] = UNSET
    timeout_client: Union[None, Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        assume_rfc6587_ntf = self.assume_rfc6587_ntf

        backlog: Union[None, Unset, int]
        if isinstance(self.backlog, Unset):
            backlog = UNSET
        else:
            backlog = self.backlog

        dont_parse_log = self.dont_parse_log

        maxconn: Union[None, Unset, int]
        if isinstance(self.maxconn, Unset):
            maxconn = UNSET
        else:
            maxconn = self.maxconn

        metadata = self.metadata

        timeout_client: Union[None, Unset, int]
        if isinstance(self.timeout_client, Unset):
            timeout_client = UNSET
        else:
            timeout_client = self.timeout_client

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
            }
        )
        if assume_rfc6587_ntf is not UNSET:
            field_dict["assume-rfc6587-ntf"] = assume_rfc6587_ntf
        if backlog is not UNSET:
            field_dict["backlog"] = backlog
        if dont_parse_log is not UNSET:
            field_dict["dont-parse-log"] = dont_parse_log
        if maxconn is not UNSET:
            field_dict["maxconn"] = maxconn
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if timeout_client is not UNSET:
            field_dict["timeout_client"] = timeout_client

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        assume_rfc6587_ntf = d.pop("assume-rfc6587-ntf", UNSET)

        def _parse_backlog(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        backlog = _parse_backlog(d.pop("backlog", UNSET))

        dont_parse_log = d.pop("dont-parse-log", UNSET)

        def _parse_maxconn(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        maxconn = _parse_maxconn(d.pop("maxconn", UNSET))

        metadata = d.pop("metadata", UNSET)

        def _parse_timeout_client(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        timeout_client = _parse_timeout_client(d.pop("timeout_client", UNSET))

        log_forward_1 = cls(
            name=name,
            assume_rfc6587_ntf=assume_rfc6587_ntf,
            backlog=backlog,
            dont_parse_log=dont_parse_log,
            maxconn=maxconn,
            metadata=metadata,
            timeout_client=timeout_client,
        )

        return log_forward_1
