from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.site_farms_item_cond import SiteFarmsItemCond
from ..models.site_farms_item_mode import SiteFarmsItemMode
from ..models.site_farms_item_use_as import SiteFarmsItemUseAs
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.balance import Balance
    from ..models.forwardfor import Forwardfor
    from ..models.server import Server


T = TypeVar("T", bound="SiteFarmsItem")


@_attrs_define
class SiteFarmsItem:
    """
    Attributes:
        name (str):
        use_as (SiteFarmsItemUseAs):
        balance (Union[Unset, Balance]):
        cond (Union[Unset, SiteFarmsItemCond]):
        cond_test (Union[Unset, str]):
        forwardfor (Union[Unset, Forwardfor]):
        mode (Union[Unset, SiteFarmsItemMode]):
        servers (Union[Unset, list['Server']]):
    """

    name: str
    use_as: SiteFarmsItemUseAs
    balance: Union[Unset, "Balance"] = UNSET
    cond: Union[Unset, SiteFarmsItemCond] = UNSET
    cond_test: Union[Unset, str] = UNSET
    forwardfor: Union[Unset, "Forwardfor"] = UNSET
    mode: Union[Unset, SiteFarmsItemMode] = UNSET
    servers: Union[Unset, list["Server"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        use_as = self.use_as.value

        balance: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.balance, Unset):
            balance = self.balance.to_dict()

        cond: Union[Unset, str] = UNSET
        if not isinstance(self.cond, Unset):
            cond = self.cond.value

        cond_test = self.cond_test

        forwardfor: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.forwardfor, Unset):
            forwardfor = self.forwardfor.to_dict()

        mode: Union[Unset, str] = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        servers: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.servers, Unset):
            servers = []
            for servers_item_data in self.servers:
                servers_item = servers_item_data.to_dict()
                servers.append(servers_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "use_as": use_as,
            }
        )
        if balance is not UNSET:
            field_dict["balance"] = balance
        if cond is not UNSET:
            field_dict["cond"] = cond
        if cond_test is not UNSET:
            field_dict["cond_test"] = cond_test
        if forwardfor is not UNSET:
            field_dict["forwardfor"] = forwardfor
        if mode is not UNSET:
            field_dict["mode"] = mode
        if servers is not UNSET:
            field_dict["servers"] = servers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.balance import Balance
        from ..models.forwardfor import Forwardfor
        from ..models.server import Server

        d = dict(src_dict)
        name = d.pop("name")

        use_as = SiteFarmsItemUseAs(d.pop("use_as"))

        _balance = d.pop("balance", UNSET)
        balance: Union[Unset, Balance]
        if isinstance(_balance, Unset):
            balance = UNSET
        else:
            balance = Balance.from_dict(_balance)

        _cond = d.pop("cond", UNSET)
        cond: Union[Unset, SiteFarmsItemCond]
        if isinstance(_cond, Unset):
            cond = UNSET
        else:
            cond = SiteFarmsItemCond(_cond)

        cond_test = d.pop("cond_test", UNSET)

        _forwardfor = d.pop("forwardfor", UNSET)
        forwardfor: Union[Unset, Forwardfor]
        if isinstance(_forwardfor, Unset):
            forwardfor = UNSET
        else:
            forwardfor = Forwardfor.from_dict(_forwardfor)

        _mode = d.pop("mode", UNSET)
        mode: Union[Unset, SiteFarmsItemMode]
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = SiteFarmsItemMode(_mode)

        _servers = d.pop("servers", UNSET)
        servers: Union[Unset, list[Server]] = UNSET
        if not isinstance(_servers, Unset):
            servers = []
            for servers_item_data in _servers:
                servers_item = Server.from_dict(servers_item_data)

                servers.append(servers_item)

        site_farms_item = cls(
            name=name,
            use_as=use_as,
            balance=balance,
            cond=cond,
            cond_test=cond_test,
            forwardfor=forwardfor,
            mode=mode,
            servers=servers,
        )

        site_farms_item.additional_properties = d
        return site_farms_item

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
