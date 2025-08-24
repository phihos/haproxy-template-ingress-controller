from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.http_check_error_status import HTTPCheckErrorStatus
from ..models.http_check_match import HTTPCheckMatch
from ..models.http_check_method import HTTPCheckMethod
from ..models.http_check_ok_status import HTTPCheckOkStatus
from ..models.http_check_tout_status import HTTPCheckToutStatus
from ..models.http_check_type import HTTPCheckType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.return_header import ReturnHeader


T = TypeVar("T", bound="HTTPCheck")


@_attrs_define
class HTTPCheck:
    """
    Attributes:
        type_ (HTTPCheckType):
        addr (Union[Unset, str]):
        alpn (Union[Unset, str]):
        body (Union[Unset, str]):
        body_log_format (Union[Unset, str]):
        check_comment (Union[Unset, str]):
        default (Union[Unset, bool]):
        error_status (Union[Unset, HTTPCheckErrorStatus]):
        exclamation_mark (Union[Unset, bool]):
        headers (Union[Unset, list['ReturnHeader']]):
        linger (Union[Unset, bool]):
        match (Union[Unset, HTTPCheckMatch]):
        metadata (Union[Unset, Any]):
        method (Union[Unset, HTTPCheckMethod]):
        min_recv (Union[None, Unset, int]):
        ok_status (Union[Unset, HTTPCheckOkStatus]):
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
        tout_status (Union[Unset, HTTPCheckToutStatus]):
        uri (Union[Unset, str]):
        uri_log_format (Union[Unset, str]):
        var_expr (Union[Unset, str]):
        var_format (Union[Unset, str]):
        var_name (Union[Unset, str]):
        var_scope (Union[Unset, str]):
        version (Union[Unset, str]):
        via_socks4 (Union[Unset, bool]):
    """

    type_: HTTPCheckType
    addr: Union[Unset, str] = UNSET
    alpn: Union[Unset, str] = UNSET
    body: Union[Unset, str] = UNSET
    body_log_format: Union[Unset, str] = UNSET
    check_comment: Union[Unset, str] = UNSET
    default: Union[Unset, bool] = UNSET
    error_status: Union[Unset, HTTPCheckErrorStatus] = UNSET
    exclamation_mark: Union[Unset, bool] = UNSET
    headers: Union[Unset, list["ReturnHeader"]] = UNSET
    linger: Union[Unset, bool] = UNSET
    match: Union[Unset, HTTPCheckMatch] = UNSET
    metadata: Union[Unset, Any] = UNSET
    method: Union[Unset, HTTPCheckMethod] = UNSET
    min_recv: Union[None, Unset, int] = UNSET
    ok_status: Union[Unset, HTTPCheckOkStatus] = UNSET
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
    tout_status: Union[Unset, HTTPCheckToutStatus] = UNSET
    uri: Union[Unset, str] = UNSET
    uri_log_format: Union[Unset, str] = UNSET
    var_expr: Union[Unset, str] = UNSET
    var_format: Union[Unset, str] = UNSET
    var_name: Union[Unset, str] = UNSET
    var_scope: Union[Unset, str] = UNSET
    version: Union[Unset, str] = UNSET
    via_socks4: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        addr = self.addr

        alpn = self.alpn

        body = self.body

        body_log_format = self.body_log_format

        check_comment = self.check_comment

        default = self.default

        error_status: Union[Unset, str] = UNSET
        if not isinstance(self.error_status, Unset):
            error_status = self.error_status.value

        exclamation_mark = self.exclamation_mark

        headers: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.headers, Unset):
            headers = []
            for headers_item_data in self.headers:
                headers_item = headers_item_data.to_dict()
                headers.append(headers_item)

        linger = self.linger

        match: Union[Unset, str] = UNSET
        if not isinstance(self.match, Unset):
            match = self.match.value

        metadata = self.metadata

        method: Union[Unset, str] = UNSET
        if not isinstance(self.method, Unset):
            method = self.method.value

        min_recv: Union[None, Unset, int]
        if isinstance(self.min_recv, Unset):
            min_recv = UNSET
        else:
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

        uri = self.uri

        uri_log_format = self.uri_log_format

        var_expr = self.var_expr

        var_format = self.var_format

        var_name = self.var_name

        var_scope = self.var_scope

        version = self.version

        via_socks4 = self.via_socks4

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if addr is not UNSET:
            field_dict["addr"] = addr
        if alpn is not UNSET:
            field_dict["alpn"] = alpn
        if body is not UNSET:
            field_dict["body"] = body
        if body_log_format is not UNSET:
            field_dict["body_log_format"] = body_log_format
        if check_comment is not UNSET:
            field_dict["check_comment"] = check_comment
        if default is not UNSET:
            field_dict["default"] = default
        if error_status is not UNSET:
            field_dict["error_status"] = error_status
        if exclamation_mark is not UNSET:
            field_dict["exclamation_mark"] = exclamation_mark
        if headers is not UNSET:
            field_dict["headers"] = headers
        if linger is not UNSET:
            field_dict["linger"] = linger
        if match is not UNSET:
            field_dict["match"] = match
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if method is not UNSET:
            field_dict["method"] = method
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
        if uri is not UNSET:
            field_dict["uri"] = uri
        if uri_log_format is not UNSET:
            field_dict["uri_log_format"] = uri_log_format
        if var_expr is not UNSET:
            field_dict["var_expr"] = var_expr
        if var_format is not UNSET:
            field_dict["var_format"] = var_format
        if var_name is not UNSET:
            field_dict["var_name"] = var_name
        if var_scope is not UNSET:
            field_dict["var_scope"] = var_scope
        if version is not UNSET:
            field_dict["version"] = version
        if via_socks4 is not UNSET:
            field_dict["via_socks4"] = via_socks4

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.return_header import ReturnHeader

        d = dict(src_dict)
        type_ = HTTPCheckType(d.pop("type"))

        addr = d.pop("addr", UNSET)

        alpn = d.pop("alpn", UNSET)

        body = d.pop("body", UNSET)

        body_log_format = d.pop("body_log_format", UNSET)

        check_comment = d.pop("check_comment", UNSET)

        default = d.pop("default", UNSET)

        _error_status = d.pop("error_status", UNSET)
        error_status: Union[Unset, HTTPCheckErrorStatus]
        if isinstance(_error_status, Unset):
            error_status = UNSET
        else:
            error_status = HTTPCheckErrorStatus(_error_status)

        exclamation_mark = d.pop("exclamation_mark", UNSET)

        headers = []
        _headers = d.pop("headers", UNSET)
        for headers_item_data in _headers or []:
            headers_item = ReturnHeader.from_dict(headers_item_data)

            headers.append(headers_item)

        linger = d.pop("linger", UNSET)

        _match = d.pop("match", UNSET)
        match: Union[Unset, HTTPCheckMatch]
        if isinstance(_match, Unset):
            match = UNSET
        else:
            match = HTTPCheckMatch(_match)

        metadata = d.pop("metadata", UNSET)

        _method = d.pop("method", UNSET)
        method: Union[Unset, HTTPCheckMethod]
        if isinstance(_method, Unset):
            method = UNSET
        else:
            method = HTTPCheckMethod(_method)

        def _parse_min_recv(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        min_recv = _parse_min_recv(d.pop("min_recv", UNSET))

        _ok_status = d.pop("ok_status", UNSET)
        ok_status: Union[Unset, HTTPCheckOkStatus]
        if isinstance(_ok_status, Unset):
            ok_status = UNSET
        else:
            ok_status = HTTPCheckOkStatus(_ok_status)

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
        tout_status: Union[Unset, HTTPCheckToutStatus]
        if isinstance(_tout_status, Unset):
            tout_status = UNSET
        else:
            tout_status = HTTPCheckToutStatus(_tout_status)

        uri = d.pop("uri", UNSET)

        uri_log_format = d.pop("uri_log_format", UNSET)

        var_expr = d.pop("var_expr", UNSET)

        var_format = d.pop("var_format", UNSET)

        var_name = d.pop("var_name", UNSET)

        var_scope = d.pop("var_scope", UNSET)

        version = d.pop("version", UNSET)

        via_socks4 = d.pop("via_socks4", UNSET)

        http_check = cls(
            type_=type_,
            addr=addr,
            alpn=alpn,
            body=body,
            body_log_format=body_log_format,
            check_comment=check_comment,
            default=default,
            error_status=error_status,
            exclamation_mark=exclamation_mark,
            headers=headers,
            linger=linger,
            match=match,
            metadata=metadata,
            method=method,
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
            uri=uri,
            uri_log_format=uri_log_format,
            var_expr=var_expr,
            var_format=var_format,
            var_name=var_name,
            var_scope=var_scope,
            version=version,
            via_socks4=via_socks4,
        )

        http_check.additional_properties = d
        return http_check

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
