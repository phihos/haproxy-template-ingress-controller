from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.certificate_load_action import CertificateLoadAction


T = TypeVar("T", bound="CertificateStore")


@_attrs_define
class CertificateStore:
    """Storage mechanism to load and store certificates used in the configuration

    Attributes:
        name (str):
        crt_base (Union[Unset, str]): Default directory to fetch SSL certificates from
        key_base (Union[Unset, str]): Default directory to fetch SSL private keys from
        loads (Union[Unset, list['CertificateLoadAction']]): List of certificates to load from a Certificate Store
        metadata (Union[Unset, Any]):
    """

    name: str
    crt_base: Union[Unset, str] = UNSET
    key_base: Union[Unset, str] = UNSET
    loads: Union[Unset, list["CertificateLoadAction"]] = UNSET
    metadata: Union[Unset, Any] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        crt_base = self.crt_base

        key_base = self.key_base

        loads: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.loads, Unset):
            loads = []
            for componentsschemascrt_loads_item_data in self.loads:
                componentsschemascrt_loads_item = componentsschemascrt_loads_item_data.to_dict()
                loads.append(componentsschemascrt_loads_item)

        metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
            }
        )
        if crt_base is not UNSET:
            field_dict["crt_base"] = crt_base
        if key_base is not UNSET:
            field_dict["key_base"] = key_base
        if loads is not UNSET:
            field_dict["loads"] = loads
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.certificate_load_action import CertificateLoadAction

        d = dict(src_dict)
        name = d.pop("name")

        crt_base = d.pop("crt_base", UNSET)

        key_base = d.pop("key_base", UNSET)

        loads = []
        _loads = d.pop("loads", UNSET)
        for componentsschemascrt_loads_item_data in _loads or []:
            componentsschemascrt_loads_item = CertificateLoadAction.from_dict(componentsschemascrt_loads_item_data)

            loads.append(componentsschemascrt_loads_item)

        metadata = d.pop("metadata", UNSET)

        certificate_store = cls(
            name=name,
            crt_base=crt_base,
            key_base=key_base,
            loads=loads,
            metadata=metadata,
        )

        return certificate_store
