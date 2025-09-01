from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.site_service_http_connection_mode import SiteServiceHttpConnectionMode
from ..models.site_service_mode import SiteServiceMode
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.bind import Bind


T = TypeVar("T", bound="SiteService")


@_attrs_define
class SiteService:
    """
    Attributes:
        http_connection_mode (Union[Unset, SiteServiceHttpConnectionMode]):
        listeners (Union[Unset, list['Bind']]):
        maxconn (Union[None, Unset, int]):
        mode (Union[Unset, SiteServiceMode]):
    """

    http_connection_mode: Union[Unset, SiteServiceHttpConnectionMode] = UNSET
    listeners: Union[Unset, list["Bind"]] = UNSET
    maxconn: Union[None, Unset, int] = UNSET
    mode: Union[Unset, SiteServiceMode] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        http_connection_mode: Union[Unset, str] = UNSET
        if not isinstance(self.http_connection_mode, Unset):
            http_connection_mode = self.http_connection_mode.value

        listeners: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.listeners, Unset):
            listeners = []
            for listeners_item_data in self.listeners:
                listeners_item = listeners_item_data.to_dict()
                listeners.append(listeners_item)

        maxconn: Union[None, Unset, int]
        if isinstance(self.maxconn, Unset):
            maxconn = UNSET
        else:
            maxconn = self.maxconn

        mode: Union[Unset, str] = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if http_connection_mode is not UNSET:
            field_dict["http_connection_mode"] = http_connection_mode
        if listeners is not UNSET:
            field_dict["listeners"] = listeners
        if maxconn is not UNSET:
            field_dict["maxconn"] = maxconn
        if mode is not UNSET:
            field_dict["mode"] = mode

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.bind import Bind

        d = dict(src_dict)
        _http_connection_mode = d.pop("http_connection_mode", UNSET)
        http_connection_mode: Union[Unset, SiteServiceHttpConnectionMode]
        if isinstance(_http_connection_mode, Unset):
            http_connection_mode = UNSET
        else:
            http_connection_mode = SiteServiceHttpConnectionMode(_http_connection_mode)

        _listeners = d.pop("listeners", UNSET)
        listeners: Union[Unset, list[Bind]] = UNSET
        if not isinstance(_listeners, Unset):
            listeners = []
            for listeners_item_data in _listeners:
                listeners_item = Bind.from_dict(listeners_item_data)

                listeners.append(listeners_item)

        def _parse_maxconn(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        maxconn = _parse_maxconn(d.pop("maxconn", UNSET))

        _mode = d.pop("mode", UNSET)
        mode: Union[Unset, SiteServiceMode]
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = SiteServiceMode(_mode)

        site_service = cls(
            http_connection_mode=http_connection_mode,
            listeners=listeners,
            maxconn=maxconn,
            mode=mode,
        )

        site_service.additional_properties = d
        return site_service

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
