from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.default_bind import DefaultBind
    from ..models.log_target import LogTarget
    from ..models.server_params import ServerParams


T = TypeVar("T", bound="PeerSection")


@_attrs_define
class PeerSection:
    """Peer Section with all it's children resources

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
        binds (Union[Unset, Any]):
        log_target_list (Union[Unset, list['LogTarget']]): HAProxy log target array (corresponds to log directives)
        peer_entries (Union[Unset, Any]):
        servers (Union[Unset, Any]):
        tables (Union[Unset, Any]):
    """

    name: str
    default_bind: Union[Unset, "DefaultBind"] = UNSET
    default_server: Union[Unset, "ServerParams"] = UNSET
    disabled: Union[Unset, bool] = UNSET
    enabled: Union[Unset, bool] = UNSET
    metadata: Union[Unset, Any] = UNSET
    shards: Union[Unset, int] = UNSET
    binds: Union[Unset, Any] = UNSET
    log_target_list: Union[Unset, list["LogTarget"]] = UNSET
    peer_entries: Union[Unset, Any] = UNSET
    servers: Union[Unset, Any] = UNSET
    tables: Union[Unset, Any] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

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

        binds = self.binds

        log_target_list: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.log_target_list, Unset):
            log_target_list = []
            for componentsschemaslog_targets_item_data in self.log_target_list:
                componentsschemaslog_targets_item = componentsschemaslog_targets_item_data.to_dict()
                log_target_list.append(componentsschemaslog_targets_item)

        peer_entries = self.peer_entries

        servers = self.servers

        tables = self.tables

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
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
        if binds is not UNSET:
            field_dict["binds"] = binds
        if log_target_list is not UNSET:
            field_dict["log_target_list"] = log_target_list
        if peer_entries is not UNSET:
            field_dict["peer_entries"] = peer_entries
        if servers is not UNSET:
            field_dict["servers"] = servers
        if tables is not UNSET:
            field_dict["tables"] = tables

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.default_bind import DefaultBind
        from ..models.log_target import LogTarget
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

        binds = d.pop("binds", UNSET)

        _log_target_list = d.pop("log_target_list", UNSET)
        log_target_list: Union[Unset, list[LogTarget]] = UNSET
        if not isinstance(_log_target_list, Unset):
            log_target_list = []
            for componentsschemaslog_targets_item_data in _log_target_list:
                componentsschemaslog_targets_item = LogTarget.from_dict(componentsschemaslog_targets_item_data)

                log_target_list.append(componentsschemaslog_targets_item)

        peer_entries = d.pop("peer_entries", UNSET)

        servers = d.pop("servers", UNSET)

        tables = d.pop("tables", UNSET)

        peer_section = cls(
            name=name,
            default_bind=default_bind,
            default_server=default_server,
            disabled=disabled,
            enabled=enabled,
            metadata=metadata,
            shards=shards,
            binds=binds,
            log_target_list=log_target_list,
            peer_entries=peer_entries,
            servers=servers,
            tables=tables,
        )

        peer_section.additional_properties = d
        return peer_section

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
