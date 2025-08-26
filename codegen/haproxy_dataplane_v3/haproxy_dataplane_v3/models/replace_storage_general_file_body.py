from collections.abc import Mapping
from io import BytesIO
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from .. import types
from ..types import UNSET, File, FileTypes, Unset

T = TypeVar("T", bound="ReplaceStorageGeneralFileBody")


@_attrs_define
class ReplaceStorageGeneralFileBody:
    """
    Attributes:
        file_upload (Union[Unset, File]): General use file content
    """

    file_upload: Union[Unset, File] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file_upload: Union[Unset, FileTypes] = UNSET
        if not isinstance(self.file_upload, Unset):
            file_upload = self.file_upload.to_tuple()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if file_upload is not UNSET:
            field_dict["file_upload"] = file_upload

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        if not isinstance(self.file_upload, Unset):
            files.append(("file_upload", self.file_upload.to_tuple()))

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _file_upload = d.pop("file_upload", UNSET)
        file_upload: Union[Unset, File]
        if isinstance(_file_upload, Unset):
            file_upload = UNSET
        else:
            file_upload = File(payload=BytesIO(_file_upload))

        replace_storage_general_file_body = cls(
            file_upload=file_upload,
        )

        replace_storage_general_file_body.additional_properties = d
        return replace_storage_general_file_body

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
