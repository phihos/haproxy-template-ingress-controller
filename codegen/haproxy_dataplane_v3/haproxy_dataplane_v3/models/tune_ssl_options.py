from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.tune_ssl_options_keylog import TuneSslOptionsKeylog
from ..types import UNSET, Unset

T = TypeVar("T", bound="TuneSslOptions")


@_attrs_define
class TuneSslOptions:
    """
    Attributes:
        cachesize (Union[None, Unset, int]):
        capture_buffer_size (Union[None, Unset, int]):
        ctx_cache_size (Union[Unset, int]):
        default_dh_param (Union[Unset, int]):
        force_private_cache (Union[Unset, bool]):
        keylog (Union[Unset, TuneSslOptionsKeylog]):
        lifetime (Union[None, Unset, int]):
        maxrecord (Union[None, Unset, int]):
        ocsp_update_max_delay (Union[None, Unset, int]):
        ocsp_update_min_delay (Union[None, Unset, int]):
    """

    cachesize: Union[None, Unset, int] = UNSET
    capture_buffer_size: Union[None, Unset, int] = UNSET
    ctx_cache_size: Union[Unset, int] = UNSET
    default_dh_param: Union[Unset, int] = UNSET
    force_private_cache: Union[Unset, bool] = UNSET
    keylog: Union[Unset, TuneSslOptionsKeylog] = UNSET
    lifetime: Union[None, Unset, int] = UNSET
    maxrecord: Union[None, Unset, int] = UNSET
    ocsp_update_max_delay: Union[None, Unset, int] = UNSET
    ocsp_update_min_delay: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cachesize: Union[None, Unset, int]
        if isinstance(self.cachesize, Unset):
            cachesize = UNSET
        else:
            cachesize = self.cachesize

        capture_buffer_size: Union[None, Unset, int]
        if isinstance(self.capture_buffer_size, Unset):
            capture_buffer_size = UNSET
        else:
            capture_buffer_size = self.capture_buffer_size

        ctx_cache_size = self.ctx_cache_size

        default_dh_param = self.default_dh_param

        force_private_cache = self.force_private_cache

        keylog: Union[Unset, str] = UNSET
        if not isinstance(self.keylog, Unset):
            keylog = self.keylog.value

        lifetime: Union[None, Unset, int]
        if isinstance(self.lifetime, Unset):
            lifetime = UNSET
        else:
            lifetime = self.lifetime

        maxrecord: Union[None, Unset, int]
        if isinstance(self.maxrecord, Unset):
            maxrecord = UNSET
        else:
            maxrecord = self.maxrecord

        ocsp_update_max_delay: Union[None, Unset, int]
        if isinstance(self.ocsp_update_max_delay, Unset):
            ocsp_update_max_delay = UNSET
        else:
            ocsp_update_max_delay = self.ocsp_update_max_delay

        ocsp_update_min_delay: Union[None, Unset, int]
        if isinstance(self.ocsp_update_min_delay, Unset):
            ocsp_update_min_delay = UNSET
        else:
            ocsp_update_min_delay = self.ocsp_update_min_delay

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cachesize is not UNSET:
            field_dict["cachesize"] = cachesize
        if capture_buffer_size is not UNSET:
            field_dict["capture_buffer_size"] = capture_buffer_size
        if ctx_cache_size is not UNSET:
            field_dict["ctx_cache_size"] = ctx_cache_size
        if default_dh_param is not UNSET:
            field_dict["default_dh_param"] = default_dh_param
        if force_private_cache is not UNSET:
            field_dict["force_private_cache"] = force_private_cache
        if keylog is not UNSET:
            field_dict["keylog"] = keylog
        if lifetime is not UNSET:
            field_dict["lifetime"] = lifetime
        if maxrecord is not UNSET:
            field_dict["maxrecord"] = maxrecord
        if ocsp_update_max_delay is not UNSET:
            field_dict["ocsp_update_max_delay"] = ocsp_update_max_delay
        if ocsp_update_min_delay is not UNSET:
            field_dict["ocsp_update_min_delay"] = ocsp_update_min_delay

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_cachesize(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        cachesize = _parse_cachesize(d.pop("cachesize", UNSET))

        def _parse_capture_buffer_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        capture_buffer_size = _parse_capture_buffer_size(d.pop("capture_buffer_size", UNSET))

        ctx_cache_size = d.pop("ctx_cache_size", UNSET)

        default_dh_param = d.pop("default_dh_param", UNSET)

        force_private_cache = d.pop("force_private_cache", UNSET)

        _keylog = d.pop("keylog", UNSET)
        keylog: Union[Unset, TuneSslOptionsKeylog]
        if isinstance(_keylog, Unset):
            keylog = UNSET
        else:
            keylog = TuneSslOptionsKeylog(_keylog)

        def _parse_lifetime(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        lifetime = _parse_lifetime(d.pop("lifetime", UNSET))

        def _parse_maxrecord(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        maxrecord = _parse_maxrecord(d.pop("maxrecord", UNSET))

        def _parse_ocsp_update_max_delay(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        ocsp_update_max_delay = _parse_ocsp_update_max_delay(d.pop("ocsp_update_max_delay", UNSET))

        def _parse_ocsp_update_min_delay(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        ocsp_update_min_delay = _parse_ocsp_update_min_delay(d.pop("ocsp_update_min_delay", UNSET))

        tune_ssl_options = cls(
            cachesize=cachesize,
            capture_buffer_size=capture_buffer_size,
            ctx_cache_size=ctx_cache_size,
            default_dh_param=default_dh_param,
            force_private_cache=force_private_cache,
            keylog=keylog,
            lifetime=lifetime,
            maxrecord=maxrecord,
            ocsp_update_max_delay=ocsp_update_max_delay,
            ocsp_update_min_delay=ocsp_update_min_delay,
        )

        tune_ssl_options.additional_properties = d
        return tune_ssl_options

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
