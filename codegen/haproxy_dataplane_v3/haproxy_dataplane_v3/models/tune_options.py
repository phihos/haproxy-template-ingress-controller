from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.tune_options_applet_zero_copy_forwarding import TuneOptionsAppletZeroCopyForwarding
from ..models.tune_options_epoll_mask_events_item import TuneOptionsEpollMaskEventsItem
from ..models.tune_options_fd_edge_triggered import TuneOptionsFdEdgeTriggered
from ..models.tune_options_h1_zero_copy_fwd_recv import TuneOptionsH1ZeroCopyFwdRecv
from ..models.tune_options_h1_zero_copy_fwd_send import TuneOptionsH1ZeroCopyFwdSend
from ..models.tune_options_h2_zero_copy_fwd_send import TuneOptionsH2ZeroCopyFwdSend
from ..models.tune_options_idle_pool_shared import TuneOptionsIdlePoolShared
from ..models.tune_options_listener_default_shards import TuneOptionsListenerDefaultShards
from ..models.tune_options_listener_multi_queue import TuneOptionsListenerMultiQueue
from ..models.tune_options_pt_zero_copy_forwarding import TuneOptionsPtZeroCopyForwarding
from ..models.tune_options_sched_low_latency import TuneOptionsSchedLowLatency
from ..models.tune_options_takeover_other_tg_connections import TuneOptionsTakeoverOtherTgConnections
from ..types import UNSET, Unset

T = TypeVar("T", bound="TuneOptions")


