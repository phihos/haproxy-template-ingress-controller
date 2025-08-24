from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.frontend_base_accept_invalid_http_request import FrontendBaseAcceptInvalidHttpRequest
from ..models.frontend_base_accept_unsafe_violations_in_http_request import (
    FrontendBaseAcceptUnsafeViolationsInHttpRequest,
)
from ..models.frontend_base_clitcpka import FrontendBaseClitcpka
from ..models.frontend_base_contstats import FrontendBaseContstats
from ..models.frontend_base_disable_h2_upgrade import FrontendBaseDisableH2Upgrade
from ..models.frontend_base_dontlog_normal import FrontendBaseDontlogNormal
from ..models.frontend_base_dontlognull import FrontendBaseDontlognull
from ..models.frontend_base_h1_case_adjust_bogus_client import FrontendBaseH1CaseAdjustBogusClient
from ..models.frontend_base_http_buffer_request import FrontendBaseHttpBufferRequest
from ..models.frontend_base_http_connection_mode import FrontendBaseHttpConnectionMode
from ..models.frontend_base_http_drop_response_trailers import FrontendBaseHttpDropResponseTrailers
from ..models.frontend_base_http_ignore_probes import FrontendBaseHttpIgnoreProbes
from ..models.frontend_base_http_no_delay import FrontendBaseHttpNoDelay
from ..models.frontend_base_http_restrict_req_hdr_names import FrontendBaseHttpRestrictReqHdrNames
from ..models.frontend_base_http_use_htx import FrontendBaseHttpUseHtx
from ..models.frontend_base_http_use_proxy_header import FrontendBaseHttpUseProxyHeader
from ..models.frontend_base_httpslog import FrontendBaseHttpslog
from ..models.frontend_base_idle_close_on_response import FrontendBaseIdleCloseOnResponse
from ..models.frontend_base_independent_streams import FrontendBaseIndependentStreams
from ..models.frontend_base_log_separate_errors import FrontendBaseLogSeparateErrors
from ..models.frontend_base_log_steps_item import FrontendBaseLogStepsItem
from ..models.frontend_base_logasap import FrontendBaseLogasap
from ..models.frontend_base_mode import FrontendBaseMode
from ..models.frontend_base_nolinger import FrontendBaseNolinger
from ..models.frontend_base_socket_stats import FrontendBaseSocketStats
from ..models.frontend_base_splice_auto import FrontendBaseSpliceAuto
from ..models.frontend_base_splice_request import FrontendBaseSpliceRequest
from ..models.frontend_base_splice_response import FrontendBaseSpliceResponse
from ..models.frontend_base_tcp_smart_accept import FrontendBaseTcpSmartAccept
from ..models.frontend_base_tcpka import FrontendBaseTcpka
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.acl_lines import ACLLines
    from ..models.backend_switching_rule import BackendSwitchingRule
    from ..models.compression import Compression
    from ..models.config_stick_table import ConfigStickTable
    from ..models.declare_capture import DeclareCapture
    from ..models.email_alert import EmailAlert
    from ..models.errorfile import Errorfile
    from ..models.errorfiles import Errorfiles
    from ..models.errorloc import Errorloc
    from ..models.filter_ import Filter
    from ..models.forwardfor import Forwardfor
    from ..models.http_after_response_rule import HTTPAfterResponseRule
    from ..models.http_error_rule import HTTPErrorRule
    from ..models.http_request_rule import HTTPRequestRule
    from ..models.http_response_rule import HTTPResponseRule
    from ..models.log_target import LogTarget
    from ..models.monitor_fail import MonitorFail
    from ..models.originalto import Originalto
    from ..models.quic_initial import QUICInitial
    from ..models.ssl_frontend_use_certificate import SSLFrontendUseCertificate
    from ..models.stats_options import StatsOptions
    from ..models.tcp_request_rule import TCPRequestRule


T = TypeVar("T", bound="Frontend")


