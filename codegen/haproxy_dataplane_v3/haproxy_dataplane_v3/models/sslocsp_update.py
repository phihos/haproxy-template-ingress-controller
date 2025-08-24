from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SSLOCSPUpdate")


@_attrs_define
class SSLOCSPUpdate:
    """SSL OCSP Update

    Attributes:
        cert_id (Union[Unset, str]):
        failures (Union[Unset, int]):
        last_update (Union[Unset, str]):
        last_update_status (Union[Unset, int]):
        last_update_status_str (Union[Unset, str]):
        next_update (Union[Unset, str]):
        path (Union[Unset, str]):
        successes (Union[Unset, int]):
    """

    cert_id: Union[Unset, str] = UNSET
    failures: Union[Unset, int] = UNSET
    last_update: Union[Unset, str] = UNSET
    last_update_status: Union[Unset, int] = UNSET
    last_update_status_str: Union[Unset, str] = UNSET
    next_update: Union[Unset, str] = UNSET
    path: Union[Unset, str] = UNSET
    successes: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cert_id = self.cert_id

        failures = self.failures

        last_update = self.last_update

        last_update_status = self.last_update_status

        last_update_status_str = self.last_update_status_str

        next_update = self.next_update

        path = self.path

        successes = self.successes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cert_id is not UNSET:
            field_dict["cert_id"] = cert_id
        if failures is not UNSET:
            field_dict["failures"] = failures
        if last_update is not UNSET:
            field_dict["last_update"] = last_update
        if last_update_status is not UNSET:
            field_dict["last_update_status"] = last_update_status
        if last_update_status_str is not UNSET:
            field_dict["last_update_status_str"] = last_update_status_str
        if next_update is not UNSET:
            field_dict["next_update"] = next_update
        if path is not UNSET:
            field_dict["path"] = path
        if successes is not UNSET:
            field_dict["successes"] = successes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cert_id = d.pop("cert_id", UNSET)

        failures = d.pop("failures", UNSET)

        last_update = d.pop("last_update", UNSET)

        last_update_status = d.pop("last_update_status", UNSET)

        last_update_status_str = d.pop("last_update_status_str", UNSET)

        next_update = d.pop("next_update", UNSET)

        path = d.pop("path", UNSET)

        successes = d.pop("successes", UNSET)

        sslocsp_update = cls(
            cert_id=cert_id,
            failures=failures,
            last_update=last_update,
            last_update_status=last_update_status,
            last_update_status_str=last_update_status_str,
            next_update=next_update,
            path=path,
            successes=successes,
        )

        sslocsp_update.additional_properties = d
        return sslocsp_update

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
