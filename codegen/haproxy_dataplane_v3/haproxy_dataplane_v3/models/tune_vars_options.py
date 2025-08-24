from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TuneVarsOptions")


@_attrs_define
class TuneVarsOptions:
    """
    Attributes:
        global_max_size (Union[None, Unset, int]):
        proc_max_size (Union[None, Unset, int]):
        reqres_max_size (Union[None, Unset, int]):
        sess_max_size (Union[None, Unset, int]):
        txn_max_size (Union[None, Unset, int]):
    """

    global_max_size: Union[None, Unset, int] = UNSET
    proc_max_size: Union[None, Unset, int] = UNSET
    reqres_max_size: Union[None, Unset, int] = UNSET
    sess_max_size: Union[None, Unset, int] = UNSET
    txn_max_size: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        global_max_size: Union[None, Unset, int]
        if isinstance(self.global_max_size, Unset):
            global_max_size = UNSET
        else:
            global_max_size = self.global_max_size

        proc_max_size: Union[None, Unset, int]
        if isinstance(self.proc_max_size, Unset):
            proc_max_size = UNSET
        else:
            proc_max_size = self.proc_max_size

        reqres_max_size: Union[None, Unset, int]
        if isinstance(self.reqres_max_size, Unset):
            reqres_max_size = UNSET
        else:
            reqres_max_size = self.reqres_max_size

        sess_max_size: Union[None, Unset, int]
        if isinstance(self.sess_max_size, Unset):
            sess_max_size = UNSET
        else:
            sess_max_size = self.sess_max_size

        txn_max_size: Union[None, Unset, int]
        if isinstance(self.txn_max_size, Unset):
            txn_max_size = UNSET
        else:
            txn_max_size = self.txn_max_size

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if global_max_size is not UNSET:
            field_dict["global_max_size"] = global_max_size
        if proc_max_size is not UNSET:
            field_dict["proc_max_size"] = proc_max_size
        if reqres_max_size is not UNSET:
            field_dict["reqres_max_size"] = reqres_max_size
        if sess_max_size is not UNSET:
            field_dict["sess_max_size"] = sess_max_size
        if txn_max_size is not UNSET:
            field_dict["txn_max_size"] = txn_max_size

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_global_max_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        global_max_size = _parse_global_max_size(d.pop("global_max_size", UNSET))

        def _parse_proc_max_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        proc_max_size = _parse_proc_max_size(d.pop("proc_max_size", UNSET))

        def _parse_reqres_max_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        reqres_max_size = _parse_reqres_max_size(d.pop("reqres_max_size", UNSET))

        def _parse_sess_max_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        sess_max_size = _parse_sess_max_size(d.pop("sess_max_size", UNSET))

        def _parse_txn_max_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        txn_max_size = _parse_txn_max_size(d.pop("txn_max_size", UNSET))

        tune_vars_options = cls(
            global_max_size=global_max_size,
            proc_max_size=proc_max_size,
            reqres_max_size=reqres_max_size,
            sess_max_size=sess_max_size,
            txn_max_size=txn_max_size,
        )

        tune_vars_options.additional_properties = d
        return tune_vars_options

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
