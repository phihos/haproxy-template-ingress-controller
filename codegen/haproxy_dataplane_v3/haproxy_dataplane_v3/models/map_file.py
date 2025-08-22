from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="MapFile")


@_attrs_define
class MapFile:
    """Map File

    Attributes:
        description (Union[Unset, str]):
        file (Union[Unset, str]):
        id (Union[Unset, str]):
        size (Union[None, Unset, int]): File size in bytes.
        storage_name (Union[Unset, str]):
    """

    description: Union[Unset, str] = UNSET
    file: Union[Unset, str] = UNSET
    id: Union[Unset, str] = UNSET
    size: Union[None, Unset, int] = UNSET
    storage_name: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        description = self.description

        file = self.file

        id = self.id

        size: Union[None, Unset, int]
        if isinstance(self.size, Unset):
            size = UNSET
        else:
            size = self.size

        storage_name = self.storage_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if description is not UNSET:
            field_dict["description"] = description
        if file is not UNSET:
            field_dict["file"] = file
        if id is not UNSET:
            field_dict["id"] = id
        if size is not UNSET:
            field_dict["size"] = size
        if storage_name is not UNSET:
            field_dict["storage_name"] = storage_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        description = d.pop("description", UNSET)

        file = d.pop("file", UNSET)

        id = d.pop("id", UNSET)

        def _parse_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        size = _parse_size(d.pop("size", UNSET))

        storage_name = d.pop("storage_name", UNSET)

        map_file = cls(
            description=description,
            file=file,
            id=id,
            size=size,
            storage_name=storage_name,
        )

        map_file.additional_properties = d
        return map_file

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
