from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.forwardfor_enabled import ForwardforEnabled
from ..types import UNSET, Unset

T = TypeVar("T", bound="Forwardfor")


@_attrs_define
class Forwardfor:
    """
    Attributes:
        enabled (ForwardforEnabled):
        except_ (Union[Unset, str]):
        header (Union[Unset, str]):
        ifnone (Union[Unset, bool]):
    """

    enabled: ForwardforEnabled
    except_: Union[Unset, str] = UNSET
    header: Union[Unset, str] = UNSET
    ifnone: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        enabled = self.enabled.value

        except_ = self.except_

        header = self.header

        ifnone = self.ifnone

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
        if ifnone is not UNSET:
            field_dict["ifnone"] = ifnone

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        enabled = ForwardforEnabled(d.pop("enabled"))

        except_ = d.pop("except", UNSET)

        header = d.pop("header", UNSET)

        ifnone = d.pop("ifnone", UNSET)

        forwardfor = cls(
            enabled=enabled,
            except_=except_,
            header=header,
            ifnone=ifnone,
        )

        forwardfor.additional_properties = d
        return forwardfor

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
