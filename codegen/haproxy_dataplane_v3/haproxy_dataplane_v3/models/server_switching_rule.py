from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..models.server_switching_rule_cond import ServerSwitchingRuleCond
from ..types import UNSET, Unset

T = TypeVar("T", bound="ServerSwitchingRule")


@_attrs_define
class ServerSwitchingRule:
    """HAProxy server switching rule configuration (corresponds to use-server directive)

    Example:
        {'cond': 'if', 'cond_test': '{ req_ssl_sni -i www.example.com }', 'target_server': 'www'}

    Attributes:
        target_server (str):
        cond (Union[Unset, ServerSwitchingRuleCond]):
        cond_test (Union[Unset, str]):
        metadata (Union[Unset, Any]):
    """

    target_server: str
    cond: Union[Unset, ServerSwitchingRuleCond] = UNSET
    cond_test: Union[Unset, str] = UNSET
    metadata: Union[Unset, Any] = UNSET

    def to_dict(self) -> dict[str, Any]:
        target_server = self.target_server

        cond: Union[Unset, str] = UNSET
        if not isinstance(self.cond, Unset):
            cond = self.cond.value

        cond_test = self.cond_test

        metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "target_server": target_server,
            }
        )
        if cond is not UNSET:
            field_dict["cond"] = cond
        if cond_test is not UNSET:
            field_dict["cond_test"] = cond_test
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        target_server = d.pop("target_server")

        _cond = d.pop("cond", UNSET)
        cond: Union[Unset, ServerSwitchingRuleCond]
        if isinstance(_cond, Unset):
            cond = UNSET
        else:
            cond = ServerSwitchingRuleCond(_cond)

        cond_test = d.pop("cond_test", UNSET)

        metadata = d.pop("metadata", UNSET)

        server_switching_rule = cls(
            target_server=target_server,
            cond=cond,
            cond_test=cond_test,
            metadata=metadata,
        )

        return server_switching_rule
