from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.fcgi_log_stderr_sample import FcgiLogStderrSample


T = TypeVar("T", bound="FcgiLogStderr")


@_attrs_define
class FcgiLogStderr:
    """Enables logging of STDERR messages that the FastCGI application reports.
    It is an optional setting. By default, HAProxy Enterprise ignores STDERR messages.

        Attributes:
            address (Union[Unset, str]):
            facility (Union[Unset, str]):
            format_ (Union[Unset, str]):
            global_ (Union[Unset, bool]):
            len_ (Union[Unset, int]):
            level (Union[Unset, str]):
            minlevel (Union[Unset, str]):
            sample (Union[Unset, FcgiLogStderrSample]):
    """

    address: Union[Unset, str] = UNSET
    facility: Union[Unset, str] = UNSET
    format_: Union[Unset, str] = UNSET
    global_: Union[Unset, bool] = UNSET
    len_: Union[Unset, int] = UNSET
    level: Union[Unset, str] = UNSET
    minlevel: Union[Unset, str] = UNSET
    sample: Union[Unset, "FcgiLogStderrSample"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        address = self.address

        facility = self.facility

        format_ = self.format_

        global_ = self.global_

        len_ = self.len_

        level = self.level

        minlevel = self.minlevel

        sample: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.sample, Unset):
            sample = self.sample.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if address is not UNSET:
            field_dict["address"] = address
        if facility is not UNSET:
            field_dict["facility"] = facility
        if format_ is not UNSET:
            field_dict["format"] = format_
        if global_ is not UNSET:
            field_dict["global"] = global_
        if len_ is not UNSET:
            field_dict["len"] = len_
        if level is not UNSET:
            field_dict["level"] = level
        if minlevel is not UNSET:
            field_dict["minlevel"] = minlevel
        if sample is not UNSET:
            field_dict["sample"] = sample

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.fcgi_log_stderr_sample import FcgiLogStderrSample

        d = dict(src_dict)
        address = d.pop("address", UNSET)

        facility = d.pop("facility", UNSET)

        format_ = d.pop("format", UNSET)

        global_ = d.pop("global", UNSET)

        len_ = d.pop("len", UNSET)

        level = d.pop("level", UNSET)

        minlevel = d.pop("minlevel", UNSET)

        _sample = d.pop("sample", UNSET)
        sample: Union[Unset, FcgiLogStderrSample]
        if isinstance(_sample, Unset):
            sample = UNSET
        else:
            sample = FcgiLogStderrSample.from_dict(_sample)

        fcgi_log_stderr = cls(
            address=address,
            facility=facility,
            format_=format_,
            global_=global_,
            len_=len_,
            level=level,
            minlevel=minlevel,
            sample=sample,
        )

        fcgi_log_stderr.additional_properties = d
        return fcgi_log_stderr

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
