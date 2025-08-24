from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.http_request_rule_cond import HTTPRequestRuleCond
from ..models.http_request_rule_log_level import HTTPRequestRuleLogLevel
from ..models.http_request_rule_normalizer import HTTPRequestRuleNormalizer
from ..models.http_request_rule_protocol import HTTPRequestRuleProtocol
from ..models.http_request_rule_redir_code import HTTPRequestRuleRedirCode
from ..models.http_request_rule_redir_type import HTTPRequestRuleRedirType
from ..models.http_request_rule_return_content_format import HTTPRequestRuleReturnContentFormat
from ..models.http_request_rule_strict_mode import HTTPRequestRuleStrictMode
from ..models.http_request_rule_timeout_type import HTTPRequestRuleTimeoutType
from ..models.http_request_rule_type import HTTPRequestRuleType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.return_header import ReturnHeader


T = TypeVar("T", bound="HTTPRequestRule")


@_attrs_define
class HTTPRequestRule:
    """HAProxy HTTP request rule configuration (corresponds to http-request directives)

    Example:
        {'cond': 'unless', 'cond_test': '{ src 192.168.0.0/16 }', 'hdr_format': '%T', 'hdr_name': 'X-Haproxy-Current-
            Date', 'index': 0, 'type': 'add-header'}

    Attributes:
        type_ (HTTPRequestRuleType):
        acl_file (Union[Unset, str]):
        acl_keyfmt (Union[Unset, str]):
        auth_realm (Union[Unset, str]):
        bandwidth_limit_limit (Union[Unset, str]):
        bandwidth_limit_name (Union[Unset, str]):
        bandwidth_limit_period (Union[Unset, str]):
        cache_name (Union[Unset, str]):
        capture_id (Union[None, Unset, int]):
        capture_len (Union[Unset, int]):
        capture_sample (Union[Unset, str]):
        cond (Union[Unset, HTTPRequestRuleCond]):
        cond_test (Union[Unset, str]):
        deny_status (Union[None, Unset, int]):
        expr (Union[Unset, str]):
        hdr_format (Union[Unset, str]):
        hdr_match (Union[Unset, str]):
        hdr_method (Union[Unset, str]):
        hdr_name (Union[Unset, str]):
        hint_format (Union[Unset, str]):
        hint_name (Union[Unset, str]):
        log_level (Union[Unset, HTTPRequestRuleLogLevel]):
        lua_action (Union[Unset, str]):
        lua_params (Union[Unset, str]):
        map_file (Union[Unset, str]):
        map_keyfmt (Union[Unset, str]):
        map_valuefmt (Union[Unset, str]):
        mark_value (Union[Unset, str]):
        metadata (Union[Unset, Any]):
        method_fmt (Union[Unset, str]):
        nice_value (Union[Unset, int]):
        normalizer (Union[Unset, HTTPRequestRuleNormalizer]):
        normalizer_full (Union[Unset, bool]):
        normalizer_strict (Union[Unset, bool]):
        path_fmt (Union[Unset, str]):
        path_match (Union[Unset, str]):
        protocol (Union[Unset, HTTPRequestRuleProtocol]):
        query_fmt (Union[Unset, str]):
        redir_code (Union[Unset, HTTPRequestRuleRedirCode]):
        redir_option (Union[Unset, str]):
        redir_type (Union[Unset, HTTPRequestRuleRedirType]):
        redir_value (Union[Unset, str]):
        resolvers (Union[Unset, str]):
        return_content (Union[Unset, str]):
        return_content_format (Union[Unset, HTTPRequestRuleReturnContentFormat]):
        return_content_type (Union[None, Unset, str]):
        return_hdrs (Union[Unset, list['ReturnHeader']]):
        return_status_code (Union[None, Unset, int]):
        rst_ttl (Union[Unset, int]):
        sc_expr (Union[Unset, str]):
        sc_id (Union[Unset, int]):
        sc_idx (Union[Unset, int]):
        sc_int (Union[None, Unset, int]):
        service_name (Union[Unset, str]):
        spoe_engine (Union[Unset, str]):
        spoe_group (Union[Unset, str]):
        strict_mode (Union[Unset, HTTPRequestRuleStrictMode]):
        timeout (Union[Unset, str]):
        timeout_type (Union[Unset, HTTPRequestRuleTimeoutType]):
        tos_value (Union[Unset, str]):
        track_sc_key (Union[Unset, str]):
        track_sc_stick_counter (Union[None, Unset, int]):
        track_sc_table (Union[Unset, str]):
        uri_fmt (Union[Unset, str]):
        uri_match (Union[Unset, str]):
        var_expr (Union[Unset, str]):
        var_format (Union[Unset, str]):
        var_name (Union[Unset, str]):
        var_scope (Union[Unset, str]):
        wait_at_least (Union[None, Unset, int]):
        wait_time (Union[None, Unset, int]):
    """

    type_: HTTPRequestRuleType
    acl_file: Union[Unset, str] = UNSET
    acl_keyfmt: Union[Unset, str] = UNSET
    auth_realm: Union[Unset, str] = UNSET
    bandwidth_limit_limit: Union[Unset, str] = UNSET
    bandwidth_limit_name: Union[Unset, str] = UNSET
    bandwidth_limit_period: Union[Unset, str] = UNSET
    cache_name: Union[Unset, str] = UNSET
    capture_id: Union[None, Unset, int] = UNSET
    capture_len: Union[Unset, int] = UNSET
    capture_sample: Union[Unset, str] = UNSET
    cond: Union[Unset, HTTPRequestRuleCond] = UNSET
    cond_test: Union[Unset, str] = UNSET
    deny_status: Union[None, Unset, int] = UNSET
    expr: Union[Unset, str] = UNSET
    hdr_format: Union[Unset, str] = UNSET
    hdr_match: Union[Unset, str] = UNSET
    hdr_method: Union[Unset, str] = UNSET
    hdr_name: Union[Unset, str] = UNSET
    hint_format: Union[Unset, str] = UNSET
    hint_name: Union[Unset, str] = UNSET
    log_level: Union[Unset, HTTPRequestRuleLogLevel] = UNSET
    lua_action: Union[Unset, str] = UNSET
    lua_params: Union[Unset, str] = UNSET
    map_file: Union[Unset, str] = UNSET
    map_keyfmt: Union[Unset, str] = UNSET
    map_valuefmt: Union[Unset, str] = UNSET
    mark_value: Union[Unset, str] = UNSET
    metadata: Union[Unset, Any] = UNSET
    method_fmt: Union[Unset, str] = UNSET
    nice_value: Union[Unset, int] = UNSET
    normalizer: Union[Unset, HTTPRequestRuleNormalizer] = UNSET
    normalizer_full: Union[Unset, bool] = UNSET
    normalizer_strict: Union[Unset, bool] = UNSET
    path_fmt: Union[Unset, str] = UNSET
    path_match: Union[Unset, str] = UNSET
    protocol: Union[Unset, HTTPRequestRuleProtocol] = UNSET
    query_fmt: Union[Unset, str] = UNSET
    redir_code: Union[Unset, HTTPRequestRuleRedirCode] = UNSET
    redir_option: Union[Unset, str] = UNSET
    redir_type: Union[Unset, HTTPRequestRuleRedirType] = UNSET
    redir_value: Union[Unset, str] = UNSET
    resolvers: Union[Unset, str] = UNSET
    return_content: Union[Unset, str] = UNSET
    return_content_format: Union[Unset, HTTPRequestRuleReturnContentFormat] = UNSET
    return_content_type: Union[None, Unset, str] = UNSET
    return_hdrs: Union[Unset, list["ReturnHeader"]] = UNSET
    return_status_code: Union[None, Unset, int] = UNSET
    rst_ttl: Union[Unset, int] = UNSET
    sc_expr: Union[Unset, str] = UNSET
    sc_id: Union[Unset, int] = UNSET
    sc_idx: Union[Unset, int] = UNSET
    sc_int: Union[None, Unset, int] = UNSET
    service_name: Union[Unset, str] = UNSET
    spoe_engine: Union[Unset, str] = UNSET
    spoe_group: Union[Unset, str] = UNSET
    strict_mode: Union[Unset, HTTPRequestRuleStrictMode] = UNSET
    timeout: Union[Unset, str] = UNSET
    timeout_type: Union[Unset, HTTPRequestRuleTimeoutType] = UNSET
    tos_value: Union[Unset, str] = UNSET
    track_sc_key: Union[Unset, str] = UNSET
    track_sc_stick_counter: Union[None, Unset, int] = UNSET
    track_sc_table: Union[Unset, str] = UNSET
    uri_fmt: Union[Unset, str] = UNSET
    uri_match: Union[Unset, str] = UNSET
    var_expr: Union[Unset, str] = UNSET
    var_format: Union[Unset, str] = UNSET
    var_name: Union[Unset, str] = UNSET
    var_scope: Union[Unset, str] = UNSET
    wait_at_least: Union[None, Unset, int] = UNSET
    wait_time: Union[None, Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        acl_file = self.acl_file

        acl_keyfmt = self.acl_keyfmt

        auth_realm = self.auth_realm

        bandwidth_limit_limit = self.bandwidth_limit_limit

        bandwidth_limit_name = self.bandwidth_limit_name

        bandwidth_limit_period = self.bandwidth_limit_period

        cache_name = self.cache_name

        capture_id: Union[None, Unset, int]
        if isinstance(self.capture_id, Unset):
            capture_id = UNSET
        else:
            capture_id = self.capture_id

        capture_len = self.capture_len

        capture_sample = self.capture_sample

        cond: Union[Unset, str] = UNSET
        if not isinstance(self.cond, Unset):
            cond = self.cond.value

        cond_test = self.cond_test

        deny_status: Union[None, Unset, int]
        if isinstance(self.deny_status, Unset):
            deny_status = UNSET
        else:
            deny_status = self.deny_status

        expr = self.expr

        hdr_format = self.hdr_format

        hdr_match = self.hdr_match

        hdr_method = self.hdr_method

        hdr_name = self.hdr_name

        hint_format = self.hint_format

        hint_name = self.hint_name

        log_level: Union[Unset, str] = UNSET
        if not isinstance(self.log_level, Unset):
            log_level = self.log_level.value

        lua_action = self.lua_action

        lua_params = self.lua_params

        map_file = self.map_file

        map_keyfmt = self.map_keyfmt

        map_valuefmt = self.map_valuefmt

        mark_value = self.mark_value

        metadata = self.metadata

        method_fmt = self.method_fmt

        nice_value = self.nice_value

        normalizer: Union[Unset, str] = UNSET
        if not isinstance(self.normalizer, Unset):
            normalizer = self.normalizer.value

        normalizer_full = self.normalizer_full

        normalizer_strict = self.normalizer_strict

        path_fmt = self.path_fmt

        path_match = self.path_match

        protocol: Union[Unset, str] = UNSET
        if not isinstance(self.protocol, Unset):
            protocol = self.protocol.value

        query_fmt = self.query_fmt

        redir_code: Union[Unset, int] = UNSET
        if not isinstance(self.redir_code, Unset):
            redir_code = self.redir_code.value

        redir_option = self.redir_option

        redir_type: Union[Unset, str] = UNSET
        if not isinstance(self.redir_type, Unset):
            redir_type = self.redir_type.value

        redir_value = self.redir_value

        resolvers = self.resolvers

        return_content = self.return_content

        return_content_format: Union[Unset, str] = UNSET
        if not isinstance(self.return_content_format, Unset):
            return_content_format = self.return_content_format.value

        return_content_type: Union[None, Unset, str]
        if isinstance(self.return_content_type, Unset):
            return_content_type = UNSET
        else:
            return_content_type = self.return_content_type

        return_hdrs: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.return_hdrs, Unset):
            return_hdrs = []
            for return_hdrs_item_data in self.return_hdrs:
                return_hdrs_item = return_hdrs_item_data.to_dict()
                return_hdrs.append(return_hdrs_item)

        return_status_code: Union[None, Unset, int]
        if isinstance(self.return_status_code, Unset):
            return_status_code = UNSET
        else:
            return_status_code = self.return_status_code

        rst_ttl = self.rst_ttl

        sc_expr = self.sc_expr

        sc_id = self.sc_id

        sc_idx = self.sc_idx

        sc_int: Union[None, Unset, int]
        if isinstance(self.sc_int, Unset):
            sc_int = UNSET
        else:
            sc_int = self.sc_int

        service_name = self.service_name

        spoe_engine = self.spoe_engine

        spoe_group = self.spoe_group

        strict_mode: Union[Unset, str] = UNSET
        if not isinstance(self.strict_mode, Unset):
            strict_mode = self.strict_mode.value

        timeout = self.timeout

        timeout_type: Union[Unset, str] = UNSET
        if not isinstance(self.timeout_type, Unset):
            timeout_type = self.timeout_type.value

        tos_value = self.tos_value

        track_sc_key = self.track_sc_key

        track_sc_stick_counter: Union[None, Unset, int]
        if isinstance(self.track_sc_stick_counter, Unset):
            track_sc_stick_counter = UNSET
        else:
            track_sc_stick_counter = self.track_sc_stick_counter

        track_sc_table = self.track_sc_table

        uri_fmt = self.uri_fmt

        uri_match = self.uri_match

        var_expr = self.var_expr

        var_format = self.var_format

        var_name = self.var_name

        var_scope = self.var_scope

        wait_at_least: Union[None, Unset, int]
        if isinstance(self.wait_at_least, Unset):
            wait_at_least = UNSET
        else:
            wait_at_least = self.wait_at_least

        wait_time: Union[None, Unset, int]
        if isinstance(self.wait_time, Unset):
            wait_time = UNSET
        else:
            wait_time = self.wait_time

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "type": type_,
            }
        )
        if acl_file is not UNSET:
            field_dict["acl_file"] = acl_file
        if acl_keyfmt is not UNSET:
            field_dict["acl_keyfmt"] = acl_keyfmt
        if auth_realm is not UNSET:
            field_dict["auth_realm"] = auth_realm
        if bandwidth_limit_limit is not UNSET:
            field_dict["bandwidth_limit_limit"] = bandwidth_limit_limit
        if bandwidth_limit_name is not UNSET:
            field_dict["bandwidth_limit_name"] = bandwidth_limit_name
        if bandwidth_limit_period is not UNSET:
            field_dict["bandwidth_limit_period"] = bandwidth_limit_period
        if cache_name is not UNSET:
            field_dict["cache_name"] = cache_name
        if capture_id is not UNSET:
            field_dict["capture_id"] = capture_id
        if capture_len is not UNSET:
            field_dict["capture_len"] = capture_len
        if capture_sample is not UNSET:
            field_dict["capture_sample"] = capture_sample
        if cond is not UNSET:
            field_dict["cond"] = cond
        if cond_test is not UNSET:
            field_dict["cond_test"] = cond_test
        if deny_status is not UNSET:
            field_dict["deny_status"] = deny_status
        if expr is not UNSET:
            field_dict["expr"] = expr
        if hdr_format is not UNSET:
            field_dict["hdr_format"] = hdr_format
        if hdr_match is not UNSET:
            field_dict["hdr_match"] = hdr_match
        if hdr_method is not UNSET:
            field_dict["hdr_method"] = hdr_method
        if hdr_name is not UNSET:
            field_dict["hdr_name"] = hdr_name
        if hint_format is not UNSET:
            field_dict["hint_format"] = hint_format
        if hint_name is not UNSET:
            field_dict["hint_name"] = hint_name
        if log_level is not UNSET:
            field_dict["log_level"] = log_level
        if lua_action is not UNSET:
            field_dict["lua_action"] = lua_action
        if lua_params is not UNSET:
            field_dict["lua_params"] = lua_params
        if map_file is not UNSET:
            field_dict["map_file"] = map_file
        if map_keyfmt is not UNSET:
            field_dict["map_keyfmt"] = map_keyfmt
        if map_valuefmt is not UNSET:
            field_dict["map_valuefmt"] = map_valuefmt
        if mark_value is not UNSET:
            field_dict["mark_value"] = mark_value
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if method_fmt is not UNSET:
            field_dict["method_fmt"] = method_fmt
        if nice_value is not UNSET:
            field_dict["nice_value"] = nice_value
        if normalizer is not UNSET:
            field_dict["normalizer"] = normalizer
        if normalizer_full is not UNSET:
            field_dict["normalizer_full"] = normalizer_full
        if normalizer_strict is not UNSET:
            field_dict["normalizer_strict"] = normalizer_strict
        if path_fmt is not UNSET:
            field_dict["path_fmt"] = path_fmt
        if path_match is not UNSET:
            field_dict["path_match"] = path_match
        if protocol is not UNSET:
            field_dict["protocol"] = protocol
        if query_fmt is not UNSET:
            field_dict["query-fmt"] = query_fmt
        if redir_code is not UNSET:
            field_dict["redir_code"] = redir_code
        if redir_option is not UNSET:
            field_dict["redir_option"] = redir_option
        if redir_type is not UNSET:
            field_dict["redir_type"] = redir_type
        if redir_value is not UNSET:
            field_dict["redir_value"] = redir_value
        if resolvers is not UNSET:
            field_dict["resolvers"] = resolvers
        if return_content is not UNSET:
            field_dict["return_content"] = return_content
        if return_content_format is not UNSET:
            field_dict["return_content_format"] = return_content_format
        if return_content_type is not UNSET:
            field_dict["return_content_type"] = return_content_type
        if return_hdrs is not UNSET:
            field_dict["return_hdrs"] = return_hdrs
        if return_status_code is not UNSET:
            field_dict["return_status_code"] = return_status_code
        if rst_ttl is not UNSET:
            field_dict["rst_ttl"] = rst_ttl
        if sc_expr is not UNSET:
            field_dict["sc_expr"] = sc_expr
        if sc_id is not UNSET:
            field_dict["sc_id"] = sc_id
        if sc_idx is not UNSET:
            field_dict["sc_idx"] = sc_idx
        if sc_int is not UNSET:
            field_dict["sc_int"] = sc_int
        if service_name is not UNSET:
            field_dict["service_name"] = service_name
        if spoe_engine is not UNSET:
            field_dict["spoe_engine"] = spoe_engine
        if spoe_group is not UNSET:
            field_dict["spoe_group"] = spoe_group
        if strict_mode is not UNSET:
            field_dict["strict_mode"] = strict_mode
        if timeout is not UNSET:
            field_dict["timeout"] = timeout
        if timeout_type is not UNSET:
            field_dict["timeout_type"] = timeout_type
        if tos_value is not UNSET:
            field_dict["tos_value"] = tos_value
        if track_sc_key is not UNSET:
            field_dict["track_sc_key"] = track_sc_key
        if track_sc_stick_counter is not UNSET:
            field_dict["track_sc_stick_counter"] = track_sc_stick_counter
        if track_sc_table is not UNSET:
            field_dict["track_sc_table"] = track_sc_table
        if uri_fmt is not UNSET:
            field_dict["uri-fmt"] = uri_fmt
        if uri_match is not UNSET:
            field_dict["uri-match"] = uri_match
        if var_expr is not UNSET:
            field_dict["var_expr"] = var_expr
        if var_format is not UNSET:
            field_dict["var_format"] = var_format
        if var_name is not UNSET:
            field_dict["var_name"] = var_name
        if var_scope is not UNSET:
            field_dict["var_scope"] = var_scope
        if wait_at_least is not UNSET:
            field_dict["wait_at_least"] = wait_at_least
        if wait_time is not UNSET:
            field_dict["wait_time"] = wait_time

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.return_header import ReturnHeader

        d = dict(src_dict)
        type_ = HTTPRequestRuleType(d.pop("type"))

        acl_file = d.pop("acl_file", UNSET)

        acl_keyfmt = d.pop("acl_keyfmt", UNSET)

        auth_realm = d.pop("auth_realm", UNSET)

        bandwidth_limit_limit = d.pop("bandwidth_limit_limit", UNSET)

        bandwidth_limit_name = d.pop("bandwidth_limit_name", UNSET)

        bandwidth_limit_period = d.pop("bandwidth_limit_period", UNSET)

        cache_name = d.pop("cache_name", UNSET)

        def _parse_capture_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        capture_id = _parse_capture_id(d.pop("capture_id", UNSET))

        capture_len = d.pop("capture_len", UNSET)

        capture_sample = d.pop("capture_sample", UNSET)

        _cond = d.pop("cond", UNSET)
        cond: Union[Unset, HTTPRequestRuleCond]
        if isinstance(_cond, Unset):
            cond = UNSET
        else:
            cond = HTTPRequestRuleCond(_cond)

        cond_test = d.pop("cond_test", UNSET)

        def _parse_deny_status(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        deny_status = _parse_deny_status(d.pop("deny_status", UNSET))

        expr = d.pop("expr", UNSET)

        hdr_format = d.pop("hdr_format", UNSET)

        hdr_match = d.pop("hdr_match", UNSET)

        hdr_method = d.pop("hdr_method", UNSET)

        hdr_name = d.pop("hdr_name", UNSET)

        hint_format = d.pop("hint_format", UNSET)

        hint_name = d.pop("hint_name", UNSET)

        _log_level = d.pop("log_level", UNSET)
        log_level: Union[Unset, HTTPRequestRuleLogLevel]
        if isinstance(_log_level, Unset):
            log_level = UNSET
        else:
            log_level = HTTPRequestRuleLogLevel(_log_level)

        lua_action = d.pop("lua_action", UNSET)

        lua_params = d.pop("lua_params", UNSET)

        map_file = d.pop("map_file", UNSET)

        map_keyfmt = d.pop("map_keyfmt", UNSET)

        map_valuefmt = d.pop("map_valuefmt", UNSET)

        mark_value = d.pop("mark_value", UNSET)

        metadata = d.pop("metadata", UNSET)

        method_fmt = d.pop("method_fmt", UNSET)

        nice_value = d.pop("nice_value", UNSET)

        _normalizer = d.pop("normalizer", UNSET)
        normalizer: Union[Unset, HTTPRequestRuleNormalizer]
        if isinstance(_normalizer, Unset):
            normalizer = UNSET
        else:
            normalizer = HTTPRequestRuleNormalizer(_normalizer)

        normalizer_full = d.pop("normalizer_full", UNSET)

        normalizer_strict = d.pop("normalizer_strict", UNSET)

        path_fmt = d.pop("path_fmt", UNSET)

        path_match = d.pop("path_match", UNSET)

        _protocol = d.pop("protocol", UNSET)
        protocol: Union[Unset, HTTPRequestRuleProtocol]
        if isinstance(_protocol, Unset):
            protocol = UNSET
        else:
            protocol = HTTPRequestRuleProtocol(_protocol)

        query_fmt = d.pop("query-fmt", UNSET)

        _redir_code = d.pop("redir_code", UNSET)
        redir_code: Union[Unset, HTTPRequestRuleRedirCode]
        if isinstance(_redir_code, Unset):
            redir_code = UNSET
        else:
            redir_code = HTTPRequestRuleRedirCode(_redir_code)

        redir_option = d.pop("redir_option", UNSET)

        _redir_type = d.pop("redir_type", UNSET)
        redir_type: Union[Unset, HTTPRequestRuleRedirType]
        if isinstance(_redir_type, Unset):
            redir_type = UNSET
        else:
            redir_type = HTTPRequestRuleRedirType(_redir_type)

        redir_value = d.pop("redir_value", UNSET)

        resolvers = d.pop("resolvers", UNSET)

        return_content = d.pop("return_content", UNSET)

        _return_content_format = d.pop("return_content_format", UNSET)
        return_content_format: Union[Unset, HTTPRequestRuleReturnContentFormat]
        if isinstance(_return_content_format, Unset):
            return_content_format = UNSET
        else:
            return_content_format = HTTPRequestRuleReturnContentFormat(_return_content_format)

        def _parse_return_content_type(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        return_content_type = _parse_return_content_type(d.pop("return_content_type", UNSET))

        return_hdrs = []
        _return_hdrs = d.pop("return_hdrs", UNSET)
        for return_hdrs_item_data in _return_hdrs or []:
            return_hdrs_item = ReturnHeader.from_dict(return_hdrs_item_data)

            return_hdrs.append(return_hdrs_item)

        def _parse_return_status_code(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        return_status_code = _parse_return_status_code(d.pop("return_status_code", UNSET))

        rst_ttl = d.pop("rst_ttl", UNSET)

        sc_expr = d.pop("sc_expr", UNSET)

        sc_id = d.pop("sc_id", UNSET)

        sc_idx = d.pop("sc_idx", UNSET)

        def _parse_sc_int(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        sc_int = _parse_sc_int(d.pop("sc_int", UNSET))

        service_name = d.pop("service_name", UNSET)

        spoe_engine = d.pop("spoe_engine", UNSET)

        spoe_group = d.pop("spoe_group", UNSET)

        _strict_mode = d.pop("strict_mode", UNSET)
        strict_mode: Union[Unset, HTTPRequestRuleStrictMode]
        if isinstance(_strict_mode, Unset):
            strict_mode = UNSET
        else:
            strict_mode = HTTPRequestRuleStrictMode(_strict_mode)

        timeout = d.pop("timeout", UNSET)

        _timeout_type = d.pop("timeout_type", UNSET)
        timeout_type: Union[Unset, HTTPRequestRuleTimeoutType]
        if isinstance(_timeout_type, Unset):
            timeout_type = UNSET
        else:
            timeout_type = HTTPRequestRuleTimeoutType(_timeout_type)

        tos_value = d.pop("tos_value", UNSET)

        track_sc_key = d.pop("track_sc_key", UNSET)

        def _parse_track_sc_stick_counter(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        track_sc_stick_counter = _parse_track_sc_stick_counter(d.pop("track_sc_stick_counter", UNSET))

        track_sc_table = d.pop("track_sc_table", UNSET)

        uri_fmt = d.pop("uri-fmt", UNSET)

        uri_match = d.pop("uri-match", UNSET)

        var_expr = d.pop("var_expr", UNSET)

        var_format = d.pop("var_format", UNSET)

        var_name = d.pop("var_name", UNSET)

        var_scope = d.pop("var_scope", UNSET)

        def _parse_wait_at_least(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        wait_at_least = _parse_wait_at_least(d.pop("wait_at_least", UNSET))

        def _parse_wait_time(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        wait_time = _parse_wait_time(d.pop("wait_time", UNSET))

        http_request_rule = cls(
            type_=type_,
            acl_file=acl_file,
            acl_keyfmt=acl_keyfmt,
            auth_realm=auth_realm,
            bandwidth_limit_limit=bandwidth_limit_limit,
            bandwidth_limit_name=bandwidth_limit_name,
            bandwidth_limit_period=bandwidth_limit_period,
            cache_name=cache_name,
            capture_id=capture_id,
            capture_len=capture_len,
            capture_sample=capture_sample,
            cond=cond,
            cond_test=cond_test,
            deny_status=deny_status,
            expr=expr,
            hdr_format=hdr_format,
            hdr_match=hdr_match,
            hdr_method=hdr_method,
            hdr_name=hdr_name,
            hint_format=hint_format,
            hint_name=hint_name,
            log_level=log_level,
            lua_action=lua_action,
            lua_params=lua_params,
            map_file=map_file,
            map_keyfmt=map_keyfmt,
            map_valuefmt=map_valuefmt,
            mark_value=mark_value,
            metadata=metadata,
            method_fmt=method_fmt,
            nice_value=nice_value,
            normalizer=normalizer,
            normalizer_full=normalizer_full,
            normalizer_strict=normalizer_strict,
            path_fmt=path_fmt,
            path_match=path_match,
            protocol=protocol,
            query_fmt=query_fmt,
            redir_code=redir_code,
            redir_option=redir_option,
            redir_type=redir_type,
            redir_value=redir_value,
            resolvers=resolvers,
            return_content=return_content,
            return_content_format=return_content_format,
            return_content_type=return_content_type,
            return_hdrs=return_hdrs,
            return_status_code=return_status_code,
            rst_ttl=rst_ttl,
            sc_expr=sc_expr,
            sc_id=sc_id,
            sc_idx=sc_idx,
            sc_int=sc_int,
            service_name=service_name,
            spoe_engine=spoe_engine,
            spoe_group=spoe_group,
            strict_mode=strict_mode,
            timeout=timeout,
            timeout_type=timeout_type,
            tos_value=tos_value,
            track_sc_key=track_sc_key,
            track_sc_stick_counter=track_sc_stick_counter,
            track_sc_table=track_sc_table,
            uri_fmt=uri_fmt,
            uri_match=uri_match,
            var_expr=var_expr,
            var_format=var_format,
            var_name=var_name,
            var_scope=var_scope,
            wait_at_least=wait_at_least,
            wait_time=wait_time,
        )

        return http_request_rule
