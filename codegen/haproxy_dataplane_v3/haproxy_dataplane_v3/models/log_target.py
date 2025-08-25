from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..models.log_target_facility import LogTargetFacility
from ..models.log_target_format import LogTargetFormat
from ..models.log_target_level import LogTargetLevel
from ..models.log_target_minlevel import LogTargetMinlevel
from ..types import UNSET, Unset

T = TypeVar("T", bound="LogTarget")


@_attrs_define
class LogTarget:
    """Per-instance logging of events and traffic.

    Attributes:
        address (Union[Unset, str]):
        facility (Union[Unset, LogTargetFacility]):
        format_ (Union[Unset, LogTargetFormat]):
        global_ (Union[Unset, bool]):
        length (Union[Unset, int]):
        level (Union[Unset, LogTargetLevel]):
        metadata (Union[Unset, Any]):
        minlevel (Union[Unset, LogTargetMinlevel]):
        nolog (Union[Unset, bool]):
        profile (Union[Unset, str]):
        sample_range (Union[Unset, str]):
        sample_size (Union[Unset, int]):
    """

    address: Union[Unset, str] = UNSET
    facility: Union[Unset, LogTargetFacility] = UNSET
    format_: Union[Unset, LogTargetFormat] = UNSET
    global_: Union[Unset, bool] = UNSET
    length: Union[Unset, int] = UNSET
    level: Union[Unset, LogTargetLevel] = UNSET
    metadata: Union[Unset, Any] = UNSET
    minlevel: Union[Unset, LogTargetMinlevel] = UNSET
    nolog: Union[Unset, bool] = UNSET
    profile: Union[Unset, str] = UNSET
    sample_range: Union[Unset, str] = UNSET
    sample_size: Union[Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        address = self.address

        facility: Union[Unset, str] = UNSET
        if not isinstance(self.facility, Unset):
            facility = self.facility.value

        format_: Union[Unset, str] = UNSET
        if not isinstance(self.format_, Unset):
            format_ = self.format_.value

        global_ = self.global_

        length = self.length

        level: Union[Unset, str] = UNSET
        if not isinstance(self.level, Unset):
            level = self.level.value

        metadata = self.metadata

        minlevel: Union[Unset, str] = UNSET
        if not isinstance(self.minlevel, Unset):
            minlevel = self.minlevel.value

        nolog = self.nolog

        profile = self.profile

        sample_range = self.sample_range

        sample_size = self.sample_size

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if address is not UNSET:
            field_dict["address"] = address
        if facility is not UNSET:
            field_dict["facility"] = facility
        if format_ is not UNSET:
            field_dict["format"] = format_
        if global_ is not UNSET:
            field_dict["global"] = global_
        if length is not UNSET:
            field_dict["length"] = length
        if level is not UNSET:
            field_dict["level"] = level
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if minlevel is not UNSET:
            field_dict["minlevel"] = minlevel
        if nolog is not UNSET:
            field_dict["nolog"] = nolog
        if profile is not UNSET:
            field_dict["profile"] = profile
        if sample_range is not UNSET:
            field_dict["sample_range"] = sample_range
        if sample_size is not UNSET:
            field_dict["sample_size"] = sample_size

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        address = d.pop("address", UNSET)

        _facility = d.pop("facility", UNSET)
        facility: Union[Unset, LogTargetFacility]
        if isinstance(_facility, Unset):
            facility = UNSET
        else:
            facility = LogTargetFacility(_facility)

        _format_ = d.pop("format", UNSET)
        format_: Union[Unset, LogTargetFormat]
        if isinstance(_format_, Unset):
            format_ = UNSET
        else:
            format_ = LogTargetFormat(_format_)

        global_ = d.pop("global", UNSET)

        length = d.pop("length", UNSET)

        _level = d.pop("level", UNSET)
        level: Union[Unset, LogTargetLevel]
        if isinstance(_level, Unset):
            level = UNSET
        else:
            level = LogTargetLevel(_level)

        metadata = d.pop("metadata", UNSET)

        _minlevel = d.pop("minlevel", UNSET)
        minlevel: Union[Unset, LogTargetMinlevel]
        if isinstance(_minlevel, Unset):
            minlevel = UNSET
        else:
            minlevel = LogTargetMinlevel(_minlevel)

        nolog = d.pop("nolog", UNSET)

        profile = d.pop("profile", UNSET)

        sample_range = d.pop("sample_range", UNSET)

        sample_size = d.pop("sample_size", UNSET)

        log_target = cls(
            address=address,
            facility=facility,
            format_=format_,
            global_=global_,
            length=length,
            level=level,
            metadata=metadata,
            minlevel=minlevel,
            nolog=nolog,
            profile=profile,
            sample_range=sample_range,
            sample_size=sample_size,
        )

        return log_target