@_attrs_define
class Frontend:
    """Frontend with all it's children resources

    Attributes:
        name (str):
        accept_invalid_http_request (Union[Unset, FrontendBaseAcceptInvalidHttpRequest]):
        accept_unsafe_violations_in_http_request (Union[Unset, FrontendBaseAcceptUnsafeViolationsInHttpRequest]):
        backlog (Union[None, Unset, int]):
        clflog (Union[Unset, bool]):
        client_fin_timeout (Union[None, Unset, int]):
        client_timeout (Union[None, Unset, int]):
        clitcpka (Union[Unset, FrontendBaseClitcpka]):
        clitcpka_cnt (Union[None, Unset, int]):
        clitcpka_idle (Union[None, Unset, int]):
        clitcpka_intvl (Union[None, Unset, int]):
        compression (Union[Unset, Compression]):
        contstats (Union[Unset, FrontendBaseContstats]):
        default_backend (Union[Unset, str]):
        description (Union[Unset, str]):
        disable_h2_upgrade (Union[Unset, FrontendBaseDisableH2Upgrade]):
        disabled (Union[Unset, bool]):
        dontlog_normal (Union[Unset, FrontendBaseDontlogNormal]):
        dontlognull (Union[Unset, FrontendBaseDontlognull]):
        email_alert (Union[Unset, EmailAlert]): Send emails for important log messages.
        enabled (Union[Unset, bool]):
        error_files (Union[Unset, list['Errorfile']]):
        error_log_format (Union[Unset, str]):
        errorfiles_from_http_errors (Union[Unset, list['Errorfiles']]):
        errorloc302 (Union[Unset, Errorloc]):
        errorloc303 (Union[Unset, Errorloc]):
        forwardfor (Union[Unset, Forwardfor]):
        from_ (Union[Unset, str]):
        guid (Union[Unset, str]):
        h1_case_adjust_bogus_client (Union[Unset, FrontendBaseH1CaseAdjustBogusClient]):
        http_buffer_request (Union[Unset, FrontendBaseHttpBufferRequest]):
        http_drop_response_trailers (Union[Unset, FrontendBaseHttpDropResponseTrailers]):
        http_use_htx (Union[Unset, FrontendBaseHttpUseHtx]):
        http_connection_mode (Union[Unset, FrontendBaseHttpConnectionMode]):
        http_ignore_probes (Union[Unset, FrontendBaseHttpIgnoreProbes]):
        http_keep_alive_timeout (Union[None, Unset, int]):
        http_no_delay (Union[Unset, FrontendBaseHttpNoDelay]):
        http_request_timeout (Union[None, Unset, int]):
        http_restrict_req_hdr_names (Union[Unset, FrontendBaseHttpRestrictReqHdrNames]):
        http_use_proxy_header (Union[Unset, FrontendBaseHttpUseProxyHeader]):
        httplog (Union[Unset, bool]):
        httpslog (Union[Unset, FrontendBaseHttpslog]):
        id (Union[None, Unset, int]):
        idle_close_on_response (Union[Unset, FrontendBaseIdleCloseOnResponse]):
        independent_streams (Union[Unset, FrontendBaseIndependentStreams]):
        log_format (Union[Unset, str]):
        log_format_sd (Union[Unset, str]):
        log_separate_errors (Union[Unset, FrontendBaseLogSeparateErrors]):
        log_steps (Union[Unset, list[FrontendBaseLogStepsItem]]):
        log_tag (Union[Unset, str]):
        logasap (Union[Unset, FrontendBaseLogasap]):
        maxconn (Union[None, Unset, int]):
        metadata (Union[Unset, Any]):
        mode (Union[Unset, FrontendBaseMode]):
        monitor_fail (Union[Unset, MonitorFail]):
        monitor_uri (Union[Unset, str]):
        nolinger (Union[Unset, FrontendBaseNolinger]):
        originalto (Union[Unset, Originalto]):
        socket_stats (Union[Unset, FrontendBaseSocketStats]):
        splice_auto (Union[Unset, FrontendBaseSpliceAuto]):
        splice_request (Union[Unset, FrontendBaseSpliceRequest]):
        splice_response (Union[Unset, FrontendBaseSpliceResponse]):
        stats_options (Union[Unset, StatsOptions]):
        stick_table (Union[Unset, ConfigStickTable]):
        tarpit_timeout (Union[None, Unset, int]):
        tcp_smart_accept (Union[Unset, FrontendBaseTcpSmartAccept]):
        tcpka (Union[Unset, FrontendBaseTcpka]):
        tcplog (Union[Unset, bool]):
        unique_id_format (Union[Unset, str]):
        unique_id_header (Union[Unset, str]):
        acl_list (Union[Unset, list['ACLLines']]): HAProxy ACL lines array (corresponds to acl directives)
        backend_switching_rule_list (Union[Unset, list['BackendSwitchingRule']]): HAProxy backend switching rules array
            (corresponds to use_backend directives)
        binds (Union[Unset, Any]):
        capture_list (Union[Unset, list['DeclareCapture']]):
        filter_list (Union[Unset, list['Filter']]): HAProxy filters array (corresponds to filter directive)
        http_after_response_rule_list (Union[Unset, list['HTTPAfterResponseRule']]): HAProxy HTTP after response rules
            array (corresponds to http-after-response directives)
        http_error_rule_list (Union[Unset, list['HTTPErrorRule']]): HAProxy HTTP error rules array (corresponds to http-
            error directives)
        http_request_rule_list (Union[Unset, list['HTTPRequestRule']]): HAProxy HTTP request rules array (corresponds to
            http-request directives)
        http_response_rule_list (Union[Unset, list['HTTPResponseRule']]): HAProxy HTTP response rules array (corresponds
            to http-response directives)
        log_target_list (Union[Unset, list['LogTarget']]): HAProxy log target array (corresponds to log directives)
        quic_initial_rule_list (Union[Unset, list['QUICInitial']]):
        ssl_front_use_list (Union[Unset, list['SSLFrontendUseCertificate']]):
        tcp_request_rule_list (Union[Unset, list['TCPRequestRule']]): HAProxy TCP request rules array (corresponds to
            tcp-request directive)
    """

    name: str
    accept_invalid_http_request: Union[Unset, FrontendBaseAcceptInvalidHttpRequest] = UNSET
    accept_unsafe_violations_in_http_request: Union[Unset, FrontendBaseAcceptUnsafeViolationsInHttpRequest] = UNSET
    backlog: Union[None, Unset, int] = UNSET
    clflog: Union[Unset, bool] = UNSET
    client_fin_timeout: Union[None, Unset, int] = UNSET
    client_timeout: Union[None, Unset, int] = UNSET
    clitcpka: Union[Unset, FrontendBaseClitcpka] = UNSET
    clitcpka_cnt: Union[None, Unset, int] = UNSET
    clitcpka_idle: Union[None, Unset, int] = UNSET
    clitcpka_intvl: Union[None, Unset, int] = UNSET
    compression: Union[Unset, "Compression"] = UNSET
    contstats: Union[Unset, FrontendBaseContstats] = UNSET
    default_backend: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    disable_h2_upgrade: Union[Unset, FrontendBaseDisableH2Upgrade] = UNSET
    disabled: Union[Unset, bool] = UNSET
    dontlog_normal: Union[Unset, FrontendBaseDontlogNormal] = UNSET
    dontlognull: Union[Unset, FrontendBaseDontlognull] = UNSET
    email_alert: Union[Unset, "EmailAlert"] = UNSET
    enabled: Union[Unset, bool] = UNSET
    error_files: Union[Unset, list["Errorfile"]] = UNSET
    error_log_format: Union[Unset, str] = UNSET
    errorfiles_from_http_errors: Union[Unset, list["Errorfiles"]] = UNSET
    errorloc302: Union[Unset, "Errorloc"] = UNSET
    errorloc303: Union[Unset, "Errorloc"] = UNSET
    forwardfor: Union[Unset, "Forwardfor"] = UNSET
    from_: Union[Unset, str] = UNSET
    guid: Union[Unset, str] = UNSET
    h1_case_adjust_bogus_client: Union[Unset, FrontendBaseH1CaseAdjustBogusClient] = UNSET
    http_buffer_request: Union[Unset, FrontendBaseHttpBufferRequest] = UNSET
    http_drop_response_trailers: Union[Unset, FrontendBaseHttpDropResponseTrailers] = UNSET
    http_use_htx: Union[Unset, FrontendBaseHttpUseHtx] = UNSET
    http_connection_mode: Union[Unset, FrontendBaseHttpConnectionMode] = UNSET
    http_ignore_probes: Union[Unset, FrontendBaseHttpIgnoreProbes] = UNSET
    http_keep_alive_timeout: Union[None, Unset, int] = UNSET
    http_no_delay: Union[Unset, FrontendBaseHttpNoDelay] = UNSET
    http_request_timeout: Union[None, Unset, int] = UNSET
    http_restrict_req_hdr_names: Union[Unset, FrontendBaseHttpRestrictReqHdrNames] = UNSET
    http_use_proxy_header: Union[Unset, FrontendBaseHttpUseProxyHeader] = UNSET
    httplog: Union[Unset, bool] = UNSET
    httpslog: Union[Unset, FrontendBaseHttpslog] = UNSET
    id: Union[None, Unset, int] = UNSET
    idle_close_on_response: Union[Unset, FrontendBaseIdleCloseOnResponse] = UNSET
    independent_streams: Union[Unset, FrontendBaseIndependentStreams] = UNSET
    log_format: Union[Unset, str] = UNSET
    log_format_sd: Union[Unset, str] = UNSET
    log_separate_errors: Union[Unset, FrontendBaseLogSeparateErrors] = UNSET
    log_steps: Union[Unset, list[FrontendBaseLogStepsItem]] = UNSET
    log_tag: Union[Unset, str] = UNSET
    logasap: Union[Unset, FrontendBaseLogasap] = UNSET
    maxconn: Union[None, Unset, int] = UNSET
    metadata: Union[Unset, Any] = UNSET
    mode: Union[Unset, FrontendBaseMode] = UNSET
    monitor_fail: Union[Unset, "MonitorFail"] = UNSET
    monitor_uri: Union[Unset, str] = UNSET
    nolinger: Union[Unset, FrontendBaseNolinger] = UNSET
    originalto: Union[Unset, "Originalto"] = UNSET
    socket_stats: Union[Unset, FrontendBaseSocketStats] = UNSET
    splice_auto: Union[Unset, FrontendBaseSpliceAuto] = UNSET
    splice_request: Union[Unset, FrontendBaseSpliceRequest] = UNSET
    splice_response: Union[Unset, FrontendBaseSpliceResponse] = UNSET
    stats_options: Union[Unset, "StatsOptions"] = UNSET
    stick_table: Union[Unset, "ConfigStickTable"] = UNSET
    tarpit_timeout: Union[None, Unset, int] = UNSET
    tcp_smart_accept: Union[Unset, FrontendBaseTcpSmartAccept] = UNSET
    tcpka: Union[Unset, FrontendBaseTcpka] = UNSET
    tcplog: Union[Unset, bool] = UNSET
    unique_id_format: Union[Unset, str] = UNSET
    unique_id_header: Union[Unset, str] = UNSET
    acl_list: Union[Unset, list["ACLLines"]] = UNSET
    backend_switching_rule_list: Union[Unset, list["BackendSwitchingRule"]] = UNSET
    binds: Union[Unset, Any] = UNSET
    capture_list: Union[Unset, list["DeclareCapture"]] = UNSET
    filter_list: Union[Unset, list["Filter"]] = UNSET
    http_after_response_rule_list: Union[Unset, list["HTTPAfterResponseRule"]] = UNSET
    http_error_rule_list: Union[Unset, list["HTTPErrorRule"]] = UNSET
    http_request_rule_list: Union[Unset, list["HTTPRequestRule"]] = UNSET
    http_response_rule_list: Union[Unset, list["HTTPResponseRule"]] = UNSET
    log_target_list: Union[Unset, list["LogTarget"]] = UNSET
    quic_initial_rule_list: Union[Unset, list["QUICInitial"]] = UNSET
    ssl_front_use_list: Union[Unset, list["SSLFrontendUseCertificate"]] = UNSET
    tcp_request_rule_list: Union[Unset, list["TCPRequestRule"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        accept_invalid_http_request: Union[Unset, str] = UNSET
        if not isinstance(self.accept_invalid_http_request, Unset):
            accept_invalid_http_request = self.accept_invalid_http_request.value

        accept_unsafe_violations_in_http_request: Union[Unset, str] = UNSET
        if not isinstance(self.accept_unsafe_violations_in_http_request, Unset):
            accept_unsafe_violations_in_http_request = self.accept_unsafe_violations_in_http_request.value

        backlog: Union[None, Unset, int]
        if isinstance(self.backlog, Unset):
            backlog = UNSET
        else:
            backlog = self.backlog

        clflog = self.clflog

        client_fin_timeout: Union[None, Unset, int]
        if isinstance(self.client_fin_timeout, Unset):
            client_fin_timeout = UNSET
        else:
            client_fin_timeout = self.client_fin_timeout

        client_timeout: Union[None, Unset, int]
        if isinstance(self.client_timeout, Unset):
            client_timeout = UNSET
        else:
            client_timeout = self.client_timeout

        clitcpka: Union[Unset, str] = UNSET
        if not isinstance(self.clitcpka, Unset):
            clitcpka = self.clitcpka.value

        clitcpka_cnt: Union[None, Unset, int]
        if isinstance(self.clitcpka_cnt, Unset):
            clitcpka_cnt = UNSET
        else:
            clitcpka_cnt = self.clitcpka_cnt

        clitcpka_idle: Union[None, Unset, int]
        if isinstance(self.clitcpka_idle, Unset):
            clitcpka_idle = UNSET
        else:
            clitcpka_idle = self.clitcpka_idle

        clitcpka_intvl: Union[None, Unset, int]
        if isinstance(self.clitcpka_intvl, Unset):
            clitcpka_intvl = UNSET
        else:
            clitcpka_intvl = self.clitcpka_intvl

        compression: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.compression, Unset):
            compression = self.compression.to_dict()

        contstats: Union[Unset, str] = UNSET
        if not isinstance(self.contstats, Unset):
            contstats = self.contstats.value

        default_backend = self.default_backend

        description = self.description

        disable_h2_upgrade: Union[Unset, str] = UNSET
        if not isinstance(self.disable_h2_upgrade, Unset):
            disable_h2_upgrade = self.disable_h2_upgrade.value

        disabled = self.disabled

        dontlog_normal: Union[Unset, str] = UNSET
        if not isinstance(self.dontlog_normal, Unset):
            dontlog_normal = self.dontlog_normal.value

        dontlognull: Union[Unset, str] = UNSET
        if not isinstance(self.dontlognull, Unset):
            dontlognull = self.dontlognull.value

        email_alert: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.email_alert, Unset):
            email_alert = self.email_alert.to_dict()

        enabled = self.enabled

        error_files: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.error_files, Unset):
            error_files = []
            for error_files_item_data in self.error_files:
                error_files_item = error_files_item_data.to_dict()
                error_files.append(error_files_item)

        error_log_format = self.error_log_format

        errorfiles_from_http_errors: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.errorfiles_from_http_errors, Unset):
            errorfiles_from_http_errors = []
            for errorfiles_from_http_errors_item_data in self.errorfiles_from_http_errors:
                errorfiles_from_http_errors_item = errorfiles_from_http_errors_item_data.to_dict()
                errorfiles_from_http_errors.append(errorfiles_from_http_errors_item)

        errorloc302: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.errorloc302, Unset):
            errorloc302 = self.errorloc302.to_dict()

        errorloc303: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.errorloc303, Unset):
            errorloc303 = self.errorloc303.to_dict()

        forwardfor: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.forwardfor, Unset):
            forwardfor = self.forwardfor.to_dict()

        from_ = self.from_

        guid = self.guid

        h1_case_adjust_bogus_client: Union[Unset, str] = UNSET
        if not isinstance(self.h1_case_adjust_bogus_client, Unset):
            h1_case_adjust_bogus_client = self.h1_case_adjust_bogus_client.value

        http_buffer_request: Union[Unset, str] = UNSET
        if not isinstance(self.http_buffer_request, Unset):
            http_buffer_request = self.http_buffer_request.value

        http_drop_response_trailers: Union[Unset, str] = UNSET
        if not isinstance(self.http_drop_response_trailers, Unset):
            http_drop_response_trailers = self.http_drop_response_trailers.value

        http_use_htx: Union[Unset, str] = UNSET
        if not isinstance(self.http_use_htx, Unset):
            http_use_htx = self.http_use_htx.value

        http_connection_mode: Union[Unset, str] = UNSET
        if not isinstance(self.http_connection_mode, Unset):
            http_connection_mode = self.http_connection_mode.value

        http_ignore_probes: Union[Unset, str] = UNSET
        if not isinstance(self.http_ignore_probes, Unset):
            http_ignore_probes = self.http_ignore_probes.value

        http_keep_alive_timeout: Union[None, Unset, int]
        if isinstance(self.http_keep_alive_timeout, Unset):
            http_keep_alive_timeout = UNSET
        else:
            http_keep_alive_timeout = self.http_keep_alive_timeout

        http_no_delay: Union[Unset, str] = UNSET
        if not isinstance(self.http_no_delay, Unset):
            http_no_delay = self.http_no_delay.value

        http_request_timeout: Union[None, Unset, int]
        if isinstance(self.http_request_timeout, Unset):
            http_request_timeout = UNSET
        else:
            http_request_timeout = self.http_request_timeout

        http_restrict_req_hdr_names: Union[Unset, str] = UNSET
        if not isinstance(self.http_restrict_req_hdr_names, Unset):
            http_restrict_req_hdr_names = self.http_restrict_req_hdr_names.value

        http_use_proxy_header: Union[Unset, str] = UNSET
        if not isinstance(self.http_use_proxy_header, Unset):
            http_use_proxy_header = self.http_use_proxy_header.value

        httplog = self.httplog

        httpslog: Union[Unset, str] = UNSET
        if not isinstance(self.httpslog, Unset):
            httpslog = self.httpslog.value

        id: Union[None, Unset, int]
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        idle_close_on_response: Union[Unset, str] = UNSET
        if not isinstance(self.idle_close_on_response, Unset):
            idle_close_on_response = self.idle_close_on_response.value

        independent_streams: Union[Unset, str] = UNSET
        if not isinstance(self.independent_streams, Unset):
            independent_streams = self.independent_streams.value

        log_format = self.log_format

        log_format_sd = self.log_format_sd

        log_separate_errors: Union[Unset, str] = UNSET
        if not isinstance(self.log_separate_errors, Unset):
            log_separate_errors = self.log_separate_errors.value

        log_steps: Union[Unset, list[str]] = UNSET
        if not isinstance(self.log_steps, Unset):
            log_steps = []
            for log_steps_item_data in self.log_steps:
                log_steps_item = log_steps_item_data.value
                log_steps.append(log_steps_item)

        log_tag = self.log_tag

        logasap: Union[Unset, str] = UNSET
        if not isinstance(self.logasap, Unset):
            logasap = self.logasap.value

        maxconn: Union[None, Unset, int]
        if isinstance(self.maxconn, Unset):
            maxconn = UNSET
        else:
            maxconn = self.maxconn

        metadata = self.metadata

        mode: Union[Unset, str] = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        monitor_fail: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.monitor_fail, Unset):
            monitor_fail = self.monitor_fail.to_dict()

        monitor_uri = self.monitor_uri

        nolinger: Union[Unset, str] = UNSET
        if not isinstance(self.nolinger, Unset):
            nolinger = self.nolinger.value

        originalto: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.originalto, Unset):
            originalto = self.originalto.to_dict()

        socket_stats: Union[Unset, str] = UNSET
        if not isinstance(self.socket_stats, Unset):
            socket_stats = self.socket_stats.value

        splice_auto: Union[Unset, str] = UNSET
        if not isinstance(self.splice_auto, Unset):
            splice_auto = self.splice_auto.value

        splice_request: Union[Unset, str] = UNSET
        if not isinstance(self.splice_request, Unset):
            splice_request = self.splice_request.value

        splice_response: Union[Unset, str] = UNSET
        if not isinstance(self.splice_response, Unset):
            splice_response = self.splice_response.value

        stats_options: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.stats_options, Unset):
            stats_options = self.stats_options.to_dict()

        stick_table: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.stick_table, Unset):
            stick_table = self.stick_table.to_dict()

        tarpit_timeout: Union[None, Unset, int]
        if isinstance(self.tarpit_timeout, Unset):
            tarpit_timeout = UNSET
        else:
            tarpit_timeout = self.tarpit_timeout

        tcp_smart_accept: Union[Unset, str] = UNSET
        if not isinstance(self.tcp_smart_accept, Unset):
            tcp_smart_accept = self.tcp_smart_accept.value

        tcpka: Union[Unset, str] = UNSET
        if not isinstance(self.tcpka, Unset):
            tcpka = self.tcpka.value

        tcplog = self.tcplog

        unique_id_format = self.unique_id_format

        unique_id_header = self.unique_id_header

        acl_list: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.acl_list, Unset):
            acl_list = []
            for componentsschemasacls_item_data in self.acl_list:
                componentsschemasacls_item = componentsschemasacls_item_data.to_dict()
                acl_list.append(componentsschemasacls_item)

        backend_switching_rule_list: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.backend_switching_rule_list, Unset):
            backend_switching_rule_list = []
            for componentsschemasbackend_switching_rules_item_data in self.backend_switching_rule_list:
                componentsschemasbackend_switching_rules_item = (
                    componentsschemasbackend_switching_rules_item_data.to_dict()
                )
                backend_switching_rule_list.append(componentsschemasbackend_switching_rules_item)

        binds = self.binds

        capture_list: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.capture_list, Unset):
            capture_list = []
            for componentsschemascaptures_item_data in self.capture_list:
                componentsschemascaptures_item = componentsschemascaptures_item_data.to_dict()
                capture_list.append(componentsschemascaptures_item)

        filter_list: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.filter_list, Unset):
            filter_list = []
            for componentsschemasfilters_item_data in self.filter_list:
                componentsschemasfilters_item = componentsschemasfilters_item_data.to_dict()
                filter_list.append(componentsschemasfilters_item)

        http_after_response_rule_list: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.http_after_response_rule_list, Unset):
            http_after_response_rule_list = []
            for componentsschemashttp_after_response_rules_item_data in self.http_after_response_rule_list:
                componentsschemashttp_after_response_rules_item = (
                    componentsschemashttp_after_response_rules_item_data.to_dict()
                )
                http_after_response_rule_list.append(componentsschemashttp_after_response_rules_item)

        http_error_rule_list: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.http_error_rule_list, Unset):
            http_error_rule_list = []
            for componentsschemashttp_error_rules_item_data in self.http_error_rule_list:
                componentsschemashttp_error_rules_item = componentsschemashttp_error_rules_item_data.to_dict()
                http_error_rule_list.append(componentsschemashttp_error_rules_item)

        http_request_rule_list: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.http_request_rule_list, Unset):
            http_request_rule_list = []
            for componentsschemashttp_request_rules_item_data in self.http_request_rule_list:
                componentsschemashttp_request_rules_item = componentsschemashttp_request_rules_item_data.to_dict()
                http_request_rule_list.append(componentsschemashttp_request_rules_item)

        http_response_rule_list: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.http_response_rule_list, Unset):
            http_response_rule_list = []
            for componentsschemashttp_response_rules_item_data in self.http_response_rule_list:
                componentsschemashttp_response_rules_item = componentsschemashttp_response_rules_item_data.to_dict()
                http_response_rule_list.append(componentsschemashttp_response_rules_item)

        log_target_list: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.log_target_list, Unset):
            log_target_list = []
            for componentsschemaslog_targets_item_data in self.log_target_list:
                componentsschemaslog_targets_item = componentsschemaslog_targets_item_data.to_dict()
                log_target_list.append(componentsschemaslog_targets_item)

        quic_initial_rule_list: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.quic_initial_rule_list, Unset):
            quic_initial_rule_list = []
            for componentsschemasquic_initial_rules_item_data in self.quic_initial_rule_list:
                componentsschemasquic_initial_rules_item = componentsschemasquic_initial_rules_item_data.to_dict()
                quic_initial_rule_list.append(componentsschemasquic_initial_rules_item)

        ssl_front_use_list: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.ssl_front_use_list, Unset):
            ssl_front_use_list = []
            for componentsschemasssl_front_uses_item_data in self.ssl_front_use_list:
                componentsschemasssl_front_uses_item = componentsschemasssl_front_uses_item_data.to_dict()
                ssl_front_use_list.append(componentsschemasssl_front_uses_item)

        tcp_request_rule_list: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.tcp_request_rule_list, Unset):
            tcp_request_rule_list = []
            for componentsschemastcp_request_rules_item_data in self.tcp_request_rule_list:
                componentsschemastcp_request_rules_item = componentsschemastcp_request_rules_item_data.to_dict()
                tcp_request_rule_list.append(componentsschemastcp_request_rules_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if accept_invalid_http_request is not UNSET:
            field_dict["accept_invalid_http_request"] = accept_invalid_http_request
        if accept_unsafe_violations_in_http_request is not UNSET:
            field_dict["accept_unsafe_violations_in_http_request"] = accept_unsafe_violations_in_http_request
        if backlog is not UNSET:
            field_dict["backlog"] = backlog
        if clflog is not UNSET:
            field_dict["clflog"] = clflog
        if client_fin_timeout is not UNSET:
            field_dict["client_fin_timeout"] = client_fin_timeout
        if client_timeout is not UNSET:
            field_dict["client_timeout"] = client_timeout
        if clitcpka is not UNSET:
            field_dict["clitcpka"] = clitcpka
        if clitcpka_cnt is not UNSET:
            field_dict["clitcpka_cnt"] = clitcpka_cnt
        if clitcpka_idle is not UNSET:
            field_dict["clitcpka_idle"] = clitcpka_idle
        if clitcpka_intvl is not UNSET:
            field_dict["clitcpka_intvl"] = clitcpka_intvl
        if compression is not UNSET:
            field_dict["compression"] = compression
        if contstats is not UNSET:
            field_dict["contstats"] = contstats
        if default_backend is not UNSET:
            field_dict["default_backend"] = default_backend
        if description is not UNSET:
            field_dict["description"] = description
        if disable_h2_upgrade is not UNSET:
            field_dict["disable_h2_upgrade"] = disable_h2_upgrade
        if disabled is not UNSET:
            field_dict["disabled"] = disabled
        if dontlog_normal is not UNSET:
            field_dict["dontlog_normal"] = dontlog_normal
        if dontlognull is not UNSET:
            field_dict["dontlognull"] = dontlognull
        if email_alert is not UNSET:
            field_dict["email_alert"] = email_alert
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if error_files is not UNSET:
            field_dict["error_files"] = error_files
        if error_log_format is not UNSET:
            field_dict["error_log_format"] = error_log_format
        if errorfiles_from_http_errors is not UNSET:
            field_dict["errorfiles_from_http_errors"] = errorfiles_from_http_errors
        if errorloc302 is not UNSET:
            field_dict["errorloc302"] = errorloc302
        if errorloc303 is not UNSET:
            field_dict["errorloc303"] = errorloc303
        if forwardfor is not UNSET:
            field_dict["forwardfor"] = forwardfor
        if from_ is not UNSET:
            field_dict["from"] = from_
        if guid is not UNSET:
            field_dict["guid"] = guid
        if h1_case_adjust_bogus_client is not UNSET:
            field_dict["h1_case_adjust_bogus_client"] = h1_case_adjust_bogus_client
        if http_buffer_request is not UNSET:
            field_dict["http-buffer-request"] = http_buffer_request
        if http_drop_response_trailers is not UNSET:
            field_dict["http-drop-response-trailers"] = http_drop_response_trailers
        if http_use_htx is not UNSET:
            field_dict["http-use-htx"] = http_use_htx
        if http_connection_mode is not UNSET:
            field_dict["http_connection_mode"] = http_connection_mode
        if http_ignore_probes is not UNSET:
            field_dict["http_ignore_probes"] = http_ignore_probes
        if http_keep_alive_timeout is not UNSET:
            field_dict["http_keep_alive_timeout"] = http_keep_alive_timeout
        if http_no_delay is not UNSET:
            field_dict["http_no_delay"] = http_no_delay
        if http_request_timeout is not UNSET:
            field_dict["http_request_timeout"] = http_request_timeout
        if http_restrict_req_hdr_names is not UNSET:
            field_dict["http_restrict_req_hdr_names"] = http_restrict_req_hdr_names
        if http_use_proxy_header is not UNSET:
            field_dict["http_use_proxy_header"] = http_use_proxy_header
        if httplog is not UNSET:
            field_dict["httplog"] = httplog
        if httpslog is not UNSET:
            field_dict["httpslog"] = httpslog
        if id is not UNSET:
            field_dict["id"] = id
        if idle_close_on_response is not UNSET:
            field_dict["idle_close_on_response"] = idle_close_on_response
        if independent_streams is not UNSET:
            field_dict["independent_streams"] = independent_streams
        if log_format is not UNSET:
            field_dict["log_format"] = log_format
        if log_format_sd is not UNSET:
            field_dict["log_format_sd"] = log_format_sd
        if log_separate_errors is not UNSET:
            field_dict["log_separate_errors"] = log_separate_errors
        if log_steps is not UNSET:
            field_dict["log_steps"] = log_steps
        if log_tag is not UNSET:
            field_dict["log_tag"] = log_tag
        if logasap is not UNSET:
            field_dict["logasap"] = logasap
        if maxconn is not UNSET:
            field_dict["maxconn"] = maxconn
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if mode is not UNSET:
            field_dict["mode"] = mode
        if monitor_fail is not UNSET:
            field_dict["monitor_fail"] = monitor_fail
        if monitor_uri is not UNSET:
            field_dict["monitor_uri"] = monitor_uri
        if nolinger is not UNSET:
            field_dict["nolinger"] = nolinger
        if originalto is not UNSET:
            field_dict["originalto"] = originalto
        if socket_stats is not UNSET:
            field_dict["socket_stats"] = socket_stats
        if splice_auto is not UNSET:
            field_dict["splice_auto"] = splice_auto
        if splice_request is not UNSET:
            field_dict["splice_request"] = splice_request
        if splice_response is not UNSET:
            field_dict["splice_response"] = splice_response
        if stats_options is not UNSET:
            field_dict["stats_options"] = stats_options
        if stick_table is not UNSET:
            field_dict["stick_table"] = stick_table
        if tarpit_timeout is not UNSET:
            field_dict["tarpit_timeout"] = tarpit_timeout
        if tcp_smart_accept is not UNSET:
            field_dict["tcp_smart_accept"] = tcp_smart_accept
        if tcpka is not UNSET:
            field_dict["tcpka"] = tcpka
        if tcplog is not UNSET:
            field_dict["tcplog"] = tcplog
        if unique_id_format is not UNSET:
            field_dict["unique_id_format"] = unique_id_format
        if unique_id_header is not UNSET:
            field_dict["unique_id_header"] = unique_id_header
        if acl_list is not UNSET:
            field_dict["acl_list"] = acl_list
        if backend_switching_rule_list is not UNSET:
            field_dict["backend_switching_rule_list"] = backend_switching_rule_list
        if binds is not UNSET:
            field_dict["binds"] = binds
        if capture_list is not UNSET:
            field_dict["capture_list"] = capture_list
        if filter_list is not UNSET:
            field_dict["filter_list"] = filter_list
        if http_after_response_rule_list is not UNSET:
            field_dict["http_after_response_rule_list"] = http_after_response_rule_list
        if http_error_rule_list is not UNSET:
            field_dict["http_error_rule_list"] = http_error_rule_list
        if http_request_rule_list is not UNSET:
            field_dict["http_request_rule_list"] = http_request_rule_list
        if http_response_rule_list is not UNSET:
            field_dict["http_response_rule_list"] = http_response_rule_list
        if log_target_list is not UNSET:
            field_dict["log_target_list"] = log_target_list
        if quic_initial_rule_list is not UNSET:
            field_dict["quic_initial_rule_list"] = quic_initial_rule_list
        if ssl_front_use_list is not UNSET:
            field_dict["ssl_front_use_list"] = ssl_front_use_list
        if tcp_request_rule_list is not UNSET:
            field_dict["tcp_request_rule_list"] = tcp_request_rule_list

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.acl_lines import ACLLines
        from ..models.backend_switching_rule import BackendSwitchingRule
        from ..models.compression import Compression
        from ..models.config_stick_table import ConfigStickTable
        from ..models.declare_capture import DeclareCapture
        from ..models.email_alert import EmailAlert
        from ..models.errorfile import Errorfile
        from ..models.errorfiles import Errorfiles
        from ..models.errorloc import Errorloc
        from ..models.filter_ import Filter
        from ..models.forwardfor import Forwardfor
        from ..models.http_after_response_rule import HTTPAfterResponseRule
        from ..models.http_error_rule import HTTPErrorRule
        from ..models.http_request_rule import HTTPRequestRule
        from ..models.http_response_rule import HTTPResponseRule
        from ..models.log_target import LogTarget
        from ..models.monitor_fail import MonitorFail
        from ..models.originalto import Originalto
        from ..models.quic_initial import QUICInitial
        from ..models.ssl_frontend_use_certificate import SSLFrontendUseCertificate
        from ..models.stats_options import StatsOptions
        from ..models.tcp_request_rule import TCPRequestRule

        d = dict(src_dict)
        name = d.pop("name")

        _accept_invalid_http_request = d.pop("accept_invalid_http_request", UNSET)
        accept_invalid_http_request: Union[Unset, FrontendBaseAcceptInvalidHttpRequest]
        if isinstance(_accept_invalid_http_request, Unset):
            accept_invalid_http_request = UNSET
        else:
            accept_invalid_http_request = FrontendBaseAcceptInvalidHttpRequest(_accept_invalid_http_request)

        _accept_unsafe_violations_in_http_request = d.pop("accept_unsafe_violations_in_http_request", UNSET)
        accept_unsafe_violations_in_http_request: Union[Unset, FrontendBaseAcceptUnsafeViolationsInHttpRequest]
        if isinstance(_accept_unsafe_violations_in_http_request, Unset):
            accept_unsafe_violations_in_http_request = UNSET
        else:
            accept_unsafe_violations_in_http_request = FrontendBaseAcceptUnsafeViolationsInHttpRequest(
                _accept_unsafe_violations_in_http_request
            )

        def _parse_backlog(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        backlog = _parse_backlog(d.pop("backlog", UNSET))

        clflog = d.pop("clflog", UNSET)

        def _parse_client_fin_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        client_fin_timeout = _parse_client_fin_timeout(d.pop("client_fin_timeout", UNSET))

        def _parse_client_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        client_timeout = _parse_client_timeout(d.pop("client_timeout", UNSET))

        _clitcpka = d.pop("clitcpka", UNSET)
        clitcpka: Union[Unset, FrontendBaseClitcpka]
        if isinstance(_clitcpka, Unset):
            clitcpka = UNSET
        else:
            clitcpka = FrontendBaseClitcpka(_clitcpka)

        def _parse_clitcpka_cnt(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        clitcpka_cnt = _parse_clitcpka_cnt(d.pop("clitcpka_cnt", UNSET))

        def _parse_clitcpka_idle(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        clitcpka_idle = _parse_clitcpka_idle(d.pop("clitcpka_idle", UNSET))

        def _parse_clitcpka_intvl(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        clitcpka_intvl = _parse_clitcpka_intvl(d.pop("clitcpka_intvl", UNSET))

        _compression = d.pop("compression", UNSET)
        compression: Union[Unset, Compression]
        if isinstance(_compression, Unset):
            compression = UNSET
        else:
            compression = Compression.from_dict(_compression)

        _contstats = d.pop("contstats", UNSET)
        contstats: Union[Unset, FrontendBaseContstats]
        if isinstance(_contstats, Unset):
            contstats = UNSET
        else:
            contstats = FrontendBaseContstats(_contstats)

        default_backend = d.pop("default_backend", UNSET)

        description = d.pop("description", UNSET)

        _disable_h2_upgrade = d.pop("disable_h2_upgrade", UNSET)
        disable_h2_upgrade: Union[Unset, FrontendBaseDisableH2Upgrade]
        if isinstance(_disable_h2_upgrade, Unset):
            disable_h2_upgrade = UNSET
        else:
            disable_h2_upgrade = FrontendBaseDisableH2Upgrade(_disable_h2_upgrade)

        disabled = d.pop("disabled", UNSET)

        _dontlog_normal = d.pop("dontlog_normal", UNSET)
        dontlog_normal: Union[Unset, FrontendBaseDontlogNormal]
        if isinstance(_dontlog_normal, Unset):
            dontlog_normal = UNSET
        else:
            dontlog_normal = FrontendBaseDontlogNormal(_dontlog_normal)

        _dontlognull = d.pop("dontlognull", UNSET)
        dontlognull: Union[Unset, FrontendBaseDontlognull]
        if isinstance(_dontlognull, Unset):
            dontlognull = UNSET
        else:
            dontlognull = FrontendBaseDontlognull(_dontlognull)

        _email_alert = d.pop("email_alert", UNSET)
        email_alert: Union[Unset, EmailAlert]
        if isinstance(_email_alert, Unset):
            email_alert = UNSET
        else:
            email_alert = EmailAlert.from_dict(_email_alert)

        enabled = d.pop("enabled", UNSET)

        error_files = []
        _error_files = d.pop("error_files", UNSET)
        for error_files_item_data in _error_files or []:
            error_files_item = Errorfile.from_dict(error_files_item_data)

            error_files.append(error_files_item)

        error_log_format = d.pop("error_log_format", UNSET)

        errorfiles_from_http_errors = []
        _errorfiles_from_http_errors = d.pop("errorfiles_from_http_errors", UNSET)
        for errorfiles_from_http_errors_item_data in _errorfiles_from_http_errors or []:
            errorfiles_from_http_errors_item = Errorfiles.from_dict(errorfiles_from_http_errors_item_data)

            errorfiles_from_http_errors.append(errorfiles_from_http_errors_item)

        _errorloc302 = d.pop("errorloc302", UNSET)
        errorloc302: Union[Unset, Errorloc]
        if isinstance(_errorloc302, Unset):
            errorloc302 = UNSET
        else:
            errorloc302 = Errorloc.from_dict(_errorloc302)

        _errorloc303 = d.pop("errorloc303", UNSET)
        errorloc303: Union[Unset, Errorloc]
        if isinstance(_errorloc303, Unset):
            errorloc303 = UNSET
        else:
            errorloc303 = Errorloc.from_dict(_errorloc303)

        _forwardfor = d.pop("forwardfor", UNSET)
        forwardfor: Union[Unset, Forwardfor]
        if isinstance(_forwardfor, Unset):
            forwardfor = UNSET
        else:
            forwardfor = Forwardfor.from_dict(_forwardfor)

        from_ = d.pop("from", UNSET)

        guid = d.pop("guid", UNSET)

        _h1_case_adjust_bogus_client = d.pop("h1_case_adjust_bogus_client", UNSET)
        h1_case_adjust_bogus_client: Union[Unset, FrontendBaseH1CaseAdjustBogusClient]
        if isinstance(_h1_case_adjust_bogus_client, Unset):
            h1_case_adjust_bogus_client = UNSET
        else:
            h1_case_adjust_bogus_client = FrontendBaseH1CaseAdjustBogusClient(_h1_case_adjust_bogus_client)

        _http_buffer_request = d.pop("http-buffer-request", UNSET)
        http_buffer_request: Union[Unset, FrontendBaseHttpBufferRequest]
        if isinstance(_http_buffer_request, Unset):
            http_buffer_request = UNSET
        else:
            http_buffer_request = FrontendBaseHttpBufferRequest(_http_buffer_request)

        _http_drop_response_trailers = d.pop("http-drop-response-trailers", UNSET)
        http_drop_response_trailers: Union[Unset, FrontendBaseHttpDropResponseTrailers]
        if isinstance(_http_drop_response_trailers, Unset):
            http_drop_response_trailers = UNSET
        else:
            http_drop_response_trailers = FrontendBaseHttpDropResponseTrailers(_http_drop_response_trailers)

        _http_use_htx = d.pop("http-use-htx", UNSET)
        http_use_htx: Union[Unset, FrontendBaseHttpUseHtx]
        if isinstance(_http_use_htx, Unset):
            http_use_htx = UNSET
        else:
            http_use_htx = FrontendBaseHttpUseHtx(_http_use_htx)

        _http_connection_mode = d.pop("http_connection_mode", UNSET)
        http_connection_mode: Union[Unset, FrontendBaseHttpConnectionMode]
        if isinstance(_http_connection_mode, Unset):
            http_connection_mode = UNSET
        else:
            http_connection_mode = FrontendBaseHttpConnectionMode(_http_connection_mode)

        _http_ignore_probes = d.pop("http_ignore_probes", UNSET)
        http_ignore_probes: Union[Unset, FrontendBaseHttpIgnoreProbes]
        if isinstance(_http_ignore_probes, Unset):
            http_ignore_probes = UNSET
        else:
            http_ignore_probes = FrontendBaseHttpIgnoreProbes(_http_ignore_probes)

        def _parse_http_keep_alive_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        http_keep_alive_timeout = _parse_http_keep_alive_timeout(d.pop("http_keep_alive_timeout", UNSET))

        _http_no_delay = d.pop("http_no_delay", UNSET)
        http_no_delay: Union[Unset, FrontendBaseHttpNoDelay]
        if isinstance(_http_no_delay, Unset):
            http_no_delay = UNSET
        else:
            http_no_delay = FrontendBaseHttpNoDelay(_http_no_delay)

        def _parse_http_request_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        http_request_timeout = _parse_http_request_timeout(d.pop("http_request_timeout", UNSET))

        _http_restrict_req_hdr_names = d.pop("http_restrict_req_hdr_names", UNSET)
        http_restrict_req_hdr_names: Union[Unset, FrontendBaseHttpRestrictReqHdrNames]
        if isinstance(_http_restrict_req_hdr_names, Unset):
            http_restrict_req_hdr_names = UNSET
        else:
            http_restrict_req_hdr_names = FrontendBaseHttpRestrictReqHdrNames(_http_restrict_req_hdr_names)

        _http_use_proxy_header = d.pop("http_use_proxy_header", UNSET)
        http_use_proxy_header: Union[Unset, FrontendBaseHttpUseProxyHeader]
        if isinstance(_http_use_proxy_header, Unset):
            http_use_proxy_header = UNSET
        else:
            http_use_proxy_header = FrontendBaseHttpUseProxyHeader(_http_use_proxy_header)

        httplog = d.pop("httplog", UNSET)

        _httpslog = d.pop("httpslog", UNSET)
        httpslog: Union[Unset, FrontendBaseHttpslog]
        if isinstance(_httpslog, Unset):
            httpslog = UNSET
        else:
            httpslog = FrontendBaseHttpslog(_httpslog)

        def _parse_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        id = _parse_id(d.pop("id", UNSET))

        _idle_close_on_response = d.pop("idle_close_on_response", UNSET)
        idle_close_on_response: Union[Unset, FrontendBaseIdleCloseOnResponse]
        if isinstance(_idle_close_on_response, Unset):
            idle_close_on_response = UNSET
        else:
            idle_close_on_response = FrontendBaseIdleCloseOnResponse(_idle_close_on_response)

        _independent_streams = d.pop("independent_streams", UNSET)
        independent_streams: Union[Unset, FrontendBaseIndependentStreams]
        if isinstance(_independent_streams, Unset):
            independent_streams = UNSET
        else:
            independent_streams = FrontendBaseIndependentStreams(_independent_streams)

        log_format = d.pop("log_format", UNSET)

        log_format_sd = d.pop("log_format_sd", UNSET)

        _log_separate_errors = d.pop("log_separate_errors", UNSET)
        log_separate_errors: Union[Unset, FrontendBaseLogSeparateErrors]
        if isinstance(_log_separate_errors, Unset):
            log_separate_errors = UNSET
        else:
            log_separate_errors = FrontendBaseLogSeparateErrors(_log_separate_errors)

        log_steps = []
        _log_steps = d.pop("log_steps", UNSET)
        for log_steps_item_data in _log_steps or []:
            log_steps_item = FrontendBaseLogStepsItem(log_steps_item_data)

            log_steps.append(log_steps_item)

        log_tag = d.pop("log_tag", UNSET)

        _logasap = d.pop("logasap", UNSET)
        logasap: Union[Unset, FrontendBaseLogasap]
        if isinstance(_logasap, Unset):
            logasap = UNSET
        else:
            logasap = FrontendBaseLogasap(_logasap)

        def _parse_maxconn(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        maxconn = _parse_maxconn(d.pop("maxconn", UNSET))

        metadata = d.pop("metadata", UNSET)

        _mode = d.pop("mode", UNSET)
        mode: Union[Unset, FrontendBaseMode]
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = FrontendBaseMode(_mode)

        _monitor_fail = d.pop("monitor_fail", UNSET)
        monitor_fail: Union[Unset, MonitorFail]
        if isinstance(_monitor_fail, Unset):
            monitor_fail = UNSET
        else:
            monitor_fail = MonitorFail.from_dict(_monitor_fail)

        monitor_uri = d.pop("monitor_uri", UNSET)

        _nolinger = d.pop("nolinger", UNSET)
        nolinger: Union[Unset, FrontendBaseNolinger]
        if isinstance(_nolinger, Unset):
            nolinger = UNSET
        else:
            nolinger = FrontendBaseNolinger(_nolinger)

        _originalto = d.pop("originalto", UNSET)
        originalto: Union[Unset, Originalto]
        if isinstance(_originalto, Unset):
            originalto = UNSET
        else:
            originalto = Originalto.from_dict(_originalto)

        _socket_stats = d.pop("socket_stats", UNSET)
        socket_stats: Union[Unset, FrontendBaseSocketStats]
        if isinstance(_socket_stats, Unset):
            socket_stats = UNSET
        else:
            socket_stats = FrontendBaseSocketStats(_socket_stats)

        _splice_auto = d.pop("splice_auto", UNSET)
        splice_auto: Union[Unset, FrontendBaseSpliceAuto]
        if isinstance(_splice_auto, Unset):
            splice_auto = UNSET
        else:
            splice_auto = FrontendBaseSpliceAuto(_splice_auto)

        _splice_request = d.pop("splice_request", UNSET)
        splice_request: Union[Unset, FrontendBaseSpliceRequest]
        if isinstance(_splice_request, Unset):
            splice_request = UNSET
        else:
            splice_request = FrontendBaseSpliceRequest(_splice_request)

        _splice_response = d.pop("splice_response", UNSET)
        splice_response: Union[Unset, FrontendBaseSpliceResponse]
        if isinstance(_splice_response, Unset):
            splice_response = UNSET
        else:
            splice_response = FrontendBaseSpliceResponse(_splice_response)

        _stats_options = d.pop("stats_options", UNSET)
        stats_options: Union[Unset, StatsOptions]
        if isinstance(_stats_options, Unset):
            stats_options = UNSET
        else:
            stats_options = StatsOptions.from_dict(_stats_options)

        _stick_table = d.pop("stick_table", UNSET)
        stick_table: Union[Unset, ConfigStickTable]
        if isinstance(_stick_table, Unset):
            stick_table = UNSET
        else:
            stick_table = ConfigStickTable.from_dict(_stick_table)

        def _parse_tarpit_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        tarpit_timeout = _parse_tarpit_timeout(d.pop("tarpit_timeout", UNSET))

        _tcp_smart_accept = d.pop("tcp_smart_accept", UNSET)
        tcp_smart_accept: Union[Unset, FrontendBaseTcpSmartAccept]
        if isinstance(_tcp_smart_accept, Unset):
            tcp_smart_accept = UNSET
        else:
            tcp_smart_accept = FrontendBaseTcpSmartAccept(_tcp_smart_accept)

        _tcpka = d.pop("tcpka", UNSET)
        tcpka: Union[Unset, FrontendBaseTcpka]
        if isinstance(_tcpka, Unset):
            tcpka = UNSET
        else:
            tcpka = FrontendBaseTcpka(_tcpka)

        tcplog = d.pop("tcplog", UNSET)

        unique_id_format = d.pop("unique_id_format", UNSET)

        unique_id_header = d.pop("unique_id_header", UNSET)

        acl_list = []
        _acl_list = d.pop("acl_list", UNSET)
        for componentsschemasacls_item_data in _acl_list or []:
            componentsschemasacls_item = ACLLines.from_dict(componentsschemasacls_item_data)

            acl_list.append(componentsschemasacls_item)

        backend_switching_rule_list = []
        _backend_switching_rule_list = d.pop("backend_switching_rule_list", UNSET)
        for componentsschemasbackend_switching_rules_item_data in _backend_switching_rule_list or []:
            componentsschemasbackend_switching_rules_item = BackendSwitchingRule.from_dict(
                componentsschemasbackend_switching_rules_item_data
            )

            backend_switching_rule_list.append(componentsschemasbackend_switching_rules_item)

        binds = d.pop("binds", UNSET)

        capture_list = []
        _capture_list = d.pop("capture_list", UNSET)
        for componentsschemascaptures_item_data in _capture_list or []:
            componentsschemascaptures_item = DeclareCapture.from_dict(componentsschemascaptures_item_data)

            capture_list.append(componentsschemascaptures_item)

        filter_list = []
        _filter_list = d.pop("filter_list", UNSET)
        for componentsschemasfilters_item_data in _filter_list or []:
            componentsschemasfilters_item = Filter.from_dict(componentsschemasfilters_item_data)

            filter_list.append(componentsschemasfilters_item)

        http_after_response_rule_list = []
        _http_after_response_rule_list = d.pop("http_after_response_rule_list", UNSET)
        for componentsschemashttp_after_response_rules_item_data in _http_after_response_rule_list or []:
            componentsschemashttp_after_response_rules_item = HTTPAfterResponseRule.from_dict(
                componentsschemashttp_after_response_rules_item_data
            )

            http_after_response_rule_list.append(componentsschemashttp_after_response_rules_item)

        http_error_rule_list = []
        _http_error_rule_list = d.pop("http_error_rule_list", UNSET)
        for componentsschemashttp_error_rules_item_data in _http_error_rule_list or []:
            componentsschemashttp_error_rules_item = HTTPErrorRule.from_dict(
                componentsschemashttp_error_rules_item_data
            )

            http_error_rule_list.append(componentsschemashttp_error_rules_item)

        http_request_rule_list = []
        _http_request_rule_list = d.pop("http_request_rule_list", UNSET)
        for componentsschemashttp_request_rules_item_data in _http_request_rule_list or []:
            componentsschemashttp_request_rules_item = HTTPRequestRule.from_dict(
                componentsschemashttp_request_rules_item_data
            )

            http_request_rule_list.append(componentsschemashttp_request_rules_item)

        http_response_rule_list = []
        _http_response_rule_list = d.pop("http_response_rule_list", UNSET)
        for componentsschemashttp_response_rules_item_data in _http_response_rule_list or []:
            componentsschemashttp_response_rules_item = HTTPResponseRule.from_dict(
                componentsschemashttp_response_rules_item_data
            )

            http_response_rule_list.append(componentsschemashttp_response_rules_item)

        log_target_list = []
        _log_target_list = d.pop("log_target_list", UNSET)
        for componentsschemaslog_targets_item_data in _log_target_list or []:
            componentsschemaslog_targets_item = LogTarget.from_dict(componentsschemaslog_targets_item_data)

            log_target_list.append(componentsschemaslog_targets_item)

        quic_initial_rule_list = []
        _quic_initial_rule_list = d.pop("quic_initial_rule_list", UNSET)
        for componentsschemasquic_initial_rules_item_data in _quic_initial_rule_list or []:
            componentsschemasquic_initial_rules_item = QUICInitial.from_dict(
                componentsschemasquic_initial_rules_item_data
            )

            quic_initial_rule_list.append(componentsschemasquic_initial_rules_item)

        ssl_front_use_list = []
        _ssl_front_use_list = d.pop("ssl_front_use_list", UNSET)
        for componentsschemasssl_front_uses_item_data in _ssl_front_use_list or []:
            componentsschemasssl_front_uses_item = SSLFrontendUseCertificate.from_dict(
                componentsschemasssl_front_uses_item_data
            )

            ssl_front_use_list.append(componentsschemasssl_front_uses_item)

        tcp_request_rule_list = []
        _tcp_request_rule_list = d.pop("tcp_request_rule_list", UNSET)
        for componentsschemastcp_request_rules_item_data in _tcp_request_rule_list or []:
            componentsschemastcp_request_rules_item = TCPRequestRule.from_dict(
                componentsschemastcp_request_rules_item_data
            )

            tcp_request_rule_list.append(componentsschemastcp_request_rules_item)

        frontend = cls(
            name=name,
            accept_invalid_http_request=accept_invalid_http_request,
            accept_unsafe_violations_in_http_request=accept_unsafe_violations_in_http_request,
            backlog=backlog,
            clflog=clflog,
            client_fin_timeout=client_fin_timeout,
            client_timeout=client_timeout,
            clitcpka=clitcpka,
            clitcpka_cnt=clitcpka_cnt,
            clitcpka_idle=clitcpka_idle,
            clitcpka_intvl=clitcpka_intvl,
            compression=compression,
            contstats=contstats,
            default_backend=default_backend,
            description=description,
            disable_h2_upgrade=disable_h2_upgrade,
            disabled=disabled,
            dontlog_normal=dontlog_normal,
            dontlognull=dontlognull,
            email_alert=email_alert,
            enabled=enabled,
            error_files=error_files,
            error_log_format=error_log_format,
            errorfiles_from_http_errors=errorfiles_from_http_errors,
            errorloc302=errorloc302,
            errorloc303=errorloc303,
            forwardfor=forwardfor,
            from_=from_,
            guid=guid,
            h1_case_adjust_bogus_client=h1_case_adjust_bogus_client,
            http_buffer_request=http_buffer_request,
            http_drop_response_trailers=http_drop_response_trailers,
            http_use_htx=http_use_htx,
            http_connection_mode=http_connection_mode,
            http_ignore_probes=http_ignore_probes,
            http_keep_alive_timeout=http_keep_alive_timeout,
            http_no_delay=http_no_delay,
            http_request_timeout=http_request_timeout,
            http_restrict_req_hdr_names=http_restrict_req_hdr_names,
            http_use_proxy_header=http_use_proxy_header,
            httplog=httplog,
            httpslog=httpslog,
            id=id,
            idle_close_on_response=idle_close_on_response,
            independent_streams=independent_streams,
            log_format=log_format,
            log_format_sd=log_format_sd,
            log_separate_errors=log_separate_errors,
            log_steps=log_steps,
            log_tag=log_tag,
            logasap=logasap,
            maxconn=maxconn,
            metadata=metadata,
            mode=mode,
            monitor_fail=monitor_fail,
            monitor_uri=monitor_uri,
            nolinger=nolinger,
            originalto=originalto,
            socket_stats=socket_stats,
            splice_auto=splice_auto,
            splice_request=splice_request,
            splice_response=splice_response,
            stats_options=stats_options,
            stick_table=stick_table,
            tarpit_timeout=tarpit_timeout,
            tcp_smart_accept=tcp_smart_accept,
            tcpka=tcpka,
            tcplog=tcplog,
            unique_id_format=unique_id_format,
            unique_id_header=unique_id_header,
            acl_list=acl_list,
            backend_switching_rule_list=backend_switching_rule_list,
            binds=binds,
            capture_list=capture_list,
            filter_list=filter_list,
            http_after_response_rule_list=http_after_response_rule_list,
            http_error_rule_list=http_error_rule_list,
            http_request_rule_list=http_request_rule_list,
            http_response_rule_list=http_response_rule_list,
            log_target_list=log_target_list,
            quic_initial_rule_list=quic_initial_rule_list,
            ssl_front_use_list=ssl_front_use_list,
            tcp_request_rule_list=tcp_request_rule_list,
        )

        frontend.additional_properties = d
        return frontend

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
