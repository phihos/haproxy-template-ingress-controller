from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.compression_algo_req import CompressionAlgoReq
from ..models.compression_algorithms_item import CompressionAlgorithmsItem
from ..models.compression_algos_res_item import CompressionAlgosResItem
from ..models.compression_direction import CompressionDirection
from ..types import UNSET, Unset

T = TypeVar("T", bound="Compression")


@_attrs_define
class Compression:
    """
    Attributes:
        algo_req (Union[Unset, CompressionAlgoReq]):
        algorithms (Union[Unset, list[CompressionAlgorithmsItem]]):
        algos_res (Union[Unset, list[CompressionAlgosResItem]]):
        direction (Union[Unset, CompressionDirection]):
        minsize_req (Union[Unset, int]):
        minsize_res (Union[Unset, int]):
        offload (Union[Unset, bool]):
        types (Union[Unset, list[str]]):
        types_req (Union[Unset, list[str]]):
        types_res (Union[Unset, list[str]]):
    """

    algo_req: Union[Unset, CompressionAlgoReq] = UNSET
    algorithms: Union[Unset, list[CompressionAlgorithmsItem]] = UNSET
    algos_res: Union[Unset, list[CompressionAlgosResItem]] = UNSET
    direction: Union[Unset, CompressionDirection] = UNSET
    minsize_req: Union[Unset, int] = UNSET
    minsize_res: Union[Unset, int] = UNSET
    offload: Union[Unset, bool] = UNSET
    types: Union[Unset, list[str]] = UNSET
    types_req: Union[Unset, list[str]] = UNSET
    types_res: Union[Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        algo_req: Union[Unset, str] = UNSET
        if not isinstance(self.algo_req, Unset):
            algo_req = self.algo_req.value

        algorithms: Union[Unset, list[str]] = UNSET
        if not isinstance(self.algorithms, Unset):
            algorithms = []
            for algorithms_item_data in self.algorithms:
                algorithms_item = algorithms_item_data.value
                algorithms.append(algorithms_item)

        algos_res: Union[Unset, list[str]] = UNSET
        if not isinstance(self.algos_res, Unset):
            algos_res = []
            for algos_res_item_data in self.algos_res:
                algos_res_item = algos_res_item_data.value
                algos_res.append(algos_res_item)

        direction: Union[Unset, str] = UNSET
        if not isinstance(self.direction, Unset):
            direction = self.direction.value

        minsize_req = self.minsize_req

        minsize_res = self.minsize_res

        offload = self.offload

        types: Union[Unset, list[str]] = UNSET
        if not isinstance(self.types, Unset):
            types = self.types

        types_req: Union[Unset, list[str]] = UNSET
        if not isinstance(self.types_req, Unset):
            types_req = self.types_req

        types_res: Union[Unset, list[str]] = UNSET
        if not isinstance(self.types_res, Unset):
            types_res = self.types_res

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if algo_req is not UNSET:
            field_dict["algo-req"] = algo_req
        if algorithms is not UNSET:
            field_dict["algorithms"] = algorithms
        if algos_res is not UNSET:
            field_dict["algos-res"] = algos_res
        if direction is not UNSET:
            field_dict["direction"] = direction
        if minsize_req is not UNSET:
            field_dict["minsize_req"] = minsize_req
        if minsize_res is not UNSET:
            field_dict["minsize_res"] = minsize_res
        if offload is not UNSET:
            field_dict["offload"] = offload
        if types is not UNSET:
            field_dict["types"] = types
        if types_req is not UNSET:
            field_dict["types-req"] = types_req
        if types_res is not UNSET:
            field_dict["types-res"] = types_res

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _algo_req = d.pop("algo-req", UNSET)
        algo_req: Union[Unset, CompressionAlgoReq]
        if isinstance(_algo_req, Unset):
            algo_req = UNSET
        else:
            algo_req = CompressionAlgoReq(_algo_req)

        algorithms = []
        _algorithms = d.pop("algorithms", UNSET)
        for algorithms_item_data in _algorithms or []:
            algorithms_item = CompressionAlgorithmsItem(algorithms_item_data)

            algorithms.append(algorithms_item)

        algos_res = []
        _algos_res = d.pop("algos-res", UNSET)
        for algos_res_item_data in _algos_res or []:
            algos_res_item = CompressionAlgosResItem(algos_res_item_data)

            algos_res.append(algos_res_item)

        _direction = d.pop("direction", UNSET)
        direction: Union[Unset, CompressionDirection]
        if isinstance(_direction, Unset):
            direction = UNSET
        else:
            direction = CompressionDirection(_direction)

        minsize_req = d.pop("minsize_req", UNSET)

        minsize_res = d.pop("minsize_res", UNSET)

        offload = d.pop("offload", UNSET)

        types = cast(list[str], d.pop("types", UNSET))

        types_req = cast(list[str], d.pop("types-req", UNSET))

        types_res = cast(list[str], d.pop("types-res", UNSET))

        compression = cls(
            algo_req=algo_req,
            algorithms=algorithms,
            algos_res=algos_res,
            direction=direction,
            minsize_req=minsize_req,
            minsize_res=minsize_res,
            offload=offload,
            types=types,
            types_req=types_req,
            types_res=types_res,
        )

        compression.additional_properties = d
        return compression

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
