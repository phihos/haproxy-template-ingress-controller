from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.http_error_rule_return_content_format import HTTPErrorRuleReturnContentFormat
from ..models.http_error_rule_status import HTTPErrorRuleStatus
from ..models.http_error_rule_type import HTTPErrorRuleType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.return_header import ReturnHeader


T = TypeVar("T", bound="HTTPErrorRule")


@_attrs_define
class HTTPErrorRule:
    """HAProxy HTTP error rule configuration (corresponds to http-error directives)

    Example:
        {'index': 0, 'status': 425, 'type': 'status'}

    Attributes:
        status (HTTPErrorRuleStatus):
        type_ (HTTPErrorRuleType):
        metadata (Union[Unset, Any]):
        return_content (Union[Unset, str]):
        return_content_format (Union[Unset, HTTPErrorRuleReturnContentFormat]):
        return_content_type (Union[None, Unset, str]):
        return_hdrs (Union[Unset, list['ReturnHeader']]):
    """

    status: HTTPErrorRuleStatus
    type_: HTTPErrorRuleType
    metadata: Union[Unset, Any] = UNSET
    return_content: Union[Unset, str] = UNSET
    return_content_format: Union[Unset, HTTPErrorRuleReturnContentFormat] = UNSET
    return_content_type: Union[None, Unset, str] = UNSET
    return_hdrs: Union[Unset, list["ReturnHeader"]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        status = self.status.value

        type_ = self.type_.value

        metadata = self.metadata

        return_content = self.return_content

        return_content_format: Union[Unset, str] = UNSET
        if not isinstance(self.return_content_format, Unset):
            return_content_format = self.return_content_format.value

        return_content_type: Union[None, Unset, str]
        if isinstance(self.return_content_type, Unset):
            return_content_type = UNSET
        else:
            return_content_type = self.return_content_type

        return_hdrs: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.return_hdrs, Unset):
            return_hdrs = []
            for return_hdrs_item_data in self.return_hdrs:
                return_hdrs_item = return_hdrs_item_data.to_dict()
                return_hdrs.append(return_hdrs_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "status": status,
                "type": type_,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if return_content is not UNSET:
            field_dict["return_content"] = return_content
        if return_content_format is not UNSET:
            field_dict["return_content_format"] = return_content_format
        if return_content_type is not UNSET:
            field_dict["return_content_type"] = return_content_type
        if return_hdrs is not UNSET:
            field_dict["return_hdrs"] = return_hdrs

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.return_header import ReturnHeader

        d = dict(src_dict)
        status = HTTPErrorRuleStatus(d.pop("status"))

        type_ = HTTPErrorRuleType(d.pop("type"))

        metadata = d.pop("metadata", UNSET)

        return_content = d.pop("return_content", UNSET)

        _return_content_format = d.pop("return_content_format", UNSET)
        return_content_format: Union[Unset, HTTPErrorRuleReturnContentFormat]
        if isinstance(_return_content_format, Unset):
            return_content_format = UNSET
        else:
            return_content_format = HTTPErrorRuleReturnContentFormat(_return_content_format)

        def _parse_return_content_type(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        return_content_type = _parse_return_content_type(d.pop("return_content_type", UNSET))

        return_hdrs = []
        _return_hdrs = d.pop("return_hdrs", UNSET)
        for return_hdrs_item_data in _return_hdrs or []:
            return_hdrs_item = ReturnHeader.from_dict(return_hdrs_item_data)

            return_hdrs.append(return_hdrs_item)

        http_error_rule = cls(
            status=status,
            type_=type_,
            metadata=metadata,
            return_content=return_content,
            return_content_format=return_content_format,
            return_content_type=return_content_type,
            return_hdrs=return_hdrs,
        )

        return http_error_rule
