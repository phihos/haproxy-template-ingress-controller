from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.program_start_on_reload import ProgramStartOnReload
from ..types import UNSET, Unset

T = TypeVar("T", bound="Program")


@_attrs_define
class Program:
    """HAProxy program configuration

    Example:
        {'command': 'spoa-mirror --runtime 0 --mirror-url http://test.local', 'group': 'mygroupname', 'name': 'mirror',
            'start-on-reload': 'enabled', 'user': 'myusername'}

    Attributes:
        command (str): The command to be run, with flags and options.
        name (str):
        group (Union[Unset, str]): The group to run the command as, if different than the HAProxy group.
        metadata (Union[Unset, Any]):
        start_on_reload (Union[Unset, ProgramStartOnReload]): HAProxy stops and recreates child programs at reload.
        user (Union[Unset, str]): The user to run the command as, if different than the HAProxy user.
    """

    command: str
    name: str
    group: Union[Unset, str] = UNSET
    metadata: Union[Unset, Any] = UNSET
    start_on_reload: Union[Unset, ProgramStartOnReload] = UNSET
    user: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        command = self.command

        name = self.name

        group = self.group

        metadata = self.metadata

        start_on_reload: Union[Unset, str] = UNSET
        if not isinstance(self.start_on_reload, Unset):
            start_on_reload = self.start_on_reload.value

        user = self.user

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "command": command,
                "name": name,
            }
        )
        if group is not UNSET:
            field_dict["group"] = group
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if start_on_reload is not UNSET:
            field_dict["start-on-reload"] = start_on_reload
        if user is not UNSET:
            field_dict["user"] = user

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        command = d.pop("command")

        name = d.pop("name")

        group = d.pop("group", UNSET)

        metadata = d.pop("metadata", UNSET)

        _start_on_reload = d.pop("start-on-reload", UNSET)
        start_on_reload: Union[Unset, ProgramStartOnReload]
        if isinstance(_start_on_reload, Unset):
            start_on_reload = UNSET
        else:
            start_on_reload = ProgramStartOnReload(_start_on_reload)

        user = d.pop("user", UNSET)

        program = cls(
            command=command,
            name=name,
            group=group,
            metadata=metadata,
            start_on_reload=start_on_reload,
            user=user,
        )

        program.additional_properties = d
        return program

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
