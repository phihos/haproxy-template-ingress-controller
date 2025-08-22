import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProcessInfoItem")


@_attrs_define
class ProcessInfoItem:
    """
    Attributes:
        active_peers (Union[None, Unset, int]):
        busy_polling (Union[None, Unset, int]):
        bytes_out_rate (Union[None, Unset, int]):
        compress_bps_in (Union[None, Unset, int]):
        compress_bps_out (Union[None, Unset, int]):
        compress_bps_rate_lim (Union[None, Unset, int]):
        conn_rate (Union[None, Unset, int]):
        conn_rate_limit (Union[None, Unset, int]):
        connected_peers (Union[None, Unset, int]):
        cum_conns (Union[None, Unset, int]):
        cum_req (Union[None, Unset, int]):
        cum_ssl_conns (Union[None, Unset, int]):
        curr_conns (Union[None, Unset, int]):
        curr_ssl_conns (Union[None, Unset, int]):
        dropped_logs (Union[None, Unset, int]):
        failed_resolutions (Union[None, Unset, int]):
        hard_max_conn (Union[None, Unset, int]):
        idle_pct (Union[None, Unset, int]):
        jobs (Union[None, Unset, int]):
        listeners (Union[None, Unset, int]):
        max_conn (Union[None, Unset, int]):
        max_conn_rate (Union[None, Unset, int]):
        max_pipes (Union[None, Unset, int]):
        max_sess_rate (Union[None, Unset, int]):
        max_sock (Union[None, Unset, int]):
        max_ssl_conns (Union[None, Unset, int]):
        max_ssl_rate (Union[None, Unset, int]):
        max_zlib_mem_usage (Union[None, Unset, int]):
        mem_max_mb (Union[None, Unset, int]):
        nbthread (Union[None, Unset, int]): Number of threads
        node (Union[Unset, str]):
        pid (Union[None, Unset, int]): Process id of the replying worker process
        pipes_free (Union[None, Unset, int]):
        pipes_used (Union[None, Unset, int]):
        pool_alloc_mb (Union[None, Unset, int]):
        pool_failed (Union[None, Unset, int]):
        pool_used_mb (Union[None, Unset, int]):
        process_num (Union[None, Unset, int]): Process number
        processes (Union[None, Unset, int]): Number of spawned processes
        release_date (Union[Unset, datetime.date]): HAProxy version release date
        run_queue (Union[None, Unset, int]):
        sess_rate (Union[None, Unset, int]):
        sess_rate_limit (Union[None, Unset, int]):
        ssl_backend_key_rate (Union[None, Unset, int]):
        ssl_backend_max_key_rate (Union[None, Unset, int]):
        ssl_cache_lookups (Union[None, Unset, int]):
        ssl_cache_misses (Union[None, Unset, int]):
        ssl_frontend_key_rate (Union[None, Unset, int]):
        ssl_frontend_max_key_rate (Union[None, Unset, int]):
        ssl_frontend_session_reuse (Union[None, Unset, int]):
        ssl_rate (Union[None, Unset, int]):
        ssl_rate_limit (Union[None, Unset, int]):
        stopping (Union[None, Unset, int]):
        tasks (Union[None, Unset, int]):
        total_bytes_out (Union[None, Unset, int]):
        ulimit_n (Union[None, Unset, int]):
        unstoppable (Union[None, Unset, int]):
        uptime (Union[None, Unset, int]): HAProxy uptime in s
        version (Union[Unset, str]): HAProxy version string
        zlib_mem_usage (Union[None, Unset, int]):
    """

    active_peers: Union[None, Unset, int] = UNSET
    busy_polling: Union[None, Unset, int] = UNSET
    bytes_out_rate: Union[None, Unset, int] = UNSET
    compress_bps_in: Union[None, Unset, int] = UNSET
    compress_bps_out: Union[None, Unset, int] = UNSET
    compress_bps_rate_lim: Union[None, Unset, int] = UNSET
    conn_rate: Union[None, Unset, int] = UNSET
    conn_rate_limit: Union[None, Unset, int] = UNSET
    connected_peers: Union[None, Unset, int] = UNSET
    cum_conns: Union[None, Unset, int] = UNSET
    cum_req: Union[None, Unset, int] = UNSET
    cum_ssl_conns: Union[None, Unset, int] = UNSET
    curr_conns: Union[None, Unset, int] = UNSET
    curr_ssl_conns: Union[None, Unset, int] = UNSET
    dropped_logs: Union[None, Unset, int] = UNSET
    failed_resolutions: Union[None, Unset, int] = UNSET
    hard_max_conn: Union[None, Unset, int] = UNSET
    idle_pct: Union[None, Unset, int] = UNSET
    jobs: Union[None, Unset, int] = UNSET
    listeners: Union[None, Unset, int] = UNSET
    max_conn: Union[None, Unset, int] = UNSET
    max_conn_rate: Union[None, Unset, int] = UNSET
    max_pipes: Union[None, Unset, int] = UNSET
    max_sess_rate: Union[None, Unset, int] = UNSET
    max_sock: Union[None, Unset, int] = UNSET
    max_ssl_conns: Union[None, Unset, int] = UNSET
    max_ssl_rate: Union[None, Unset, int] = UNSET
    max_zlib_mem_usage: Union[None, Unset, int] = UNSET
    mem_max_mb: Union[None, Unset, int] = UNSET
    nbthread: Union[None, Unset, int] = UNSET
    node: Union[Unset, str] = UNSET
    pid: Union[None, Unset, int] = UNSET
    pipes_free: Union[None, Unset, int] = UNSET
    pipes_used: Union[None, Unset, int] = UNSET
    pool_alloc_mb: Union[None, Unset, int] = UNSET
    pool_failed: Union[None, Unset, int] = UNSET
    pool_used_mb: Union[None, Unset, int] = UNSET
    process_num: Union[None, Unset, int] = UNSET
    processes: Union[None, Unset, int] = UNSET
    release_date: Union[Unset, datetime.date] = UNSET
    run_queue: Union[None, Unset, int] = UNSET
    sess_rate: Union[None, Unset, int] = UNSET
    sess_rate_limit: Union[None, Unset, int] = UNSET
    ssl_backend_key_rate: Union[None, Unset, int] = UNSET
    ssl_backend_max_key_rate: Union[None, Unset, int] = UNSET
    ssl_cache_lookups: Union[None, Unset, int] = UNSET
    ssl_cache_misses: Union[None, Unset, int] = UNSET
    ssl_frontend_key_rate: Union[None, Unset, int] = UNSET
    ssl_frontend_max_key_rate: Union[None, Unset, int] = UNSET
    ssl_frontend_session_reuse: Union[None, Unset, int] = UNSET
    ssl_rate: Union[None, Unset, int] = UNSET
    ssl_rate_limit: Union[None, Unset, int] = UNSET
    stopping: Union[None, Unset, int] = UNSET
    tasks: Union[None, Unset, int] = UNSET
    total_bytes_out: Union[None, Unset, int] = UNSET
    ulimit_n: Union[None, Unset, int] = UNSET
    unstoppable: Union[None, Unset, int] = UNSET
    uptime: Union[None, Unset, int] = UNSET
    version: Union[Unset, str] = UNSET
    zlib_mem_usage: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        active_peers: Union[None, Unset, int]
        if isinstance(self.active_peers, Unset):
            active_peers = UNSET
        else:
            active_peers = self.active_peers

        busy_polling: Union[None, Unset, int]
        if isinstance(self.busy_polling, Unset):
            busy_polling = UNSET
        else:
            busy_polling = self.busy_polling

        bytes_out_rate: Union[None, Unset, int]
        if isinstance(self.bytes_out_rate, Unset):
            bytes_out_rate = UNSET
        else:
            bytes_out_rate = self.bytes_out_rate

        compress_bps_in: Union[None, Unset, int]
        if isinstance(self.compress_bps_in, Unset):
            compress_bps_in = UNSET
        else:
            compress_bps_in = self.compress_bps_in

        compress_bps_out: Union[None, Unset, int]
        if isinstance(self.compress_bps_out, Unset):
            compress_bps_out = UNSET
        else:
            compress_bps_out = self.compress_bps_out

        compress_bps_rate_lim: Union[None, Unset, int]
        if isinstance(self.compress_bps_rate_lim, Unset):
            compress_bps_rate_lim = UNSET
        else:
            compress_bps_rate_lim = self.compress_bps_rate_lim

        conn_rate: Union[None, Unset, int]
        if isinstance(self.conn_rate, Unset):
            conn_rate = UNSET
        else:
            conn_rate = self.conn_rate

        conn_rate_limit: Union[None, Unset, int]
        if isinstance(self.conn_rate_limit, Unset):
            conn_rate_limit = UNSET
        else:
            conn_rate_limit = self.conn_rate_limit

        connected_peers: Union[None, Unset, int]
        if isinstance(self.connected_peers, Unset):
            connected_peers = UNSET
        else:
            connected_peers = self.connected_peers

        cum_conns: Union[None, Unset, int]
        if isinstance(self.cum_conns, Unset):
            cum_conns = UNSET
        else:
            cum_conns = self.cum_conns

        cum_req: Union[None, Unset, int]
        if isinstance(self.cum_req, Unset):
            cum_req = UNSET
        else:
            cum_req = self.cum_req

        cum_ssl_conns: Union[None, Unset, int]
        if isinstance(self.cum_ssl_conns, Unset):
            cum_ssl_conns = UNSET
        else:
            cum_ssl_conns = self.cum_ssl_conns

        curr_conns: Union[None, Unset, int]
        if isinstance(self.curr_conns, Unset):
            curr_conns = UNSET
        else:
            curr_conns = self.curr_conns

        curr_ssl_conns: Union[None, Unset, int]
        if isinstance(self.curr_ssl_conns, Unset):
            curr_ssl_conns = UNSET
        else:
            curr_ssl_conns = self.curr_ssl_conns

        dropped_logs: Union[None, Unset, int]
        if isinstance(self.dropped_logs, Unset):
            dropped_logs = UNSET
        else:
            dropped_logs = self.dropped_logs

        failed_resolutions: Union[None, Unset, int]
        if isinstance(self.failed_resolutions, Unset):
            failed_resolutions = UNSET
        else:
            failed_resolutions = self.failed_resolutions

        hard_max_conn: Union[None, Unset, int]
        if isinstance(self.hard_max_conn, Unset):
            hard_max_conn = UNSET
        else:
            hard_max_conn = self.hard_max_conn

        idle_pct: Union[None, Unset, int]
        if isinstance(self.idle_pct, Unset):
            idle_pct = UNSET
        else:
            idle_pct = self.idle_pct

        jobs: Union[None, Unset, int]
        if isinstance(self.jobs, Unset):
            jobs = UNSET
        else:
            jobs = self.jobs

        listeners: Union[None, Unset, int]
        if isinstance(self.listeners, Unset):
            listeners = UNSET
        else:
            listeners = self.listeners

        max_conn: Union[None, Unset, int]
        if isinstance(self.max_conn, Unset):
            max_conn = UNSET
        else:
            max_conn = self.max_conn

        max_conn_rate: Union[None, Unset, int]
        if isinstance(self.max_conn_rate, Unset):
            max_conn_rate = UNSET
        else:
            max_conn_rate = self.max_conn_rate

        max_pipes: Union[None, Unset, int]
        if isinstance(self.max_pipes, Unset):
            max_pipes = UNSET
        else:
            max_pipes = self.max_pipes

        max_sess_rate: Union[None, Unset, int]
        if isinstance(self.max_sess_rate, Unset):
            max_sess_rate = UNSET
        else:
            max_sess_rate = self.max_sess_rate

        max_sock: Union[None, Unset, int]
        if isinstance(self.max_sock, Unset):
            max_sock = UNSET
        else:
            max_sock = self.max_sock

        max_ssl_conns: Union[None, Unset, int]
        if isinstance(self.max_ssl_conns, Unset):
            max_ssl_conns = UNSET
        else:
            max_ssl_conns = self.max_ssl_conns

        max_ssl_rate: Union[None, Unset, int]
        if isinstance(self.max_ssl_rate, Unset):
            max_ssl_rate = UNSET
        else:
            max_ssl_rate = self.max_ssl_rate

        max_zlib_mem_usage: Union[None, Unset, int]
        if isinstance(self.max_zlib_mem_usage, Unset):
            max_zlib_mem_usage = UNSET
        else:
            max_zlib_mem_usage = self.max_zlib_mem_usage

        mem_max_mb: Union[None, Unset, int]
        if isinstance(self.mem_max_mb, Unset):
            mem_max_mb = UNSET
        else:
            mem_max_mb = self.mem_max_mb

        nbthread: Union[None, Unset, int]
        if isinstance(self.nbthread, Unset):
            nbthread = UNSET
        else:
            nbthread = self.nbthread

        node = self.node

        pid: Union[None, Unset, int]
        if isinstance(self.pid, Unset):
            pid = UNSET
        else:
            pid = self.pid

        pipes_free: Union[None, Unset, int]
        if isinstance(self.pipes_free, Unset):
            pipes_free = UNSET
        else:
            pipes_free = self.pipes_free

        pipes_used: Union[None, Unset, int]
        if isinstance(self.pipes_used, Unset):
            pipes_used = UNSET
        else:
            pipes_used = self.pipes_used

        pool_alloc_mb: Union[None, Unset, int]
        if isinstance(self.pool_alloc_mb, Unset):
            pool_alloc_mb = UNSET
        else:
            pool_alloc_mb = self.pool_alloc_mb

        pool_failed: Union[None, Unset, int]
        if isinstance(self.pool_failed, Unset):
            pool_failed = UNSET
        else:
            pool_failed = self.pool_failed

        pool_used_mb: Union[None, Unset, int]
        if isinstance(self.pool_used_mb, Unset):
            pool_used_mb = UNSET
        else:
            pool_used_mb = self.pool_used_mb

        process_num: Union[None, Unset, int]
        if isinstance(self.process_num, Unset):
            process_num = UNSET
        else:
            process_num = self.process_num

        processes: Union[None, Unset, int]
        if isinstance(self.processes, Unset):
            processes = UNSET
        else:
            processes = self.processes

        release_date: Union[Unset, str] = UNSET
        if not isinstance(self.release_date, Unset):
            release_date = self.release_date.isoformat()

        run_queue: Union[None, Unset, int]
        if isinstance(self.run_queue, Unset):
            run_queue = UNSET
        else:
            run_queue = self.run_queue

        sess_rate: Union[None, Unset, int]
        if isinstance(self.sess_rate, Unset):
            sess_rate = UNSET
        else:
            sess_rate = self.sess_rate

        sess_rate_limit: Union[None, Unset, int]
        if isinstance(self.sess_rate_limit, Unset):
            sess_rate_limit = UNSET
        else:
            sess_rate_limit = self.sess_rate_limit

        ssl_backend_key_rate: Union[None, Unset, int]
        if isinstance(self.ssl_backend_key_rate, Unset):
            ssl_backend_key_rate = UNSET
        else:
            ssl_backend_key_rate = self.ssl_backend_key_rate

        ssl_backend_max_key_rate: Union[None, Unset, int]
        if isinstance(self.ssl_backend_max_key_rate, Unset):
            ssl_backend_max_key_rate = UNSET
        else:
            ssl_backend_max_key_rate = self.ssl_backend_max_key_rate

        ssl_cache_lookups: Union[None, Unset, int]
        if isinstance(self.ssl_cache_lookups, Unset):
            ssl_cache_lookups = UNSET
        else:
            ssl_cache_lookups = self.ssl_cache_lookups

        ssl_cache_misses: Union[None, Unset, int]
        if isinstance(self.ssl_cache_misses, Unset):
            ssl_cache_misses = UNSET
        else:
            ssl_cache_misses = self.ssl_cache_misses

        ssl_frontend_key_rate: Union[None, Unset, int]
        if isinstance(self.ssl_frontend_key_rate, Unset):
            ssl_frontend_key_rate = UNSET
        else:
            ssl_frontend_key_rate = self.ssl_frontend_key_rate

        ssl_frontend_max_key_rate: Union[None, Unset, int]
        if isinstance(self.ssl_frontend_max_key_rate, Unset):
            ssl_frontend_max_key_rate = UNSET
        else:
            ssl_frontend_max_key_rate = self.ssl_frontend_max_key_rate

        ssl_frontend_session_reuse: Union[None, Unset, int]
        if isinstance(self.ssl_frontend_session_reuse, Unset):
            ssl_frontend_session_reuse = UNSET
        else:
            ssl_frontend_session_reuse = self.ssl_frontend_session_reuse

        ssl_rate: Union[None, Unset, int]
        if isinstance(self.ssl_rate, Unset):
            ssl_rate = UNSET
        else:
            ssl_rate = self.ssl_rate

        ssl_rate_limit: Union[None, Unset, int]
        if isinstance(self.ssl_rate_limit, Unset):
            ssl_rate_limit = UNSET
        else:
            ssl_rate_limit = self.ssl_rate_limit

        stopping: Union[None, Unset, int]
        if isinstance(self.stopping, Unset):
            stopping = UNSET
        else:
            stopping = self.stopping

        tasks: Union[None, Unset, int]
        if isinstance(self.tasks, Unset):
            tasks = UNSET
        else:
            tasks = self.tasks

        total_bytes_out: Union[None, Unset, int]
        if isinstance(self.total_bytes_out, Unset):
            total_bytes_out = UNSET
        else:
            total_bytes_out = self.total_bytes_out

        ulimit_n: Union[None, Unset, int]
        if isinstance(self.ulimit_n, Unset):
            ulimit_n = UNSET
        else:
            ulimit_n = self.ulimit_n

        unstoppable: Union[None, Unset, int]
        if isinstance(self.unstoppable, Unset):
            unstoppable = UNSET
        else:
            unstoppable = self.unstoppable

        uptime: Union[None, Unset, int]
        if isinstance(self.uptime, Unset):
            uptime = UNSET
        else:
            uptime = self.uptime

        version = self.version

        zlib_mem_usage: Union[None, Unset, int]
        if isinstance(self.zlib_mem_usage, Unset):
            zlib_mem_usage = UNSET
        else:
            zlib_mem_usage = self.zlib_mem_usage

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if active_peers is not UNSET:
            field_dict["active_peers"] = active_peers
        if busy_polling is not UNSET:
            field_dict["busy_polling"] = busy_polling
        if bytes_out_rate is not UNSET:
            field_dict["bytes_out_rate"] = bytes_out_rate
        if compress_bps_in is not UNSET:
            field_dict["compress_bps_in"] = compress_bps_in
        if compress_bps_out is not UNSET:
            field_dict["compress_bps_out"] = compress_bps_out
        if compress_bps_rate_lim is not UNSET:
            field_dict["compress_bps_rate_lim"] = compress_bps_rate_lim
        if conn_rate is not UNSET:
            field_dict["conn_rate"] = conn_rate
        if conn_rate_limit is not UNSET:
            field_dict["conn_rate_limit"] = conn_rate_limit
        if connected_peers is not UNSET:
            field_dict["connected_peers"] = connected_peers
        if cum_conns is not UNSET:
            field_dict["cum_conns"] = cum_conns
        if cum_req is not UNSET:
            field_dict["cum_req"] = cum_req
        if cum_ssl_conns is not UNSET:
            field_dict["cum_ssl_conns"] = cum_ssl_conns
        if curr_conns is not UNSET:
            field_dict["curr_conns"] = curr_conns
        if curr_ssl_conns is not UNSET:
            field_dict["curr_ssl_conns"] = curr_ssl_conns
        if dropped_logs is not UNSET:
            field_dict["dropped_logs"] = dropped_logs
        if failed_resolutions is not UNSET:
            field_dict["failed_resolutions"] = failed_resolutions
        if hard_max_conn is not UNSET:
            field_dict["hard_max_conn"] = hard_max_conn
        if idle_pct is not UNSET:
            field_dict["idle_pct"] = idle_pct
        if jobs is not UNSET:
            field_dict["jobs"] = jobs
        if listeners is not UNSET:
            field_dict["listeners"] = listeners
        if max_conn is not UNSET:
            field_dict["max_conn"] = max_conn
        if max_conn_rate is not UNSET:
            field_dict["max_conn_rate"] = max_conn_rate
        if max_pipes is not UNSET:
            field_dict["max_pipes"] = max_pipes
        if max_sess_rate is not UNSET:
            field_dict["max_sess_rate"] = max_sess_rate
        if max_sock is not UNSET:
            field_dict["max_sock"] = max_sock
        if max_ssl_conns is not UNSET:
            field_dict["max_ssl_conns"] = max_ssl_conns
        if max_ssl_rate is not UNSET:
            field_dict["max_ssl_rate"] = max_ssl_rate
        if max_zlib_mem_usage is not UNSET:
            field_dict["max_zlib_mem_usage"] = max_zlib_mem_usage
        if mem_max_mb is not UNSET:
            field_dict["mem_max_mb"] = mem_max_mb
        if nbthread is not UNSET:
            field_dict["nbthread"] = nbthread
        if node is not UNSET:
            field_dict["node"] = node
        if pid is not UNSET:
            field_dict["pid"] = pid
        if pipes_free is not UNSET:
            field_dict["pipes_free"] = pipes_free
        if pipes_used is not UNSET:
            field_dict["pipes_used"] = pipes_used
        if pool_alloc_mb is not UNSET:
            field_dict["pool_alloc_mb"] = pool_alloc_mb
        if pool_failed is not UNSET:
            field_dict["pool_failed"] = pool_failed
        if pool_used_mb is not UNSET:
            field_dict["pool_used_mb"] = pool_used_mb
        if process_num is not UNSET:
            field_dict["process_num"] = process_num
        if processes is not UNSET:
            field_dict["processes"] = processes
        if release_date is not UNSET:
            field_dict["release_date"] = release_date
        if run_queue is not UNSET:
            field_dict["run_queue"] = run_queue
        if sess_rate is not UNSET:
            field_dict["sess_rate"] = sess_rate
        if sess_rate_limit is not UNSET:
            field_dict["sess_rate_limit"] = sess_rate_limit
        if ssl_backend_key_rate is not UNSET:
            field_dict["ssl_backend_key_rate"] = ssl_backend_key_rate
        if ssl_backend_max_key_rate is not UNSET:
            field_dict["ssl_backend_max_key_rate"] = ssl_backend_max_key_rate
        if ssl_cache_lookups is not UNSET:
            field_dict["ssl_cache_lookups"] = ssl_cache_lookups
        if ssl_cache_misses is not UNSET:
            field_dict["ssl_cache_misses"] = ssl_cache_misses
        if ssl_frontend_key_rate is not UNSET:
            field_dict["ssl_frontend_key_rate"] = ssl_frontend_key_rate
        if ssl_frontend_max_key_rate is not UNSET:
            field_dict["ssl_frontend_max_key_rate"] = ssl_frontend_max_key_rate
        if ssl_frontend_session_reuse is not UNSET:
            field_dict["ssl_frontend_session_reuse"] = ssl_frontend_session_reuse
        if ssl_rate is not UNSET:
            field_dict["ssl_rate"] = ssl_rate
        if ssl_rate_limit is not UNSET:
            field_dict["ssl_rate_limit"] = ssl_rate_limit
        if stopping is not UNSET:
            field_dict["stopping"] = stopping
        if tasks is not UNSET:
            field_dict["tasks"] = tasks
        if total_bytes_out is not UNSET:
            field_dict["total_bytes_out"] = total_bytes_out
        if ulimit_n is not UNSET:
            field_dict["ulimit_n"] = ulimit_n
        if unstoppable is not UNSET:
            field_dict["unstoppable"] = unstoppable
        if uptime is not UNSET:
            field_dict["uptime"] = uptime
        if version is not UNSET:
            field_dict["version"] = version
        if zlib_mem_usage is not UNSET:
            field_dict["zlib_mem_usage"] = zlib_mem_usage

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_active_peers(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        active_peers = _parse_active_peers(d.pop("active_peers", UNSET))

        def _parse_busy_polling(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        busy_polling = _parse_busy_polling(d.pop("busy_polling", UNSET))

        def _parse_bytes_out_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        bytes_out_rate = _parse_bytes_out_rate(d.pop("bytes_out_rate", UNSET))

        def _parse_compress_bps_in(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        compress_bps_in = _parse_compress_bps_in(d.pop("compress_bps_in", UNSET))

        def _parse_compress_bps_out(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        compress_bps_out = _parse_compress_bps_out(d.pop("compress_bps_out", UNSET))

        def _parse_compress_bps_rate_lim(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        compress_bps_rate_lim = _parse_compress_bps_rate_lim(d.pop("compress_bps_rate_lim", UNSET))

        def _parse_conn_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        conn_rate = _parse_conn_rate(d.pop("conn_rate", UNSET))

        def _parse_conn_rate_limit(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        conn_rate_limit = _parse_conn_rate_limit(d.pop("conn_rate_limit", UNSET))

        def _parse_connected_peers(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        connected_peers = _parse_connected_peers(d.pop("connected_peers", UNSET))

        def _parse_cum_conns(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        cum_conns = _parse_cum_conns(d.pop("cum_conns", UNSET))

        def _parse_cum_req(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        cum_req = _parse_cum_req(d.pop("cum_req", UNSET))

        def _parse_cum_ssl_conns(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        cum_ssl_conns = _parse_cum_ssl_conns(d.pop("cum_ssl_conns", UNSET))

        def _parse_curr_conns(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        curr_conns = _parse_curr_conns(d.pop("curr_conns", UNSET))

        def _parse_curr_ssl_conns(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        curr_ssl_conns = _parse_curr_ssl_conns(d.pop("curr_ssl_conns", UNSET))

        def _parse_dropped_logs(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        dropped_logs = _parse_dropped_logs(d.pop("dropped_logs", UNSET))

        def _parse_failed_resolutions(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        failed_resolutions = _parse_failed_resolutions(d.pop("failed_resolutions", UNSET))

        def _parse_hard_max_conn(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        hard_max_conn = _parse_hard_max_conn(d.pop("hard_max_conn", UNSET))

        def _parse_idle_pct(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        idle_pct = _parse_idle_pct(d.pop("idle_pct", UNSET))

        def _parse_jobs(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        jobs = _parse_jobs(d.pop("jobs", UNSET))

        def _parse_listeners(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        listeners = _parse_listeners(d.pop("listeners", UNSET))

        def _parse_max_conn(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_conn = _parse_max_conn(d.pop("max_conn", UNSET))

        def _parse_max_conn_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_conn_rate = _parse_max_conn_rate(d.pop("max_conn_rate", UNSET))

        def _parse_max_pipes(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_pipes = _parse_max_pipes(d.pop("max_pipes", UNSET))

        def _parse_max_sess_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_sess_rate = _parse_max_sess_rate(d.pop("max_sess_rate", UNSET))

        def _parse_max_sock(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_sock = _parse_max_sock(d.pop("max_sock", UNSET))

        def _parse_max_ssl_conns(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_ssl_conns = _parse_max_ssl_conns(d.pop("max_ssl_conns", UNSET))

        def _parse_max_ssl_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_ssl_rate = _parse_max_ssl_rate(d.pop("max_ssl_rate", UNSET))

        def _parse_max_zlib_mem_usage(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_zlib_mem_usage = _parse_max_zlib_mem_usage(d.pop("max_zlib_mem_usage", UNSET))

        def _parse_mem_max_mb(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        mem_max_mb = _parse_mem_max_mb(d.pop("mem_max_mb", UNSET))

        def _parse_nbthread(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        nbthread = _parse_nbthread(d.pop("nbthread", UNSET))

        node = d.pop("node", UNSET)

        def _parse_pid(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        pid = _parse_pid(d.pop("pid", UNSET))

        def _parse_pipes_free(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        pipes_free = _parse_pipes_free(d.pop("pipes_free", UNSET))

        def _parse_pipes_used(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        pipes_used = _parse_pipes_used(d.pop("pipes_used", UNSET))

        def _parse_pool_alloc_mb(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        pool_alloc_mb = _parse_pool_alloc_mb(d.pop("pool_alloc_mb", UNSET))

        def _parse_pool_failed(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        pool_failed = _parse_pool_failed(d.pop("pool_failed", UNSET))

        def _parse_pool_used_mb(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        pool_used_mb = _parse_pool_used_mb(d.pop("pool_used_mb", UNSET))

        def _parse_process_num(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        process_num = _parse_process_num(d.pop("process_num", UNSET))

        def _parse_processes(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        processes = _parse_processes(d.pop("processes", UNSET))

        _release_date = d.pop("release_date", UNSET)
        release_date: Union[Unset, datetime.date]
        if isinstance(_release_date, Unset):
            release_date = UNSET
        else:
            release_date = isoparse(_release_date).date()

        def _parse_run_queue(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        run_queue = _parse_run_queue(d.pop("run_queue", UNSET))

        def _parse_sess_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        sess_rate = _parse_sess_rate(d.pop("sess_rate", UNSET))

        def _parse_sess_rate_limit(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        sess_rate_limit = _parse_sess_rate_limit(d.pop("sess_rate_limit", UNSET))

        def _parse_ssl_backend_key_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        ssl_backend_key_rate = _parse_ssl_backend_key_rate(d.pop("ssl_backend_key_rate", UNSET))

        def _parse_ssl_backend_max_key_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        ssl_backend_max_key_rate = _parse_ssl_backend_max_key_rate(d.pop("ssl_backend_max_key_rate", UNSET))

        def _parse_ssl_cache_lookups(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        ssl_cache_lookups = _parse_ssl_cache_lookups(d.pop("ssl_cache_lookups", UNSET))

        def _parse_ssl_cache_misses(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        ssl_cache_misses = _parse_ssl_cache_misses(d.pop("ssl_cache_misses", UNSET))

        def _parse_ssl_frontend_key_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        ssl_frontend_key_rate = _parse_ssl_frontend_key_rate(d.pop("ssl_frontend_key_rate", UNSET))

        def _parse_ssl_frontend_max_key_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        ssl_frontend_max_key_rate = _parse_ssl_frontend_max_key_rate(d.pop("ssl_frontend_max_key_rate", UNSET))

        def _parse_ssl_frontend_session_reuse(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        ssl_frontend_session_reuse = _parse_ssl_frontend_session_reuse(d.pop("ssl_frontend_session_reuse", UNSET))

        def _parse_ssl_rate(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        ssl_rate = _parse_ssl_rate(d.pop("ssl_rate", UNSET))

        def _parse_ssl_rate_limit(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        ssl_rate_limit = _parse_ssl_rate_limit(d.pop("ssl_rate_limit", UNSET))

        def _parse_stopping(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        stopping = _parse_stopping(d.pop("stopping", UNSET))

        def _parse_tasks(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        tasks = _parse_tasks(d.pop("tasks", UNSET))

        def _parse_total_bytes_out(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        total_bytes_out = _parse_total_bytes_out(d.pop("total_bytes_out", UNSET))

        def _parse_ulimit_n(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        ulimit_n = _parse_ulimit_n(d.pop("ulimit_n", UNSET))

        def _parse_unstoppable(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        unstoppable = _parse_unstoppable(d.pop("unstoppable", UNSET))

        def _parse_uptime(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        uptime = _parse_uptime(d.pop("uptime", UNSET))

        version = d.pop("version", UNSET)

        def _parse_zlib_mem_usage(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        zlib_mem_usage = _parse_zlib_mem_usage(d.pop("zlib_mem_usage", UNSET))

        process_info_item = cls(
            active_peers=active_peers,
            busy_polling=busy_polling,
            bytes_out_rate=bytes_out_rate,
            compress_bps_in=compress_bps_in,
            compress_bps_out=compress_bps_out,
            compress_bps_rate_lim=compress_bps_rate_lim,
            conn_rate=conn_rate,
            conn_rate_limit=conn_rate_limit,
            connected_peers=connected_peers,
            cum_conns=cum_conns,
            cum_req=cum_req,
            cum_ssl_conns=cum_ssl_conns,
            curr_conns=curr_conns,
            curr_ssl_conns=curr_ssl_conns,
            dropped_logs=dropped_logs,
            failed_resolutions=failed_resolutions,
            hard_max_conn=hard_max_conn,
            idle_pct=idle_pct,
            jobs=jobs,
            listeners=listeners,
            max_conn=max_conn,
            max_conn_rate=max_conn_rate,
            max_pipes=max_pipes,
            max_sess_rate=max_sess_rate,
            max_sock=max_sock,
            max_ssl_conns=max_ssl_conns,
            max_ssl_rate=max_ssl_rate,
            max_zlib_mem_usage=max_zlib_mem_usage,
            mem_max_mb=mem_max_mb,
            nbthread=nbthread,
            node=node,
            pid=pid,
            pipes_free=pipes_free,
            pipes_used=pipes_used,
            pool_alloc_mb=pool_alloc_mb,
            pool_failed=pool_failed,
            pool_used_mb=pool_used_mb,
            process_num=process_num,
            processes=processes,
            release_date=release_date,
            run_queue=run_queue,
            sess_rate=sess_rate,
            sess_rate_limit=sess_rate_limit,
            ssl_backend_key_rate=ssl_backend_key_rate,
            ssl_backend_max_key_rate=ssl_backend_max_key_rate,
            ssl_cache_lookups=ssl_cache_lookups,
            ssl_cache_misses=ssl_cache_misses,
            ssl_frontend_key_rate=ssl_frontend_key_rate,
            ssl_frontend_max_key_rate=ssl_frontend_max_key_rate,
            ssl_frontend_session_reuse=ssl_frontend_session_reuse,
            ssl_rate=ssl_rate,
            ssl_rate_limit=ssl_rate_limit,
            stopping=stopping,
            tasks=tasks,
            total_bytes_out=total_bytes_out,
            ulimit_n=ulimit_n,
            unstoppable=unstoppable,
            uptime=uptime,
            version=version,
            zlib_mem_usage=zlib_mem_usage,
        )

        process_info_item.additional_properties = d
        return process_info_item

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
