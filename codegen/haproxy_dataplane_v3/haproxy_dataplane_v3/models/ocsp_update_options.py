from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.ocsp_update_options_mode import OcspUpdateOptionsMode
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.ocsp_update_options_httpproxy import OcspUpdateOptionsHttpproxy


T = TypeVar("T", bound="OcspUpdateOptions")


@_attrs_define
class OcspUpdateOptions:
    """
    Attributes:
        disable (Union[None, Unset, bool]):  Default: False.
        httpproxy (Union[Unset, OcspUpdateOptionsHttpproxy]):
        maxdelay (Union[None, Unset, int]): Sets the maximum interval between two automatic updates of the same OCSP
            response.This time is expressed in seconds
        mindelay (Union[None, Unset, int]): Sets the minimum interval between two automatic updates of the same OCSP
            response. This time is expressed in seconds
        mode (Union[Unset, OcspUpdateOptionsMode]):
    """

    disable: Union[None, Unset, bool] = False
    httpproxy: Union[Unset, "OcspUpdateOptionsHttpproxy"] = UNSET
    maxdelay: Union[None, Unset, int] = UNSET
    mindelay: Union[None, Unset, int] = UNSET
    mode: Union[Unset, OcspUpdateOptionsMode] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        disable: Union[None, Unset, bool]
        if isinstance(self.disable, Unset):
            disable = UNSET
        else:
            disable = self.disable

        httpproxy: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.httpproxy, Unset):
            httpproxy = self.httpproxy.to_dict()

        maxdelay: Union[None, Unset, int]
        if isinstance(self.maxdelay, Unset):
            maxdelay = UNSET
        else:
            maxdelay = self.maxdelay

        mindelay: Union[None, Unset, int]
        if isinstance(self.mindelay, Unset):
            mindelay = UNSET
        else:
            mindelay = self.mindelay

        mode: Union[Unset, str] = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if disable is not UNSET:
            field_dict["disable"] = disable
        if httpproxy is not UNSET:
            field_dict["httpproxy"] = httpproxy
        if maxdelay is not UNSET:
            field_dict["maxdelay"] = maxdelay
        if mindelay is not UNSET:
            field_dict["mindelay"] = mindelay
        if mode is not UNSET:
            field_dict["mode"] = mode

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.ocsp_update_options_httpproxy import OcspUpdateOptionsHttpproxy

        d = dict(src_dict)

        def _parse_disable(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        disable = _parse_disable(d.pop("disable", UNSET))

        _httpproxy = d.pop("httpproxy", UNSET)
        httpproxy: Union[Unset, OcspUpdateOptionsHttpproxy]
        if isinstance(_httpproxy, Unset):
            httpproxy = UNSET
        else:
            httpproxy = OcspUpdateOptionsHttpproxy.from_dict(_httpproxy)

        def _parse_maxdelay(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        maxdelay = _parse_maxdelay(d.pop("maxdelay", UNSET))

        def _parse_mindelay(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        mindelay = _parse_mindelay(d.pop("mindelay", UNSET))

        _mode = d.pop("mode", UNSET)
        mode: Union[Unset, OcspUpdateOptionsMode]
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = OcspUpdateOptionsMode(_mode)

        ocsp_update_options = cls(
            disable=disable,
            httpproxy=httpproxy,
            maxdelay=maxdelay,
            mindelay=mindelay,
            mode=mode,
        )

        ocsp_update_options.additional_properties = d
        return ocsp_update_options

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
