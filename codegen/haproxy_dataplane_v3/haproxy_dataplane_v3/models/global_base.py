from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.global_base_cpu_policy import GlobalBaseCpuPolicy
from ..models.global_base_numa_cpu_mapping import GlobalBaseNumaCpuMapping
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.debug_options import DebugOptions
    from ..models.device_atlas_options import DeviceAtlasOptions
    from ..models.environment_options import EnvironmentOptions
    from ..models.fifty_one_degrees_options import FiftyOneDegreesOptions
    from ..models.global_base_cpu_maps_item import GlobalBaseCpuMapsItem
    from ..models.global_base_cpu_set_item import GlobalBaseCpuSetItem
    from ..models.global_base_default_path import GlobalBaseDefaultPath
    from ..models.global_base_h1_case_adjust_item import GlobalBaseH1CaseAdjustItem
    from ..models.global_base_harden import GlobalBaseHarden
    from ..models.global_base_log_send_hostname import GlobalBaseLogSendHostname
    from ..models.global_base_runtime_apis_item import GlobalBaseRuntimeApisItem
    from ..models.global_base_set_var_fmt_item import GlobalBaseSetVarFmtItem
    from ..models.global_base_set_var_item import GlobalBaseSetVarItem
    from ..models.global_base_thread_group_lines_item import GlobalBaseThreadGroupLinesItem
    from ..models.http_client_options import HttpClientOptions
    from ..models.http_codes import HttpCodes
    from ..models.lua_options import LuaOptions
    from ..models.ocsp_update_options import OcspUpdateOptions
    from ..models.performance_options import PerformanceOptions
    from ..models.ssl_options import SslOptions
    from ..models.tune_buffer_options import TuneBufferOptions
    from ..models.tune_lua_options import TuneLuaOptions
    from ..models.tune_options import TuneOptions
    from ..models.tune_quic_options import TuneQuicOptions
    from ..models.tune_ssl_options import TuneSslOptions
    from ..models.tune_vars_options import TuneVarsOptions
    from ..models.tune_zlib_options import TuneZlibOptions
    from ..models.wurfl_options import WurflOptions


T = TypeVar("T", bound="GlobalBase")


