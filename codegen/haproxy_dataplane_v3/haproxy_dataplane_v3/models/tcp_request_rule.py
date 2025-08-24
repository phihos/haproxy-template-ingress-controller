from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.tcp_request_rule_action import TCPRequestRuleAction
from ..models.tcp_request_rule_cond import TCPRequestRuleCond
from ..models.tcp_request_rule_log_level import TCPRequestRuleLogLevel
from ..models.tcp_request_rule_resolve_protocol import TCPRequestRuleResolveProtocol
from ..models.tcp_request_rule_type import TCPRequestRuleType
from ..types import UNSET, Unset

T = TypeVar("T", bound="TCPRequestRule")


@_attrs_define
class TCPRequestRule:
    """HAProxy TCP Request Rule configuration (corresponds to tcp-request)

    Example:
        {'cond': 'if', 'cond_test': '{ src 192.168.0.0/16 }', 'index': 0, 'type': 'connection'}

    Attributes:
        type_ (TCPRequestRuleType):
        action (Union[Unset, TCPRequestRuleAction]):
        bandwidth_limit_limit (Union[Unset, str]):
        bandwidth_limit_name (Union[Unset, str]):
        bandwidth_limit_period (Union[Unset, str]):
        capture_len (Union[Unset, int]):
        capture_sample (Union[Unset, str]):
        cond (Union[Unset, TCPRequestRuleCond]):
        cond_test (Union[Unset, str]):
        expr (Union[Unset, str]):
        gpt_value (Union[Unset, str]):
        log_level (Union[Unset, TCPRequestRuleLogLevel]):
        lua_action (Union[Unset, str]):
        lua_params (Union[Unset, str]):
        mark_value (Union[Unset, str]):
        metadata (Union[Unset, Any]):
        nice_value (Union[Unset, int]):
        resolve_protocol (Union[Unset, TCPRequestRuleResolveProtocol]):
        resolve_resolvers (Union[Unset, str]):
        resolve_var (Union[Unset, str]):
        rst_ttl (Union[Unset, int]):
        sc_idx (Union[Unset, str]):
        sc_inc_id (Union[Unset, str]):
        sc_int (Union[None, Unset, int]):
        server_name (Union[Unset, str]):
        service_name (Union[Unset, str]):
        spoe_engine_name (Union[Unset, str]):
        spoe_group_name (Union[Unset, str]):
        switch_mode_proto (Union[Unset, str]):
        timeout (Union[None, Unset, int]):
        tos_value (Union[Unset, str]):
        track_key (Union[Unset, str]):
        track_stick_counter (Union[None, Unset, int]):
        track_table (Union[Unset, str]):
        var_format (Union[Unset, str]):
        var_name (Union[Unset, str]):
        var_scope (Union[Unset, str]):
    """

    type_: TCPRequestRuleType
    action: Union[Unset, TCPRequestRuleAction] = UNSET
    bandwidth_limit_limit: Union[Unset, str] = UNSET
    bandwidth_limit_name: Union[Unset, str] = UNSET
    bandwidth_limit_period: Union[Unset, str] = UNSET
    capture_len: Union[Unset, int] = UNSET
    capture_sample: Union[Unset, str] = UNSET
    cond: Union[Unset, TCPRequestRuleCond] = UNSET
    cond_test: Union[Unset, str] = UNSET
    expr: Union[Unset, str] = UNSET
    gpt_value: Union[Unset, str] = UNSET
    log_level: Union[Unset, TCPRequestRuleLogLevel] = UNSET
    lua_action: Union[Unset, str] = UNSET
    lua_params: Union[Unset, str] = UNSET
    mark_value: Union[Unset, str] = UNSET
    metadata: Union[Unset, Any] = UNSET
    nice_value: Union[Unset, int] = UNSET
    resolve_protocol: Union[Unset, TCPRequestRuleResolveProtocol] = UNSET
    resolve_resolvers: Union[Unset, str] = UNSET
    resolve_var: Union[Unset, str] = UNSET
    rst_ttl: Union[Unset, int] = UNSET
    sc_idx: Union[Unset, str] = UNSET
    sc_inc_id: Union[Unset, str] = UNSET
    sc_int: Union[None, Unset, int] = UNSET
    server_name: Union[Unset, str] = UNSET
    service_name: Union[Unset, str] = UNSET
    spoe_engine_name: Union[Unset, str] = UNSET
    spoe_group_name: Union[Unset, str] = UNSET
    switch_mode_proto: Union[Unset, str] = UNSET
    timeout: Union[None, Unset, int] = UNSET
    tos_value: Union[Unset, str] = UNSET
    track_key: Union[Unset, str] = UNSET
    track_stick_counter: Union[None, Unset, int] = UNSET
    track_table: Union[Unset, str] = UNSET
    var_format: Union[Unset, str] = UNSET
    var_name: Union[Unset, str] = UNSET
    var_scope: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        action: Union[Unset, str] = UNSET
        if not isinstance(self.action, Unset):
            action = self.action.value

        bandwidth_limit_limit = self.bandwidth_limit_limit

        bandwidth_limit_name = self.bandwidth_limit_name

        bandwidth_limit_period = self.bandwidth_limit_period

        capture_len = self.capture_len

        capture_sample = self.capture_sample

        cond: Union[Unset, str] = UNSET
        if not isinstance(self.cond, Unset):
            cond = self.cond.value

        cond_test = self.cond_test

        expr = self.expr

        gpt_value = self.gpt_value

        log_level: Union[Unset, str] = UNSET
        if not isinstance(self.log_level, Unset):
            log_level = self.log_level.value

        lua_action = self.lua_action

        lua_params = self.lua_params

        mark_value = self.mark_value

        metadata = self.metadata

        nice_value = self.nice_value

        resolve_protocol: Union[Unset, str] = UNSET
        if not isinstance(self.resolve_protocol, Unset):
            resolve_protocol = self.resolve_protocol.value

        resolve_resolvers = self.resolve_resolvers

        resolve_var = self.resolve_var

        rst_ttl = self.rst_ttl

        sc_idx = self.sc_idx

        sc_inc_id = self.sc_inc_id

        sc_int: Union[None, Unset, int]
        if isinstance(self.sc_int, Unset):
            sc_int = UNSET
        else:
            sc_int = self.sc_int

        server_name = self.server_name

        service_name = self.service_name

        spoe_engine_name = self.spoe_engine_name

        spoe_group_name = self.spoe_group_name

        switch_mode_proto = self.switch_mode_proto

        timeout: Union[None, Unset, int]
        if isinstance(self.timeout, Unset):
            timeout = UNSET
        else:
            timeout = self.timeout

        tos_value = self.tos_value

        track_key = self.track_key

        track_stick_counter: Union[None, Unset, int]
        if isinstance(self.track_stick_counter, Unset):
            track_stick_counter = UNSET
        else:
            track_stick_counter = self.track_stick_counter

        track_table = self.track_table

        var_format = self.var_format

        var_name = self.var_name

        var_scope = self.var_scope

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "type": type_,
            }
        )
        if action is not UNSET:
            field_dict["action"] = action
        if bandwidth_limit_limit is not UNSET:
            field_dict["bandwidth_limit_limit"] = bandwidth_limit_limit
        if bandwidth_limit_name is not UNSET:
            field_dict["bandwidth_limit_name"] = bandwidth_limit_name
        if bandwidth_limit_period is not UNSET:
            field_dict["bandwidth_limit_period"] = bandwidth_limit_period
        if capture_len is not UNSET:
            field_dict["capture_len"] = capture_len
        if capture_sample is not UNSET:
            field_dict["capture_sample"] = capture_sample
        if cond is not UNSET:
            field_dict["cond"] = cond
        if cond_test is not UNSET:
            field_dict["cond_test"] = cond_test
        if expr is not UNSET:
            field_dict["expr"] = expr
        if gpt_value is not UNSET:
            field_dict["gpt_value"] = gpt_value
        if log_level is not UNSET:
            field_dict["log_level"] = log_level
        if lua_action is not UNSET:
            field_dict["lua_action"] = lua_action
        if lua_params is not UNSET:
            field_dict["lua_params"] = lua_params
        if mark_value is not UNSET:
            field_dict["mark_value"] = mark_value
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if nice_value is not UNSET:
            field_dict["nice_value"] = nice_value
        if resolve_protocol is not UNSET:
            field_dict["resolve_protocol"] = resolve_protocol
        if resolve_resolvers is not UNSET:
            field_dict["resolve_resolvers"] = resolve_resolvers
        if resolve_var is not UNSET:
            field_dict["resolve_var"] = resolve_var
        if rst_ttl is not UNSET:
            field_dict["rst_ttl"] = rst_ttl
        if sc_idx is not UNSET:
            field_dict["sc_idx"] = sc_idx
        if sc_inc_id is not UNSET:
            field_dict["sc_inc_id"] = sc_inc_id
        if sc_int is not UNSET:
            field_dict["sc_int"] = sc_int
        if server_name is not UNSET:
            field_dict["server_name"] = server_name
        if service_name is not UNSET:
            field_dict["service_name"] = service_name
        if spoe_engine_name is not UNSET:
            field_dict["spoe_engine_name"] = spoe_engine_name
        if spoe_group_name is not UNSET:
            field_dict["spoe_group_name"] = spoe_group_name
        if switch_mode_proto is not UNSET:
            field_dict["switch_mode_proto"] = switch_mode_proto
        if timeout is not UNSET:
            field_dict["timeout"] = timeout
        if tos_value is not UNSET:
            field_dict["tos_value"] = tos_value
        if track_key is not UNSET:
            field_dict["track_key"] = track_key
        if track_stick_counter is not UNSET:
            field_dict["track_stick_counter"] = track_stick_counter
        if track_table is not UNSET:
            field_dict["track_table"] = track_table
        if var_format is not UNSET:
            field_dict["var_format"] = var_format
        if var_name is not UNSET:
            field_dict["var_name"] = var_name
        if var_scope is not UNSET:
            field_dict["var_scope"] = var_scope

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = TCPRequestRuleType(d.pop("type"))

        _action = d.pop("action", UNSET)
        action: Union[Unset, TCPRequestRuleAction]
        if isinstance(_action, Unset):
            action = UNSET
        else:
            action = TCPRequestRuleAction(_action)

        bandwidth_limit_limit = d.pop("bandwidth_limit_limit", UNSET)

        bandwidth_limit_name = d.pop("bandwidth_limit_name", UNSET)

        bandwidth_limit_period = d.pop("bandwidth_limit_period", UNSET)

        capture_len = d.pop("capture_len", UNSET)

        capture_sample = d.pop("capture_sample", UNSET)

        _cond = d.pop("cond", UNSET)
        cond: Union[Unset, TCPRequestRuleCond]
        if isinstance(_cond, Unset):
            cond = UNSET
        else:
            cond = TCPRequestRuleCond(_cond)

        cond_test = d.pop("cond_test", UNSET)

        expr = d.pop("expr", UNSET)

        gpt_value = d.pop("gpt_value", UNSET)

        _log_level = d.pop("log_level", UNSET)
        log_level: Union[Unset, TCPRequestRuleLogLevel]
        if isinstance(_log_level, Unset):
            log_level = UNSET
        else:
            log_level = TCPRequestRuleLogLevel(_log_level)

        lua_action = d.pop("lua_action", UNSET)

        lua_params = d.pop("lua_params", UNSET)

        mark_value = d.pop("mark_value", UNSET)

        metadata = d.pop("metadata", UNSET)

        nice_value = d.pop("nice_value", UNSET)

        _resolve_protocol = d.pop("resolve_protocol", UNSET)
        resolve_protocol: Union[Unset, TCPRequestRuleResolveProtocol]
        if isinstance(_resolve_protocol, Unset):
            resolve_protocol = UNSET
        else:
            resolve_protocol = TCPRequestRuleResolveProtocol(_resolve_protocol)

        resolve_resolvers = d.pop("resolve_resolvers", UNSET)

        resolve_var = d.pop("resolve_var", UNSET)

        rst_ttl = d.pop("rst_ttl", UNSET)

        sc_idx = d.pop("sc_idx", UNSET)

        sc_inc_id = d.pop("sc_inc_id", UNSET)

        def _parse_sc_int(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        sc_int = _parse_sc_int(d.pop("sc_int", UNSET))

        server_name = d.pop("server_name", UNSET)

        service_name = d.pop("service_name", UNSET)

        spoe_engine_name = d.pop("spoe_engine_name", UNSET)

        spoe_group_name = d.pop("spoe_group_name", UNSET)

        switch_mode_proto = d.pop("switch_mode_proto", UNSET)

        def _parse_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        timeout = _parse_timeout(d.pop("timeout", UNSET))

        tos_value = d.pop("tos_value", UNSET)

        track_key = d.pop("track_key", UNSET)

        def _parse_track_stick_counter(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        track_stick_counter = _parse_track_stick_counter(d.pop("track_stick_counter", UNSET))

        track_table = d.pop("track_table", UNSET)

        var_format = d.pop("var_format", UNSET)

        var_name = d.pop("var_name", UNSET)

        var_scope = d.pop("var_scope", UNSET)

        tcp_request_rule = cls(
            type_=type_,
            action=action,
            bandwidth_limit_limit=bandwidth_limit_limit,
            bandwidth_limit_name=bandwidth_limit_name,
            bandwidth_limit_period=bandwidth_limit_period,
            capture_len=capture_len,
            capture_sample=capture_sample,
            cond=cond,
            cond_test=cond_test,
            expr=expr,
            gpt_value=gpt_value,
            log_level=log_level,
            lua_action=lua_action,
            lua_params=lua_params,
            mark_value=mark_value,
            metadata=metadata,
            nice_value=nice_value,
            resolve_protocol=resolve_protocol,
            resolve_resolvers=resolve_resolvers,
            resolve_var=resolve_var,
            rst_ttl=rst_ttl,
            sc_idx=sc_idx,
            sc_inc_id=sc_inc_id,
            sc_int=sc_int,
            server_name=server_name,
            service_name=service_name,
            spoe_engine_name=spoe_engine_name,
            spoe_group_name=spoe_group_name,
            switch_mode_proto=switch_mode_proto,
            timeout=timeout,
            tos_value=tos_value,
            track_key=track_key,
            track_stick_counter=track_stick_counter,
            track_table=track_table,
            var_format=var_format,
            var_name=var_name,
            var_scope=var_scope,
        )

        return tcp_request_rule
