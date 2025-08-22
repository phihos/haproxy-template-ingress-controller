from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.environment_options_presetenv_item import EnvironmentOptionsPresetenvItem
    from ..models.environment_options_setenv_item import EnvironmentOptionsSetenvItem


T = TypeVar("T", bound="EnvironmentOptions")


@_attrs_define
class EnvironmentOptions:
    """
    Attributes:
        presetenv (Union[Unset, list['EnvironmentOptionsPresetenvItem']]):
        resetenv (Union[Unset, str]):
        setenv (Union[Unset, list['EnvironmentOptionsSetenvItem']]):
        unsetenv (Union[Unset, str]):
    """

    presetenv: Union[Unset, list["EnvironmentOptionsPresetenvItem"]] = UNSET
    resetenv: Union[Unset, str] = UNSET
    setenv: Union[Unset, list["EnvironmentOptionsSetenvItem"]] = UNSET
    unsetenv: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        presetenv: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.presetenv, Unset):
            presetenv = []
            for presetenv_item_data in self.presetenv:
                presetenv_item = presetenv_item_data.to_dict()
                presetenv.append(presetenv_item)

        resetenv = self.resetenv

        setenv: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.setenv, Unset):
            setenv = []
            for setenv_item_data in self.setenv:
                setenv_item = setenv_item_data.to_dict()
                setenv.append(setenv_item)

        unsetenv = self.unsetenv

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if presetenv is not UNSET:
            field_dict["presetenv"] = presetenv
        if resetenv is not UNSET:
            field_dict["resetenv"] = resetenv
        if setenv is not UNSET:
            field_dict["setenv"] = setenv
        if unsetenv is not UNSET:
            field_dict["unsetenv"] = unsetenv

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.environment_options_presetenv_item import EnvironmentOptionsPresetenvItem
        from ..models.environment_options_setenv_item import EnvironmentOptionsSetenvItem

        d = dict(src_dict)
        presetenv = []
        _presetenv = d.pop("presetenv", UNSET)
        for presetenv_item_data in _presetenv or []:
            presetenv_item = EnvironmentOptionsPresetenvItem.from_dict(presetenv_item_data)

            presetenv.append(presetenv_item)

        resetenv = d.pop("resetenv", UNSET)

        setenv = []
        _setenv = d.pop("setenv", UNSET)
        for setenv_item_data in _setenv or []:
            setenv_item = EnvironmentOptionsSetenvItem.from_dict(setenv_item_data)

            setenv.append(setenv_item)

        unsetenv = d.pop("unsetenv", UNSET)

        environment_options = cls(
            presetenv=presetenv,
            resetenv=resetenv,
            setenv=setenv,
            unsetenv=unsetenv,
        )

        environment_options.additional_properties = d
        return environment_options

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