@_attrs_define
class GlobalBase:
    """HAProxy global configuration

    Attributes:
        chroot (Union[Unset, str]):
        close_spread_time (Union[None, Unset, int]):
        cluster_secret (Union[Unset, str]):
        cpu_maps (Union[Unset, list['GlobalBaseCpuMapsItem']]):
        cpu_policy (Union[Unset, GlobalBaseCpuPolicy]):
        cpu_set (Union[Unset, list['GlobalBaseCpuSetItem']]):
        daemon (Union[Unset, bool]):
        debug_options (Union[Unset, DebugOptions]):
        default_path (Union[Unset, GlobalBaseDefaultPath]):
        description (Union[Unset, str]):
        device_atlas_options (Union[Unset, DeviceAtlasOptions]):
        dns_accept_family (Union[Unset, str]):
        environment_options (Union[Unset, EnvironmentOptions]):
        expose_deprecated_directives (Union[Unset, bool]):
        expose_experimental_directives (Union[Unset, bool]):
        external_check (Union[Unset, bool]):
        fifty_one_degrees_options (Union[Unset, FiftyOneDegreesOptions]):
        force_cfg_parser_pause (Union[None, Unset, int]):
        gid (Union[Unset, int]):
        grace (Union[None, Unset, int]):
        group (Union[Unset, str]):
        h1_accept_payload_with_any_method (Union[Unset, bool]):
        h1_case_adjust (Union[Unset, list['GlobalBaseH1CaseAdjustItem']]):
        h1_case_adjust_file (Union[Unset, str]):
        h1_do_not_close_on_insecure_transfer_encoding (Union[Unset, bool]):
        h2_workaround_bogus_websocket_clients (Union[Unset, bool]):
        hard_stop_after (Union[None, Unset, int]):
        harden (Union[Unset, GlobalBaseHarden]):
        http_client_options (Union[Unset, HttpClientOptions]):
        http_err_codes (Union[Unset, list['HttpCodes']]):
        http_fail_codes (Union[Unset, list['HttpCodes']]):
        insecure_fork_wanted (Union[Unset, bool]):
        insecure_setuid_wanted (Union[Unset, bool]):
        limited_quic (Union[Unset, bool]):
        localpeer (Union[Unset, str]):
        log_send_hostname (Union[Unset, GlobalBaseLogSendHostname]):
        lua_options (Union[Unset, LuaOptions]):
        master_worker (Union[Unset, bool]):
        metadata (Union[Unset, Any]):
        mworker_max_reloads (Union[None, Unset, int]):
        nbthread (Union[Unset, int]):
        no_quic (Union[Unset, bool]):
        node (Union[Unset, str]):
        numa_cpu_mapping (Union[Unset, GlobalBaseNumaCpuMapping]):
        ocsp_update_options (Union[Unset, OcspUpdateOptions]):
        performance_options (Union[Unset, PerformanceOptions]):
        pidfile (Union[Unset, str]):
        pp2_never_send_local (Union[Unset, bool]):
        prealloc_fd (Union[Unset, bool]):
        runtime_apis (Union[Unset, list['GlobalBaseRuntimeApisItem']]):
        set_dumpable (Union[Unset, bool]):
        set_var (Union[Unset, list['GlobalBaseSetVarItem']]):
        set_var_fmt (Union[Unset, list['GlobalBaseSetVarFmtItem']]):
        setcap (Union[Unset, str]):
        ssl_options (Union[Unset, SslOptions]):
        stats_file (Union[Unset, str]):
        stats_maxconn (Union[None, Unset, int]):
        stats_timeout (Union[None, Unset, int]):
        strict_limits (Union[Unset, bool]):
        thread_group_lines (Union[Unset, list['GlobalBaseThreadGroupLinesItem']]):
        thread_groups (Union[Unset, int]):
        tune_buffer_options (Union[Unset, TuneBufferOptions]):
        tune_lua_options (Union[Unset, TuneLuaOptions]):
        tune_options (Union[Unset, TuneOptions]):
        tune_quic_options (Union[Unset, TuneQuicOptions]):
        tune_ssl_options (Union[Unset, TuneSslOptions]):
        tune_vars_options (Union[Unset, TuneVarsOptions]):
        tune_zlib_options (Union[Unset, TuneZlibOptions]):
        uid (Union[Unset, int]):
        ulimit_n (Union[Unset, int]):
        user (Union[Unset, str]):
        warn_blocked_traffic_after (Union[None, Unset, int]):
        wurfl_options (Union[Unset, WurflOptions]):
    """

    chroot: Union[Unset, str] = UNSET
    close_spread_time: Union[None, Unset, int] = UNSET
    cluster_secret: Union[Unset, str] = UNSET
    cpu_maps: Union[Unset, list["GlobalBaseCpuMapsItem"]] = UNSET
    cpu_policy: Union[Unset, GlobalBaseCpuPolicy] = UNSET
    cpu_set: Union[Unset, list["GlobalBaseCpuSetItem"]] = UNSET
    daemon: Union[Unset, bool] = UNSET
    debug_options: Union[Unset, "DebugOptions"] = UNSET
    default_path: Union[Unset, "GlobalBaseDefaultPath"] = UNSET
    description: Union[Unset, str] = UNSET
    device_atlas_options: Union[Unset, "DeviceAtlasOptions"] = UNSET
    dns_accept_family: Union[Unset, str] = UNSET
    environment_options: Union[Unset, "EnvironmentOptions"] = UNSET
    expose_deprecated_directives: Union[Unset, bool] = UNSET
    expose_experimental_directives: Union[Unset, bool] = UNSET
    external_check: Union[Unset, bool] = UNSET
    fifty_one_degrees_options: Union[Unset, "FiftyOneDegreesOptions"] = UNSET
    force_cfg_parser_pause: Union[None, Unset, int] = UNSET
    gid: Union[Unset, int] = UNSET
    grace: Union[None, Unset, int] = UNSET
    group: Union[Unset, str] = UNSET
    h1_accept_payload_with_any_method: Union[Unset, bool] = UNSET
    h1_case_adjust: Union[Unset, list["GlobalBaseH1CaseAdjustItem"]] = UNSET
    h1_case_adjust_file: Union[Unset, str] = UNSET
    h1_do_not_close_on_insecure_transfer_encoding: Union[Unset, bool] = UNSET
    h2_workaround_bogus_websocket_clients: Union[Unset, bool] = UNSET
    hard_stop_after: Union[None, Unset, int] = UNSET
    harden: Union[Unset, "GlobalBaseHarden"] = UNSET
    http_client_options: Union[Unset, "HttpClientOptions"] = UNSET
    http_err_codes: Union[Unset, list["HttpCodes"]] = UNSET
    http_fail_codes: Union[Unset, list["HttpCodes"]] = UNSET
    insecure_fork_wanted: Union[Unset, bool] = UNSET
    insecure_setuid_wanted: Union[Unset, bool] = UNSET
    limited_quic: Union[Unset, bool] = UNSET
    localpeer: Union[Unset, str] = UNSET
    log_send_hostname: Union[Unset, "GlobalBaseLogSendHostname"] = UNSET
    lua_options: Union[Unset, "LuaOptions"] = UNSET
    master_worker: Union[Unset, bool] = UNSET
    metadata: Union[Unset, Any] = UNSET
    mworker_max_reloads: Union[None, Unset, int] = UNSET
    nbthread: Union[Unset, int] = UNSET
    no_quic: Union[Unset, bool] = UNSET
    node: Union[Unset, str] = UNSET
    numa_cpu_mapping: Union[Unset, GlobalBaseNumaCpuMapping] = UNSET
    ocsp_update_options: Union[Unset, "OcspUpdateOptions"] = UNSET
    performance_options: Union[Unset, "PerformanceOptions"] = UNSET
    pidfile: Union[Unset, str] = UNSET
    pp2_never_send_local: Union[Unset, bool] = UNSET
    prealloc_fd: Union[Unset, bool] = UNSET
    runtime_apis: Union[Unset, list["GlobalBaseRuntimeApisItem"]] = UNSET
    set_dumpable: Union[Unset, bool] = UNSET
    set_var: Union[Unset, list["GlobalBaseSetVarItem"]] = UNSET
    set_var_fmt: Union[Unset, list["GlobalBaseSetVarFmtItem"]] = UNSET
    setcap: Union[Unset, str] = UNSET
    ssl_options: Union[Unset, "SslOptions"] = UNSET
    stats_file: Union[Unset, str] = UNSET
    stats_maxconn: Union[None, Unset, int] = UNSET
    stats_timeout: Union[None, Unset, int] = UNSET
    strict_limits: Union[Unset, bool] = UNSET
    thread_group_lines: Union[Unset, list["GlobalBaseThreadGroupLinesItem"]] = UNSET
    thread_groups: Union[Unset, int] = UNSET
    tune_buffer_options: Union[Unset, "TuneBufferOptions"] = UNSET
    tune_lua_options: Union[Unset, "TuneLuaOptions"] = UNSET
    tune_options: Union[Unset, "TuneOptions"] = UNSET
    tune_quic_options: Union[Unset, "TuneQuicOptions"] = UNSET
    tune_ssl_options: Union[Unset, "TuneSslOptions"] = UNSET
    tune_vars_options: Union[Unset, "TuneVarsOptions"] = UNSET
    tune_zlib_options: Union[Unset, "TuneZlibOptions"] = UNSET
    uid: Union[Unset, int] = UNSET
    ulimit_n: Union[Unset, int] = UNSET
    user: Union[Unset, str] = UNSET
    warn_blocked_traffic_after: Union[None, Unset, int] = UNSET
    wurfl_options: Union[Unset, "WurflOptions"] = UNSET

    def to_dict(self) -> dict[str, Any]:
        chroot = self.chroot

        close_spread_time: Union[None, Unset, int]
        if isinstance(self.close_spread_time, Unset):
            close_spread_time = UNSET
        else:
            close_spread_time = self.close_spread_time

        cluster_secret = self.cluster_secret

        cpu_maps: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.cpu_maps, Unset):
            cpu_maps = []
            for cpu_maps_item_data in self.cpu_maps:
                cpu_maps_item = cpu_maps_item_data.to_dict()
                cpu_maps.append(cpu_maps_item)

        cpu_policy: Union[Unset, str] = UNSET
        if not isinstance(self.cpu_policy, Unset):
            cpu_policy = self.cpu_policy.value

        cpu_set: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.cpu_set, Unset):
            cpu_set = []
            for cpu_set_item_data in self.cpu_set:
                cpu_set_item = cpu_set_item_data.to_dict()
                cpu_set.append(cpu_set_item)

        daemon = self.daemon

        debug_options: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.debug_options, Unset):
            debug_options = self.debug_options.to_dict()

        default_path: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.default_path, Unset):
            default_path = self.default_path.to_dict()

        description = self.description

        device_atlas_options: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.device_atlas_options, Unset):
            device_atlas_options = self.device_atlas_options.to_dict()

        dns_accept_family = self.dns_accept_family

        environment_options: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.environment_options, Unset):
            environment_options = self.environment_options.to_dict()

        expose_deprecated_directives = self.expose_deprecated_directives

        expose_experimental_directives = self.expose_experimental_directives

        external_check = self.external_check

        fifty_one_degrees_options: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.fifty_one_degrees_options, Unset):
            fifty_one_degrees_options = self.fifty_one_degrees_options.to_dict()

        force_cfg_parser_pause: Union[None, Unset, int]
        if isinstance(self.force_cfg_parser_pause, Unset):
            force_cfg_parser_pause = UNSET
        else:
            force_cfg_parser_pause = self.force_cfg_parser_pause

        gid = self.gid

        grace: Union[None, Unset, int]
        if isinstance(self.grace, Unset):
            grace = UNSET
        else:
            grace = self.grace

        group = self.group

        h1_accept_payload_with_any_method = self.h1_accept_payload_with_any_method

        h1_case_adjust: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.h1_case_adjust, Unset):
            h1_case_adjust = []
            for h1_case_adjust_item_data in self.h1_case_adjust:
                h1_case_adjust_item = h1_case_adjust_item_data.to_dict()
                h1_case_adjust.append(h1_case_adjust_item)

        h1_case_adjust_file = self.h1_case_adjust_file

        h1_do_not_close_on_insecure_transfer_encoding = self.h1_do_not_close_on_insecure_transfer_encoding

        h2_workaround_bogus_websocket_clients = self.h2_workaround_bogus_websocket_clients

        hard_stop_after: Union[None, Unset, int]
        if isinstance(self.hard_stop_after, Unset):
            hard_stop_after = UNSET
        else:
            hard_stop_after = self.hard_stop_after

        harden: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.harden, Unset):
            harden = self.harden.to_dict()

        http_client_options: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.http_client_options, Unset):
            http_client_options = self.http_client_options.to_dict()

        http_err_codes: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.http_err_codes, Unset):
            http_err_codes = []
            for http_err_codes_item_data in self.http_err_codes:
                http_err_codes_item = http_err_codes_item_data.to_dict()
                http_err_codes.append(http_err_codes_item)

        http_fail_codes: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.http_fail_codes, Unset):
            http_fail_codes = []
            for http_fail_codes_item_data in self.http_fail_codes:
                http_fail_codes_item = http_fail_codes_item_data.to_dict()
                http_fail_codes.append(http_fail_codes_item)

        insecure_fork_wanted = self.insecure_fork_wanted

        insecure_setuid_wanted = self.insecure_setuid_wanted

        limited_quic = self.limited_quic

        localpeer = self.localpeer

        log_send_hostname: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.log_send_hostname, Unset):
            log_send_hostname = self.log_send_hostname.to_dict()

        lua_options: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.lua_options, Unset):
            lua_options = self.lua_options.to_dict()

        master_worker = self.master_worker

        metadata = self.metadata

        mworker_max_reloads: Union[None, Unset, int]
        if isinstance(self.mworker_max_reloads, Unset):
            mworker_max_reloads = UNSET
        else:
            mworker_max_reloads = self.mworker_max_reloads

        nbthread = self.nbthread

        no_quic = self.no_quic

        node = self.node

        numa_cpu_mapping: Union[Unset, str] = UNSET
        if not isinstance(self.numa_cpu_mapping, Unset):
            numa_cpu_mapping = self.numa_cpu_mapping.value

        ocsp_update_options: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.ocsp_update_options, Unset):
            ocsp_update_options = self.ocsp_update_options.to_dict()

        performance_options: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.performance_options, Unset):
            performance_options = self.performance_options.to_dict()

        pidfile = self.pidfile

        pp2_never_send_local = self.pp2_never_send_local

        prealloc_fd = self.prealloc_fd

        runtime_apis: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.runtime_apis, Unset):
            runtime_apis = []
            for runtime_apis_item_data in self.runtime_apis:
                runtime_apis_item = runtime_apis_item_data.to_dict()
                runtime_apis.append(runtime_apis_item)

        set_dumpable = self.set_dumpable

        set_var: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.set_var, Unset):
            set_var = []
            for set_var_item_data in self.set_var:
                set_var_item = set_var_item_data.to_dict()
                set_var.append(set_var_item)

        set_var_fmt: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.set_var_fmt, Unset):
            set_var_fmt = []
            for set_var_fmt_item_data in self.set_var_fmt:
                set_var_fmt_item = set_var_fmt_item_data.to_dict()
                set_var_fmt.append(set_var_fmt_item)

        setcap = self.setcap

        ssl_options: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.ssl_options, Unset):
            ssl_options = self.ssl_options.to_dict()

        stats_file = self.stats_file

        stats_maxconn: Union[None, Unset, int]
        if isinstance(self.stats_maxconn, Unset):
            stats_maxconn = UNSET
        else:
            stats_maxconn = self.stats_maxconn

        stats_timeout: Union[None, Unset, int]
        if isinstance(self.stats_timeout, Unset):
            stats_timeout = UNSET
        else:
            stats_timeout = self.stats_timeout

        strict_limits = self.strict_limits

        thread_group_lines: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.thread_group_lines, Unset):
            thread_group_lines = []
            for thread_group_lines_item_data in self.thread_group_lines:
                thread_group_lines_item = thread_group_lines_item_data.to_dict()
                thread_group_lines.append(thread_group_lines_item)

        thread_groups = self.thread_groups

        tune_buffer_options: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.tune_buffer_options, Unset):
            tune_buffer_options = self.tune_buffer_options.to_dict()

        tune_lua_options: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.tune_lua_options, Unset):
            tune_lua_options = self.tune_lua_options.to_dict()

        tune_options: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.tune_options, Unset):
            tune_options = self.tune_options.to_dict()

        tune_quic_options: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.tune_quic_options, Unset):
            tune_quic_options = self.tune_quic_options.to_dict()

        tune_ssl_options: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.tune_ssl_options, Unset):
            tune_ssl_options = self.tune_ssl_options.to_dict()

        tune_vars_options: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.tune_vars_options, Unset):
            tune_vars_options = self.tune_vars_options.to_dict()

        tune_zlib_options: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.tune_zlib_options, Unset):
            tune_zlib_options = self.tune_zlib_options.to_dict()

        uid = self.uid

        ulimit_n = self.ulimit_n

        user = self.user

        warn_blocked_traffic_after: Union[None, Unset, int]
        if isinstance(self.warn_blocked_traffic_after, Unset):
            warn_blocked_traffic_after = UNSET
        else:
            warn_blocked_traffic_after = self.warn_blocked_traffic_after

        wurfl_options: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.wurfl_options, Unset):
            wurfl_options = self.wurfl_options.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update({})
        if chroot is not UNSET:
            field_dict["chroot"] = chroot
        if close_spread_time is not UNSET:
            field_dict["close_spread_time"] = close_spread_time
        if cluster_secret is not UNSET:
            field_dict["cluster_secret"] = cluster_secret
        if cpu_maps is not UNSET:
            field_dict["cpu_maps"] = cpu_maps
        if cpu_policy is not UNSET:
            field_dict["cpu_policy"] = cpu_policy
        if cpu_set is not UNSET:
            field_dict["cpu_set"] = cpu_set
        if daemon is not UNSET:
            field_dict["daemon"] = daemon
        if debug_options is not UNSET:
            field_dict["debug_options"] = debug_options
        if default_path is not UNSET:
            field_dict["default_path"] = default_path
        if description is not UNSET:
            field_dict["description"] = description
        if device_atlas_options is not UNSET:
            field_dict["device_atlas_options"] = device_atlas_options
        if dns_accept_family is not UNSET:
            field_dict["dns_accept_family"] = dns_accept_family
        if environment_options is not UNSET:
            field_dict["environment_options"] = environment_options
        if expose_deprecated_directives is not UNSET:
            field_dict["expose_deprecated_directives"] = expose_deprecated_directives
        if expose_experimental_directives is not UNSET:
            field_dict["expose_experimental_directives"] = expose_experimental_directives
        if external_check is not UNSET:
            field_dict["external_check"] = external_check
        if fifty_one_degrees_options is not UNSET:
            field_dict["fifty_one_degrees_options"] = fifty_one_degrees_options
        if force_cfg_parser_pause is not UNSET:
            field_dict["force_cfg_parser_pause"] = force_cfg_parser_pause
        if gid is not UNSET:
            field_dict["gid"] = gid
        if grace is not UNSET:
            field_dict["grace"] = grace
        if group is not UNSET:
            field_dict["group"] = group
        if h1_accept_payload_with_any_method is not UNSET:
            field_dict["h1_accept_payload_with_any_method"] = h1_accept_payload_with_any_method
        if h1_case_adjust is not UNSET:
            field_dict["h1_case_adjust"] = h1_case_adjust
        if h1_case_adjust_file is not UNSET:
            field_dict["h1_case_adjust_file"] = h1_case_adjust_file
        if h1_do_not_close_on_insecure_transfer_encoding is not UNSET:
            field_dict["h1_do_not_close_on_insecure_transfer_encoding"] = h1_do_not_close_on_insecure_transfer_encoding
        if h2_workaround_bogus_websocket_clients is not UNSET:
            field_dict["h2_workaround_bogus_websocket_clients"] = h2_workaround_bogus_websocket_clients
        if hard_stop_after is not UNSET:
            field_dict["hard_stop_after"] = hard_stop_after
        if harden is not UNSET:
            field_dict["harden"] = harden
        if http_client_options is not UNSET:
            field_dict["http_client_options"] = http_client_options
        if http_err_codes is not UNSET:
            field_dict["http_err_codes"] = http_err_codes
        if http_fail_codes is not UNSET:
            field_dict["http_fail_codes"] = http_fail_codes
        if insecure_fork_wanted is not UNSET:
            field_dict["insecure_fork_wanted"] = insecure_fork_wanted
        if insecure_setuid_wanted is not UNSET:
            field_dict["insecure_setuid_wanted"] = insecure_setuid_wanted
        if limited_quic is not UNSET:
            field_dict["limited_quic"] = limited_quic
        if localpeer is not UNSET:
            field_dict["localpeer"] = localpeer
        if log_send_hostname is not UNSET:
            field_dict["log_send_hostname"] = log_send_hostname
        if lua_options is not UNSET:
            field_dict["lua_options"] = lua_options
        if master_worker is not UNSET:
            field_dict["master-worker"] = master_worker
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if mworker_max_reloads is not UNSET:
            field_dict["mworker_max_reloads"] = mworker_max_reloads
        if nbthread is not UNSET:
            field_dict["nbthread"] = nbthread
        if no_quic is not UNSET:
            field_dict["no_quic"] = no_quic
        if node is not UNSET:
            field_dict["node"] = node
        if numa_cpu_mapping is not UNSET:
            field_dict["numa_cpu_mapping"] = numa_cpu_mapping
        if ocsp_update_options is not UNSET:
            field_dict["ocsp_update_options"] = ocsp_update_options
        if performance_options is not UNSET:
            field_dict["performance_options"] = performance_options
        if pidfile is not UNSET:
            field_dict["pidfile"] = pidfile
        if pp2_never_send_local is not UNSET:
            field_dict["pp2_never_send_local"] = pp2_never_send_local
        if prealloc_fd is not UNSET:
            field_dict["prealloc_fd"] = prealloc_fd
        if runtime_apis is not UNSET:
            field_dict["runtime_apis"] = runtime_apis
        if set_dumpable is not UNSET:
            field_dict["set_dumpable"] = set_dumpable
        if set_var is not UNSET:
            field_dict["set_var"] = set_var
        if set_var_fmt is not UNSET:
            field_dict["set_var_fmt"] = set_var_fmt
        if setcap is not UNSET:
            field_dict["setcap"] = setcap
        if ssl_options is not UNSET:
            field_dict["ssl_options"] = ssl_options
        if stats_file is not UNSET:
            field_dict["stats_file"] = stats_file
        if stats_maxconn is not UNSET:
            field_dict["stats_maxconn"] = stats_maxconn
        if stats_timeout is not UNSET:
            field_dict["stats_timeout"] = stats_timeout
        if strict_limits is not UNSET:
            field_dict["strict_limits"] = strict_limits
        if thread_group_lines is not UNSET:
            field_dict["thread_group_lines"] = thread_group_lines
        if thread_groups is not UNSET:
            field_dict["thread_groups"] = thread_groups
        if tune_buffer_options is not UNSET:
            field_dict["tune_buffer_options"] = tune_buffer_options
        if tune_lua_options is not UNSET:
            field_dict["tune_lua_options"] = tune_lua_options
        if tune_options is not UNSET:
            field_dict["tune_options"] = tune_options
        if tune_quic_options is not UNSET:
            field_dict["tune_quic_options"] = tune_quic_options
        if tune_ssl_options is not UNSET:
            field_dict["tune_ssl_options"] = tune_ssl_options
        if tune_vars_options is not UNSET:
            field_dict["tune_vars_options"] = tune_vars_options
        if tune_zlib_options is not UNSET:
            field_dict["tune_zlib_options"] = tune_zlib_options
        if uid is not UNSET:
            field_dict["uid"] = uid
        if ulimit_n is not UNSET:
            field_dict["ulimit_n"] = ulimit_n
        if user is not UNSET:
            field_dict["user"] = user
        if warn_blocked_traffic_after is not UNSET:
            field_dict["warn_blocked_traffic_after"] = warn_blocked_traffic_after
        if wurfl_options is not UNSET:
            field_dict["wurfl_options"] = wurfl_options

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.debug_options import DebugOptions
        from ..models.device_atlas_options import DeviceAtlasOptions
        from ..models.environment_options import EnvironmentOptions
        from ..models.fifty_one_degrees_options import FiftyOneDegreesOptions
        from ..models.global_base_cpu_maps_item import GlobalBaseCpuMapsItem
        from ..models.global_base_cpu_set_item import GlobalBaseCpuSetItem
        from ..models.global_base_default_path import GlobalBaseDefaultPath
        from ..models.global_base_h1_case_adjust_item import GlobalBaseH1CaseAdjustItem
        from ..models.global_base_harden import GlobalBaseHarden
        from ..models.global_base_log_send_hostname import GlobalBaseLogSendHostname
        from ..models.global_base_runtime_apis_item import GlobalBaseRuntimeApisItem
        from ..models.global_base_set_var_fmt_item import GlobalBaseSetVarFmtItem
        from ..models.global_base_set_var_item import GlobalBaseSetVarItem
        from ..models.global_base_thread_group_lines_item import GlobalBaseThreadGroupLinesItem
        from ..models.http_client_options import HttpClientOptions
        from ..models.http_codes import HttpCodes
        from ..models.lua_options import LuaOptions
        from ..models.ocsp_update_options import OcspUpdateOptions
        from ..models.performance_options import PerformanceOptions
        from ..models.ssl_options import SslOptions
        from ..models.tune_buffer_options import TuneBufferOptions
        from ..models.tune_lua_options import TuneLuaOptions
        from ..models.tune_options import TuneOptions
        from ..models.tune_quic_options import TuneQuicOptions
        from ..models.tune_ssl_options import TuneSslOptions
        from ..models.tune_vars_options import TuneVarsOptions
        from ..models.tune_zlib_options import TuneZlibOptions
        from ..models.wurfl_options import WurflOptions

        d = dict(src_dict)
        chroot = d.pop("chroot", UNSET)

        def _parse_close_spread_time(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        close_spread_time = _parse_close_spread_time(d.pop("close_spread_time", UNSET))

        cluster_secret = d.pop("cluster_secret", UNSET)

        cpu_maps = []
        _cpu_maps = d.pop("cpu_maps", UNSET)
        for cpu_maps_item_data in _cpu_maps or []:
            cpu_maps_item = GlobalBaseCpuMapsItem.from_dict(cpu_maps_item_data)

            cpu_maps.append(cpu_maps_item)

        _cpu_policy = d.pop("cpu_policy", UNSET)
        cpu_policy: Union[Unset, GlobalBaseCpuPolicy]
        if isinstance(_cpu_policy, Unset):
            cpu_policy = UNSET
        else:
            cpu_policy = GlobalBaseCpuPolicy(_cpu_policy)

        cpu_set = []
        _cpu_set = d.pop("cpu_set", UNSET)
        for cpu_set_item_data in _cpu_set or []:
            cpu_set_item = GlobalBaseCpuSetItem.from_dict(cpu_set_item_data)

            cpu_set.append(cpu_set_item)

        daemon = d.pop("daemon", UNSET)

        _debug_options = d.pop("debug_options", UNSET)
        debug_options: Union[Unset, DebugOptions]
        if isinstance(_debug_options, Unset):
            debug_options = UNSET
        else:
            debug_options = DebugOptions.from_dict(_debug_options)

        _default_path = d.pop("default_path", UNSET)
        default_path: Union[Unset, GlobalBaseDefaultPath]
        if isinstance(_default_path, Unset):
            default_path = UNSET
        else:
            default_path = GlobalBaseDefaultPath.from_dict(_default_path)

        description = d.pop("description", UNSET)

        _device_atlas_options = d.pop("device_atlas_options", UNSET)
        device_atlas_options: Union[Unset, DeviceAtlasOptions]
        if isinstance(_device_atlas_options, Unset):
            device_atlas_options = UNSET
        else:
            device_atlas_options = DeviceAtlasOptions.from_dict(_device_atlas_options)

        dns_accept_family = d.pop("dns_accept_family", UNSET)

        _environment_options = d.pop("environment_options", UNSET)
        environment_options: Union[Unset, EnvironmentOptions]
        if isinstance(_environment_options, Unset):
            environment_options = UNSET
        else:
            environment_options = EnvironmentOptions.from_dict(_environment_options)

        expose_deprecated_directives = d.pop("expose_deprecated_directives", UNSET)

        expose_experimental_directives = d.pop("expose_experimental_directives", UNSET)

        external_check = d.pop("external_check", UNSET)

        _fifty_one_degrees_options = d.pop("fifty_one_degrees_options", UNSET)
        fifty_one_degrees_options: Union[Unset, FiftyOneDegreesOptions]
        if isinstance(_fifty_one_degrees_options, Unset):
            fifty_one_degrees_options = UNSET
        else:
            fifty_one_degrees_options = FiftyOneDegreesOptions.from_dict(_fifty_one_degrees_options)

        def _parse_force_cfg_parser_pause(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        force_cfg_parser_pause = _parse_force_cfg_parser_pause(d.pop("force_cfg_parser_pause", UNSET))

        gid = d.pop("gid", UNSET)

        def _parse_grace(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        grace = _parse_grace(d.pop("grace", UNSET))

        group = d.pop("group", UNSET)

        h1_accept_payload_with_any_method = d.pop("h1_accept_payload_with_any_method", UNSET)

        h1_case_adjust = []
        _h1_case_adjust = d.pop("h1_case_adjust", UNSET)
        for h1_case_adjust_item_data in _h1_case_adjust or []:
            h1_case_adjust_item = GlobalBaseH1CaseAdjustItem.from_dict(h1_case_adjust_item_data)

            h1_case_adjust.append(h1_case_adjust_item)

        h1_case_adjust_file = d.pop("h1_case_adjust_file", UNSET)

        h1_do_not_close_on_insecure_transfer_encoding = d.pop("h1_do_not_close_on_insecure_transfer_encoding", UNSET)

        h2_workaround_bogus_websocket_clients = d.pop("h2_workaround_bogus_websocket_clients", UNSET)

        def _parse_hard_stop_after(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        hard_stop_after = _parse_hard_stop_after(d.pop("hard_stop_after", UNSET))

        _harden = d.pop("harden", UNSET)
        harden: Union[Unset, GlobalBaseHarden]
        if isinstance(_harden, Unset):
            harden = UNSET
        else:
            harden = GlobalBaseHarden.from_dict(_harden)

        _http_client_options = d.pop("http_client_options", UNSET)
        http_client_options: Union[Unset, HttpClientOptions]
        if isinstance(_http_client_options, Unset):
            http_client_options = UNSET
        else:
            http_client_options = HttpClientOptions.from_dict(_http_client_options)

        http_err_codes = []
        _http_err_codes = d.pop("http_err_codes", UNSET)
        for http_err_codes_item_data in _http_err_codes or []:
            http_err_codes_item = HttpCodes.from_dict(http_err_codes_item_data)

            http_err_codes.append(http_err_codes_item)

        http_fail_codes = []
        _http_fail_codes = d.pop("http_fail_codes", UNSET)
        for http_fail_codes_item_data in _http_fail_codes or []:
            http_fail_codes_item = HttpCodes.from_dict(http_fail_codes_item_data)

            http_fail_codes.append(http_fail_codes_item)

        insecure_fork_wanted = d.pop("insecure_fork_wanted", UNSET)

        insecure_setuid_wanted = d.pop("insecure_setuid_wanted", UNSET)

        limited_quic = d.pop("limited_quic", UNSET)

        localpeer = d.pop("localpeer", UNSET)

        _log_send_hostname = d.pop("log_send_hostname", UNSET)
        log_send_hostname: Union[Unset, GlobalBaseLogSendHostname]
        if isinstance(_log_send_hostname, Unset):
            log_send_hostname = UNSET
        else:
            log_send_hostname = GlobalBaseLogSendHostname.from_dict(_log_send_hostname)

        _lua_options = d.pop("lua_options", UNSET)
        lua_options: Union[Unset, LuaOptions]
        if isinstance(_lua_options, Unset):
            lua_options = UNSET
        else:
            lua_options = LuaOptions.from_dict(_lua_options)

        master_worker = d.pop("master-worker", UNSET)

        metadata = d.pop("metadata", UNSET)

        def _parse_mworker_max_reloads(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        mworker_max_reloads = _parse_mworker_max_reloads(d.pop("mworker_max_reloads", UNSET))

        nbthread = d.pop("nbthread", UNSET)

        no_quic = d.pop("no_quic", UNSET)

        node = d.pop("node", UNSET)

        _numa_cpu_mapping = d.pop("numa_cpu_mapping", UNSET)
        numa_cpu_mapping: Union[Unset, GlobalBaseNumaCpuMapping]
        if isinstance(_numa_cpu_mapping, Unset):
            numa_cpu_mapping = UNSET
        else:
            numa_cpu_mapping = GlobalBaseNumaCpuMapping(_numa_cpu_mapping)

        _ocsp_update_options = d.pop("ocsp_update_options", UNSET)
        ocsp_update_options: Union[Unset, OcspUpdateOptions]
        if isinstance(_ocsp_update_options, Unset):
            ocsp_update_options = UNSET
        else:
            ocsp_update_options = OcspUpdateOptions.from_dict(_ocsp_update_options)

        _performance_options = d.pop("performance_options", UNSET)
        performance_options: Union[Unset, PerformanceOptions]
        if isinstance(_performance_options, Unset):
            performance_options = UNSET
        else:
            performance_options = PerformanceOptions.from_dict(_performance_options)

        pidfile = d.pop("pidfile", UNSET)

        pp2_never_send_local = d.pop("pp2_never_send_local", UNSET)

        prealloc_fd = d.pop("prealloc_fd", UNSET)

        runtime_apis = []
        _runtime_apis = d.pop("runtime_apis", UNSET)
        for runtime_apis_item_data in _runtime_apis or []:
            runtime_apis_item = GlobalBaseRuntimeApisItem.from_dict(runtime_apis_item_data)

            runtime_apis.append(runtime_apis_item)

        set_dumpable = d.pop("set_dumpable", UNSET)

        set_var = []
        _set_var = d.pop("set_var", UNSET)
        for set_var_item_data in _set_var or []:
            set_var_item = GlobalBaseSetVarItem.from_dict(set_var_item_data)

            set_var.append(set_var_item)

        set_var_fmt = []
        _set_var_fmt = d.pop("set_var_fmt", UNSET)
        for set_var_fmt_item_data in _set_var_fmt or []:
            set_var_fmt_item = GlobalBaseSetVarFmtItem.from_dict(set_var_fmt_item_data)

            set_var_fmt.append(set_var_fmt_item)

        setcap = d.pop("setcap", UNSET)

        _ssl_options = d.pop("ssl_options", UNSET)
        ssl_options: Union[Unset, SslOptions]
        if isinstance(_ssl_options, Unset):
            ssl_options = UNSET
        else:
            ssl_options = SslOptions.from_dict(_ssl_options)

        stats_file = d.pop("stats_file", UNSET)

        def _parse_stats_maxconn(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        stats_maxconn = _parse_stats_maxconn(d.pop("stats_maxconn", UNSET))

        def _parse_stats_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        stats_timeout = _parse_stats_timeout(d.pop("stats_timeout", UNSET))

        strict_limits = d.pop("strict_limits", UNSET)

        thread_group_lines = []
        _thread_group_lines = d.pop("thread_group_lines", UNSET)
        for thread_group_lines_item_data in _thread_group_lines or []:
            thread_group_lines_item = GlobalBaseThreadGroupLinesItem.from_dict(thread_group_lines_item_data)

            thread_group_lines.append(thread_group_lines_item)

        thread_groups = d.pop("thread_groups", UNSET)

        _tune_buffer_options = d.pop("tune_buffer_options", UNSET)
        tune_buffer_options: Union[Unset, TuneBufferOptions]
        if isinstance(_tune_buffer_options, Unset):
            tune_buffer_options = UNSET
        else:
            tune_buffer_options = TuneBufferOptions.from_dict(_tune_buffer_options)

        _tune_lua_options = d.pop("tune_lua_options", UNSET)
        tune_lua_options: Union[Unset, TuneLuaOptions]
        if isinstance(_tune_lua_options, Unset):
            tune_lua_options = UNSET
        else:
            tune_lua_options = TuneLuaOptions.from_dict(_tune_lua_options)

        _tune_options = d.pop("tune_options", UNSET)
        tune_options: Union[Unset, TuneOptions]
        if isinstance(_tune_options, Unset):
            tune_options = UNSET
        else:
            tune_options = TuneOptions.from_dict(_tune_options)

        _tune_quic_options = d.pop("tune_quic_options", UNSET)
        tune_quic_options: Union[Unset, TuneQuicOptions]
        if isinstance(_tune_quic_options, Unset):
            tune_quic_options = UNSET
        else:
            tune_quic_options = TuneQuicOptions.from_dict(_tune_quic_options)

        _tune_ssl_options = d.pop("tune_ssl_options", UNSET)
        tune_ssl_options: Union[Unset, TuneSslOptions]
        if isinstance(_tune_ssl_options, Unset):
            tune_ssl_options = UNSET
        else:
            tune_ssl_options = TuneSslOptions.from_dict(_tune_ssl_options)

        _tune_vars_options = d.pop("tune_vars_options", UNSET)
        tune_vars_options: Union[Unset, TuneVarsOptions]
        if isinstance(_tune_vars_options, Unset):
            tune_vars_options = UNSET
        else:
            tune_vars_options = TuneVarsOptions.from_dict(_tune_vars_options)

        _tune_zlib_options = d.pop("tune_zlib_options", UNSET)
        tune_zlib_options: Union[Unset, TuneZlibOptions]
        if isinstance(_tune_zlib_options, Unset):
            tune_zlib_options = UNSET
        else:
            tune_zlib_options = TuneZlibOptions.from_dict(_tune_zlib_options)

        uid = d.pop("uid", UNSET)

        ulimit_n = d.pop("ulimit_n", UNSET)

        user = d.pop("user", UNSET)

        def _parse_warn_blocked_traffic_after(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        warn_blocked_traffic_after = _parse_warn_blocked_traffic_after(d.pop("warn_blocked_traffic_after", UNSET))

        _wurfl_options = d.pop("wurfl_options", UNSET)
        wurfl_options: Union[Unset, WurflOptions]
        if isinstance(_wurfl_options, Unset):
            wurfl_options = UNSET
        else:
            wurfl_options = WurflOptions.from_dict(_wurfl_options)

        global_base = cls(
            chroot=chroot,
            close_spread_time=close_spread_time,
            cluster_secret=cluster_secret,
            cpu_maps=cpu_maps,
            cpu_policy=cpu_policy,
            cpu_set=cpu_set,
            daemon=daemon,
            debug_options=debug_options,
            default_path=default_path,
            description=description,
            device_atlas_options=device_atlas_options,
            dns_accept_family=dns_accept_family,
            environment_options=environment_options,
            expose_deprecated_directives=expose_deprecated_directives,
            expose_experimental_directives=expose_experimental_directives,
            external_check=external_check,
            fifty_one_degrees_options=fifty_one_degrees_options,
            force_cfg_parser_pause=force_cfg_parser_pause,
            gid=gid,
            grace=grace,
            group=group,
            h1_accept_payload_with_any_method=h1_accept_payload_with_any_method,
            h1_case_adjust=h1_case_adjust,
            h1_case_adjust_file=h1_case_adjust_file,
            h1_do_not_close_on_insecure_transfer_encoding=h1_do_not_close_on_insecure_transfer_encoding,
            h2_workaround_bogus_websocket_clients=h2_workaround_bogus_websocket_clients,
            hard_stop_after=hard_stop_after,
            harden=harden,
            http_client_options=http_client_options,
            http_err_codes=http_err_codes,
            http_fail_codes=http_fail_codes,
            insecure_fork_wanted=insecure_fork_wanted,
            insecure_setuid_wanted=insecure_setuid_wanted,
            limited_quic=limited_quic,
            localpeer=localpeer,
            log_send_hostname=log_send_hostname,
            lua_options=lua_options,
            master_worker=master_worker,
            metadata=metadata,
            mworker_max_reloads=mworker_max_reloads,
            nbthread=nbthread,
            no_quic=no_quic,
            node=node,
            numa_cpu_mapping=numa_cpu_mapping,
            ocsp_update_options=ocsp_update_options,
            performance_options=performance_options,
            pidfile=pidfile,
            pp2_never_send_local=pp2_never_send_local,
            prealloc_fd=prealloc_fd,
            runtime_apis=runtime_apis,
            set_dumpable=set_dumpable,
            set_var=set_var,
            set_var_fmt=set_var_fmt,
            setcap=setcap,
            ssl_options=ssl_options,
            stats_file=stats_file,
            stats_maxconn=stats_maxconn,
            stats_timeout=stats_timeout,
            strict_limits=strict_limits,
            thread_group_lines=thread_group_lines,
            thread_groups=thread_groups,
            tune_buffer_options=tune_buffer_options,
            tune_lua_options=tune_lua_options,
            tune_options=tune_options,
            tune_quic_options=tune_quic_options,
            tune_ssl_options=tune_ssl_options,
            tune_vars_options=tune_vars_options,
            tune_zlib_options=tune_zlib_options,
            uid=uid,
            ulimit_n=ulimit_n,
            user=user,
            warn_blocked_traffic_after=warn_blocked_traffic_after,
            wurfl_options=wurfl_options,
        )

        return global_base
