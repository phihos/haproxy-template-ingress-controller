from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.default_bind import DefaultBind
    from ..models.server_params import ServerParams


T = TypeVar("T", bound="PeerSectionBase")


@_attrs_define
class PeerSectionBase:
    """HAProxy peer_section configuration

    Attributes:
        name (str):
        default_bind (Union[Unset, DefaultBind]): HAProxy default bind configuration
        default_server (Union[Unset, ServerParams]):
        disabled (Union[Unset, bool]):
        enabled (Union[Unset, bool]):
        metadata (Union[Unset, Any]):
        shards (Union[Unset, int]): In some configurations, one would like to distribute the stick-table contents
            to some peers in place of sending all the stick-table contents to each peer
            declared in the "peers" section. In such cases, "shards" specifies the
            number of peer involved in this stick-table contents distribution.
    """

    name: str
    default_bind: Union[Unset, "DefaultBind"] = UNSET
    default_server: Union[Unset, "ServerParams"] = UNSET
    disabled: Union[Unset, bool] = UNSET
    enabled: Union[Unset, bool] = UNSET
    metadata: Union[Unset, Any] = UNSET
    shards: Union[Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        default_bind: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.default_bind, Unset):
            default_bind = self.default_bind.to_dict()

        default_server: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.default_server, Unset):
            default_server = self.default_server.to_dict()

        disabled = self.disabled

        enabled = self.enabled

        metadata = self.metadata

        shards = self.shards

        field_dict: dict[str, Any] = {}
        field_dict.update(
            {
                "name": name,
            }
        )
        if default_bind is not UNSET:
            field_dict["default_bind"] = default_bind
        if default_server is not UNSET:
            field_dict["default_server"] = default_server
        if disabled is not UNSET:
            field_dict["disabled"] = disabled
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if shards is not UNSET:
            field_dict["shards"] = shards

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.default_bind import DefaultBind
        from ..models.server_params import ServerParams

        d = dict(src_dict)
        name = d.pop("name")

        _default_bind = d.pop("default_bind", UNSET)
        default_bind: Union[Unset, DefaultBind]
        if isinstance(_default_bind, Unset):
            default_bind = UNSET
        else:
            default_bind = DefaultBind.from_dict(_default_bind)

        _default_server = d.pop("default_server", UNSET)
        default_server: Union[Unset, ServerParams]
        if isinstance(_default_server, Unset):
            default_server = UNSET
        else:
            default_server = ServerParams.from_dict(_default_server)

        disabled = d.pop("disabled", UNSET)

        enabled = d.pop("enabled", UNSET)

        metadata = d.pop("metadata", UNSET)

        shards = d.pop("shards", UNSET)

        peer_section_base = cls(
            name=name,
            default_bind=default_bind,
            default_server=default_server,
            disabled=disabled,
            enabled=enabled,
            metadata=metadata,
            shards=shards,
        )

        return peer_section_base
