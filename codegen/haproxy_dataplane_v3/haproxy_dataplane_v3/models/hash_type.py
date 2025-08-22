from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.hash_type_function import HashTypeFunction
from ..models.hash_type_method import HashTypeMethod
from ..models.hash_type_modifier import HashTypeModifier
from ..types import UNSET, Unset

T = TypeVar("T", bound="HashType")


@_attrs_define
class HashType:
    """
    Attributes:
        function (Union[Unset, HashTypeFunction]):
        method (Union[Unset, HashTypeMethod]):
        modifier (Union[Unset, HashTypeModifier]):
    """

    function: Union[Unset, HashTypeFunction] = UNSET
    method: Union[Unset, HashTypeMethod] = UNSET
    modifier: Union[Unset, HashTypeModifier] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        function: Union[Unset, str] = UNSET
        if not isinstance(self.function, Unset):
            function = self.function.value

        method: Union[Unset, str] = UNSET
        if not isinstance(self.method, Unset):
            method = self.method.value

        modifier: Union[Unset, str] = UNSET
        if not isinstance(self.modifier, Unset):
            modifier = self.modifier.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if function is not UNSET:
            field_dict["function"] = function
        if method is not UNSET:
            field_dict["method"] = method
        if modifier is not UNSET:
            field_dict["modifier"] = modifier

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _function = d.pop("function", UNSET)
        function: Union[Unset, HashTypeFunction]
        if isinstance(_function, Unset):
            function = UNSET
        else:
            function = HashTypeFunction(_function)

        _method = d.pop("method", UNSET)
        method: Union[Unset, HashTypeMethod]
        if isinstance(_method, Unset):
            method = UNSET
        else:
            method = HashTypeMethod(_method)

        _modifier = d.pop("modifier", UNSET)
        modifier: Union[Unset, HashTypeModifier]
        if isinstance(_modifier, Unset):
            modifier = UNSET
        else:
            modifier = HashTypeModifier(_modifier)

        hash_type = cls(
            function=function,
            method=method,
            modifier=modifier,
        )

        hash_type.additional_properties = d
        return hash_type

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
