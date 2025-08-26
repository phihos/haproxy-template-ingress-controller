from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..models.quic_initial_cond import QUICInitialCond
from ..models.quic_initial_type import QUICInitialType
from ..types import UNSET, Unset

T = TypeVar("T", bound="QUICInitial")


@_attrs_define
class QUICInitial:
    """QUIC Initial configuration

    Example:
        {'type': 'reject'}

    Attributes:
        type_ (QUICInitialType):
        cond (Union[Unset, QUICInitialCond]):
        cond_test (Union[Unset, str]):
        metadata (Union[Unset, Any]):
    """

    type_: QUICInitialType
    cond: Union[Unset, QUICInitialCond] = UNSET
    cond_test: Union[Unset, str] = UNSET
    metadata: Union[Unset, Any] = UNSET

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        cond: Union[Unset, str] = UNSET
        if not isinstance(self.cond, Unset):
            cond = self.cond.value

        cond_test = self.cond_test

        metadata = self.metadata

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "type": type_,
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
        type_ = QUICInitialType(d.pop("type"))

        _cond = d.pop("cond", UNSET)
        cond: Union[Unset, QUICInitialCond]
        if isinstance(_cond, Unset):
            cond = UNSET
        else:
            cond = QUICInitialCond(_cond)

        cond_test = d.pop("cond_test", UNSET)

        metadata = d.pop("metadata", UNSET)

        quic_initial = cls(
            type_=type_,
            cond=cond,
            cond_test=cond_test,
            metadata=metadata,
        )

        return quic_initial
