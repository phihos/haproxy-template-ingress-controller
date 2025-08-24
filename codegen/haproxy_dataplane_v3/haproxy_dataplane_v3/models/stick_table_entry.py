from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="StickTableEntry")


@_attrs_define
class StickTableEntry:
    """One entry in stick table

    Attributes:
        bytes_in_cnt (Union[None, Unset, int]):
        bytes_in_rate (Union[None, Unset, int]):
        bytes_out_cnt (Union[None, Unset, int]):
        bytes_out_rate (Union[None, Unset, int]):
        conn_cnt (Union[None, Unset, int]):
        conn_cur (Union[None, Unset, int]):
        conn_rate (Union[None, Unset, int]):
        exp (Union[None, Unset, int]):
        glitch_cnt (Union[None, Unset, int]):
        glitch_rate (Union[None, Unset, int]):
        gpc0 (Union[None, Unset, int]):
        gpc0_rate (Union[None, Unset, int]):
        gpc1 (Union[None, Unset, int]):
        gpc1_rate (Union[None, Unset, int]):
        gpt0 (Union[None, Unset, int]):
        http_err_cnt (Union[None, Unset, int]):
        http_err_rate (Union[None, Unset, int]):
        http_req_cnt (Union[None, Unset, int]):
        http_req_rate (Union[None, Unset, int]):
        id (Union[Unset, str]):
        key (Union[Unset, str]):
        server_id (Union[None, Unset, int]):
        sess_cnt (Union[None, Unset, int]):
        sess_rate (Union[None, Unset, int]):
        use (Union[Unset, bool]):
    """

    bytes_in_cnt: Union[None, Unset, int] = UNSET
    bytes_in_rate: Union[None, Unset, int] = UNSET
    bytes_out_cnt: Union[None, Unset, int] = UNSET
    bytes_out_rate: Union[None, Unset, int] = UNSET
    conn_cnt: Union[None, Unset, int] = UNSET
    conn_cur: Union[None, Unset, int] = UNSET
    conn_rate: Union[None, Unset, int] = UNSET
    exp: Union[None, Unset, int] = UNSET
    glitch_cnt: Union[None, Unset, int] = UNSET
    glitch_rate: Union[None, Unset, int] = UNSET
    gpc0: Union[None, Unset, int] = UNSET
    gpc0_rate: Union[None, Unset, int] = UNSET
    gpc1: Union[None, Unset, int] = UNSET
    gpc1_rate: Union[None, Unset, int] = UNSET
    gpt0: Union[None, Unset, int] = UNSET
    http_err_cnt: Union[None, Unset, int] = UNSET
    http_err_rate: Union[None, Unset, int] = UNSET
    http_req_cnt: Union[None, Unset, int] = UNSET
    http_req_rate: Union[None, Unset, int] = UNSET
    id: Union[Unset, str] = UNSET
    key: Union[Unset, str] = UNSET
    server_id: Union[None, Unset, int] = UNSET
    sess_cnt: Union[None, Unset, int] = UNSET
    sess_rate: Union[None, Unset, int] = UNSET
    use: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        bytes_in_cnt: Union[None, Unset, int]
        if isinstance(self.bytes_in_cnt, Unset):
            bytes_in_cnt = UNSET
        else:
            bytes_in_cnt = self.bytes_in_cnt

        bytes_in_rate: Union[None, Unset, int]
        if isinstance(self.bytes_in_rate, Unset):
            bytes_in_rate = UNSET
        else:
            bytes_in_rate = self.bytes_in_rate

        bytes_out_cnt: Union[None, Unset, int]
        if isinstance(self.bytes_out_cnt, Unset):
            bytes_out_cnt = UNSET
        else:
            bytes_out_cnt = self.bytes_out_cnt

        bytes_out_rate: Union[None, Unset, int]
        if isinstance(self.bytes_out_rate, Unset):
            bytes_out_rate = UNSET
        else:
            bytes_out_rate = self.bytes_out_rate

        conn_cnt: Union[None, Unset, int]
        if isinstance(self.conn_cnt, Unset):
            conn_cnt = UNSET
        else:
            conn_cnt = self.conn_cnt

        conn_cur: Union[None, Unset, int]
        if isinstance(self.conn_cur, Unset):
            conn_cur = UNSET
        else:
            conn_cur = self.conn_cur

        conn_rate: Union[None, Unset, int]
        if isinstance(self.conn_rate, Unset):
            conn_rate = UNSET
        else:
            conn_rate = self.conn_rate

        exp: Union[None, Unset, int]
        if isinstance(self.exp, Unset):
            exp = UNSET
        else:
            exp = self.exp

        glitch_cnt: Union[None, Unset, int]
        if isinstance(self.glitch_cnt, Unset):
            glitch_cnt = UNSET
        else:
            glitch_cnt = self.glitch_cnt

        glitch_rate: Union[None, Unset, int]
        if isinstance(self.glitch_rate, Unset):
            glitch_rate = UNSET
        else:
            glitch_rate = self.glitch_rate

        gpc0: Union[None, Unset, int]
        if isinstance(self.gpc0, Unset):
            gpc0 = UNSET
        else:
            gpc0 = self.gpc0

        gpc0_rate: Union[None, Unset, int]
        if isinstance(self.gpc0_rate, Unset):
            gpc0_rate = UNSET
        else:
            gpc0_rate = self.gpc0_rate

        gpc1: Union[None, Unset, int]
        if isinstance(self.gpc1, Unset):
            gpc1 = UNSET
        else:
            gpc1 = self.gpc1

        gpc1_rate: Union[None, Unset, int]
        if isinstance(self.gpc1_rate, Unset):
            gpc1_rate = UNSET
        else:
            gpc1_rate = self.gpc1_rate

        gpt0: Union[None, Unset, int]
        if isinstance(self.gpt0, Unset):
            gpt0 = UNSET
        else:
            gpt0 = self.gpt0

        http_err_cnt: Union[None, Unset, int]
        if isinstance(self.http_err_cnt, Unset):
            http_err_cnt = UNSET
        else:
            http_err_cnt = self.http_err_cnt

        http_err_rate: Union[None, Unset, int]
        if isinstance(self.http_err_rate, Unset):
            http_err_rate = UNSET
        else:
            http_err_rate = self.http_err_rate

        http_req_cnt: Union[None, Unset, int]
        if isinstance(self.http_req_cnt, Unset):
            http_req_cnt = UNSET
        else:
            http_req_cnt = self.http_req_cnt

        http_req_rate: Union[None, Unset, int]
        if isinstance(self.http_req_rate, Unset):
            http_req_rate = UNSET
        else:
            http_req_rate = self.http_req_rate

        id = self.id

        key = self.key

        server_id: Union[None, Unset, int]
        if isinstance(self.server_id, Unset):
            server_id = UNSET
        else:
            server_id = self.server_id

        sess_cnt: Union[None, Unset, int]
        if isinstance(self.sess_cnt, Unset):
            sess_cnt = UNSET
        else:
            sess_cnt = self.sess_cnt

        sess_rate: Union[None, Unset, int]
        if isinstance(self.sess_rate, Unset):
            sess_rate = UNSET
        else:
            sess_rate = self.sess_rate

        use = self.use

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if bytes_in_cnt is not UNSET:
            field_dict["bytes_in_cnt"] = bytes_in_cnt
        if bytes_in_rate is not UNSET:
            field_dict["bytes_in_rate"] = bytes_in_rate
        if bytes_out_cnt is not UNSET:
            field_dict["bytes_out_cnt"] = bytes_out_cnt
        if bytes_out_rate is not UNSET:
            field_dict["bytes_out_rate"] = bytes_out_rate
        if conn_cnt is not UNSET:
            field_dict["conn_cnt"] = conn_cnt
        if conn_cur is not UNSET:
            field_dict["conn_cur"] = conn_cur
        if conn_rate is not UNSET:
            field_dict["conn_rate"] = conn_rate
        if exp is not UNSET:
            field_dict["exp"] = exp
        if glitch_cnt is not UNSET:
            field_dict["glitch_cnt"] = glitch_cnt
        if glitch_rate is not UNSET:
            field_dict["glitch_rate"] = glitch_rate
        if gpc0 is not UNSET:
            field_dict["gpc0"] = gpc0
        if gpc0_rate is not UNSET:
            field_dict["gpc0_rate"] = gpc0_rate
        if gpc1 is not UNSET:
            field_dict["gpc1"] = gpc1
        if gpc1_rate is not UNSET:
            field_dict["gpc1_rate"] = gpc1_rate
        if gpt0 is not UNSET:
            field_dict["gpt0"] = gpt0
        if http_err_cnt is not UNSET:
            field_dict["http_err_cnt"] = http_err_cnt
        if http_err_rate is not UNSET:
            field_dict["http_err_rate"] = http_err_rate
        if http_req_cnt is not UNSET:
            field_dict["http_req_cnt"] = http_req_cnt
        if http_req_rate is not UNSET:
            field_dict["http_req_rate"] = http_req_rate
        if id is not UNSET:
            field_dict["id"] = id
        if key is not UNSET:
            field_dict["key"] = key
        if server_id is not UNSET:
            field_dict["server_id"] = server_id
        if sess_cnt is not UNSET:
            field_dict["sess_cnt"] = sess_cnt
        if sess_rate is not UNSET:
            field_dict["sess_rate"] = sess_rate
        if use is not UNSET:
            field_dict["use"] = use

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_bytes_in_cnt(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        bytes_in_cnt = _parse_bytes_in_cnt(d.pop("bytes_in_cnt", UNSET))

        def _parse_bytes_in_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        bytes_in_rate = _parse_bytes_in_rate(d.pop("bytes_in_rate", UNSET))

        def _parse_bytes_out_cnt(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        bytes_out_cnt = _parse_bytes_out_cnt(d.pop("bytes_out_cnt", UNSET))

        def _parse_bytes_out_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        bytes_out_rate = _parse_bytes_out_rate(d.pop("bytes_out_rate", UNSET))

        def _parse_conn_cnt(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        conn_cnt = _parse_conn_cnt(d.pop("conn_cnt", UNSET))

        def _parse_conn_cur(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        conn_cur = _parse_conn_cur(d.pop("conn_cur", UNSET))

        def _parse_conn_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        conn_rate = _parse_conn_rate(d.pop("conn_rate", UNSET))

        def _parse_exp(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        exp = _parse_exp(d.pop("exp", UNSET))

        def _parse_glitch_cnt(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        glitch_cnt = _parse_glitch_cnt(d.pop("glitch_cnt", UNSET))

        def _parse_glitch_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        glitch_rate = _parse_glitch_rate(d.pop("glitch_rate", UNSET))

        def _parse_gpc0(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        gpc0 = _parse_gpc0(d.pop("gpc0", UNSET))

        def _parse_gpc0_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        gpc0_rate = _parse_gpc0_rate(d.pop("gpc0_rate", UNSET))

        def _parse_gpc1(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        gpc1 = _parse_gpc1(d.pop("gpc1", UNSET))

        def _parse_gpc1_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        gpc1_rate = _parse_gpc1_rate(d.pop("gpc1_rate", UNSET))

        def _parse_gpt0(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        gpt0 = _parse_gpt0(d.pop("gpt0", UNSET))

        def _parse_http_err_cnt(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        http_err_cnt = _parse_http_err_cnt(d.pop("http_err_cnt", UNSET))

        def _parse_http_err_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        http_err_rate = _parse_http_err_rate(d.pop("http_err_rate", UNSET))

        def _parse_http_req_cnt(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        http_req_cnt = _parse_http_req_cnt(d.pop("http_req_cnt", UNSET))

        def _parse_http_req_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        http_req_rate = _parse_http_req_rate(d.pop("http_req_rate", UNSET))

        id = d.pop("id", UNSET)

        key = d.pop("key", UNSET)

        def _parse_server_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        server_id = _parse_server_id(d.pop("server_id", UNSET))

        def _parse_sess_cnt(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        sess_cnt = _parse_sess_cnt(d.pop("sess_cnt", UNSET))

        def _parse_sess_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        sess_rate = _parse_sess_rate(d.pop("sess_rate", UNSET))

        use = d.pop("use", UNSET)

        stick_table_entry = cls(
            bytes_in_cnt=bytes_in_cnt,
            bytes_in_rate=bytes_in_rate,
            bytes_out_cnt=bytes_out_cnt,
            bytes_out_rate=bytes_out_rate,
            conn_cnt=conn_cnt,
            conn_cur=conn_cur,
            conn_rate=conn_rate,
            exp=exp,
            glitch_cnt=glitch_cnt,
            glitch_rate=glitch_rate,
            gpc0=gpc0,
            gpc0_rate=gpc0_rate,
            gpc1=gpc1,
            gpc1_rate=gpc1_rate,
            gpt0=gpt0,
            http_err_cnt=http_err_cnt,
            http_err_rate=http_err_rate,
            http_req_cnt=http_req_cnt,
            http_req_rate=http_req_rate,
            id=id,
            key=key,
            server_id=server_id,
            sess_cnt=sess_cnt,
            sess_rate=sess_rate,
            use=use,
        )

        stick_table_entry.additional_properties = d
        return stick_table_entry

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
