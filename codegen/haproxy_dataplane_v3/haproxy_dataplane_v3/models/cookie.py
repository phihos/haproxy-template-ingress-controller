from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.cookie_type import CookieType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cookie_attr_item import CookieAttrItem
    from ..models.cookie_domain_item import CookieDomainItem


T = TypeVar("T", bound="Cookie")


@_attrs_define
class Cookie:
    """
    Attributes:
        name (str):
        attr (Union[Unset, list['CookieAttrItem']]):
        domain (Union[Unset, list['CookieDomainItem']]):
        dynamic (Union[Unset, bool]):
        httponly (Union[Unset, bool]):
        indirect (Union[Unset, bool]):
        maxidle (Union[Unset, int]):
        maxlife (Union[Unset, int]):
        nocache (Union[Unset, bool]):
        postonly (Union[Unset, bool]):
        preserve (Union[Unset, bool]):
        secure (Union[Unset, bool]):
        type_ (Union[Unset, CookieType]):
    """

    name: str
    attr: Union[Unset, list["CookieAttrItem"]] = UNSET
    domain: Union[Unset, list["CookieDomainItem"]] = UNSET
    dynamic: Union[Unset, bool] = UNSET
    httponly: Union[Unset, bool] = UNSET
    indirect: Union[Unset, bool] = UNSET
    maxidle: Union[Unset, int] = UNSET
    maxlife: Union[Unset, int] = UNSET
    nocache: Union[Unset, bool] = UNSET
    postonly: Union[Unset, bool] = UNSET
    preserve: Union[Unset, bool] = UNSET
    secure: Union[Unset, bool] = UNSET
    type_: Union[Unset, CookieType] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        attr: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.attr, Unset):
            attr = []
            for attr_item_data in self.attr:
                attr_item = attr_item_data.to_dict()
                attr.append(attr_item)

        domain: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.domain, Unset):
            domain = []
            for domain_item_data in self.domain:
                domain_item = domain_item_data.to_dict()
                domain.append(domain_item)

        dynamic = self.dynamic

        httponly = self.httponly

        indirect = self.indirect

        maxidle = self.maxidle

        maxlife = self.maxlife

        nocache = self.nocache

        postonly = self.postonly

        preserve = self.preserve

        secure = self.secure

        type_: Union[Unset, str] = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if attr is not UNSET:
            field_dict["attr"] = attr
        if domain is not UNSET:
            field_dict["domain"] = domain
        if dynamic is not UNSET:
            field_dict["dynamic"] = dynamic
        if httponly is not UNSET:
            field_dict["httponly"] = httponly
        if indirect is not UNSET:
            field_dict["indirect"] = indirect
        if maxidle is not UNSET:
            field_dict["maxidle"] = maxidle
        if maxlife is not UNSET:
            field_dict["maxlife"] = maxlife
        if nocache is not UNSET:
            field_dict["nocache"] = nocache
        if postonly is not UNSET:
            field_dict["postonly"] = postonly
        if preserve is not UNSET:
            field_dict["preserve"] = preserve
        if secure is not UNSET:
            field_dict["secure"] = secure
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cookie_attr_item import CookieAttrItem
        from ..models.cookie_domain_item import CookieDomainItem

        d = dict(src_dict)
        name = d.pop("name")

        attr = []
        _attr = d.pop("attr", UNSET)
        for attr_item_data in _attr or []:
            attr_item = CookieAttrItem.from_dict(attr_item_data)

            attr.append(attr_item)

        domain = []
        _domain = d.pop("domain", UNSET)
        for domain_item_data in _domain or []:
            domain_item = CookieDomainItem.from_dict(domain_item_data)

            domain.append(domain_item)

        dynamic = d.pop("dynamic", UNSET)

        httponly = d.pop("httponly", UNSET)

        indirect = d.pop("indirect", UNSET)

        maxidle = d.pop("maxidle", UNSET)

        maxlife = d.pop("maxlife", UNSET)

        nocache = d.pop("nocache", UNSET)

        postonly = d.pop("postonly", UNSET)

        preserve = d.pop("preserve", UNSET)

        secure = d.pop("secure", UNSET)

        _type_ = d.pop("type", UNSET)
        type_: Union[Unset, CookieType]
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = CookieType(_type_)

        cookie = cls(
            name=name,
            attr=attr,
            domain=domain,
            dynamic=dynamic,
            httponly=httponly,
            indirect=indirect,
            maxidle=maxidle,
            maxlife=maxlife,
            nocache=nocache,
            postonly=postonly,
            preserve=preserve,
            secure=secure,
            type_=type_,
        )

        cookie.additional_properties = d
        return cookie

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
