from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.http_after_response_rule_cond import HTTPAfterResponseRuleCond
from ..models.http_after_response_rule_log_level import HTTPAfterResponseRuleLogLevel
from ..models.http_after_response_rule_strict_mode import HTTPAfterResponseRuleStrictMode
from ..models.http_after_response_rule_type import HTTPAfterResponseRuleType
from ..types import UNSET, Unset

T = TypeVar("T", bound="HTTPAfterResponseRule")


@_attrs_define
class HTTPAfterResponseRule:
    """HAProxy HTTP after response rule configuration (corresponds to http-after-response directives)

    Example:
        {'cond': 'unless', 'cond_test': '{ src 192.168.0.0/16 }', 'hdr_format': 'max-age=31536000', 'hdr_name': 'Strict-
            Transport-Security', 'type': 'set-header'}

    Attributes:
        type_ (HTTPAfterResponseRuleType):
        acl_file (Union[Unset, str]):
        acl_keyfmt (Union[Unset, str]):
        capture_id (Union[None, Unset, int]):
        capture_len (Union[Unset, int]):
        capture_sample (Union[Unset, str]):
        cond (Union[Unset, HTTPAfterResponseRuleCond]):
        cond_test (Union[Unset, str]):
        hdr_format (Union[Unset, str]):
        hdr_match (Union[Unset, str]):
        hdr_method (Union[Unset, str]):
        hdr_name (Union[Unset, str]):
        log_level (Union[Unset, HTTPAfterResponseRuleLogLevel]):
        map_file (Union[Unset, str]):
        map_keyfmt (Union[Unset, str]):
        map_valuefmt (Union[Unset, str]):
        metadata (Union[Unset, Any]):
        sc_expr (Union[Unset, str]):
        sc_id (Union[Unset, int]):
        sc_idx (Union[Unset, int]):
        sc_int (Union[None, Unset, int]):
        status (Union[Unset, int]):
        status_reason (Union[Unset, str]):
        strict_mode (Union[Unset, HTTPAfterResponseRuleStrictMode]):
        var_expr (Union[Unset, str]):
        var_format (Union[Unset, str]):
        var_name (Union[Unset, str]):
        var_scope (Union[Unset, str]):
    """

    type_: HTTPAfterResponseRuleType
    acl_file: Union[Unset, str] = UNSET
    acl_keyfmt: Union[Unset, str] = UNSET
    capture_id: Union[None, Unset, int] = UNSET
    capture_len: Union[Unset, int] = UNSET
    capture_sample: Union[Unset, str] = UNSET
    cond: Union[Unset, HTTPAfterResponseRuleCond] = UNSET
    cond_test: Union[Unset, str] = UNSET
    hdr_format: Union[Unset, str] = UNSET
    hdr_match: Union[Unset, str] = UNSET
    hdr_method: Union[Unset, str] = UNSET
    hdr_name: Union[Unset, str] = UNSET
    log_level: Union[Unset, HTTPAfterResponseRuleLogLevel] = UNSET
    map_file: Union[Unset, str] = UNSET
    map_keyfmt: Union[Unset, str] = UNSET
    map_valuefmt: Union[Unset, str] = UNSET
    metadata: Union[Unset, Any] = UNSET
    sc_expr: Union[Unset, str] = UNSET
    sc_id: Union[Unset, int] = UNSET
    sc_idx: Union[Unset, int] = UNSET
    sc_int: Union[None, Unset, int] = UNSET
    status: Union[Unset, int] = UNSET
    status_reason: Union[Unset, str] = UNSET
    strict_mode: Union[Unset, HTTPAfterResponseRuleStrictMode] = UNSET
    var_expr: Union[Unset, str] = UNSET
    var_format: Union[Unset, str] = UNSET
    var_name: Union[Unset, str] = UNSET
    var_scope: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        acl_file = self.acl_file

        acl_keyfmt = self.acl_keyfmt

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

        hdr_format = self.hdr_format

        hdr_match = self.hdr_match

        hdr_method = self.hdr_method

        hdr_name = self.hdr_name

        log_level: Union[Unset, str] = UNSET
        if not isinstance(self.log_level, Unset):
            log_level = self.log_level.value

        map_file = self.map_file

        map_keyfmt = self.map_keyfmt

        map_valuefmt = self.map_valuefmt

        metadata = self.metadata

        sc_expr = self.sc_expr

        sc_id = self.sc_id

        sc_idx = self.sc_idx

        sc_int: Union[None, Unset, int]
        if isinstance(self.sc_int, Unset):
            sc_int = UNSET
        else:
            sc_int = self.sc_int

        status = self.status

        status_reason = self.status_reason

        strict_mode: Union[Unset, str] = UNSET
        if not isinstance(self.strict_mode, Unset):
            strict_mode = self.strict_mode.value

        var_expr = self.var_expr

        var_format = self.var_format

        var_name = self.var_name

        var_scope = self.var_scope

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
        if hdr_format is not UNSET:
            field_dict["hdr_format"] = hdr_format
        if hdr_match is not UNSET:
            field_dict["hdr_match"] = hdr_match
        if hdr_method is not UNSET:
            field_dict["hdr_method"] = hdr_method
        if hdr_name is not UNSET:
            field_dict["hdr_name"] = hdr_name
        if log_level is not UNSET:
            field_dict["log_level"] = log_level
        if map_file is not UNSET:
            field_dict["map_file"] = map_file
        if map_keyfmt is not UNSET:
            field_dict["map_keyfmt"] = map_keyfmt
        if map_valuefmt is not UNSET:
            field_dict["map_valuefmt"] = map_valuefmt
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if sc_expr is not UNSET:
            field_dict["sc_expr"] = sc_expr
        if sc_id is not UNSET:
            field_dict["sc_id"] = sc_id
        if sc_idx is not UNSET:
            field_dict["sc_idx"] = sc_idx
        if sc_int is not UNSET:
            field_dict["sc_int"] = sc_int
        if status is not UNSET:
            field_dict["status"] = status
        if status_reason is not UNSET:
            field_dict["status_reason"] = status_reason
        if strict_mode is not UNSET:
            field_dict["strict_mode"] = strict_mode
        if var_expr is not UNSET:
            field_dict["var_expr"] = var_expr
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
        type_ = HTTPAfterResponseRuleType(d.pop("type"))

        acl_file = d.pop("acl_file", UNSET)

        acl_keyfmt = d.pop("acl_keyfmt", UNSET)

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
        cond: Union[Unset, HTTPAfterResponseRuleCond]
        if isinstance(_cond, Unset):
            cond = UNSET
        else:
            cond = HTTPAfterResponseRuleCond(_cond)

        cond_test = d.pop("cond_test", UNSET)

        hdr_format = d.pop("hdr_format", UNSET)

        hdr_match = d.pop("hdr_match", UNSET)

        hdr_method = d.pop("hdr_method", UNSET)

        hdr_name = d.pop("hdr_name", UNSET)

        _log_level = d.pop("log_level", UNSET)
        log_level: Union[Unset, HTTPAfterResponseRuleLogLevel]
        if isinstance(_log_level, Unset):
            log_level = UNSET
        else:
            log_level = HTTPAfterResponseRuleLogLevel(_log_level)

        map_file = d.pop("map_file", UNSET)

        map_keyfmt = d.pop("map_keyfmt", UNSET)

        map_valuefmt = d.pop("map_valuefmt", UNSET)

        metadata = d.pop("metadata", UNSET)

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

        status = d.pop("status", UNSET)

        status_reason = d.pop("status_reason", UNSET)

        _strict_mode = d.pop("strict_mode", UNSET)
        strict_mode: Union[Unset, HTTPAfterResponseRuleStrictMode]
        if isinstance(_strict_mode, Unset):
            strict_mode = UNSET
        else:
            strict_mode = HTTPAfterResponseRuleStrictMode(_strict_mode)

        var_expr = d.pop("var_expr", UNSET)

        var_format = d.pop("var_format", UNSET)

        var_name = d.pop("var_name", UNSET)

        var_scope = d.pop("var_scope", UNSET)

        http_after_response_rule = cls(
            type_=type_,
            acl_file=acl_file,
            acl_keyfmt=acl_keyfmt,
            capture_id=capture_id,
            capture_len=capture_len,
            capture_sample=capture_sample,
            cond=cond,
            cond_test=cond_test,
            hdr_format=hdr_format,
            hdr_match=hdr_match,
            hdr_method=hdr_method,
            hdr_name=hdr_name,
            log_level=log_level,
            map_file=map_file,
            map_keyfmt=map_keyfmt,
            map_valuefmt=map_valuefmt,
            metadata=metadata,
            sc_expr=sc_expr,
            sc_id=sc_id,
            sc_idx=sc_idx,
            sc_int=sc_int,
            status=status,
            status_reason=status_reason,
            strict_mode=strict_mode,
            var_expr=var_expr,
            var_format=var_format,
            var_name=var_name,
            var_scope=var_scope,
        )

        return http_after_response_rule
