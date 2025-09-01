from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.log_profile_step import LogProfileStep


T = TypeVar("T", bound="LogProfile")


@_attrs_define
class LogProfile:
    """Defines a logging profile for one or more steps.

    Attributes:
        name (str): Name of the logging profile.
        log_tag (Union[Unset, str]): Override syslog log tag set by other "log-tag" directives.
        metadata (Union[Unset, Any]):
        steps (Union[Unset, list['LogProfileStep']]): List of steps where to override the logging.
    """

    name: str
    log_tag: Union[Unset, str] = UNSET
    metadata: Union[Unset, Any] = UNSET
    steps: Union[Unset, list["LogProfileStep"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        log_tag = self.log_tag

        metadata = self.metadata

        steps: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.steps, Unset):
            steps = []
            for componentsschemaslog_profile_steps_item_data in self.steps:
                componentsschemaslog_profile_steps_item = componentsschemaslog_profile_steps_item_data.to_dict()
                steps.append(componentsschemaslog_profile_steps_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if log_tag is not UNSET:
            field_dict["log_tag"] = log_tag
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if steps is not UNSET:
            field_dict["steps"] = steps

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.log_profile_step import LogProfileStep

        d = dict(src_dict)
        name = d.pop("name")

        log_tag = d.pop("log_tag", UNSET)

        metadata = d.pop("metadata", UNSET)

        _steps = d.pop("steps", UNSET)
        steps: Union[Unset, list[LogProfileStep]] = UNSET
        if not isinstance(_steps, Unset):
            steps = []
            for componentsschemaslog_profile_steps_item_data in _steps:
                componentsschemaslog_profile_steps_item = LogProfileStep.from_dict(
                    componentsschemaslog_profile_steps_item_data
                )

                steps.append(componentsschemaslog_profile_steps_item)

        log_profile = cls(
            name=name,
            log_tag=log_tag,
            metadata=metadata,
            steps=steps,
        )

        log_profile.additional_properties = d
        return log_profile

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
