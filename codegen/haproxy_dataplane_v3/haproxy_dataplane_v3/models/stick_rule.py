from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..models.stick_rule_cond import StickRuleCond
from ..models.stick_rule_type import StickRuleType
from ..types import UNSET, Unset

T = TypeVar("T", bound="StickRule")


@_attrs_define
class StickRule:
    """Define a pattern used to create an entry in a stickiness table or matching condition or associate a user to a
    server.

        Example:
            {'pattern': 'src', 'type': 'match'}

        Attributes:
            pattern (str):
            type_ (StickRuleType):
            cond (Union[Unset, StickRuleCond]):
            cond_test (Union[Unset, str]):
            metadata (Union[Unset, Any]):
            table (Union[Unset, str]):
    """

    pattern: str
    type_: StickRuleType
    cond: Union[Unset, StickRuleCond] = UNSET
    cond_test: Union[Unset, str] = UNSET
    metadata: Union[Unset, Any] = UNSET
    table: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        pattern = self.pattern

        type_ = self.type_.value

        cond: Union[Unset, str] = UNSET
        if not isinstance(self.cond, Unset):
            cond = self.cond.value

        cond_test = self.cond_test

        metadata = self.metadata

        table = self.table

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "pattern": pattern,
                "type": type_,
            }
        )
        if cond is not UNSET:
            field_dict["cond"] = cond
        if cond_test is not UNSET:
            field_dict["cond_test"] = cond_test
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if table is not UNSET:
            field_dict["table"] = table

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        pattern = d.pop("pattern")

        type_ = StickRuleType(d.pop("type"))

        _cond = d.pop("cond", UNSET)
        cond: Union[Unset, StickRuleCond]
        if isinstance(_cond, Unset):
            cond = UNSET
        else:
            cond = StickRuleCond(_cond)

        cond_test = d.pop("cond_test", UNSET)

        metadata = d.pop("metadata", UNSET)

        table = d.pop("table", UNSET)

        stick_rule = cls(
            pattern=pattern,
            type_=type_,
            cond=cond,
            cond_test=cond_test,
            metadata=metadata,
            table=table,
        )

        return stick_rule
