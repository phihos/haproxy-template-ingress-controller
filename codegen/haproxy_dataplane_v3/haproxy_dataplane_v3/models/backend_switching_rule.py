from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..models.backend_switching_rule_cond import BackendSwitchingRuleCond
from ..types import UNSET, Unset

T = TypeVar("T", bound="BackendSwitchingRule")


@_attrs_define
class BackendSwitchingRule:
    """HAProxy backend switching rule configuration (corresponds to use_backend directive)

    Example:
        {'cond': 'if', 'cond_test': '{ req_ssl_sni -i www.example.com }', 'index': 0, 'name': 'test_backend'}

    Attributes:
        name (str):
        cond (Union[Unset, BackendSwitchingRuleCond]):
        cond_test (Union[Unset, str]):
        metadata (Union[Unset, Any]):
    """

    name: str
    cond: Union[Unset, BackendSwitchingRuleCond] = UNSET
    cond_test: Union[Unset, str] = UNSET
    metadata: Union[Unset, Any] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        cond: Union[Unset, str] = UNSET
        if not isinstance(self.cond, Unset):
            cond = self.cond.value

        cond_test = self.cond_test

        metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
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
        name = d.pop("name")

        _cond = d.pop("cond", UNSET)
        cond: Union[Unset, BackendSwitchingRuleCond]
        if isinstance(_cond, Unset):
            cond = UNSET
        else:
            cond = BackendSwitchingRuleCond(_cond)

        cond_test = d.pop("cond_test", UNSET)

        metadata = d.pop("metadata", UNSET)

        backend_switching_rule = cls(
            name=name,
            cond=cond,
            cond_test=cond_test,
            metadata=metadata,
        )

        return backend_switching_rule
