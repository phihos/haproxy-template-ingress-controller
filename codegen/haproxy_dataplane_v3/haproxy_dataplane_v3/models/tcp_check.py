from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.tcp_check_action import TCPCheckAction
from ..models.tcp_check_error_status import TCPCheckErrorStatus
from ..models.tcp_check_match import TCPCheckMatch
from ..models.tcp_check_ok_status import TCPCheckOkStatus
from ..models.tcp_check_tout_status import TCPCheckToutStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="TCPCheck")


@_attrs_define
class TCPCheck:
    """
    Attributes:
        action (TCPCheckAction):
        addr (Union[Unset, str]):
        alpn (Union[Unset, str]):
        check_comment (Union[Unset, str]):
        data (Union[Unset, str]):
        default (Union[Unset, bool]):
        error_status (Union[Unset, TCPCheckErrorStatus]):
        exclamation_mark (Union[Unset, bool]):
        fmt (Union[Unset, str]):
        hex_fmt (Union[Unset, str]):
        hex_string (Union[Unset, str]):
        linger (Union[Unset, bool]):
        match (Union[Unset, TCPCheckMatch]):
        metadata (Union[Unset, Any]):
        min_recv (Union[Unset, int]):
        ok_status (Union[Unset, TCPCheckOkStatus]):
        on_error (Union[Unset, str]):
        on_success (Union[Unset, str]):
        pattern (Union[Unset, str]):
        port (Union[None, Unset, int]):
        port_string (Union[Unset, str]):
        proto (Union[Unset, str]):
        send_proxy (Union[Unset, bool]):
        sni (Union[Unset, str]):
        ssl (Union[Unset, bool]):
        status_code (Union[Unset, str]):
        tout_status (Union[Unset, TCPCheckToutStatus]):
        var_expr (Union[Unset, str]):
        var_fmt (Union[Unset, str]):
        var_name (Union[Unset, str]):
        var_scope (Union[Unset, str]):
        via_socks4 (Union[Unset, bool]):
    """

    action: TCPCheckAction
    addr: Union[Unset, str] = UNSET
    alpn: Union[Unset, str] = UNSET
    check_comment: Union[Unset, str] = UNSET
    data: Union[Unset, str] = UNSET
    default: Union[Unset, bool] = UNSET
    error_status: Union[Unset, TCPCheckErrorStatus] = UNSET
    exclamation_mark: Union[Unset, bool] = UNSET
    fmt: Union[Unset, str] = UNSET
    hex_fmt: Union[Unset, str] = UNSET
    hex_string: Union[Unset, str] = UNSET
    linger: Union[Unset, bool] = UNSET
    match: Union[Unset, TCPCheckMatch] = UNSET
    metadata: Union[Unset, Any] = UNSET
    min_recv: Union[Unset, int] = UNSET
    ok_status: Union[Unset, TCPCheckOkStatus] = UNSET
    on_error: Union[Unset, str] = UNSET
    on_success: Union[Unset, str] = UNSET
    pattern: Union[Unset, str] = UNSET
    port: Union[None, Unset, int] = UNSET
    port_string: Union[Unset, str] = UNSET
    proto: Union[Unset, str] = UNSET
    send_proxy: Union[Unset, bool] = UNSET
    sni: Union[Unset, str] = UNSET
    ssl: Union[Unset, bool] = UNSET
    status_code: Union[Unset, str] = UNSET
    tout_status: Union[Unset, TCPCheckToutStatus] = UNSET
    var_expr: Union[Unset, str] = UNSET
    var_fmt: Union[Unset, str] = UNSET
    var_name: Union[Unset, str] = UNSET
    var_scope: Union[Unset, str] = UNSET
    via_socks4: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        action = self.action.value

        addr = self.addr

        alpn = self.alpn

        check_comment = self.check_comment

        data = self.data

        default = self.default

        error_status: Union[Unset, str] = UNSET
        if not isinstance(self.error_status, Unset):
            error_status = self.error_status.value

        exclamation_mark = self.exclamation_mark

        fmt = self.fmt

        hex_fmt = self.hex_fmt

        hex_string = self.hex_string

        linger = self.linger

        match: Union[Unset, str] = UNSET
        if not isinstance(self.match, Unset):
            match = self.match.value

        metadata = self.metadata

        min_recv = self.min_recv

        ok_status: Union[Unset, str] = UNSET
        if not isinstance(self.ok_status, Unset):
            ok_status = self.ok_status.value

        on_error = self.on_error

        on_success = self.on_success

        pattern = self.pattern

        port: Union[None, Unset, int]
        if isinstance(self.port, Unset):
            port = UNSET
        else:
            port = self.port

        port_string = self.port_string

        proto = self.proto

        send_proxy = self.send_proxy

        sni = self.sni

        ssl = self.ssl

        status_code = self.status_code

        tout_status: Union[Unset, str] = UNSET
        if not isinstance(self.tout_status, Unset):
            tout_status = self.tout_status.value

        var_expr = self.var_expr

        var_fmt = self.var_fmt

        var_name = self.var_name

        var_scope = self.var_scope

        via_socks4 = self.via_socks4

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "action": action,
            }
        )
        if addr is not UNSET:
            field_dict["addr"] = addr
        if alpn is not UNSET:
            field_dict["alpn"] = alpn
        if check_comment is not UNSET:
            field_dict["check_comment"] = check_comment
        if data is not UNSET:
            field_dict["data"] = data
        if default is not UNSET:
            field_dict["default"] = default
        if error_status is not UNSET:
            field_dict["error_status"] = error_status
        if exclamation_mark is not UNSET:
            field_dict["exclamation_mark"] = exclamation_mark
        if fmt is not UNSET:
            field_dict["fmt"] = fmt
        if hex_fmt is not UNSET:
            field_dict["hex_fmt"] = hex_fmt
        if hex_string is not UNSET:
            field_dict["hex_string"] = hex_string
        if linger is not UNSET:
            field_dict["linger"] = linger
        if match is not UNSET:
            field_dict["match"] = match
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if min_recv is not UNSET:
            field_dict["min_recv"] = min_recv
        if ok_status is not UNSET:
            field_dict["ok_status"] = ok_status
        if on_error is not UNSET:
            field_dict["on_error"] = on_error
        if on_success is not UNSET:
            field_dict["on_success"] = on_success
        if pattern is not UNSET:
            field_dict["pattern"] = pattern
        if port is not UNSET:
            field_dict["port"] = port
        if port_string is not UNSET:
            field_dict["port_string"] = port_string
        if proto is not UNSET:
            field_dict["proto"] = proto
        if send_proxy is not UNSET:
            field_dict["send_proxy"] = send_proxy
        if sni is not UNSET:
            field_dict["sni"] = sni
        if ssl is not UNSET:
            field_dict["ssl"] = ssl
        if status_code is not UNSET:
            field_dict["status-code"] = status_code
        if tout_status is not UNSET:
            field_dict["tout_status"] = tout_status
        if var_expr is not UNSET:
            field_dict["var_expr"] = var_expr
        if var_fmt is not UNSET:
            field_dict["var_fmt"] = var_fmt
        if var_name is not UNSET:
            field_dict["var_name"] = var_name
        if var_scope is not UNSET:
            field_dict["var_scope"] = var_scope
        if via_socks4 is not UNSET:
            field_dict["via_socks4"] = via_socks4

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        action = TCPCheckAction(d.pop("action"))

        addr = d.pop("addr", UNSET)

        alpn = d.pop("alpn", UNSET)

        check_comment = d.pop("check_comment", UNSET)

        data = d.pop("data", UNSET)

        default = d.pop("default", UNSET)

        _error_status = d.pop("error_status", UNSET)
        error_status: Union[Unset, TCPCheckErrorStatus]
        if isinstance(_error_status, Unset):
            error_status = UNSET
        else:
            error_status = TCPCheckErrorStatus(_error_status)

        exclamation_mark = d.pop("exclamation_mark", UNSET)

        fmt = d.pop("fmt", UNSET)

        hex_fmt = d.pop("hex_fmt", UNSET)

        hex_string = d.pop("hex_string", UNSET)

        linger = d.pop("linger", UNSET)

        _match = d.pop("match", UNSET)
        match: Union[Unset, TCPCheckMatch]
        if isinstance(_match, Unset):
            match = UNSET
        else:
            match = TCPCheckMatch(_match)

        metadata = d.pop("metadata", UNSET)

        min_recv = d.pop("min_recv", UNSET)

        _ok_status = d.pop("ok_status", UNSET)
        ok_status: Union[Unset, TCPCheckOkStatus]
        if isinstance(_ok_status, Unset):
            ok_status = UNSET
        else:
            ok_status = TCPCheckOkStatus(_ok_status)

        on_error = d.pop("on_error", UNSET)

        on_success = d.pop("on_success", UNSET)

        pattern = d.pop("pattern", UNSET)

        def _parse_port(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        port = _parse_port(d.pop("port", UNSET))

        port_string = d.pop("port_string", UNSET)

        proto = d.pop("proto", UNSET)

        send_proxy = d.pop("send_proxy", UNSET)

        sni = d.pop("sni", UNSET)

        ssl = d.pop("ssl", UNSET)

        status_code = d.pop("status-code", UNSET)

        _tout_status = d.pop("tout_status", UNSET)
        tout_status: Union[Unset, TCPCheckToutStatus]
        if isinstance(_tout_status, Unset):
            tout_status = UNSET
        else:
            tout_status = TCPCheckToutStatus(_tout_status)

        var_expr = d.pop("var_expr", UNSET)

        var_fmt = d.pop("var_fmt", UNSET)

        var_name = d.pop("var_name", UNSET)

        var_scope = d.pop("var_scope", UNSET)

        via_socks4 = d.pop("via_socks4", UNSET)

        tcp_check = cls(
            action=action,
            addr=addr,
            alpn=alpn,
            check_comment=check_comment,
            data=data,
            default=default,
            error_status=error_status,
            exclamation_mark=exclamation_mark,
            fmt=fmt,
            hex_fmt=hex_fmt,
            hex_string=hex_string,
            linger=linger,
            match=match,
            metadata=metadata,
            min_recv=min_recv,
            ok_status=ok_status,
            on_error=on_error,
            on_success=on_success,
            pattern=pattern,
            port=port,
            port_string=port_string,
            proto=proto,
            send_proxy=send_proxy,
            sni=sni,
            ssl=ssl,
            status_code=status_code,
            tout_status=tout_status,
            var_expr=var_expr,
            var_fmt=var_fmt,
            var_name=var_name,
            var_scope=var_scope,
            via_socks4=via_socks4,
        )

        tcp_check.additional_properties = d
        return tcp_check

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
