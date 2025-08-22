from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.tcp_response_rule_action import TCPResponseRuleAction
from ..models.tcp_response_rule_cond import TCPResponseRuleCond
from ..models.tcp_response_rule_log_level import TCPResponseRuleLogLevel
from ..models.tcp_response_rule_type import TCPResponseRuleType
from ..types import UNSET, Unset

T = TypeVar("T", bound="TCPResponseRule")


@_attrs_define
class TCPResponseRule:
    """HAProxy TCP Response Rule configuration (corresponds to tcp-response)

    Example:
        {'cond': 'if', 'cond_test': '{ src 192.168.0.0/16 }', 'index': 0, 'type': 'content'}

    Attributes:
        type_ (TCPResponseRuleType):
        action (Union[Unset, TCPResponseRuleAction]):
        bandwidth_limit_limit (Union[Unset, str]):
        bandwidth_limit_name (Union[Unset, str]):
        bandwidth_limit_period (Union[Unset, str]):
        cond (Union[Unset, TCPResponseRuleCond]):
        cond_test (Union[Unset, str]):
        expr (Union[Unset, str]):
        log_level (Union[Unset, TCPResponseRuleLogLevel]):
        lua_action (Union[Unset, str]):
        lua_params (Union[Unset, str]):
        mark_value (Union[Unset, str]):
        metadata (Union[Unset, Any]):
        nice_value (Union[Unset, int]):
        rst_ttl (Union[Unset, int]):
        sc_expr (Union[Unset, str]):
        sc_id (Union[Unset, int]):
        sc_idx (Union[Unset, int]):
        sc_int (Union[None, Unset, int]):
        spoe_engine (Union[Unset, str]):
        spoe_group (Union[Unset, str]):
        timeout (Union[None, Unset, int]):
        tos_value (Union[Unset, str]):
        var_format (Union[Unset, str]):
        var_name (Union[Unset, str]):
        var_scope (Union[Unset, str]):
    """

    type_: TCPResponseRuleType
    action: Union[Unset, TCPResponseRuleAction] = UNSET
    bandwidth_limit_limit: Union[Unset, str] = UNSET
    bandwidth_limit_name: Union[Unset, str] = UNSET
    bandwidth_limit_period: Union[Unset, str] = UNSET
    cond: Union[Unset, TCPResponseRuleCond] = UNSET
    cond_test: Union[Unset, str] = UNSET
    expr: Union[Unset, str] = UNSET
    log_level: Union[Unset, TCPResponseRuleLogLevel] = UNSET
    lua_action: Union[Unset, str] = UNSET
    lua_params: Union[Unset, str] = UNSET
    mark_value: Union[Unset, str] = UNSET
    metadata: Union[Unset, Any] = UNSET
    nice_value: Union[Unset, int] = UNSET
    rst_ttl: Union[Unset, int] = UNSET
    sc_expr: Union[Unset, str] = UNSET
    sc_id: Union[Unset, int] = UNSET
    sc_idx: Union[Unset, int] = UNSET
    sc_int: Union[None, Unset, int] = UNSET
    spoe_engine: Union[Unset, str] = UNSET
    spoe_group: Union[Unset, str] = UNSET
    timeout: Union[None, Unset, int] = UNSET
    tos_value: Union[Unset, str] = UNSET
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

        cond: Union[Unset, str] = UNSET
        if not isinstance(self.cond, Unset):
            cond = self.cond.value

        cond_test = self.cond_test

        expr = self.expr

        log_level: Union[Unset, str] = UNSET
        if not isinstance(self.log_level, Unset):
            log_level = self.log_level.value

        lua_action = self.lua_action

        lua_params = self.lua_params

        mark_value = self.mark_value

        metadata = self.metadata

        nice_value = self.nice_value

        rst_ttl = self.rst_ttl

        sc_expr = self.sc_expr

        sc_id = self.sc_id

        sc_idx = self.sc_idx

        sc_int: Union[None, Unset, int]
        if isinstance(self.sc_int, Unset):
            sc_int = UNSET
        else:
            sc_int = self.sc_int

        spoe_engine = self.spoe_engine

        spoe_group = self.spoe_group

        timeout: Union[None, Unset, int]
        if isinstance(self.timeout, Unset):
            timeout = UNSET
        else:
            timeout = self.timeout

        tos_value = self.tos_value

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
        if cond is not UNSET:
            field_dict["cond"] = cond
        if cond_test is not UNSET:
            field_dict["cond_test"] = cond_test
        if expr is not UNSET:
            field_dict["expr"] = expr
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
        if spoe_engine is not UNSET:
            field_dict["spoe_engine"] = spoe_engine
        if spoe_group is not UNSET:
            field_dict["spoe_group"] = spoe_group
        if timeout is not UNSET:
            field_dict["timeout"] = timeout
        if tos_value is not UNSET:
            field_dict["tos_value"] = tos_value
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
        type_ = TCPResponseRuleType(d.pop("type"))

        _action = d.pop("action", UNSET)
        action: Union[Unset, TCPResponseRuleAction]
        if isinstance(_action, Unset):
            action = UNSET
        else:
            action = TCPResponseRuleAction(_action)

        bandwidth_limit_limit = d.pop("bandwidth_limit_limit", UNSET)

        bandwidth_limit_name = d.pop("bandwidth_limit_name", UNSET)

        bandwidth_limit_period = d.pop("bandwidth_limit_period", UNSET)

        _cond = d.pop("cond", UNSET)
        cond: Union[Unset, TCPResponseRuleCond]
        if isinstance(_cond, Unset):
            cond = UNSET
        else:
            cond = TCPResponseRuleCond(_cond)

        cond_test = d.pop("cond_test", UNSET)

        expr = d.pop("expr", UNSET)

        _log_level = d.pop("log_level", UNSET)
        log_level: Union[Unset, TCPResponseRuleLogLevel]
        if isinstance(_log_level, Unset):
            log_level = UNSET
        else:
            log_level = TCPResponseRuleLogLevel(_log_level)

        lua_action = d.pop("lua_action", UNSET)

        lua_params = d.pop("lua_params", UNSET)

        mark_value = d.pop("mark_value", UNSET)

        metadata = d.pop("metadata", UNSET)

        nice_value = d.pop("nice_value", UNSET)

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

        spoe_engine = d.pop("spoe_engine", UNSET)

        spoe_group = d.pop("spoe_group", UNSET)

        def _parse_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        timeout = _parse_timeout(d.pop("timeout", UNSET))

        tos_value = d.pop("tos_value", UNSET)

        var_format = d.pop("var_format", UNSET)

        var_name = d.pop("var_name", UNSET)

        var_scope = d.pop("var_scope", UNSET)

        tcp_response_rule = cls(
            type_=type_,
            action=action,
            bandwidth_limit_limit=bandwidth_limit_limit,
            bandwidth_limit_name=bandwidth_limit_name,
            bandwidth_limit_period=bandwidth_limit_period,
            cond=cond,
            cond_test=cond_test,
            expr=expr,
            log_level=log_level,
            lua_action=lua_action,
            lua_params=lua_params,
            mark_value=mark_value,
            metadata=metadata,
            nice_value=nice_value,
            rst_ttl=rst_ttl,
            sc_expr=sc_expr,
            sc_id=sc_id,
            sc_idx=sc_idx,
            sc_int=sc_int,
            spoe_engine=spoe_engine,
            spoe_group=spoe_group,
            timeout=timeout,
            tos_value=tos_value,
            var_format=var_format,
            var_name=var_name,
            var_scope=var_scope,
        )

        return tcp_response_rule
