from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.tune_quic_options_socket_owner import TuneQuicOptionsSocketOwner
from ..models.tune_quic_options_zero_copy_fwd_send import TuneQuicOptionsZeroCopyFwdSend
from ..types import UNSET, Unset

T = TypeVar("T", bound="TuneQuicOptions")


@_attrs_define
class TuneQuicOptions:
    """
    Attributes:
        frontend_conn_tx_buffers_limit (Union[None, Unset, int]):
        frontend_max_idle_timeout (Union[None, Unset, int]):
        frontend_max_streams_bidi (Union[None, Unset, int]):
        frontend_max_tx_memory (Union[None, Unset, int]):
        max_frame_loss (Union[None, Unset, int]):
        reorder_ratio (Union[None, Unset, int]):
        retry_threshold (Union[None, Unset, int]):
        socket_owner (Union[Unset, TuneQuicOptionsSocketOwner]):
        zero_copy_fwd_send (Union[Unset, TuneQuicOptionsZeroCopyFwdSend]):
    """

    frontend_conn_tx_buffers_limit: Union[None, Unset, int] = UNSET
    frontend_max_idle_timeout: Union[None, Unset, int] = UNSET
    frontend_max_streams_bidi: Union[None, Unset, int] = UNSET
    frontend_max_tx_memory: Union[None, Unset, int] = UNSET
    max_frame_loss: Union[None, Unset, int] = UNSET
    reorder_ratio: Union[None, Unset, int] = UNSET
    retry_threshold: Union[None, Unset, int] = UNSET
    socket_owner: Union[Unset, TuneQuicOptionsSocketOwner] = UNSET
    zero_copy_fwd_send: Union[Unset, TuneQuicOptionsZeroCopyFwdSend] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        frontend_conn_tx_buffers_limit: Union[None, Unset, int]
        if isinstance(self.frontend_conn_tx_buffers_limit, Unset):
            frontend_conn_tx_buffers_limit = UNSET
        else:
            frontend_conn_tx_buffers_limit = self.frontend_conn_tx_buffers_limit

        frontend_max_idle_timeout: Union[None, Unset, int]
        if isinstance(self.frontend_max_idle_timeout, Unset):
            frontend_max_idle_timeout = UNSET
        else:
            frontend_max_idle_timeout = self.frontend_max_idle_timeout

        frontend_max_streams_bidi: Union[None, Unset, int]
        if isinstance(self.frontend_max_streams_bidi, Unset):
            frontend_max_streams_bidi = UNSET
        else:
            frontend_max_streams_bidi = self.frontend_max_streams_bidi

        frontend_max_tx_memory: Union[None, Unset, int]
        if isinstance(self.frontend_max_tx_memory, Unset):
            frontend_max_tx_memory = UNSET
        else:
            frontend_max_tx_memory = self.frontend_max_tx_memory

        max_frame_loss: Union[None, Unset, int]
        if isinstance(self.max_frame_loss, Unset):
            max_frame_loss = UNSET
        else:
            max_frame_loss = self.max_frame_loss

        reorder_ratio: Union[None, Unset, int]
        if isinstance(self.reorder_ratio, Unset):
            reorder_ratio = UNSET
        else:
            reorder_ratio = self.reorder_ratio

        retry_threshold: Union[None, Unset, int]
        if isinstance(self.retry_threshold, Unset):
            retry_threshold = UNSET
        else:
            retry_threshold = self.retry_threshold

        socket_owner: Union[Unset, str] = UNSET
        if not isinstance(self.socket_owner, Unset):
            socket_owner = self.socket_owner.value

        zero_copy_fwd_send: Union[Unset, str] = UNSET
        if not isinstance(self.zero_copy_fwd_send, Unset):
            zero_copy_fwd_send = self.zero_copy_fwd_send.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if frontend_conn_tx_buffers_limit is not UNSET:
            field_dict["frontend_conn_tx_buffers_limit"] = frontend_conn_tx_buffers_limit
        if frontend_max_idle_timeout is not UNSET:
            field_dict["frontend_max_idle_timeout"] = frontend_max_idle_timeout
        if frontend_max_streams_bidi is not UNSET:
            field_dict["frontend_max_streams_bidi"] = frontend_max_streams_bidi
        if frontend_max_tx_memory is not UNSET:
            field_dict["frontend_max_tx_memory"] = frontend_max_tx_memory
        if max_frame_loss is not UNSET:
            field_dict["max_frame_loss"] = max_frame_loss
        if reorder_ratio is not UNSET:
            field_dict["reorder_ratio"] = reorder_ratio
        if retry_threshold is not UNSET:
            field_dict["retry_threshold"] = retry_threshold
        if socket_owner is not UNSET:
            field_dict["socket_owner"] = socket_owner
        if zero_copy_fwd_send is not UNSET:
            field_dict["zero_copy_fwd_send"] = zero_copy_fwd_send

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_frontend_conn_tx_buffers_limit(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        frontend_conn_tx_buffers_limit = _parse_frontend_conn_tx_buffers_limit(
            d.pop("frontend_conn_tx_buffers_limit", UNSET)
        )

        def _parse_frontend_max_idle_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        frontend_max_idle_timeout = _parse_frontend_max_idle_timeout(d.pop("frontend_max_idle_timeout", UNSET))

        def _parse_frontend_max_streams_bidi(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        frontend_max_streams_bidi = _parse_frontend_max_streams_bidi(d.pop("frontend_max_streams_bidi", UNSET))

        def _parse_frontend_max_tx_memory(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        frontend_max_tx_memory = _parse_frontend_max_tx_memory(d.pop("frontend_max_tx_memory", UNSET))

        def _parse_max_frame_loss(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_frame_loss = _parse_max_frame_loss(d.pop("max_frame_loss", UNSET))

        def _parse_reorder_ratio(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        reorder_ratio = _parse_reorder_ratio(d.pop("reorder_ratio", UNSET))

        def _parse_retry_threshold(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        retry_threshold = _parse_retry_threshold(d.pop("retry_threshold", UNSET))

        _socket_owner = d.pop("socket_owner", UNSET)
        socket_owner: Union[Unset, TuneQuicOptionsSocketOwner]
        if isinstance(_socket_owner, Unset):
            socket_owner = UNSET
        else:
            socket_owner = TuneQuicOptionsSocketOwner(_socket_owner)

        _zero_copy_fwd_send = d.pop("zero_copy_fwd_send", UNSET)
        zero_copy_fwd_send: Union[Unset, TuneQuicOptionsZeroCopyFwdSend]
        if isinstance(_zero_copy_fwd_send, Unset):
            zero_copy_fwd_send = UNSET
        else:
            zero_copy_fwd_send = TuneQuicOptionsZeroCopyFwdSend(_zero_copy_fwd_send)

        tune_quic_options = cls(
            frontend_conn_tx_buffers_limit=frontend_conn_tx_buffers_limit,
            frontend_max_idle_timeout=frontend_max_idle_timeout,
            frontend_max_streams_bidi=frontend_max_streams_bidi,
            frontend_max_tx_memory=frontend_max_tx_memory,
            max_frame_loss=max_frame_loss,
            reorder_ratio=reorder_ratio,
            retry_threshold=retry_threshold,
            socket_owner=socket_owner,
            zero_copy_fwd_send=zero_copy_fwd_send,
        )

        tune_quic_options.additional_properties = d
        return tune_quic_options

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
