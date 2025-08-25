from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.trace_event import TraceEvent


T = TypeVar("T", bound="Traces")


@_attrs_define
class Traces:
    """Trace events configuration

    Attributes:
        entries (Union[Unset, list['TraceEvent']]): list of entries in a traces section
        metadata (Union[Unset, Any]):
    """

    entries: Union[Unset, list["TraceEvent"]] = UNSET
    metadata: Union[Unset, Any] = UNSET

    def to_dict(self) -> dict[str, Any]:
        entries: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.entries, Unset):
            entries = []
            for componentsschemastrace_entries_item_data in self.entries:
                componentsschemastrace_entries_item = componentsschemastrace_entries_item_data.to_dict()
                entries.append(componentsschemastrace_entries_item)

        metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if entries is not UNSET:
            field_dict["entries"] = entries
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trace_event import TraceEvent

        d = dict(src_dict)
        entries = []
        _entries = d.pop("entries", UNSET)
        for componentsschemastrace_entries_item_data in _entries or []:
            componentsschemastrace_entries_item = TraceEvent.from_dict(componentsschemastrace_entries_item_data)

            entries.append(componentsschemastrace_entries_item)

        metadata = d.pop("metadata", UNSET)

        traces = cls(
            entries=entries,
            metadata=metadata,
        )

        return traces
