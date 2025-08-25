from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.errorfile import Errorfile


T = TypeVar("T", bound="HttpErrorsSection")


@_attrs_define
class HttpErrorsSection:
    """A globally declared group of HTTP errors

    Example:
        {'error_files': [{'code': 400, 'name': '/etc/haproxy/errorfiles/site1/400.http'}, {'code': 404, 'name':
            '/etc/haproxy/errorfiles/site1/404.http'}], 'name': 'website-1'}

    Attributes:
        error_files (list['Errorfile']):
        name (str):
        metadata (Union[Unset, Any]):
    """

    error_files: list["Errorfile"]
    name: str
    metadata: Union[Unset, Any] = UNSET

    def to_dict(self) -> dict[str, Any]:
        error_files = []
        for error_files_item_data in self.error_files:
            error_files_item = error_files_item_data.to_dict()
            error_files.append(error_files_item)

        name = self.name

        metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "error_files": error_files,
                "name": name,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.errorfile import Errorfile

        d = dict(src_dict)
        error_files = []
        _error_files = d.pop("error_files")
        for error_files_item_data in _error_files:
            error_files_item = Errorfile.from_dict(error_files_item_data)

            error_files.append(error_files_item)

        name = d.pop("name")

        metadata = d.pop("metadata", UNSET)

        http_errors_section = cls(
            error_files=error_files,
            name=name,
            metadata=metadata,
        )

        return http_errors_section
