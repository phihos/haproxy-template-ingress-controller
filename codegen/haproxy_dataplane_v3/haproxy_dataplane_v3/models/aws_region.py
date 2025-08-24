from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.aws_region_ipv_4_address import AWSRegionIpv4Address
from ..models.aws_region_server_slots_growth_type import AWSRegionServerSlotsGrowthType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.aws_filters import AwsFilters


T = TypeVar("T", bound="AWSRegion")


@_attrs_define
class AWSRegion:
    """AWS region configuration

    Example:
        {'access_key_id': '****************L7GT', 'allowlist': [{'key': 'tag-key', 'value':
            'Instance:Having:This:Tag'}], 'denylist': [{'key': 'tag:Environment', 'value': 'development'}], 'enabled': True,
            'id': '0', 'ipv4_address': 'private', 'name': 'frontend-service', 'region': 'us-east-1', 'retry_timeout': 1,
            'secret_access_key': '****************soLl'}

    Attributes:
        enabled (bool):
        ipv4_address (AWSRegionIpv4Address): Select which IPv4 address the Service Discovery has to use for the backend
            server entry
        name (str):
        region (str):
        retry_timeout (int): Duration in seconds in-between data pulling requests to the AWS region
        access_key_id (Union[Unset, str]): AWS Access Key ID.
        allowlist (Union[Unset, list['AwsFilters']]): Specify the AWS filters used to filter the EC2 instances to add
        denylist (Union[Unset, list['AwsFilters']]): Specify the AWS filters used to filter the EC2 instances to ignore
        description (Union[Unset, str]):
        id (Union[None, Unset, str]): Auto generated ID.
        secret_access_key (Union[Unset, str]): AWS Secret Access Key.
        server_slots_base (Union[Unset, int]):  Default: 10.
        server_slots_growth_increment (Union[Unset, int]):
        server_slots_growth_type (Union[Unset, AWSRegionServerSlotsGrowthType]):  Default:
            AWSRegionServerSlotsGrowthType.EXPONENTIAL.
    """

    enabled: bool
    ipv4_address: AWSRegionIpv4Address
    name: str
    region: str
    retry_timeout: int
    access_key_id: Union[Unset, str] = UNSET
    allowlist: Union[Unset, list["AwsFilters"]] = UNSET
    denylist: Union[Unset, list["AwsFilters"]] = UNSET
    description: Union[Unset, str] = UNSET
    id: Union[None, Unset, str] = UNSET
    secret_access_key: Union[Unset, str] = UNSET
    server_slots_base: Union[Unset, int] = 10
    server_slots_growth_increment: Union[Unset, int] = UNSET
    server_slots_growth_type: Union[Unset, AWSRegionServerSlotsGrowthType] = AWSRegionServerSlotsGrowthType.EXPONENTIAL
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        enabled = self.enabled

        ipv4_address = self.ipv4_address.value

        name = self.name

        region = self.region

        retry_timeout = self.retry_timeout

        access_key_id = self.access_key_id

        allowlist: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.allowlist, Unset):
            allowlist = []
            for allowlist_item_data in self.allowlist:
                allowlist_item = allowlist_item_data.to_dict()
                allowlist.append(allowlist_item)

        denylist: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.denylist, Unset):
            denylist = []
            for denylist_item_data in self.denylist:
                denylist_item = denylist_item_data.to_dict()
                denylist.append(denylist_item)

        description = self.description

        id: Union[None, Unset, str]
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        secret_access_key = self.secret_access_key

        server_slots_base = self.server_slots_base

        server_slots_growth_increment = self.server_slots_growth_increment

        server_slots_growth_type: Union[Unset, str] = UNSET
        if not isinstance(self.server_slots_growth_type, Unset):
            server_slots_growth_type = self.server_slots_growth_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "enabled": enabled,
                "ipv4_address": ipv4_address,
                "name": name,
                "region": region,
                "retry_timeout": retry_timeout,
            }
        )
        if access_key_id is not UNSET:
            field_dict["access_key_id"] = access_key_id
        if allowlist is not UNSET:
            field_dict["allowlist"] = allowlist
        if denylist is not UNSET:
            field_dict["denylist"] = denylist
        if description is not UNSET:
            field_dict["description"] = description
        if id is not UNSET:
            field_dict["id"] = id
        if secret_access_key is not UNSET:
            field_dict["secret_access_key"] = secret_access_key
        if server_slots_base is not UNSET:
            field_dict["server_slots_base"] = server_slots_base
        if server_slots_growth_increment is not UNSET:
            field_dict["server_slots_growth_increment"] = server_slots_growth_increment
        if server_slots_growth_type is not UNSET:
            field_dict["server_slots_growth_type"] = server_slots_growth_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.aws_filters import AwsFilters

        d = dict(src_dict)
        enabled = d.pop("enabled")

        ipv4_address = AWSRegionIpv4Address(d.pop("ipv4_address"))

        name = d.pop("name")

        region = d.pop("region")

        retry_timeout = d.pop("retry_timeout")

        access_key_id = d.pop("access_key_id", UNSET)

        allowlist = []
        _allowlist = d.pop("allowlist", UNSET)
        for allowlist_item_data in _allowlist or []:
            allowlist_item = AwsFilters.from_dict(allowlist_item_data)

            allowlist.append(allowlist_item)

        denylist = []
        _denylist = d.pop("denylist", UNSET)
        for denylist_item_data in _denylist or []:
            denylist_item = AwsFilters.from_dict(denylist_item_data)

            denylist.append(denylist_item)

        description = d.pop("description", UNSET)

        def _parse_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        id = _parse_id(d.pop("id", UNSET))

        secret_access_key = d.pop("secret_access_key", UNSET)

        server_slots_base = d.pop("server_slots_base", UNSET)

        server_slots_growth_increment = d.pop("server_slots_growth_increment", UNSET)

        _server_slots_growth_type = d.pop("server_slots_growth_type", UNSET)
        server_slots_growth_type: Union[Unset, AWSRegionServerSlotsGrowthType]
        if isinstance(_server_slots_growth_type, Unset):
            server_slots_growth_type = UNSET
        else:
            server_slots_growth_type = AWSRegionServerSlotsGrowthType(_server_slots_growth_type)

        aws_region = cls(
            enabled=enabled,
            ipv4_address=ipv4_address,
            name=name,
            region=region,
            retry_timeout=retry_timeout,
            access_key_id=access_key_id,
            allowlist=allowlist,
            denylist=denylist,
            description=description,
            id=id,
            secret_access_key=secret_access_key,
            server_slots_base=server_slots_base,
            server_slots_growth_increment=server_slots_growth_increment,
            server_slots_growth_type=server_slots_growth_type,
        )

        aws_region.additional_properties = d
        return aws_region

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