@_attrs_define
class TuneOptions:
    """
    Attributes:
        applet_zero_copy_forwarding (Union[Unset, TuneOptionsAppletZeroCopyForwarding]):
        comp_maxlevel (Union[Unset, int]):
        disable_fast_forward (Union[Unset, bool]):
        disable_zero_copy_forwarding (Union[Unset, bool]):
        epoll_mask_events (Union[Unset, list[TuneOptionsEpollMaskEventsItem]]):
        events_max_events_at_once (Union[Unset, int]):
        fail_alloc (Union[Unset, bool]):
        fd_edge_triggered (Union[Unset, TuneOptionsFdEdgeTriggered]):
        glitches_kill_cpu_usage (Union[None, Unset, int]):
        h1_zero_copy_fwd_recv (Union[Unset, TuneOptionsH1ZeroCopyFwdRecv]):
        h1_zero_copy_fwd_send (Union[Unset, TuneOptionsH1ZeroCopyFwdSend]):
        h2_be_glitches_threshold (Union[None, Unset, int]):
        h2_be_initial_window_size (Union[Unset, int]):
        h2_be_max_concurrent_streams (Union[Unset, int]):
        h2_be_rxbuf (Union[None, Unset, int]):
        h2_fe_glitches_threshold (Union[None, Unset, int]):
        h2_fe_initial_window_size (Union[Unset, int]):
        h2_fe_max_concurrent_streams (Union[Unset, int]):
        h2_fe_max_total_streams (Union[None, Unset, int]):
        h2_fe_rxbuf (Union[None, Unset, int]):
        h2_header_table_size (Union[Unset, int]):
        h2_initial_window_size (Union[None, Unset, int]):
        h2_max_concurrent_streams (Union[Unset, int]):
        h2_max_frame_size (Union[Unset, int]):
        h2_zero_copy_fwd_send (Union[Unset, TuneOptionsH2ZeroCopyFwdSend]):
        http_cookielen (Union[Unset, int]):
        http_logurilen (Union[Unset, int]):
        http_maxhdr (Union[Unset, int]):
        idle_pool_shared (Union[Unset, TuneOptionsIdlePoolShared]):
        idletimer (Union[None, Unset, int]):
        listener_default_shards (Union[Unset, TuneOptionsListenerDefaultShards]):
        listener_multi_queue (Union[Unset, TuneOptionsListenerMultiQueue]):
        max_checks_per_thread (Union[None, Unset, int]):
        max_rules_at_once (Union[None, Unset, int]):
        maxaccept (Union[Unset, int]):
        maxpollevents (Union[Unset, int]):
        maxrewrite (Union[Unset, int]):
        memory_hot_size (Union[None, Unset, int]):
        notsent_lowat_client (Union[None, Unset, int]):
        notsent_lowat_server (Union[None, Unset, int]):
        pattern_cache_size (Union[None, Unset, int]):
        peers_max_updates_at_once (Union[Unset, int]):
        pool_high_fd_ratio (Union[Unset, int]):
        pool_low_fd_ratio (Union[Unset, int]):
        pt_zero_copy_forwarding (Union[Unset, TuneOptionsPtZeroCopyForwarding]):
        renice_runtime (Union[None, Unset, int]):
        renice_startup (Union[None, Unset, int]):
        ring_queues (Union[None, Unset, int]):
        runqueue_depth (Union[Unset, int]):
        sched_low_latency (Union[Unset, TuneOptionsSchedLowLatency]):
        stick_counters (Union[None, Unset, int]):
        takeover_other_tg_connections (Union[Unset, TuneOptionsTakeoverOtherTgConnections]):
    """

    applet_zero_copy_forwarding: Union[Unset, TuneOptionsAppletZeroCopyForwarding] = UNSET
    comp_maxlevel: Union[Unset, int] = UNSET
    disable_fast_forward: Union[Unset, bool] = UNSET
    disable_zero_copy_forwarding: Union[Unset, bool] = UNSET
    epoll_mask_events: Union[Unset, list[TuneOptionsEpollMaskEventsItem]] = UNSET
    events_max_events_at_once: Union[Unset, int] = UNSET
    fail_alloc: Union[Unset, bool] = UNSET
    fd_edge_triggered: Union[Unset, TuneOptionsFdEdgeTriggered] = UNSET
    glitches_kill_cpu_usage: Union[None, Unset, int] = UNSET
    h1_zero_copy_fwd_recv: Union[Unset, TuneOptionsH1ZeroCopyFwdRecv] = UNSET
    h1_zero_copy_fwd_send: Union[Unset, TuneOptionsH1ZeroCopyFwdSend] = UNSET
    h2_be_glitches_threshold: Union[None, Unset, int] = UNSET
    h2_be_initial_window_size: Union[Unset, int] = UNSET
    h2_be_max_concurrent_streams: Union[Unset, int] = UNSET
    h2_be_rxbuf: Union[None, Unset, int] = UNSET
    h2_fe_glitches_threshold: Union[None, Unset, int] = UNSET
    h2_fe_initial_window_size: Union[Unset, int] = UNSET
    h2_fe_max_concurrent_streams: Union[Unset, int] = UNSET
    h2_fe_max_total_streams: Union[None, Unset, int] = UNSET
    h2_fe_rxbuf: Union[None, Unset, int] = UNSET
    h2_header_table_size: Union[Unset, int] = UNSET
    h2_initial_window_size: Union[None, Unset, int] = UNSET
    h2_max_concurrent_streams: Union[Unset, int] = UNSET
    h2_max_frame_size: Union[Unset, int] = UNSET
    h2_zero_copy_fwd_send: Union[Unset, TuneOptionsH2ZeroCopyFwdSend] = UNSET
    http_cookielen: Union[Unset, int] = UNSET
    http_logurilen: Union[Unset, int] = UNSET
    http_maxhdr: Union[Unset, int] = UNSET
    idle_pool_shared: Union[Unset, TuneOptionsIdlePoolShared] = UNSET
    idletimer: Union[None, Unset, int] = UNSET
    listener_default_shards: Union[Unset, TuneOptionsListenerDefaultShards] = UNSET
    listener_multi_queue: Union[Unset, TuneOptionsListenerMultiQueue] = UNSET
    max_checks_per_thread: Union[None, Unset, int] = UNSET
    max_rules_at_once: Union[None, Unset, int] = UNSET
    maxaccept: Union[Unset, int] = UNSET
    maxpollevents: Union[Unset, int] = UNSET
    maxrewrite: Union[Unset, int] = UNSET
    memory_hot_size: Union[None, Unset, int] = UNSET
    notsent_lowat_client: Union[None, Unset, int] = UNSET
    notsent_lowat_server: Union[None, Unset, int] = UNSET
    pattern_cache_size: Union[None, Unset, int] = UNSET
    peers_max_updates_at_once: Union[Unset, int] = UNSET
    pool_high_fd_ratio: Union[Unset, int] = UNSET
    pool_low_fd_ratio: Union[Unset, int] = UNSET
    pt_zero_copy_forwarding: Union[Unset, TuneOptionsPtZeroCopyForwarding] = UNSET
    renice_runtime: Union[None, Unset, int] = UNSET
    renice_startup: Union[None, Unset, int] = UNSET
    ring_queues: Union[None, Unset, int] = UNSET
    runqueue_depth: Union[Unset, int] = UNSET
    sched_low_latency: Union[Unset, TuneOptionsSchedLowLatency] = UNSET
    stick_counters: Union[None, Unset, int] = UNSET
    takeover_other_tg_connections: Union[Unset, TuneOptionsTakeoverOtherTgConnections] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        applet_zero_copy_forwarding: Union[Unset, str] = UNSET
        if not isinstance(self.applet_zero_copy_forwarding, Unset):
            applet_zero_copy_forwarding = self.applet_zero_copy_forwarding.value

        comp_maxlevel = self.comp_maxlevel

        disable_fast_forward = self.disable_fast_forward

        disable_zero_copy_forwarding = self.disable_zero_copy_forwarding

        epoll_mask_events: Union[Unset, list[str]] = UNSET
        if not isinstance(self.epoll_mask_events, Unset):
            epoll_mask_events = []
            for epoll_mask_events_item_data in self.epoll_mask_events:
                epoll_mask_events_item = epoll_mask_events_item_data.value
                epoll_mask_events.append(epoll_mask_events_item)

        events_max_events_at_once = self.events_max_events_at_once

        fail_alloc = self.fail_alloc

        fd_edge_triggered: Union[Unset, str] = UNSET
        if not isinstance(self.fd_edge_triggered, Unset):
            fd_edge_triggered = self.fd_edge_triggered.value

        glitches_kill_cpu_usage: Union[None, Unset, int]
        if isinstance(self.glitches_kill_cpu_usage, Unset):
            glitches_kill_cpu_usage = UNSET
        else:
            glitches_kill_cpu_usage = self.glitches_kill_cpu_usage

        h1_zero_copy_fwd_recv: Union[Unset, str] = UNSET
        if not isinstance(self.h1_zero_copy_fwd_recv, Unset):
            h1_zero_copy_fwd_recv = self.h1_zero_copy_fwd_recv.value

        h1_zero_copy_fwd_send: Union[Unset, str] = UNSET
        if not isinstance(self.h1_zero_copy_fwd_send, Unset):
            h1_zero_copy_fwd_send = self.h1_zero_copy_fwd_send.value

        h2_be_glitches_threshold: Union[None, Unset, int]
        if isinstance(self.h2_be_glitches_threshold, Unset):
            h2_be_glitches_threshold = UNSET
        else:
            h2_be_glitches_threshold = self.h2_be_glitches_threshold

        h2_be_initial_window_size = self.h2_be_initial_window_size

        h2_be_max_concurrent_streams = self.h2_be_max_concurrent_streams

        h2_be_rxbuf: Union[None, Unset, int]
        if isinstance(self.h2_be_rxbuf, Unset):
            h2_be_rxbuf = UNSET
        else:
            h2_be_rxbuf = self.h2_be_rxbuf

        h2_fe_glitches_threshold: Union[None, Unset, int]
        if isinstance(self.h2_fe_glitches_threshold, Unset):
            h2_fe_glitches_threshold = UNSET
        else:
            h2_fe_glitches_threshold = self.h2_fe_glitches_threshold

        h2_fe_initial_window_size = self.h2_fe_initial_window_size

        h2_fe_max_concurrent_streams = self.h2_fe_max_concurrent_streams

        h2_fe_max_total_streams: Union[None, Unset, int]
        if isinstance(self.h2_fe_max_total_streams, Unset):
            h2_fe_max_total_streams = UNSET
        else:
            h2_fe_max_total_streams = self.h2_fe_max_total_streams

        h2_fe_rxbuf: Union[None, Unset, int]
        if isinstance(self.h2_fe_rxbuf, Unset):
            h2_fe_rxbuf = UNSET
        else:
            h2_fe_rxbuf = self.h2_fe_rxbuf

        h2_header_table_size = self.h2_header_table_size

        h2_initial_window_size: Union[None, Unset, int]
        if isinstance(self.h2_initial_window_size, Unset):
            h2_initial_window_size = UNSET
        else:
            h2_initial_window_size = self.h2_initial_window_size

        h2_max_concurrent_streams = self.h2_max_concurrent_streams

        h2_max_frame_size = self.h2_max_frame_size

        h2_zero_copy_fwd_send: Union[Unset, str] = UNSET
        if not isinstance(self.h2_zero_copy_fwd_send, Unset):
            h2_zero_copy_fwd_send = self.h2_zero_copy_fwd_send.value

        http_cookielen = self.http_cookielen

        http_logurilen = self.http_logurilen

        http_maxhdr = self.http_maxhdr

        idle_pool_shared: Union[Unset, str] = UNSET
        if not isinstance(self.idle_pool_shared, Unset):
            idle_pool_shared = self.idle_pool_shared.value

        idletimer: Union[None, Unset, int]
        if isinstance(self.idletimer, Unset):
            idletimer = UNSET
        else:
            idletimer = self.idletimer

        listener_default_shards: Union[Unset, str] = UNSET
        if not isinstance(self.listener_default_shards, Unset):
            listener_default_shards = self.listener_default_shards.value

        listener_multi_queue: Union[Unset, str] = UNSET
        if not isinstance(self.listener_multi_queue, Unset):
            listener_multi_queue = self.listener_multi_queue.value

        max_checks_per_thread: Union[None, Unset, int]
        if isinstance(self.max_checks_per_thread, Unset):
            max_checks_per_thread = UNSET
        else:
            max_checks_per_thread = self.max_checks_per_thread

        max_rules_at_once: Union[None, Unset, int]
        if isinstance(self.max_rules_at_once, Unset):
            max_rules_at_once = UNSET
        else:
            max_rules_at_once = self.max_rules_at_once

        maxaccept = self.maxaccept

        maxpollevents = self.maxpollevents

        maxrewrite = self.maxrewrite

        memory_hot_size: Union[None, Unset, int]
        if isinstance(self.memory_hot_size, Unset):
            memory_hot_size = UNSET
        else:
            memory_hot_size = self.memory_hot_size

        notsent_lowat_client: Union[None, Unset, int]
        if isinstance(self.notsent_lowat_client, Unset):
            notsent_lowat_client = UNSET
        else:
            notsent_lowat_client = self.notsent_lowat_client

        notsent_lowat_server: Union[None, Unset, int]
        if isinstance(self.notsent_lowat_server, Unset):
            notsent_lowat_server = UNSET
        else:
            notsent_lowat_server = self.notsent_lowat_server

        pattern_cache_size: Union[None, Unset, int]
        if isinstance(self.pattern_cache_size, Unset):
            pattern_cache_size = UNSET
        else:
            pattern_cache_size = self.pattern_cache_size

        peers_max_updates_at_once = self.peers_max_updates_at_once

        pool_high_fd_ratio = self.pool_high_fd_ratio

        pool_low_fd_ratio = self.pool_low_fd_ratio

        pt_zero_copy_forwarding: Union[Unset, str] = UNSET
        if not isinstance(self.pt_zero_copy_forwarding, Unset):
            pt_zero_copy_forwarding = self.pt_zero_copy_forwarding.value

        renice_runtime: Union[None, Unset, int]
        if isinstance(self.renice_runtime, Unset):
            renice_runtime = UNSET
        else:
            renice_runtime = self.renice_runtime

        renice_startup: Union[None, Unset, int]
        if isinstance(self.renice_startup, Unset):
            renice_startup = UNSET
        else:
            renice_startup = self.renice_startup

        ring_queues: Union[None, Unset, int]
        if isinstance(self.ring_queues, Unset):
            ring_queues = UNSET
        else:
            ring_queues = self.ring_queues

        runqueue_depth = self.runqueue_depth

        sched_low_latency: Union[Unset, str] = UNSET
        if not isinstance(self.sched_low_latency, Unset):
            sched_low_latency = self.sched_low_latency.value

        stick_counters: Union[None, Unset, int]
        if isinstance(self.stick_counters, Unset):
            stick_counters = UNSET
        else:
            stick_counters = self.stick_counters

        takeover_other_tg_connections: Union[Unset, str] = UNSET
        if not isinstance(self.takeover_other_tg_connections, Unset):
            takeover_other_tg_connections = self.takeover_other_tg_connections.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if applet_zero_copy_forwarding is not UNSET:
            field_dict["applet_zero_copy_forwarding"] = applet_zero_copy_forwarding
        if comp_maxlevel is not UNSET:
            field_dict["comp_maxlevel"] = comp_maxlevel
        if disable_fast_forward is not UNSET:
            field_dict["disable_fast_forward"] = disable_fast_forward
        if disable_zero_copy_forwarding is not UNSET:
            field_dict["disable_zero_copy_forwarding"] = disable_zero_copy_forwarding
        if epoll_mask_events is not UNSET:
            field_dict["epoll_mask_events"] = epoll_mask_events
        if events_max_events_at_once is not UNSET:
            field_dict["events_max_events_at_once"] = events_max_events_at_once
        if fail_alloc is not UNSET:
            field_dict["fail_alloc"] = fail_alloc
        if fd_edge_triggered is not UNSET:
            field_dict["fd_edge_triggered"] = fd_edge_triggered
        if glitches_kill_cpu_usage is not UNSET:
            field_dict["glitches_kill_cpu_usage"] = glitches_kill_cpu_usage
        if h1_zero_copy_fwd_recv is not UNSET:
            field_dict["h1_zero_copy_fwd_recv"] = h1_zero_copy_fwd_recv
        if h1_zero_copy_fwd_send is not UNSET:
            field_dict["h1_zero_copy_fwd_send"] = h1_zero_copy_fwd_send
        if h2_be_glitches_threshold is not UNSET:
            field_dict["h2_be_glitches_threshold"] = h2_be_glitches_threshold
        if h2_be_initial_window_size is not UNSET:
            field_dict["h2_be_initial_window_size"] = h2_be_initial_window_size
        if h2_be_max_concurrent_streams is not UNSET:
            field_dict["h2_be_max_concurrent_streams"] = h2_be_max_concurrent_streams
        if h2_be_rxbuf is not UNSET:
            field_dict["h2_be_rxbuf"] = h2_be_rxbuf
        if h2_fe_glitches_threshold is not UNSET:
            field_dict["h2_fe_glitches_threshold"] = h2_fe_glitches_threshold
        if h2_fe_initial_window_size is not UNSET:
            field_dict["h2_fe_initial_window_size"] = h2_fe_initial_window_size
        if h2_fe_max_concurrent_streams is not UNSET:
            field_dict["h2_fe_max_concurrent_streams"] = h2_fe_max_concurrent_streams
        if h2_fe_max_total_streams is not UNSET:
            field_dict["h2_fe_max_total_streams"] = h2_fe_max_total_streams
        if h2_fe_rxbuf is not UNSET:
            field_dict["h2_fe_rxbuf"] = h2_fe_rxbuf
        if h2_header_table_size is not UNSET:
            field_dict["h2_header_table_size"] = h2_header_table_size
        if h2_initial_window_size is not UNSET:
            field_dict["h2_initial_window_size"] = h2_initial_window_size
        if h2_max_concurrent_streams is not UNSET:
            field_dict["h2_max_concurrent_streams"] = h2_max_concurrent_streams
        if h2_max_frame_size is not UNSET:
            field_dict["h2_max_frame_size"] = h2_max_frame_size
        if h2_zero_copy_fwd_send is not UNSET:
            field_dict["h2_zero_copy_fwd_send"] = h2_zero_copy_fwd_send
        if http_cookielen is not UNSET:
            field_dict["http_cookielen"] = http_cookielen
        if http_logurilen is not UNSET:
            field_dict["http_logurilen"] = http_logurilen
        if http_maxhdr is not UNSET:
            field_dict["http_maxhdr"] = http_maxhdr
        if idle_pool_shared is not UNSET:
            field_dict["idle_pool_shared"] = idle_pool_shared
        if idletimer is not UNSET:
            field_dict["idletimer"] = idletimer
        if listener_default_shards is not UNSET:
            field_dict["listener_default_shards"] = listener_default_shards
        if listener_multi_queue is not UNSET:
            field_dict["listener_multi_queue"] = listener_multi_queue
        if max_checks_per_thread is not UNSET:
            field_dict["max_checks_per_thread"] = max_checks_per_thread
        if max_rules_at_once is not UNSET:
            field_dict["max_rules_at_once"] = max_rules_at_once
        if maxaccept is not UNSET:
            field_dict["maxaccept"] = maxaccept
        if maxpollevents is not UNSET:
            field_dict["maxpollevents"] = maxpollevents
        if maxrewrite is not UNSET:
            field_dict["maxrewrite"] = maxrewrite
        if memory_hot_size is not UNSET:
            field_dict["memory_hot_size"] = memory_hot_size
        if notsent_lowat_client is not UNSET:
            field_dict["notsent_lowat_client"] = notsent_lowat_client
        if notsent_lowat_server is not UNSET:
            field_dict["notsent_lowat_server"] = notsent_lowat_server
        if pattern_cache_size is not UNSET:
            field_dict["pattern_cache_size"] = pattern_cache_size
        if peers_max_updates_at_once is not UNSET:
            field_dict["peers_max_updates_at_once"] = peers_max_updates_at_once
        if pool_high_fd_ratio is not UNSET:
            field_dict["pool_high_fd_ratio"] = pool_high_fd_ratio
        if pool_low_fd_ratio is not UNSET:
            field_dict["pool_low_fd_ratio"] = pool_low_fd_ratio
        if pt_zero_copy_forwarding is not UNSET:
            field_dict["pt_zero_copy_forwarding"] = pt_zero_copy_forwarding
        if renice_runtime is not UNSET:
            field_dict["renice_runtime"] = renice_runtime
        if renice_startup is not UNSET:
            field_dict["renice_startup"] = renice_startup
        if ring_queues is not UNSET:
            field_dict["ring_queues"] = ring_queues
        if runqueue_depth is not UNSET:
            field_dict["runqueue_depth"] = runqueue_depth
        if sched_low_latency is not UNSET:
            field_dict["sched_low_latency"] = sched_low_latency
        if stick_counters is not UNSET:
            field_dict["stick_counters"] = stick_counters
        if takeover_other_tg_connections is not UNSET:
            field_dict["takeover_other_tg_connections"] = takeover_other_tg_connections

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _applet_zero_copy_forwarding = d.pop("applet_zero_copy_forwarding", UNSET)
        applet_zero_copy_forwarding: Union[Unset, TuneOptionsAppletZeroCopyForwarding]
        if isinstance(_applet_zero_copy_forwarding, Unset):
            applet_zero_copy_forwarding = UNSET
        else:
            applet_zero_copy_forwarding = TuneOptionsAppletZeroCopyForwarding(_applet_zero_copy_forwarding)

        comp_maxlevel = d.pop("comp_maxlevel", UNSET)

        disable_fast_forward = d.pop("disable_fast_forward", UNSET)

        disable_zero_copy_forwarding = d.pop("disable_zero_copy_forwarding", UNSET)

        _epoll_mask_events = d.pop("epoll_mask_events", UNSET)
        epoll_mask_events: Union[Unset, list[TuneOptionsEpollMaskEventsItem]] = UNSET
        if not isinstance(_epoll_mask_events, Unset):
            epoll_mask_events = []
            for epoll_mask_events_item_data in _epoll_mask_events:
                epoll_mask_events_item = TuneOptionsEpollMaskEventsItem(epoll_mask_events_item_data)

                epoll_mask_events.append(epoll_mask_events_item)

        events_max_events_at_once = d.pop("events_max_events_at_once", UNSET)

        fail_alloc = d.pop("fail_alloc", UNSET)

        _fd_edge_triggered = d.pop("fd_edge_triggered", UNSET)
        fd_edge_triggered: Union[Unset, TuneOptionsFdEdgeTriggered]
        if isinstance(_fd_edge_triggered, Unset):
            fd_edge_triggered = UNSET
        else:
            fd_edge_triggered = TuneOptionsFdEdgeTriggered(_fd_edge_triggered)

        def _parse_glitches_kill_cpu_usage(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        glitches_kill_cpu_usage = _parse_glitches_kill_cpu_usage(d.pop("glitches_kill_cpu_usage", UNSET))

        _h1_zero_copy_fwd_recv = d.pop("h1_zero_copy_fwd_recv", UNSET)
        h1_zero_copy_fwd_recv: Union[Unset, TuneOptionsH1ZeroCopyFwdRecv]
        if isinstance(_h1_zero_copy_fwd_recv, Unset):
            h1_zero_copy_fwd_recv = UNSET
        else:
            h1_zero_copy_fwd_recv = TuneOptionsH1ZeroCopyFwdRecv(_h1_zero_copy_fwd_recv)

        _h1_zero_copy_fwd_send = d.pop("h1_zero_copy_fwd_send", UNSET)
        h1_zero_copy_fwd_send: Union[Unset, TuneOptionsH1ZeroCopyFwdSend]
        if isinstance(_h1_zero_copy_fwd_send, Unset):
            h1_zero_copy_fwd_send = UNSET
        else:
            h1_zero_copy_fwd_send = TuneOptionsH1ZeroCopyFwdSend(_h1_zero_copy_fwd_send)

        def _parse_h2_be_glitches_threshold(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        h2_be_glitches_threshold = _parse_h2_be_glitches_threshold(d.pop("h2_be_glitches_threshold", UNSET))

        h2_be_initial_window_size = d.pop("h2_be_initial_window_size", UNSET)

        h2_be_max_concurrent_streams = d.pop("h2_be_max_concurrent_streams", UNSET)

        def _parse_h2_be_rxbuf(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        h2_be_rxbuf = _parse_h2_be_rxbuf(d.pop("h2_be_rxbuf", UNSET))

        def _parse_h2_fe_glitches_threshold(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        h2_fe_glitches_threshold = _parse_h2_fe_glitches_threshold(d.pop("h2_fe_glitches_threshold", UNSET))

        h2_fe_initial_window_size = d.pop("h2_fe_initial_window_size", UNSET)

        h2_fe_max_concurrent_streams = d.pop("h2_fe_max_concurrent_streams", UNSET)

        def _parse_h2_fe_max_total_streams(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        h2_fe_max_total_streams = _parse_h2_fe_max_total_streams(d.pop("h2_fe_max_total_streams", UNSET))

        def _parse_h2_fe_rxbuf(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        h2_fe_rxbuf = _parse_h2_fe_rxbuf(d.pop("h2_fe_rxbuf", UNSET))

        h2_header_table_size = d.pop("h2_header_table_size", UNSET)

        def _parse_h2_initial_window_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        h2_initial_window_size = _parse_h2_initial_window_size(d.pop("h2_initial_window_size", UNSET))

        h2_max_concurrent_streams = d.pop("h2_max_concurrent_streams", UNSET)

        h2_max_frame_size = d.pop("h2_max_frame_size", UNSET)

        _h2_zero_copy_fwd_send = d.pop("h2_zero_copy_fwd_send", UNSET)
        h2_zero_copy_fwd_send: Union[Unset, TuneOptionsH2ZeroCopyFwdSend]
        if isinstance(_h2_zero_copy_fwd_send, Unset):
            h2_zero_copy_fwd_send = UNSET
        else:
            h2_zero_copy_fwd_send = TuneOptionsH2ZeroCopyFwdSend(_h2_zero_copy_fwd_send)

        http_cookielen = d.pop("http_cookielen", UNSET)

        http_logurilen = d.pop("http_logurilen", UNSET)

        http_maxhdr = d.pop("http_maxhdr", UNSET)

        _idle_pool_shared = d.pop("idle_pool_shared", UNSET)
        idle_pool_shared: Union[Unset, TuneOptionsIdlePoolShared]
        if isinstance(_idle_pool_shared, Unset):
            idle_pool_shared = UNSET
        else:
            idle_pool_shared = TuneOptionsIdlePoolShared(_idle_pool_shared)

        def _parse_idletimer(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        idletimer = _parse_idletimer(d.pop("idletimer", UNSET))

        _listener_default_shards = d.pop("listener_default_shards", UNSET)
        listener_default_shards: Union[Unset, TuneOptionsListenerDefaultShards]
        if isinstance(_listener_default_shards, Unset):
            listener_default_shards = UNSET
        else:
            listener_default_shards = TuneOptionsListenerDefaultShards(_listener_default_shards)

        _listener_multi_queue = d.pop("listener_multi_queue", UNSET)
        listener_multi_queue: Union[Unset, TuneOptionsListenerMultiQueue]
        if isinstance(_listener_multi_queue, Unset):
            listener_multi_queue = UNSET
        else:
            listener_multi_queue = TuneOptionsListenerMultiQueue(_listener_multi_queue)

        def _parse_max_checks_per_thread(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_checks_per_thread = _parse_max_checks_per_thread(d.pop("max_checks_per_thread", UNSET))

        def _parse_max_rules_at_once(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_rules_at_once = _parse_max_rules_at_once(d.pop("max_rules_at_once", UNSET))

        maxaccept = d.pop("maxaccept", UNSET)

        maxpollevents = d.pop("maxpollevents", UNSET)

        maxrewrite = d.pop("maxrewrite", UNSET)

        def _parse_memory_hot_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        memory_hot_size = _parse_memory_hot_size(d.pop("memory_hot_size", UNSET))

        def _parse_notsent_lowat_client(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        notsent_lowat_client = _parse_notsent_lowat_client(d.pop("notsent_lowat_client", UNSET))

        def _parse_notsent_lowat_server(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        notsent_lowat_server = _parse_notsent_lowat_server(d.pop("notsent_lowat_server", UNSET))

        def _parse_pattern_cache_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        pattern_cache_size = _parse_pattern_cache_size(d.pop("pattern_cache_size", UNSET))

        peers_max_updates_at_once = d.pop("peers_max_updates_at_once", UNSET)

        pool_high_fd_ratio = d.pop("pool_high_fd_ratio", UNSET)

        pool_low_fd_ratio = d.pop("pool_low_fd_ratio", UNSET)

        _pt_zero_copy_forwarding = d.pop("pt_zero_copy_forwarding", UNSET)
        pt_zero_copy_forwarding: Union[Unset, TuneOptionsPtZeroCopyForwarding]
        if isinstance(_pt_zero_copy_forwarding, Unset):
            pt_zero_copy_forwarding = UNSET
        else:
            pt_zero_copy_forwarding = TuneOptionsPtZeroCopyForwarding(_pt_zero_copy_forwarding)

        def _parse_renice_runtime(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        renice_runtime = _parse_renice_runtime(d.pop("renice_runtime", UNSET))

        def _parse_renice_startup(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        renice_startup = _parse_renice_startup(d.pop("renice_startup", UNSET))

        def _parse_ring_queues(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        ring_queues = _parse_ring_queues(d.pop("ring_queues", UNSET))

        runqueue_depth = d.pop("runqueue_depth", UNSET)

        _sched_low_latency = d.pop("sched_low_latency", UNSET)
        sched_low_latency: Union[Unset, TuneOptionsSchedLowLatency]
        if isinstance(_sched_low_latency, Unset):
            sched_low_latency = UNSET
        else:
            sched_low_latency = TuneOptionsSchedLowLatency(_sched_low_latency)

        def _parse_stick_counters(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        stick_counters = _parse_stick_counters(d.pop("stick_counters", UNSET))

        _takeover_other_tg_connections = d.pop("takeover_other_tg_connections", UNSET)
        takeover_other_tg_connections: Union[Unset, TuneOptionsTakeoverOtherTgConnections]
        if isinstance(_takeover_other_tg_connections, Unset):
            takeover_other_tg_connections = UNSET
        else:
            takeover_other_tg_connections = TuneOptionsTakeoverOtherTgConnections(_takeover_other_tg_connections)

        tune_options = cls(
            applet_zero_copy_forwarding=applet_zero_copy_forwarding,
            comp_maxlevel=comp_maxlevel,
            disable_fast_forward=disable_fast_forward,
            disable_zero_copy_forwarding=disable_zero_copy_forwarding,
            epoll_mask_events=epoll_mask_events,
            events_max_events_at_once=events_max_events_at_once,
            fail_alloc=fail_alloc,
            fd_edge_triggered=fd_edge_triggered,
            glitches_kill_cpu_usage=glitches_kill_cpu_usage,
            h1_zero_copy_fwd_recv=h1_zero_copy_fwd_recv,
            h1_zero_copy_fwd_send=h1_zero_copy_fwd_send,
            h2_be_glitches_threshold=h2_be_glitches_threshold,
            h2_be_initial_window_size=h2_be_initial_window_size,
            h2_be_max_concurrent_streams=h2_be_max_concurrent_streams,
            h2_be_rxbuf=h2_be_rxbuf,
            h2_fe_glitches_threshold=h2_fe_glitches_threshold,
            h2_fe_initial_window_size=h2_fe_initial_window_size,
            h2_fe_max_concurrent_streams=h2_fe_max_concurrent_streams,
            h2_fe_max_total_streams=h2_fe_max_total_streams,
            h2_fe_rxbuf=h2_fe_rxbuf,
            h2_header_table_size=h2_header_table_size,
            h2_initial_window_size=h2_initial_window_size,
            h2_max_concurrent_streams=h2_max_concurrent_streams,
            h2_max_frame_size=h2_max_frame_size,
            h2_zero_copy_fwd_send=h2_zero_copy_fwd_send,
            http_cookielen=http_cookielen,
            http_logurilen=http_logurilen,
            http_maxhdr=http_maxhdr,
            idle_pool_shared=idle_pool_shared,
            idletimer=idletimer,
            listener_default_shards=listener_default_shards,
            listener_multi_queue=listener_multi_queue,
            max_checks_per_thread=max_checks_per_thread,
            max_rules_at_once=max_rules_at_once,
            maxaccept=maxaccept,
            maxpollevents=maxpollevents,
            maxrewrite=maxrewrite,
            memory_hot_size=memory_hot_size,
            notsent_lowat_client=notsent_lowat_client,
            notsent_lowat_server=notsent_lowat_server,
            pattern_cache_size=pattern_cache_size,
            peers_max_updates_at_once=peers_max_updates_at_once,
            pool_high_fd_ratio=pool_high_fd_ratio,
            pool_low_fd_ratio=pool_low_fd_ratio,
            pt_zero_copy_forwarding=pt_zero_copy_forwarding,
            renice_runtime=renice_runtime,
            renice_startup=renice_startup,
            ring_queues=ring_queues,
            runqueue_depth=runqueue_depth,
            sched_low_latency=sched_low_latency,
            stick_counters=stick_counters,
            takeover_other_tg_connections=takeover_other_tg_connections,
        )

        tune_options.additional_properties = d
        return tune_options

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
