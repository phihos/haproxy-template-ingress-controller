from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.spoe_configuration_transaction_status import SPOEConfigurationTransactionStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="SPOEConfigurationTransaction")


@_attrs_define
class SPOEConfigurationTransaction:
    """SPOE configuration transaction

    Example:
        {'_version': 2, 'id': '273e3385-2d0c-4fb1-aa27-93cbb31ff203', 'status': 'in_progress'}

    Attributes:
        field_version (Union[Unset, int]):
        id (Union[Unset, str]):
        status (Union[Unset, SPOEConfigurationTransactionStatus]):
    """

    field_version: Union[Unset, int] = UNSET
    id: Union[Unset, str] = UNSET
    status: Union[Unset, SPOEConfigurationTransactionStatus] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field_version = self.field_version

        id = self.id

        status: Union[Unset, str] = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if field_version is not UNSET:
            field_dict["_version"] = field_version
        if id is not UNSET:
            field_dict["id"] = id
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        field_version = d.pop("_version", UNSET)

        id = d.pop("id", UNSET)

        _status = d.pop("status", UNSET)
        status: Union[Unset, SPOEConfigurationTransactionStatus]
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = SPOEConfigurationTransactionStatus(_status)

        spoe_configuration_transaction = cls(
            field_version=field_version,
            id=id,
            status=status,
        )

        spoe_configuration_transaction.additional_properties = d
        return spoe_configuration_transaction

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
