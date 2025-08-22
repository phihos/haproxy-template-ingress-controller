from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.log_profile_step_drop import LogProfileStepDrop
from ..models.log_profile_step_step import LogProfileStepStep
from ..types import UNSET, Unset

T = TypeVar("T", bound="LogProfileStep")


@_attrs_define
class LogProfileStep:
    """Defines what to log for a given step.

    Attributes:
        step (LogProfileStepStep): Logging step name.
        drop (Union[Unset, LogProfileStepDrop]): If enabled, no log shall be emitted for the given step.
        format_ (Union[Unset, str]): Override "log-format" or "error-log-format" strings depending on the step.
        metadata (Union[Unset, Any]):
        sd (Union[Unset, str]): Override the "log-format-sd" string.
    """

    step: LogProfileStepStep
    drop: Union[Unset, LogProfileStepDrop] = UNSET
    format_: Union[Unset, str] = UNSET
    metadata: Union[Unset, Any] = UNSET
    sd: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        step = self.step.value

        drop: Union[Unset, str] = UNSET
        if not isinstance(self.drop, Unset):
            drop = self.drop.value

        format_ = self.format_

        metadata = self.metadata

        sd = self.sd

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "step": step,
            }
        )
        if drop is not UNSET:
            field_dict["drop"] = drop
        if format_ is not UNSET:
            field_dict["format"] = format_
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if sd is not UNSET:
            field_dict["sd"] = sd

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        step = LogProfileStepStep(d.pop("step"))

        _drop = d.pop("drop", UNSET)
        drop: Union[Unset, LogProfileStepDrop]
        if isinstance(_drop, Unset):
            drop = UNSET
        else:
            drop = LogProfileStepDrop(_drop)

        format_ = d.pop("format", UNSET)

        metadata = d.pop("metadata", UNSET)

        sd = d.pop("sd", UNSET)

        log_profile_step = cls(
            step=step,
            drop=drop,
            format_=format_,
            metadata=metadata,
            sd=sd,
        )

        log_profile_step.additional_properties = d
        return log_profile_step

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
