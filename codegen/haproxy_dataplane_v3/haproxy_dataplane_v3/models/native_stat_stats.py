from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.native_stat_stats_agent_status import NativeStatStatsAgentStatus
from ..models.native_stat_stats_check_status import NativeStatStatsCheckStatus
from ..models.native_stat_stats_mode import NativeStatStatsMode
from ..models.native_stat_stats_status import NativeStatStatsStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="NativeStatStats")


@_attrs_define
class NativeStatStats:
    """
    Example:
        {'bin': 4326578, 'bout': 889901290, 'comp_byp': 0, 'comp_in': 0, 'comp_out': 0, 'comp_rsp': 0, 'conn_rate': 12,
            'conn_rate_max': 456, 'conn_tot': 45682, 'dcon': 0, 'dreq': 4, 'dresp': 1, 'dses': 0, 'ereq': 54, 'hrsp_1xx': 0,
            'hrsp_2xx': 165, 'hrsp_3xx': 12, 'hrsp_4xx': 50, 'hrsp_5xx': 4, 'hrsp_other': 0, 'iid': 0, 'intercepted': 346,
            'last_chk': 'L4OK in 0ms', 'mode': 'http', 'pid': 3204, 'rate': 64, 'rate_lim': 20000, 'rate_max': 4000,
            'req_rate': 49, 'req_rate_max': 3965, 'req_total': 1254786, 'scur': 129, 'slim': 2000, 'smax': 2000, 'status':
            'UP', 'stot': 12902}

    Attributes:
        act (Union[None, Unset, int]):
        addr (Union[Unset, str]):
        agent_code (Union[None, Unset, int]):
        agent_desc (Union[Unset, str]):
        agent_duration (Union[None, Unset, int]):
        agent_fall (Union[None, Unset, int]):
        agent_health (Union[None, Unset, int]):
        agent_rise (Union[None, Unset, int]):
        agent_status (Union[Unset, NativeStatStatsAgentStatus]):
        algo (Union[Unset, str]):
        bck (Union[None, Unset, int]):
        bin_ (Union[None, Unset, int]):
        bout (Union[None, Unset, int]):
        check_code (Union[None, Unset, int]):
        check_desc (Union[Unset, str]):
        check_duration (Union[None, Unset, int]):
        check_fall (Union[None, Unset, int]):
        check_health (Union[None, Unset, int]):
        check_rise (Union[None, Unset, int]):
        check_status (Union[Unset, NativeStatStatsCheckStatus]):
        chkdown (Union[None, Unset, int]):
        chkfail (Union[None, Unset, int]):
        cli_abrt (Union[None, Unset, int]):
        comp_byp (Union[None, Unset, int]):
        comp_in (Union[None, Unset, int]):
        comp_out (Union[None, Unset, int]):
        comp_rsp (Union[None, Unset, int]):
        conn_rate (Union[None, Unset, int]):
        conn_rate_max (Union[None, Unset, int]):
        conn_tot (Union[None, Unset, int]):
        cookie (Union[Unset, str]):
        ctime (Union[None, Unset, int]):
        dcon (Union[None, Unset, int]):
        downtime (Union[None, Unset, int]):
        dreq (Union[None, Unset, int]):
        dresp (Union[None, Unset, int]):
        dses (Union[None, Unset, int]):
        econ (Union[None, Unset, int]):
        ereq (Union[None, Unset, int]):
        eresp (Union[None, Unset, int]):
        hanafail (Union[Unset, str]):
        hrsp_1xx (Union[None, Unset, int]):
        hrsp_2xx (Union[None, Unset, int]):
        hrsp_3xx (Union[None, Unset, int]):
        hrsp_4xx (Union[None, Unset, int]):
        hrsp_5xx (Union[None, Unset, int]):
        hrsp_other (Union[None, Unset, int]):
        iid (Union[None, Unset, int]):
        intercepted (Union[None, Unset, int]):
        last_agt (Union[None, Unset, str]):
        last_chk (Union[None, Unset, str]):
        lastchg (Union[None, Unset, int]):
        lastsess (Union[None, Unset, int]):
        lbtot (Union[None, Unset, int]):
        mode (Union[Unset, NativeStatStatsMode]):
        pid (Union[None, Unset, int]):
        qcur (Union[None, Unset, int]):
        qlimit (Union[None, Unset, int]):
        qmax (Union[None, Unset, int]):
        qtime (Union[None, Unset, int]):
        rate (Union[None, Unset, int]):
        rate_lim (Union[None, Unset, int]):
        rate_max (Union[None, Unset, int]):
        req_rate (Union[None, Unset, int]):
        req_rate_max (Union[None, Unset, int]):
        req_tot (Union[None, Unset, int]):
        rtime (Union[None, Unset, int]):
        scur (Union[None, Unset, int]):
        sid (Union[None, Unset, int]):
        slim (Union[None, Unset, int]):
        smax (Union[None, Unset, int]):
        srv_abrt (Union[None, Unset, int]):
        status (Union[Unset, NativeStatStatsStatus]):
        stot (Union[None, Unset, int]):
        throttle (Union[None, Unset, int]):
        tracked (Union[Unset, str]):
        ttime (Union[None, Unset, int]):
        weight (Union[None, Unset, int]):
        wredis (Union[None, Unset, int]):
        wretr (Union[None, Unset, int]):
    """

    act: Union[None, Unset, int] = UNSET
    addr: Union[Unset, str] = UNSET
    agent_code: Union[None, Unset, int] = UNSET
    agent_desc: Union[Unset, str] = UNSET
    agent_duration: Union[None, Unset, int] = UNSET
    agent_fall: Union[None, Unset, int] = UNSET
    agent_health: Union[None, Unset, int] = UNSET
    agent_rise: Union[None, Unset, int] = UNSET
    agent_status: Union[Unset, NativeStatStatsAgentStatus] = UNSET
    algo: Union[Unset, str] = UNSET
    bck: Union[None, Unset, int] = UNSET
    bin_: Union[None, Unset, int] = UNSET
    bout: Union[None, Unset, int] = UNSET
    check_code: Union[None, Unset, int] = UNSET
    check_desc: Union[Unset, str] = UNSET
    check_duration: Union[None, Unset, int] = UNSET
    check_fall: Union[None, Unset, int] = UNSET
    check_health: Union[None, Unset, int] = UNSET
    check_rise: Union[None, Unset, int] = UNSET
    check_status: Union[Unset, NativeStatStatsCheckStatus] = UNSET
    chkdown: Union[None, Unset, int] = UNSET
    chkfail: Union[None, Unset, int] = UNSET
    cli_abrt: Union[None, Unset, int] = UNSET
    comp_byp: Union[None, Unset, int] = UNSET
    comp_in: Union[None, Unset, int] = UNSET
    comp_out: Union[None, Unset, int] = UNSET
    comp_rsp: Union[None, Unset, int] = UNSET
    conn_rate: Union[None, Unset, int] = UNSET
    conn_rate_max: Union[None, Unset, int] = UNSET
    conn_tot: Union[None, Unset, int] = UNSET
    cookie: Union[Unset, str] = UNSET
    ctime: Union[None, Unset, int] = UNSET
    dcon: Union[None, Unset, int] = UNSET
    downtime: Union[None, Unset, int] = UNSET
    dreq: Union[None, Unset, int] = UNSET
    dresp: Union[None, Unset, int] = UNSET
    dses: Union[None, Unset, int] = UNSET
    econ: Union[None, Unset, int] = UNSET
    ereq: Union[None, Unset, int] = UNSET
    eresp: Union[None, Unset, int] = UNSET
    hanafail: Union[Unset, str] = UNSET
    hrsp_1xx: Union[None, Unset, int] = UNSET
    hrsp_2xx: Union[None, Unset, int] = UNSET
    hrsp_3xx: Union[None, Unset, int] = UNSET
    hrsp_4xx: Union[None, Unset, int] = UNSET
    hrsp_5xx: Union[None, Unset, int] = UNSET
    hrsp_other: Union[None, Unset, int] = UNSET
    iid: Union[None, Unset, int] = UNSET
    intercepted: Union[None, Unset, int] = UNSET
    last_agt: Union[None, Unset, str] = UNSET
    last_chk: Union[None, Unset, str] = UNSET
    lastchg: Union[None, Unset, int] = UNSET
    lastsess: Union[None, Unset, int] = UNSET
    lbtot: Union[None, Unset, int] = UNSET
    mode: Union[Unset, NativeStatStatsMode] = UNSET
    pid: Union[None, Unset, int] = UNSET
    qcur: Union[None, Unset, int] = UNSET
    qlimit: Union[None, Unset, int] = UNSET
    qmax: Union[None, Unset, int] = UNSET
    qtime: Union[None, Unset, int] = UNSET
    rate: Union[None, Unset, int] = UNSET
    rate_lim: Union[None, Unset, int] = UNSET
    rate_max: Union[None, Unset, int] = UNSET
    req_rate: Union[None, Unset, int] = UNSET
    req_rate_max: Union[None, Unset, int] = UNSET
    req_tot: Union[None, Unset, int] = UNSET
    rtime: Union[None, Unset, int] = UNSET
    scur: Union[None, Unset, int] = UNSET
    sid: Union[None, Unset, int] = UNSET
    slim: Union[None, Unset, int] = UNSET
    smax: Union[None, Unset, int] = UNSET
    srv_abrt: Union[None, Unset, int] = UNSET
    status: Union[Unset, NativeStatStatsStatus] = UNSET
    stot: Union[None, Unset, int] = UNSET
    throttle: Union[None, Unset, int] = UNSET
    tracked: Union[Unset, str] = UNSET
    ttime: Union[None, Unset, int] = UNSET
    weight: Union[None, Unset, int] = UNSET
    wredis: Union[None, Unset, int] = UNSET
    wretr: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        act: Union[None, Unset, int]
        if isinstance(self.act, Unset):
            act = UNSET
        else:
            act = self.act

        addr = self.addr

        agent_code: Union[None, Unset, int]
        if isinstance(self.agent_code, Unset):
            agent_code = UNSET
        else:
            agent_code = self.agent_code

        agent_desc = self.agent_desc

        agent_duration: Union[None, Unset, int]
        if isinstance(self.agent_duration, Unset):
            agent_duration = UNSET
        else:
            agent_duration = self.agent_duration

        agent_fall: Union[None, Unset, int]
        if isinstance(self.agent_fall, Unset):
            agent_fall = UNSET
        else:
            agent_fall = self.agent_fall

        agent_health: Union[None, Unset, int]
        if isinstance(self.agent_health, Unset):
            agent_health = UNSET
        else:
            agent_health = self.agent_health

        agent_rise: Union[None, Unset, int]
        if isinstance(self.agent_rise, Unset):
            agent_rise = UNSET
        else:
            agent_rise = self.agent_rise

        agent_status: Union[Unset, str] = UNSET
        if not isinstance(self.agent_status, Unset):
            agent_status = self.agent_status.value

        algo = self.algo

        bck: Union[None, Unset, int]
        if isinstance(self.bck, Unset):
            bck = UNSET
        else:
            bck = self.bck

        bin_: Union[None, Unset, int]
        if isinstance(self.bin_, Unset):
            bin_ = UNSET
        else:
            bin_ = self.bin_

        bout: Union[None, Unset, int]
        if isinstance(self.bout, Unset):
            bout = UNSET
        else:
            bout = self.bout

        check_code: Union[None, Unset, int]
        if isinstance(self.check_code, Unset):
            check_code = UNSET
        else:
            check_code = self.check_code

        check_desc = self.check_desc

        check_duration: Union[None, Unset, int]
        if isinstance(self.check_duration, Unset):
            check_duration = UNSET
        else:
            check_duration = self.check_duration

        check_fall: Union[None, Unset, int]
        if isinstance(self.check_fall, Unset):
            check_fall = UNSET
        else:
            check_fall = self.check_fall

        check_health: Union[None, Unset, int]
        if isinstance(self.check_health, Unset):
            check_health = UNSET
        else:
            check_health = self.check_health

        check_rise: Union[None, Unset, int]
        if isinstance(self.check_rise, Unset):
            check_rise = UNSET
        else:
            check_rise = self.check_rise

        check_status: Union[Unset, str] = UNSET
        if not isinstance(self.check_status, Unset):
            check_status = self.check_status.value

        chkdown: Union[None, Unset, int]
        if isinstance(self.chkdown, Unset):
            chkdown = UNSET
        else:
            chkdown = self.chkdown

        chkfail: Union[None, Unset, int]
        if isinstance(self.chkfail, Unset):
            chkfail = UNSET
        else:
            chkfail = self.chkfail

        cli_abrt: Union[None, Unset, int]
        if isinstance(self.cli_abrt, Unset):
            cli_abrt = UNSET
        else:
            cli_abrt = self.cli_abrt

        comp_byp: Union[None, Unset, int]
        if isinstance(self.comp_byp, Unset):
            comp_byp = UNSET
        else:
            comp_byp = self.comp_byp

        comp_in: Union[None, Unset, int]
        if isinstance(self.comp_in, Unset):
            comp_in = UNSET
        else:
            comp_in = self.comp_in

        comp_out: Union[None, Unset, int]
        if isinstance(self.comp_out, Unset):
            comp_out = UNSET
        else:
            comp_out = self.comp_out

        comp_rsp: Union[None, Unset, int]
        if isinstance(self.comp_rsp, Unset):
            comp_rsp = UNSET
        else:
            comp_rsp = self.comp_rsp

        conn_rate: Union[None, Unset, int]
        if isinstance(self.conn_rate, Unset):
            conn_rate = UNSET
        else:
            conn_rate = self.conn_rate

        conn_rate_max: Union[None, Unset, int]
        if isinstance(self.conn_rate_max, Unset):
            conn_rate_max = UNSET
        else:
            conn_rate_max = self.conn_rate_max

        conn_tot: Union[None, Unset, int]
        if isinstance(self.conn_tot, Unset):
            conn_tot = UNSET
        else:
            conn_tot = self.conn_tot

        cookie = self.cookie

        ctime: Union[None, Unset, int]
        if isinstance(self.ctime, Unset):
            ctime = UNSET
        else:
            ctime = self.ctime

        dcon: Union[None, Unset, int]
        if isinstance(self.dcon, Unset):
            dcon = UNSET
        else:
            dcon = self.dcon

        downtime: Union[None, Unset, int]
        if isinstance(self.downtime, Unset):
            downtime = UNSET
        else:
            downtime = self.downtime

        dreq: Union[None, Unset, int]
        if isinstance(self.dreq, Unset):
            dreq = UNSET
        else:
            dreq = self.dreq

        dresp: Union[None, Unset, int]
        if isinstance(self.dresp, Unset):
            dresp = UNSET
        else:
            dresp = self.dresp

        dses: Union[None, Unset, int]
        if isinstance(self.dses, Unset):
            dses = UNSET
        else:
            dses = self.dses

        econ: Union[None, Unset, int]
        if isinstance(self.econ, Unset):
            econ = UNSET
        else:
            econ = self.econ

        ereq: Union[None, Unset, int]
        if isinstance(self.ereq, Unset):
            ereq = UNSET
        else:
            ereq = self.ereq

        eresp: Union[None, Unset, int]
        if isinstance(self.eresp, Unset):
            eresp = UNSET
        else:
            eresp = self.eresp

        hanafail = self.hanafail

        hrsp_1xx: Union[None, Unset, int]
        if isinstance(self.hrsp_1xx, Unset):
            hrsp_1xx = UNSET
        else:
            hrsp_1xx = self.hrsp_1xx

        hrsp_2xx: Union[None, Unset, int]
        if isinstance(self.hrsp_2xx, Unset):
            hrsp_2xx = UNSET
        else:
            hrsp_2xx = self.hrsp_2xx

        hrsp_3xx: Union[None, Unset, int]
        if isinstance(self.hrsp_3xx, Unset):
            hrsp_3xx = UNSET
        else:
            hrsp_3xx = self.hrsp_3xx

        hrsp_4xx: Union[None, Unset, int]
        if isinstance(self.hrsp_4xx, Unset):
            hrsp_4xx = UNSET
        else:
            hrsp_4xx = self.hrsp_4xx

        hrsp_5xx: Union[None, Unset, int]
        if isinstance(self.hrsp_5xx, Unset):
            hrsp_5xx = UNSET
        else:
            hrsp_5xx = self.hrsp_5xx

        hrsp_other: Union[None, Unset, int]
        if isinstance(self.hrsp_other, Unset):
            hrsp_other = UNSET
        else:
            hrsp_other = self.hrsp_other

        iid: Union[None, Unset, int]
        if isinstance(self.iid, Unset):
            iid = UNSET
        else:
            iid = self.iid

        intercepted: Union[None, Unset, int]
        if isinstance(self.intercepted, Unset):
            intercepted = UNSET
        else:
            intercepted = self.intercepted

        last_agt: Union[None, Unset, str]
        if isinstance(self.last_agt, Unset):
            last_agt = UNSET
        else:
            last_agt = self.last_agt

        last_chk: Union[None, Unset, str]
        if isinstance(self.last_chk, Unset):
            last_chk = UNSET
        else:
            last_chk = self.last_chk

        lastchg: Union[None, Unset, int]
        if isinstance(self.lastchg, Unset):
            lastchg = UNSET
        else:
            lastchg = self.lastchg

        lastsess: Union[None, Unset, int]
        if isinstance(self.lastsess, Unset):
            lastsess = UNSET
        else:
            lastsess = self.lastsess

        lbtot: Union[None, Unset, int]
        if isinstance(self.lbtot, Unset):
            lbtot = UNSET
        else:
            lbtot = self.lbtot

        mode: Union[Unset, str] = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        pid: Union[None, Unset, int]
        if isinstance(self.pid, Unset):
            pid = UNSET
        else:
            pid = self.pid

        qcur: Union[None, Unset, int]
        if isinstance(self.qcur, Unset):
            qcur = UNSET
        else:
            qcur = self.qcur

        qlimit: Union[None, Unset, int]
        if isinstance(self.qlimit, Unset):
            qlimit = UNSET
        else:
            qlimit = self.qlimit

        qmax: Union[None, Unset, int]
        if isinstance(self.qmax, Unset):
            qmax = UNSET
        else:
            qmax = self.qmax

        qtime: Union[None, Unset, int]
        if isinstance(self.qtime, Unset):
            qtime = UNSET
        else:
            qtime = self.qtime

        rate: Union[None, Unset, int]
        if isinstance(self.rate, Unset):
            rate = UNSET
        else:
            rate = self.rate

        rate_lim: Union[None, Unset, int]
        if isinstance(self.rate_lim, Unset):
            rate_lim = UNSET
        else:
            rate_lim = self.rate_lim

        rate_max: Union[None, Unset, int]
        if isinstance(self.rate_max, Unset):
            rate_max = UNSET
        else:
            rate_max = self.rate_max

        req_rate: Union[None, Unset, int]
        if isinstance(self.req_rate, Unset):
            req_rate = UNSET
        else:
            req_rate = self.req_rate

        req_rate_max: Union[None, Unset, int]
        if isinstance(self.req_rate_max, Unset):
            req_rate_max = UNSET
        else:
            req_rate_max = self.req_rate_max

        req_tot: Union[None, Unset, int]
        if isinstance(self.req_tot, Unset):
            req_tot = UNSET
        else:
            req_tot = self.req_tot

        rtime: Union[None, Unset, int]
        if isinstance(self.rtime, Unset):
            rtime = UNSET
        else:
            rtime = self.rtime

        scur: Union[None, Unset, int]
        if isinstance(self.scur, Unset):
            scur = UNSET
        else:
            scur = self.scur

        sid: Union[None, Unset, int]
        if isinstance(self.sid, Unset):
            sid = UNSET
        else:
            sid = self.sid

        slim: Union[None, Unset, int]
        if isinstance(self.slim, Unset):
            slim = UNSET
        else:
            slim = self.slim

        smax: Union[None, Unset, int]
        if isinstance(self.smax, Unset):
            smax = UNSET
        else:
            smax = self.smax

        srv_abrt: Union[None, Unset, int]
        if isinstance(self.srv_abrt, Unset):
            srv_abrt = UNSET
        else:
            srv_abrt = self.srv_abrt

        status: Union[Unset, str] = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        stot: Union[None, Unset, int]
        if isinstance(self.stot, Unset):
            stot = UNSET
        else:
            stot = self.stot

        throttle: Union[None, Unset, int]
        if isinstance(self.throttle, Unset):
            throttle = UNSET
        else:
            throttle = self.throttle

        tracked = self.tracked

        ttime: Union[None, Unset, int]
        if isinstance(self.ttime, Unset):
            ttime = UNSET
        else:
            ttime = self.ttime

        weight: Union[None, Unset, int]
        if isinstance(self.weight, Unset):
            weight = UNSET
        else:
            weight = self.weight

        wredis: Union[None, Unset, int]
        if isinstance(self.wredis, Unset):
            wredis = UNSET
        else:
            wredis = self.wredis

        wretr: Union[None, Unset, int]
        if isinstance(self.wretr, Unset):
            wretr = UNSET
        else:
            wretr = self.wretr

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if act is not UNSET:
            field_dict["act"] = act
        if addr is not UNSET:
            field_dict["addr"] = addr
        if agent_code is not UNSET:
            field_dict["agent_code"] = agent_code
        if agent_desc is not UNSET:
            field_dict["agent_desc"] = agent_desc
        if agent_duration is not UNSET:
            field_dict["agent_duration"] = agent_duration
        if agent_fall is not UNSET:
            field_dict["agent_fall"] = agent_fall
        if agent_health is not UNSET:
            field_dict["agent_health"] = agent_health
        if agent_rise is not UNSET:
            field_dict["agent_rise"] = agent_rise
        if agent_status is not UNSET:
            field_dict["agent_status"] = agent_status
        if algo is not UNSET:
            field_dict["algo"] = algo
        if bck is not UNSET:
            field_dict["bck"] = bck
        if bin_ is not UNSET:
            field_dict["bin"] = bin_
        if bout is not UNSET:
            field_dict["bout"] = bout
        if check_code is not UNSET:
            field_dict["check_code"] = check_code
        if check_desc is not UNSET:
            field_dict["check_desc"] = check_desc
        if check_duration is not UNSET:
            field_dict["check_duration"] = check_duration
        if check_fall is not UNSET:
            field_dict["check_fall"] = check_fall
        if check_health is not UNSET:
            field_dict["check_health"] = check_health
        if check_rise is not UNSET:
            field_dict["check_rise"] = check_rise
        if check_status is not UNSET:
            field_dict["check_status"] = check_status
        if chkdown is not UNSET:
            field_dict["chkdown"] = chkdown
        if chkfail is not UNSET:
            field_dict["chkfail"] = chkfail
        if cli_abrt is not UNSET:
            field_dict["cli_abrt"] = cli_abrt
        if comp_byp is not UNSET:
            field_dict["comp_byp"] = comp_byp
        if comp_in is not UNSET:
            field_dict["comp_in"] = comp_in
        if comp_out is not UNSET:
            field_dict["comp_out"] = comp_out
        if comp_rsp is not UNSET:
            field_dict["comp_rsp"] = comp_rsp
        if conn_rate is not UNSET:
            field_dict["conn_rate"] = conn_rate
        if conn_rate_max is not UNSET:
            field_dict["conn_rate_max"] = conn_rate_max
        if conn_tot is not UNSET:
            field_dict["conn_tot"] = conn_tot
        if cookie is not UNSET:
            field_dict["cookie"] = cookie
        if ctime is not UNSET:
            field_dict["ctime"] = ctime
        if dcon is not UNSET:
            field_dict["dcon"] = dcon
        if downtime is not UNSET:
            field_dict["downtime"] = downtime
        if dreq is not UNSET:
            field_dict["dreq"] = dreq
        if dresp is not UNSET:
            field_dict["dresp"] = dresp
        if dses is not UNSET:
            field_dict["dses"] = dses
        if econ is not UNSET:
            field_dict["econ"] = econ
        if ereq is not UNSET:
            field_dict["ereq"] = ereq
        if eresp is not UNSET:
            field_dict["eresp"] = eresp
        if hanafail is not UNSET:
            field_dict["hanafail"] = hanafail
        if hrsp_1xx is not UNSET:
            field_dict["hrsp_1xx"] = hrsp_1xx
        if hrsp_2xx is not UNSET:
            field_dict["hrsp_2xx"] = hrsp_2xx
        if hrsp_3xx is not UNSET:
            field_dict["hrsp_3xx"] = hrsp_3xx
        if hrsp_4xx is not UNSET:
            field_dict["hrsp_4xx"] = hrsp_4xx
        if hrsp_5xx is not UNSET:
            field_dict["hrsp_5xx"] = hrsp_5xx
        if hrsp_other is not UNSET:
            field_dict["hrsp_other"] = hrsp_other
        if iid is not UNSET:
            field_dict["iid"] = iid
        if intercepted is not UNSET:
            field_dict["intercepted"] = intercepted
        if last_agt is not UNSET:
            field_dict["last_agt"] = last_agt
        if last_chk is not UNSET:
            field_dict["last_chk"] = last_chk
        if lastchg is not UNSET:
            field_dict["lastchg"] = lastchg
        if lastsess is not UNSET:
            field_dict["lastsess"] = lastsess
        if lbtot is not UNSET:
            field_dict["lbtot"] = lbtot
        if mode is not UNSET:
            field_dict["mode"] = mode
        if pid is not UNSET:
            field_dict["pid"] = pid
        if qcur is not UNSET:
            field_dict["qcur"] = qcur
        if qlimit is not UNSET:
            field_dict["qlimit"] = qlimit
        if qmax is not UNSET:
            field_dict["qmax"] = qmax
        if qtime is not UNSET:
            field_dict["qtime"] = qtime
        if rate is not UNSET:
            field_dict["rate"] = rate
        if rate_lim is not UNSET:
            field_dict["rate_lim"] = rate_lim
        if rate_max is not UNSET:
            field_dict["rate_max"] = rate_max
        if req_rate is not UNSET:
            field_dict["req_rate"] = req_rate
        if req_rate_max is not UNSET:
            field_dict["req_rate_max"] = req_rate_max
        if req_tot is not UNSET:
            field_dict["req_tot"] = req_tot
        if rtime is not UNSET:
            field_dict["rtime"] = rtime
        if scur is not UNSET:
            field_dict["scur"] = scur
        if sid is not UNSET:
            field_dict["sid"] = sid
        if slim is not UNSET:
            field_dict["slim"] = slim
        if smax is not UNSET:
            field_dict["smax"] = smax
        if srv_abrt is not UNSET:
            field_dict["srv_abrt"] = srv_abrt
        if status is not UNSET:
            field_dict["status"] = status
        if stot is not UNSET:
            field_dict["stot"] = stot
        if throttle is not UNSET:
            field_dict["throttle"] = throttle
        if tracked is not UNSET:
            field_dict["tracked"] = tracked
        if ttime is not UNSET:
            field_dict["ttime"] = ttime
        if weight is not UNSET:
            field_dict["weight"] = weight
        if wredis is not UNSET:
            field_dict["wredis"] = wredis
        if wretr is not UNSET:
            field_dict["wretr"] = wretr

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_act(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        act = _parse_act(d.pop("act", UNSET))

        addr = d.pop("addr", UNSET)

        def _parse_agent_code(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        agent_code = _parse_agent_code(d.pop("agent_code", UNSET))

        agent_desc = d.pop("agent_desc", UNSET)

        def _parse_agent_duration(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        agent_duration = _parse_agent_duration(d.pop("agent_duration", UNSET))

        def _parse_agent_fall(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        agent_fall = _parse_agent_fall(d.pop("agent_fall", UNSET))

        def _parse_agent_health(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        agent_health = _parse_agent_health(d.pop("agent_health", UNSET))

        def _parse_agent_rise(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        agent_rise = _parse_agent_rise(d.pop("agent_rise", UNSET))

        _agent_status = d.pop("agent_status", UNSET)
        agent_status: Union[Unset, NativeStatStatsAgentStatus]
        if isinstance(_agent_status, Unset):
            agent_status = UNSET
        else:
            agent_status = NativeStatStatsAgentStatus(_agent_status)

        algo = d.pop("algo", UNSET)

        def _parse_bck(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        bck = _parse_bck(d.pop("bck", UNSET))

        def _parse_bin_(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        bin_ = _parse_bin_(d.pop("bin", UNSET))

        def _parse_bout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        bout = _parse_bout(d.pop("bout", UNSET))

        def _parse_check_code(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        check_code = _parse_check_code(d.pop("check_code", UNSET))

        check_desc = d.pop("check_desc", UNSET)

        def _parse_check_duration(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        check_duration = _parse_check_duration(d.pop("check_duration", UNSET))

        def _parse_check_fall(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        check_fall = _parse_check_fall(d.pop("check_fall", UNSET))

        def _parse_check_health(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        check_health = _parse_check_health(d.pop("check_health", UNSET))

        def _parse_check_rise(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        check_rise = _parse_check_rise(d.pop("check_rise", UNSET))

        _check_status = d.pop("check_status", UNSET)
        check_status: Union[Unset, NativeStatStatsCheckStatus]
        if isinstance(_check_status, Unset):
            check_status = UNSET
        else:
            check_status = NativeStatStatsCheckStatus(_check_status)

        def _parse_chkdown(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        chkdown = _parse_chkdown(d.pop("chkdown", UNSET))

        def _parse_chkfail(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        chkfail = _parse_chkfail(d.pop("chkfail", UNSET))

        def _parse_cli_abrt(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        cli_abrt = _parse_cli_abrt(d.pop("cli_abrt", UNSET))

        def _parse_comp_byp(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        comp_byp = _parse_comp_byp(d.pop("comp_byp", UNSET))

        def _parse_comp_in(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        comp_in = _parse_comp_in(d.pop("comp_in", UNSET))

        def _parse_comp_out(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        comp_out = _parse_comp_out(d.pop("comp_out", UNSET))

        def _parse_comp_rsp(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        comp_rsp = _parse_comp_rsp(d.pop("comp_rsp", UNSET))

        def _parse_conn_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        conn_rate = _parse_conn_rate(d.pop("conn_rate", UNSET))

        def _parse_conn_rate_max(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        conn_rate_max = _parse_conn_rate_max(d.pop("conn_rate_max", UNSET))

        def _parse_conn_tot(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        conn_tot = _parse_conn_tot(d.pop("conn_tot", UNSET))

        cookie = d.pop("cookie", UNSET)

        def _parse_ctime(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        ctime = _parse_ctime(d.pop("ctime", UNSET))

        def _parse_dcon(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        dcon = _parse_dcon(d.pop("dcon", UNSET))

        def _parse_downtime(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        downtime = _parse_downtime(d.pop("downtime", UNSET))

        def _parse_dreq(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        dreq = _parse_dreq(d.pop("dreq", UNSET))

        def _parse_dresp(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        dresp = _parse_dresp(d.pop("dresp", UNSET))

        def _parse_dses(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        dses = _parse_dses(d.pop("dses", UNSET))

        def _parse_econ(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        econ = _parse_econ(d.pop("econ", UNSET))

        def _parse_ereq(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        ereq = _parse_ereq(d.pop("ereq", UNSET))

        def _parse_eresp(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        eresp = _parse_eresp(d.pop("eresp", UNSET))

        hanafail = d.pop("hanafail", UNSET)

        def _parse_hrsp_1xx(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        hrsp_1xx = _parse_hrsp_1xx(d.pop("hrsp_1xx", UNSET))

        def _parse_hrsp_2xx(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        hrsp_2xx = _parse_hrsp_2xx(d.pop("hrsp_2xx", UNSET))

        def _parse_hrsp_3xx(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        hrsp_3xx = _parse_hrsp_3xx(d.pop("hrsp_3xx", UNSET))

        def _parse_hrsp_4xx(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        hrsp_4xx = _parse_hrsp_4xx(d.pop("hrsp_4xx", UNSET))

        def _parse_hrsp_5xx(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        hrsp_5xx = _parse_hrsp_5xx(d.pop("hrsp_5xx", UNSET))

        def _parse_hrsp_other(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        hrsp_other = _parse_hrsp_other(d.pop("hrsp_other", UNSET))

        def _parse_iid(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        iid = _parse_iid(d.pop("iid", UNSET))

        def _parse_intercepted(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        intercepted = _parse_intercepted(d.pop("intercepted", UNSET))

        def _parse_last_agt(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        last_agt = _parse_last_agt(d.pop("last_agt", UNSET))

        def _parse_last_chk(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        last_chk = _parse_last_chk(d.pop("last_chk", UNSET))

        def _parse_lastchg(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        lastchg = _parse_lastchg(d.pop("lastchg", UNSET))

        def _parse_lastsess(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        lastsess = _parse_lastsess(d.pop("lastsess", UNSET))

        def _parse_lbtot(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        lbtot = _parse_lbtot(d.pop("lbtot", UNSET))

        _mode = d.pop("mode", UNSET)
        mode: Union[Unset, NativeStatStatsMode]
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = NativeStatStatsMode(_mode)

        def _parse_pid(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        pid = _parse_pid(d.pop("pid", UNSET))

        def _parse_qcur(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        qcur = _parse_qcur(d.pop("qcur", UNSET))

        def _parse_qlimit(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        qlimit = _parse_qlimit(d.pop("qlimit", UNSET))

        def _parse_qmax(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        qmax = _parse_qmax(d.pop("qmax", UNSET))

        def _parse_qtime(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        qtime = _parse_qtime(d.pop("qtime", UNSET))

        def _parse_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        rate = _parse_rate(d.pop("rate", UNSET))

        def _parse_rate_lim(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        rate_lim = _parse_rate_lim(d.pop("rate_lim", UNSET))

        def _parse_rate_max(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        rate_max = _parse_rate_max(d.pop("rate_max", UNSET))

        def _parse_req_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        req_rate = _parse_req_rate(d.pop("req_rate", UNSET))

        def _parse_req_rate_max(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        req_rate_max = _parse_req_rate_max(d.pop("req_rate_max", UNSET))

        def _parse_req_tot(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        req_tot = _parse_req_tot(d.pop("req_tot", UNSET))

        def _parse_rtime(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        rtime = _parse_rtime(d.pop("rtime", UNSET))

        def _parse_scur(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        scur = _parse_scur(d.pop("scur", UNSET))

        def _parse_sid(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        sid = _parse_sid(d.pop("sid", UNSET))

        def _parse_slim(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        slim = _parse_slim(d.pop("slim", UNSET))

        def _parse_smax(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        smax = _parse_smax(d.pop("smax", UNSET))

        def _parse_srv_abrt(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        srv_abrt = _parse_srv_abrt(d.pop("srv_abrt", UNSET))

        _status = d.pop("status", UNSET)
        status: Union[Unset, NativeStatStatsStatus]
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = NativeStatStatsStatus(_status)

        def _parse_stot(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        stot = _parse_stot(d.pop("stot", UNSET))

        def _parse_throttle(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        throttle = _parse_throttle(d.pop("throttle", UNSET))

        tracked = d.pop("tracked", UNSET)

        def _parse_ttime(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        ttime = _parse_ttime(d.pop("ttime", UNSET))

        def _parse_weight(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        weight = _parse_weight(d.pop("weight", UNSET))

        def _parse_wredis(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        wredis = _parse_wredis(d.pop("wredis", UNSET))

        def _parse_wretr(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        wretr = _parse_wretr(d.pop("wretr", UNSET))

        native_stat_stats = cls(
            act=act,
            addr=addr,
            agent_code=agent_code,
            agent_desc=agent_desc,
            agent_duration=agent_duration,
            agent_fall=agent_fall,
            agent_health=agent_health,
            agent_rise=agent_rise,
            agent_status=agent_status,
            algo=algo,
            bck=bck,
            bin_=bin_,
            bout=bout,
            check_code=check_code,
            check_desc=check_desc,
            check_duration=check_duration,
            check_fall=check_fall,
            check_health=check_health,
            check_rise=check_rise,
            check_status=check_status,
            chkdown=chkdown,
            chkfail=chkfail,
            cli_abrt=cli_abrt,
            comp_byp=comp_byp,
            comp_in=comp_in,
            comp_out=comp_out,
            comp_rsp=comp_rsp,
            conn_rate=conn_rate,
            conn_rate_max=conn_rate_max,
            conn_tot=conn_tot,
            cookie=cookie,
            ctime=ctime,
            dcon=dcon,
            downtime=downtime,
            dreq=dreq,
            dresp=dresp,
            dses=dses,
            econ=econ,
            ereq=ereq,
            eresp=eresp,
            hanafail=hanafail,
            hrsp_1xx=hrsp_1xx,
            hrsp_2xx=hrsp_2xx,
            hrsp_3xx=hrsp_3xx,
            hrsp_4xx=hrsp_4xx,
            hrsp_5xx=hrsp_5xx,
            hrsp_other=hrsp_other,
            iid=iid,
            intercepted=intercepted,
            last_agt=last_agt,
            last_chk=last_chk,
            lastchg=lastchg,
            lastsess=lastsess,
            lbtot=lbtot,
            mode=mode,
            pid=pid,
            qcur=qcur,
            qlimit=qlimit,
            qmax=qmax,
            qtime=qtime,
            rate=rate,
            rate_lim=rate_lim,
            rate_max=rate_max,
            req_rate=req_rate,
            req_rate_max=req_rate_max,
            req_tot=req_tot,
            rtime=rtime,
            scur=scur,
            sid=sid,
            slim=slim,
            smax=smax,
            srv_abrt=srv_abrt,
            status=status,
            stot=stot,
            throttle=throttle,
            tracked=tracked,
            ttime=ttime,
            weight=weight,
            wredis=wredis,
            wretr=wretr,
        )

        native_stat_stats.additional_properties = d
        return native_stat_stats

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
