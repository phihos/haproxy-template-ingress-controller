from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.log_target import LogTarget


T = TypeVar("T", bound="LogForward")


@_attrs_define
class LogForward:
    """LogForward with all it's children resources

    Attributes:
        name (str):
        assume_rfc6587_ntf (Union[Unset, bool]):
        backlog (Union[None, Unset, int]):
        dont_parse_log (Union[Unset, bool]):
        maxconn (Union[None, Unset, int]):
        metadata (Union[Unset, Any]):
        timeout_client (Union[None, Unset, int]):
        binds (Union[Unset, Any]):
        dgram_binds (Union[Unset, Any]):
        log_target_list (Union[Unset, list['LogTarget']]): HAProxy log target array (corresponds to log directives)
    """

    name: str
    assume_rfc6587_ntf: Union[Unset, bool] = UNSET
    backlog: Union[None, Unset, int] = UNSET
    dont_parse_log: Union[Unset, bool] = UNSET
    maxconn: Union[None, Unset, int] = UNSET
    metadata: Union[Unset, Any] = UNSET
    timeout_client: Union[None, Unset, int] = UNSET
    binds: Union[Unset, Any] = UNSET
    dgram_binds: Union[Unset, Any] = UNSET
    log_target_list: Union[Unset, list["LogTarget"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

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

        binds = self.binds

        dgram_binds = self.dgram_binds

        log_target_list: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.log_target_list, Unset):
            log_target_list = []
            for componentsschemaslog_targets_item_data in self.log_target_list:
                componentsschemaslog_targets_item = componentsschemaslog_targets_item_data.to_dict()
                log_target_list.append(componentsschemaslog_targets_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
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
        if binds is not UNSET:
            field_dict["binds"] = binds
        if dgram_binds is not UNSET:
            field_dict["dgram_binds"] = dgram_binds
        if log_target_list is not UNSET:
            field_dict["log_target_list"] = log_target_list

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.log_target import LogTarget

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

        binds = d.pop("binds", UNSET)

        dgram_binds = d.pop("dgram_binds", UNSET)

        _log_target_list = d.pop("log_target_list", UNSET)
        log_target_list: Union[Unset, list[LogTarget]] = UNSET
        if not isinstance(_log_target_list, Unset):
            log_target_list = []
            for componentsschemaslog_targets_item_data in _log_target_list:
                componentsschemaslog_targets_item = LogTarget.from_dict(componentsschemaslog_targets_item_data)

                log_target_list.append(componentsschemaslog_targets_item)

        log_forward = cls(
            name=name,
            assume_rfc6587_ntf=assume_rfc6587_ntf,
            backlog=backlog,
            dont_parse_log=dont_parse_log,
            maxconn=maxconn,
            metadata=metadata,
            timeout_client=timeout_client,
            binds=binds,
            dgram_binds=dgram_binds,
            log_target_list=log_target_list,
        )

        log_forward.additional_properties = d
        return log_forward

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
