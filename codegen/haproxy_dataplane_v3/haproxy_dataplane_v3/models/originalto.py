from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.originalto_enabled import OriginaltoEnabled
from ..types import UNSET, Unset

T = TypeVar("T", bound="Originalto")


@_attrs_define
class Originalto:
    """
    Attributes:
        enabled (OriginaltoEnabled):
        except_ (Union[Unset, str]):
        header (Union[Unset, str]):
    """

    enabled: OriginaltoEnabled
    except_: Union[Unset, str] = UNSET
    header: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        enabled = self.enabled.value

        except_ = self.except_

        header = self.header

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "enabled": enabled,
            }
        )
        if except_ is not UNSET:
            field_dict["except"] = except_
        if header is not UNSET:
            field_dict["header"] = header

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        enabled = OriginaltoEnabled(d.pop("enabled"))

        except_ = d.pop("except", UNSET)

        header = d.pop("header", UNSET)

        originalto = cls(
            enabled=enabled,
            except_=except_,
            header=header,
        )

        originalto.additional_properties = d
        return originalto

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
