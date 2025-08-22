from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.balance_algorithm import BalanceAlgorithm
from ..types import UNSET, Unset

T = TypeVar("T", bound="Balance")


@_attrs_define
class Balance:
    """
    Attributes:
        algorithm (BalanceAlgorithm):
        hash_expression (Union[Unset, str]):
        hdr_name (Union[Unset, str]):
        hdr_use_domain_only (Union[Unset, bool]):
        random_draws (Union[Unset, int]):
        rdp_cookie_name (Union[Unset, str]):
        uri_depth (Union[Unset, int]):
        uri_len (Union[Unset, int]):
        uri_path_only (Union[Unset, bool]):
        uri_whole (Union[Unset, bool]):
        url_param (Union[Unset, str]):
        url_param_check_post (Union[Unset, int]):
        url_param_max_wait (Union[Unset, int]):
    """

    algorithm: BalanceAlgorithm
    hash_expression: Union[Unset, str] = UNSET
    hdr_name: Union[Unset, str] = UNSET
    hdr_use_domain_only: Union[Unset, bool] = UNSET
    random_draws: Union[Unset, int] = UNSET
    rdp_cookie_name: Union[Unset, str] = UNSET
    uri_depth: Union[Unset, int] = UNSET
    uri_len: Union[Unset, int] = UNSET
    uri_path_only: Union[Unset, bool] = UNSET
    uri_whole: Union[Unset, bool] = UNSET
    url_param: Union[Unset, str] = UNSET
    url_param_check_post: Union[Unset, int] = UNSET
    url_param_max_wait: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        algorithm = self.algorithm.value

        hash_expression = self.hash_expression

        hdr_name = self.hdr_name

        hdr_use_domain_only = self.hdr_use_domain_only

        random_draws = self.random_draws

        rdp_cookie_name = self.rdp_cookie_name

        uri_depth = self.uri_depth

        uri_len = self.uri_len

        uri_path_only = self.uri_path_only

        uri_whole = self.uri_whole

        url_param = self.url_param

        url_param_check_post = self.url_param_check_post

        url_param_max_wait = self.url_param_max_wait

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "algorithm": algorithm,
            }
        )
        if hash_expression is not UNSET:
            field_dict["hash_expression"] = hash_expression
        if hdr_name is not UNSET:
            field_dict["hdr_name"] = hdr_name
        if hdr_use_domain_only is not UNSET:
            field_dict["hdr_use_domain_only"] = hdr_use_domain_only
        if random_draws is not UNSET:
            field_dict["random_draws"] = random_draws
        if rdp_cookie_name is not UNSET:
            field_dict["rdp_cookie_name"] = rdp_cookie_name
        if uri_depth is not UNSET:
            field_dict["uri_depth"] = uri_depth
        if uri_len is not UNSET:
            field_dict["uri_len"] = uri_len
        if uri_path_only is not UNSET:
            field_dict["uri_path_only"] = uri_path_only
        if uri_whole is not UNSET:
            field_dict["uri_whole"] = uri_whole
        if url_param is not UNSET:
            field_dict["url_param"] = url_param
        if url_param_check_post is not UNSET:
            field_dict["url_param_check_post"] = url_param_check_post
        if url_param_max_wait is not UNSET:
            field_dict["url_param_max_wait"] = url_param_max_wait

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        algorithm = BalanceAlgorithm(d.pop("algorithm"))

        hash_expression = d.pop("hash_expression", UNSET)

        hdr_name = d.pop("hdr_name", UNSET)

        hdr_use_domain_only = d.pop("hdr_use_domain_only", UNSET)

        random_draws = d.pop("random_draws", UNSET)

        rdp_cookie_name = d.pop("rdp_cookie_name", UNSET)

        uri_depth = d.pop("uri_depth", UNSET)

        uri_len = d.pop("uri_len", UNSET)

        uri_path_only = d.pop("uri_path_only", UNSET)

        uri_whole = d.pop("uri_whole", UNSET)

        url_param = d.pop("url_param", UNSET)

        url_param_check_post = d.pop("url_param_check_post", UNSET)

        url_param_max_wait = d.pop("url_param_max_wait", UNSET)

        balance = cls(
            algorithm=algorithm,
            hash_expression=hash_expression,
            hdr_name=hdr_name,
            hdr_use_domain_only=hdr_use_domain_only,
            random_draws=random_draws,
            rdp_cookie_name=rdp_cookie_name,
            uri_depth=uri_depth,
            uri_len=uri_len,
            uri_path_only=uri_path_only,
            uri_whole=uri_whole,
            url_param=url_param,
            url_param_check_post=url_param_check_post,
            url_param_max_wait=url_param_max_wait,
        )

        balance.additional_properties = d
        return balance

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
