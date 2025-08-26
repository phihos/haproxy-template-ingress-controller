from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.site_farms_item import SiteFarmsItem
    from ..models.site_service import SiteService


T = TypeVar("T", bound="Site")


@_attrs_define
class Site:
    """Site configuration. Sites are considered as one service and all farms connected to that service.
    Farms are connected to service using use-backend and default_backend directives. Sites let you
    configure simple HAProxy configurations, for more advanced options use /haproxy/configuration
    endpoints.

        Example:
            {'farms': [{'balance': {'algorithm': 'roundrobin'}, 'mode': 'http', 'name': 'www_backend', 'servers':
                [{'address': '127.0.1.1', 'name': 'www_server', 'port': 4567}, {'address': '127.0.1.2', 'name':
                'www_server_new', 'port': 4567}], 'use_as': 'default'}], 'name': 'test_site', 'service':
                {'http_connection_mode': 'httpclose', 'maxconn': 2000, 'mode': 'http'}}

        Attributes:
            name (str):
            farms (Union[Unset, list['SiteFarmsItem']]):
            service (Union[Unset, SiteService]):
    """

    name: str
    farms: Union[Unset, list["SiteFarmsItem"]] = UNSET
    service: Union[Unset, "SiteService"] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        farms: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.farms, Unset):
            farms = []
            for farms_item_data in self.farms:
                farms_item = farms_item_data.to_dict()
                farms.append(farms_item)

        service: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.service, Unset):
            service = self.service.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )
        if farms is not UNSET:
            field_dict["farms"] = farms
        if service is not UNSET:
            field_dict["service"] = service

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.site_farms_item import SiteFarmsItem
        from ..models.site_service import SiteService

        d = dict(src_dict)
        name = d.pop("name")

        farms = []
        _farms = d.pop("farms", UNSET)
        for farms_item_data in _farms or []:
            farms_item = SiteFarmsItem.from_dict(farms_item_data)

            farms.append(farms_item)

        _service = d.pop("service", UNSET)
        service: Union[Unset, SiteService]
        if isinstance(_service, Unset):
            service = UNSET
        else:
            service = SiteService.from_dict(_service)

        site = cls(
            name=name,
            farms=farms,
            service=service,
        )

        return site
