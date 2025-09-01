from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.defaults_base_abortonclose import DefaultsBaseAbortonclose
from ..models.defaults_base_accept_invalid_http_request import DefaultsBaseAcceptInvalidHttpRequest
from ..models.defaults_base_accept_invalid_http_response import DefaultsBaseAcceptInvalidHttpResponse
from ..models.defaults_base_accept_unsafe_violations_in_http_request import (
    DefaultsBaseAcceptUnsafeViolationsInHttpRequest,
)
from ..models.defaults_base_accept_unsafe_violations_in_http_response import (
    DefaultsBaseAcceptUnsafeViolationsInHttpResponse,
)
from ..models.defaults_base_adv_check import DefaultsBaseAdvCheck
from ..models.defaults_base_allbackups import DefaultsBaseAllbackups
from ..models.defaults_base_checkcache import DefaultsBaseCheckcache
from ..models.defaults_base_clitcpka import DefaultsBaseClitcpka
from ..models.defaults_base_contstats import DefaultsBaseContstats
from ..models.defaults_base_disable_h2_upgrade import DefaultsBaseDisableH2Upgrade
from ..models.defaults_base_dontlog_normal import DefaultsBaseDontlogNormal
from ..models.defaults_base_dontlognull import DefaultsBaseDontlognull
from ..models.defaults_base_external_check import DefaultsBaseExternalCheck
from ..models.defaults_base_h1_case_adjust_bogus_client import DefaultsBaseH1CaseAdjustBogusClient
from ..models.defaults_base_h1_case_adjust_bogus_server import DefaultsBaseH1CaseAdjustBogusServer
from ..models.defaults_base_hash_preserve_affinity import DefaultsBaseHashPreserveAffinity
from ..models.defaults_base_http_buffer_request import DefaultsBaseHttpBufferRequest
from ..models.defaults_base_http_connection_mode import DefaultsBaseHttpConnectionMode
from ..models.defaults_base_http_drop_request_trailers import DefaultsBaseHttpDropRequestTrailers
from ..models.defaults_base_http_drop_response_trailers import DefaultsBaseHttpDropResponseTrailers
from ..models.defaults_base_http_ignore_probes import DefaultsBaseHttpIgnoreProbes
from ..models.defaults_base_http_no_delay import DefaultsBaseHttpNoDelay
from ..models.defaults_base_http_pretend_keepalive import DefaultsBaseHttpPretendKeepalive
from ..models.defaults_base_http_restrict_req_hdr_names import DefaultsBaseHttpRestrictReqHdrNames
from ..models.defaults_base_http_reuse import DefaultsBaseHttpReuse
from ..models.defaults_base_http_use_htx import DefaultsBaseHttpUseHtx
from ..models.defaults_base_http_use_proxy_header import DefaultsBaseHttpUseProxyHeader
from ..models.defaults_base_httpslog import DefaultsBaseHttpslog
from ..models.defaults_base_idle_close_on_response import DefaultsBaseIdleCloseOnResponse
from ..models.defaults_base_independent_streams import DefaultsBaseIndependentStreams
from ..models.defaults_base_load_server_state_from_file import DefaultsBaseLoadServerStateFromFile
from ..models.defaults_base_log_health_checks import DefaultsBaseLogHealthChecks
from ..models.defaults_base_log_separate_errors import DefaultsBaseLogSeparateErrors
from ..models.defaults_base_log_steps_item import DefaultsBaseLogStepsItem
from ..models.defaults_base_logasap import DefaultsBaseLogasap
from ..models.defaults_base_mode import DefaultsBaseMode
from ..models.defaults_base_nolinger import DefaultsBaseNolinger
from ..models.defaults_base_persist import DefaultsBasePersist
from ..models.defaults_base_prefer_last_server import DefaultsBasePreferLastServer
from ..models.defaults_base_socket_stats import DefaultsBaseSocketStats
from ..models.defaults_base_splice_auto import DefaultsBaseSpliceAuto
from ..models.defaults_base_splice_request import DefaultsBaseSpliceRequest
from ..models.defaults_base_splice_response import DefaultsBaseSpliceResponse
from ..models.defaults_base_srvtcpka import DefaultsBaseSrvtcpka
from ..models.defaults_base_tcp_smart_accept import DefaultsBaseTcpSmartAccept
from ..models.defaults_base_tcp_smart_connect import DefaultsBaseTcpSmartConnect
from ..models.defaults_base_tcpka import DefaultsBaseTcpka
from ..models.defaults_base_transparent import DefaultsBaseTransparent
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.balance import Balance
    from ..models.compression import Compression
    from ..models.cookie import Cookie
    from ..models.email_alert import EmailAlert
    from ..models.errorfile import Errorfile
    from ..models.errorfiles import Errorfiles
    from ..models.errorloc import Errorloc
    from ..models.forwardfor import Forwardfor
    from ..models.hash_type import HashType
    from ..models.httpchk_params import HttpchkParams
    from ..models.mysql_check_params import MysqlCheckParams
    from ..models.originalto import Originalto
    from ..models.persist_rule import PersistRule
    from ..models.pgsql_check_params import PgsqlCheckParams
    from ..models.redispatch import Redispatch
    from ..models.server_params import ServerParams
    from ..models.smtpchk_params import SmtpchkParams
    from ..models.source import Source
    from ..models.stats_options import StatsOptions


T = TypeVar("T", bound="DefaultsBase")


@_attrs_define
class DefaultsBase:
    """HAProxy defaults configuration

    Attributes:
        abortonclose (Union[Unset, DefaultsBaseAbortonclose]):
        accept_invalid_http_request (Union[Unset, DefaultsBaseAcceptInvalidHttpRequest]):
        accept_invalid_http_response (Union[Unset, DefaultsBaseAcceptInvalidHttpResponse]):
        accept_unsafe_violations_in_http_request (Union[Unset, DefaultsBaseAcceptUnsafeViolationsInHttpRequest]):
        accept_unsafe_violations_in_http_response (Union[Unset, DefaultsBaseAcceptUnsafeViolationsInHttpResponse]):
        adv_check (Union[Unset, DefaultsBaseAdvCheck]):
        allbackups (Union[Unset, DefaultsBaseAllbackups]):
        backlog (Union[None, Unset, int]):
        balance (Union[Unset, Balance]):
        check_timeout (Union[None, Unset, int]):
        checkcache (Union[Unset, DefaultsBaseCheckcache]):
        clflog (Union[Unset, bool]):
        client_fin_timeout (Union[None, Unset, int]):
        client_timeout (Union[None, Unset, int]):
        clitcpka (Union[Unset, DefaultsBaseClitcpka]):
        clitcpka_cnt (Union[None, Unset, int]):
        clitcpka_idle (Union[None, Unset, int]):
        clitcpka_intvl (Union[None, Unset, int]):
        compression (Union[Unset, Compression]):
        connect_timeout (Union[None, Unset, int]):
        contstats (Union[Unset, DefaultsBaseContstats]):
        cookie (Union[Unset, Cookie]):
        default_backend (Union[Unset, str]):
        default_server (Union[Unset, ServerParams]):
        disable_h2_upgrade (Union[Unset, DefaultsBaseDisableH2Upgrade]):
        disabled (Union[Unset, bool]):
        dontlog_normal (Union[Unset, DefaultsBaseDontlogNormal]):
        dontlognull (Union[Unset, DefaultsBaseDontlognull]):
        dynamic_cookie_key (Union[Unset, str]):
        email_alert (Union[Unset, EmailAlert]): Send emails for important log messages.
        enabled (Union[Unset, bool]):
        error_files (Union[Unset, list['Errorfile']]):
        error_log_format (Union[Unset, str]):
        errorfiles_from_http_errors (Union[Unset, list['Errorfiles']]):
        errorloc302 (Union[Unset, Errorloc]):
        errorloc303 (Union[Unset, Errorloc]):
        external_check (Union[Unset, DefaultsBaseExternalCheck]):
        external_check_command (Union[Unset, str]):
        external_check_path (Union[Unset, str]):
        forwardfor (Union[Unset, Forwardfor]):
        from_ (Union[Unset, str]):
        fullconn (Union[None, Unset, int]):
        h1_case_adjust_bogus_client (Union[Unset, DefaultsBaseH1CaseAdjustBogusClient]):
        h1_case_adjust_bogus_server (Union[Unset, DefaultsBaseH1CaseAdjustBogusServer]):
        hash_balance_factor (Union[None, Unset, int]):
        hash_preserve_affinity (Union[Unset, DefaultsBaseHashPreserveAffinity]):
        hash_type (Union[Unset, HashType]):
        http_buffer_request (Union[Unset, DefaultsBaseHttpBufferRequest]):
        http_drop_request_trailers (Union[Unset, DefaultsBaseHttpDropRequestTrailers]):
        http_drop_response_trailers (Union[Unset, DefaultsBaseHttpDropResponseTrailers]):
        http_use_htx (Union[Unset, DefaultsBaseHttpUseHtx]):
        http_connection_mode (Union[Unset, DefaultsBaseHttpConnectionMode]):
        http_ignore_probes (Union[Unset, DefaultsBaseHttpIgnoreProbes]):
        http_keep_alive_timeout (Union[None, Unset, int]):
        http_no_delay (Union[Unset, DefaultsBaseHttpNoDelay]):
        http_pretend_keepalive (Union[Unset, DefaultsBaseHttpPretendKeepalive]):
        http_request_timeout (Union[None, Unset, int]):
        http_restrict_req_hdr_names (Union[Unset, DefaultsBaseHttpRestrictReqHdrNames]):
        http_reuse (Union[Unset, DefaultsBaseHttpReuse]):
        http_send_name_header (Union[None, Unset, str]):
        http_use_proxy_header (Union[Unset, DefaultsBaseHttpUseProxyHeader]):
        httpchk_params (Union[Unset, HttpchkParams]):
        httplog (Union[Unset, bool]):
        httpslog (Union[Unset, DefaultsBaseHttpslog]):
        idle_close_on_response (Union[Unset, DefaultsBaseIdleCloseOnResponse]):
        independent_streams (Union[Unset, DefaultsBaseIndependentStreams]):
        load_server_state_from_file (Union[Unset, DefaultsBaseLoadServerStateFromFile]):
        log_format (Union[Unset, str]):
        log_format_sd (Union[Unset, str]):
        log_health_checks (Union[Unset, DefaultsBaseLogHealthChecks]):
        log_separate_errors (Union[Unset, DefaultsBaseLogSeparateErrors]):
        log_steps (Union[Unset, list[DefaultsBaseLogStepsItem]]):
        log_tag (Union[Unset, str]):
        logasap (Union[Unset, DefaultsBaseLogasap]):
        max_keep_alive_queue (Union[None, Unset, int]):
        maxconn (Union[None, Unset, int]):
        metadata (Union[Unset, Any]):
        mode (Union[Unset, DefaultsBaseMode]):
        monitor_uri (Union[Unset, str]):
        mysql_check_params (Union[Unset, MysqlCheckParams]):
        name (Union[Unset, str]):
        nolinger (Union[Unset, DefaultsBaseNolinger]):
        originalto (Union[Unset, Originalto]):
        persist (Union[Unset, DefaultsBasePersist]):
        persist_rule (Union[Unset, PersistRule]):
        pgsql_check_params (Union[Unset, PgsqlCheckParams]):
        prefer_last_server (Union[Unset, DefaultsBasePreferLastServer]):
        queue_timeout (Union[None, Unset, int]):
        redispatch (Union[Unset, Redispatch]):
        retries (Union[None, Unset, int]):
        retry_on (Union[Unset, str]):
        server_fin_timeout (Union[None, Unset, int]):
        server_timeout (Union[None, Unset, int]):
        smtpchk_params (Union[Unset, SmtpchkParams]):
        socket_stats (Union[Unset, DefaultsBaseSocketStats]):
        source (Union[Unset, Source]):
        splice_auto (Union[Unset, DefaultsBaseSpliceAuto]):
        splice_request (Union[Unset, DefaultsBaseSpliceRequest]):
        splice_response (Union[Unset, DefaultsBaseSpliceResponse]):
        srvtcpka (Union[Unset, DefaultsBaseSrvtcpka]):
        srvtcpka_cnt (Union[None, Unset, int]):
        srvtcpka_idle (Union[None, Unset, int]):
        srvtcpka_intvl (Union[None, Unset, int]):
        stats_options (Union[Unset, StatsOptions]):
        tarpit_timeout (Union[None, Unset, int]):
        tcp_smart_accept (Union[Unset, DefaultsBaseTcpSmartAccept]):
        tcp_smart_connect (Union[Unset, DefaultsBaseTcpSmartConnect]):
        tcpka (Union[Unset, DefaultsBaseTcpka]):
        tcplog (Union[Unset, bool]):
        transparent (Union[Unset, DefaultsBaseTransparent]):
        tunnel_timeout (Union[None, Unset, int]):
        unique_id_format (Union[Unset, str]):
        unique_id_header (Union[Unset, str]):
    """

    abortonclose: Union[Unset, DefaultsBaseAbortonclose] = UNSET
    accept_invalid_http_request: Union[Unset, DefaultsBaseAcceptInvalidHttpRequest] = UNSET
    accept_invalid_http_response: Union[Unset, DefaultsBaseAcceptInvalidHttpResponse] = UNSET
    accept_unsafe_violations_in_http_request: Union[Unset, DefaultsBaseAcceptUnsafeViolationsInHttpRequest] = UNSET
    accept_unsafe_violations_in_http_response: Union[Unset, DefaultsBaseAcceptUnsafeViolationsInHttpResponse] = UNSET
    adv_check: Union[Unset, DefaultsBaseAdvCheck] = UNSET
    allbackups: Union[Unset, DefaultsBaseAllbackups] = UNSET
    backlog: Union[None, Unset, int] = UNSET
    balance: Union[Unset, "Balance"] = UNSET
    check_timeout: Union[None, Unset, int] = UNSET
    checkcache: Union[Unset, DefaultsBaseCheckcache] = UNSET
    clflog: Union[Unset, bool] = UNSET
    client_fin_timeout: Union[None, Unset, int] = UNSET
    client_timeout: Union[None, Unset, int] = UNSET
    clitcpka: Union[Unset, DefaultsBaseClitcpka] = UNSET
    clitcpka_cnt: Union[None, Unset, int] = UNSET
    clitcpka_idle: Union[None, Unset, int] = UNSET
    clitcpka_intvl: Union[None, Unset, int] = UNSET
    compression: Union[Unset, "Compression"] = UNSET
    connect_timeout: Union[None, Unset, int] = UNSET
    contstats: Union[Unset, DefaultsBaseContstats] = UNSET
    cookie: Union[Unset, "Cookie"] = UNSET
    default_backend: Union[Unset, str] = UNSET
    default_server: Union[Unset, "ServerParams"] = UNSET
    disable_h2_upgrade: Union[Unset, DefaultsBaseDisableH2Upgrade] = UNSET
    disabled: Union[Unset, bool] = UNSET
    dontlog_normal: Union[Unset, DefaultsBaseDontlogNormal] = UNSET
    dontlognull: Union[Unset, DefaultsBaseDontlognull] = UNSET
    dynamic_cookie_key: Union[Unset, str] = UNSET
    email_alert: Union[Unset, "EmailAlert"] = UNSET
    enabled: Union[Unset, bool] = UNSET
    error_files: Union[Unset, list["Errorfile"]] = UNSET
    error_log_format: Union[Unset, str] = UNSET
    errorfiles_from_http_errors: Union[Unset, list["Errorfiles"]] = UNSET
    errorloc302: Union[Unset, "Errorloc"] = UNSET
    errorloc303: Union[Unset, "Errorloc"] = UNSET
    external_check: Union[Unset, DefaultsBaseExternalCheck] = UNSET
    external_check_command: Union[Unset, str] = UNSET
    external_check_path: Union[Unset, str] = UNSET
    forwardfor: Union[Unset, "Forwardfor"] = UNSET
    from_: Union[Unset, str] = UNSET
    fullconn: Union[None, Unset, int] = UNSET
    h1_case_adjust_bogus_client: Union[Unset, DefaultsBaseH1CaseAdjustBogusClient] = UNSET
    h1_case_adjust_bogus_server: Union[Unset, DefaultsBaseH1CaseAdjustBogusServer] = UNSET
    hash_balance_factor: Union[None, Unset, int] = UNSET
    hash_preserve_affinity: Union[Unset, DefaultsBaseHashPreserveAffinity] = UNSET
    hash_type: Union[Unset, "HashType"] = UNSET
    http_buffer_request: Union[Unset, DefaultsBaseHttpBufferRequest] = UNSET
    http_drop_request_trailers: Union[Unset, DefaultsBaseHttpDropRequestTrailers] = UNSET
    http_drop_response_trailers: Union[Unset, DefaultsBaseHttpDropResponseTrailers] = UNSET
    http_use_htx: Union[Unset, DefaultsBaseHttpUseHtx] = UNSET
    http_connection_mode: Union[Unset, DefaultsBaseHttpConnectionMode] = UNSET
    http_ignore_probes: Union[Unset, DefaultsBaseHttpIgnoreProbes] = UNSET
    http_keep_alive_timeout: Union[None, Unset, int] = UNSET
    http_no_delay: Union[Unset, DefaultsBaseHttpNoDelay] = UNSET
    http_pretend_keepalive: Union[Unset, DefaultsBaseHttpPretendKeepalive] = UNSET
    http_request_timeout: Union[None, Unset, int] = UNSET
    http_restrict_req_hdr_names: Union[Unset, DefaultsBaseHttpRestrictReqHdrNames] = UNSET
    http_reuse: Union[Unset, DefaultsBaseHttpReuse] = UNSET
    http_send_name_header: Union[None, Unset, str] = UNSET
    http_use_proxy_header: Union[Unset, DefaultsBaseHttpUseProxyHeader] = UNSET
    httpchk_params: Union[Unset, "HttpchkParams"] = UNSET
    httplog: Union[Unset, bool] = UNSET
    httpslog: Union[Unset, DefaultsBaseHttpslog] = UNSET
    idle_close_on_response: Union[Unset, DefaultsBaseIdleCloseOnResponse] = UNSET
    independent_streams: Union[Unset, DefaultsBaseIndependentStreams] = UNSET
    load_server_state_from_file: Union[Unset, DefaultsBaseLoadServerStateFromFile] = UNSET
    log_format: Union[Unset, str] = UNSET
    log_format_sd: Union[Unset, str] = UNSET
    log_health_checks: Union[Unset, DefaultsBaseLogHealthChecks] = UNSET
    log_separate_errors: Union[Unset, DefaultsBaseLogSeparateErrors] = UNSET
    log_steps: Union[Unset, list[DefaultsBaseLogStepsItem]] = UNSET
    log_tag: Union[Unset, str] = UNSET
    logasap: Union[Unset, DefaultsBaseLogasap] = UNSET
    max_keep_alive_queue: Union[None, Unset, int] = UNSET
    maxconn: Union[None, Unset, int] = UNSET
    metadata: Union[Unset, Any] = UNSET
    mode: Union[Unset, DefaultsBaseMode] = UNSET
    monitor_uri: Union[Unset, str] = UNSET
    mysql_check_params: Union[Unset, "MysqlCheckParams"] = UNSET
    name: Union[Unset, str] = UNSET
    nolinger: Union[Unset, DefaultsBaseNolinger] = UNSET
    originalto: Union[Unset, "Originalto"] = UNSET
    persist: Union[Unset, DefaultsBasePersist] = UNSET
    persist_rule: Union[Unset, "PersistRule"] = UNSET
    pgsql_check_params: Union[Unset, "PgsqlCheckParams"] = UNSET
    prefer_last_server: Union[Unset, DefaultsBasePreferLastServer] = UNSET
    queue_timeout: Union[None, Unset, int] = UNSET
    redispatch: Union[Unset, "Redispatch"] = UNSET
    retries: Union[None, Unset, int] = UNSET
    retry_on: Union[Unset, str] = UNSET
    server_fin_timeout: Union[None, Unset, int] = UNSET
    server_timeout: Union[None, Unset, int] = UNSET
    smtpchk_params: Union[Unset, "SmtpchkParams"] = UNSET
    socket_stats: Union[Unset, DefaultsBaseSocketStats] = UNSET
    source: Union[Unset, "Source"] = UNSET
    splice_auto: Union[Unset, DefaultsBaseSpliceAuto] = UNSET
    splice_request: Union[Unset, DefaultsBaseSpliceRequest] = UNSET
    splice_response: Union[Unset, DefaultsBaseSpliceResponse] = UNSET
    srvtcpka: Union[Unset, DefaultsBaseSrvtcpka] = UNSET
    srvtcpka_cnt: Union[None, Unset, int] = UNSET
    srvtcpka_idle: Union[None, Unset, int] = UNSET
    srvtcpka_intvl: Union[None, Unset, int] = UNSET
    stats_options: Union[Unset, "StatsOptions"] = UNSET
    tarpit_timeout: Union[None, Unset, int] = UNSET
    tcp_smart_accept: Union[Unset, DefaultsBaseTcpSmartAccept] = UNSET
    tcp_smart_connect: Union[Unset, DefaultsBaseTcpSmartConnect] = UNSET
    tcpka: Union[Unset, DefaultsBaseTcpka] = UNSET
    tcplog: Union[Unset, bool] = UNSET
    transparent: Union[Unset, DefaultsBaseTransparent] = UNSET
    tunnel_timeout: Union[None, Unset, int] = UNSET
    unique_id_format: Union[Unset, str] = UNSET
    unique_id_header: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        abortonclose: Union[Unset, str] = UNSET
        if not isinstance(self.abortonclose, Unset):
            abortonclose = self.abortonclose.value

        accept_invalid_http_request: Union[Unset, str] = UNSET
        if not isinstance(self.accept_invalid_http_request, Unset):
            accept_invalid_http_request = self.accept_invalid_http_request.value

        accept_invalid_http_response: Union[Unset, str] = UNSET
        if not isinstance(self.accept_invalid_http_response, Unset):
            accept_invalid_http_response = self.accept_invalid_http_response.value

        accept_unsafe_violations_in_http_request: Union[Unset, str] = UNSET
        if not isinstance(self.accept_unsafe_violations_in_http_request, Unset):
            accept_unsafe_violations_in_http_request = self.accept_unsafe_violations_in_http_request.value

        accept_unsafe_violations_in_http_response: Union[Unset, str] = UNSET
        if not isinstance(self.accept_unsafe_violations_in_http_response, Unset):
            accept_unsafe_violations_in_http_response = self.accept_unsafe_violations_in_http_response.value

        adv_check: Union[Unset, str] = UNSET
        if not isinstance(self.adv_check, Unset):
            adv_check = self.adv_check.value

        allbackups: Union[Unset, str] = UNSET
        if not isinstance(self.allbackups, Unset):
            allbackups = self.allbackups.value

        backlog: Union[None, Unset, int]
        if isinstance(self.backlog, Unset):
            backlog = UNSET
        else:
            backlog = self.backlog

        balance: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.balance, Unset):
            balance = self.balance.to_dict()

        check_timeout: Union[None, Unset, int]
        if isinstance(self.check_timeout, Unset):
            check_timeout = UNSET
        else:
            check_timeout = self.check_timeout

        checkcache: Union[Unset, str] = UNSET
        if not isinstance(self.checkcache, Unset):
            checkcache = self.checkcache.value

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

        connect_timeout: Union[None, Unset, int]
        if isinstance(self.connect_timeout, Unset):
            connect_timeout = UNSET
        else:
            connect_timeout = self.connect_timeout

        contstats: Union[Unset, str] = UNSET
        if not isinstance(self.contstats, Unset):
            contstats = self.contstats.value

        cookie: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.cookie, Unset):
            cookie = self.cookie.to_dict()

        default_backend = self.default_backend

        default_server: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.default_server, Unset):
            default_server = self.default_server.to_dict()

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

        dynamic_cookie_key = self.dynamic_cookie_key

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

        external_check: Union[Unset, str] = UNSET
        if not isinstance(self.external_check, Unset):
            external_check = self.external_check.value

        external_check_command = self.external_check_command

        external_check_path = self.external_check_path

        forwardfor: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.forwardfor, Unset):
            forwardfor = self.forwardfor.to_dict()

        from_ = self.from_

        fullconn: Union[None, Unset, int]
        if isinstance(self.fullconn, Unset):
            fullconn = UNSET
        else:
            fullconn = self.fullconn

        h1_case_adjust_bogus_client: Union[Unset, str] = UNSET
        if not isinstance(self.h1_case_adjust_bogus_client, Unset):
            h1_case_adjust_bogus_client = self.h1_case_adjust_bogus_client.value

        h1_case_adjust_bogus_server: Union[Unset, str] = UNSET
        if not isinstance(self.h1_case_adjust_bogus_server, Unset):
            h1_case_adjust_bogus_server = self.h1_case_adjust_bogus_server.value

        hash_balance_factor: Union[None, Unset, int]
        if isinstance(self.hash_balance_factor, Unset):
            hash_balance_factor = UNSET
        else:
            hash_balance_factor = self.hash_balance_factor

        hash_preserve_affinity: Union[Unset, str] = UNSET
        if not isinstance(self.hash_preserve_affinity, Unset):
            hash_preserve_affinity = self.hash_preserve_affinity.value

        hash_type: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.hash_type, Unset):
            hash_type = self.hash_type.to_dict()

        http_buffer_request: Union[Unset, str] = UNSET
        if not isinstance(self.http_buffer_request, Unset):
            http_buffer_request = self.http_buffer_request.value

        http_drop_request_trailers: Union[Unset, str] = UNSET
        if not isinstance(self.http_drop_request_trailers, Unset):
            http_drop_request_trailers = self.http_drop_request_trailers.value

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

        http_pretend_keepalive: Union[Unset, str] = UNSET
        if not isinstance(self.http_pretend_keepalive, Unset):
            http_pretend_keepalive = self.http_pretend_keepalive.value

        http_request_timeout: Union[None, Unset, int]
        if isinstance(self.http_request_timeout, Unset):
            http_request_timeout = UNSET
        else:
            http_request_timeout = self.http_request_timeout

        http_restrict_req_hdr_names: Union[Unset, str] = UNSET
        if not isinstance(self.http_restrict_req_hdr_names, Unset):
            http_restrict_req_hdr_names = self.http_restrict_req_hdr_names.value

        http_reuse: Union[Unset, str] = UNSET
        if not isinstance(self.http_reuse, Unset):
            http_reuse = self.http_reuse.value

        http_send_name_header: Union[None, Unset, str]
        if isinstance(self.http_send_name_header, Unset):
            http_send_name_header = UNSET
        else:
            http_send_name_header = self.http_send_name_header

        http_use_proxy_header: Union[Unset, str] = UNSET
        if not isinstance(self.http_use_proxy_header, Unset):
            http_use_proxy_header = self.http_use_proxy_header.value

        httpchk_params: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.httpchk_params, Unset):
            httpchk_params = self.httpchk_params.to_dict()

        httplog = self.httplog

        httpslog: Union[Unset, str] = UNSET
        if not isinstance(self.httpslog, Unset):
            httpslog = self.httpslog.value

        idle_close_on_response: Union[Unset, str] = UNSET
        if not isinstance(self.idle_close_on_response, Unset):
            idle_close_on_response = self.idle_close_on_response.value

        independent_streams: Union[Unset, str] = UNSET
        if not isinstance(self.independent_streams, Unset):
            independent_streams = self.independent_streams.value

        load_server_state_from_file: Union[Unset, str] = UNSET
        if not isinstance(self.load_server_state_from_file, Unset):
            load_server_state_from_file = self.load_server_state_from_file.value

        log_format = self.log_format

        log_format_sd = self.log_format_sd

        log_health_checks: Union[Unset, str] = UNSET
        if not isinstance(self.log_health_checks, Unset):
            log_health_checks = self.log_health_checks.value

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

        max_keep_alive_queue: Union[None, Unset, int]
        if isinstance(self.max_keep_alive_queue, Unset):
            max_keep_alive_queue = UNSET
        else:
            max_keep_alive_queue = self.max_keep_alive_queue

        maxconn: Union[None, Unset, int]
        if isinstance(self.maxconn, Unset):
            maxconn = UNSET
        else:
            maxconn = self.maxconn

        metadata = self.metadata

        mode: Union[Unset, str] = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        monitor_uri = self.monitor_uri

        mysql_check_params: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.mysql_check_params, Unset):
            mysql_check_params = self.mysql_check_params.to_dict()

        name = self.name

        nolinger: Union[Unset, str] = UNSET
        if not isinstance(self.nolinger, Unset):
            nolinger = self.nolinger.value

        originalto: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.originalto, Unset):
            originalto = self.originalto.to_dict()

        persist: Union[Unset, str] = UNSET
        if not isinstance(self.persist, Unset):
            persist = self.persist.value

        persist_rule: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.persist_rule, Unset):
            persist_rule = self.persist_rule.to_dict()

        pgsql_check_params: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.pgsql_check_params, Unset):
            pgsql_check_params = self.pgsql_check_params.to_dict()

        prefer_last_server: Union[Unset, str] = UNSET
        if not isinstance(self.prefer_last_server, Unset):
            prefer_last_server = self.prefer_last_server.value

        queue_timeout: Union[None, Unset, int]
        if isinstance(self.queue_timeout, Unset):
            queue_timeout = UNSET
        else:
            queue_timeout = self.queue_timeout

        redispatch: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.redispatch, Unset):
            redispatch = self.redispatch.to_dict()

        retries: Union[None, Unset, int]
        if isinstance(self.retries, Unset):
            retries = UNSET
        else:
            retries = self.retries

        retry_on = self.retry_on

        server_fin_timeout: Union[None, Unset, int]
        if isinstance(self.server_fin_timeout, Unset):
            server_fin_timeout = UNSET
        else:
            server_fin_timeout = self.server_fin_timeout

        server_timeout: Union[None, Unset, int]
        if isinstance(self.server_timeout, Unset):
            server_timeout = UNSET
        else:
            server_timeout = self.server_timeout

        smtpchk_params: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.smtpchk_params, Unset):
            smtpchk_params = self.smtpchk_params.to_dict()

        socket_stats: Union[Unset, str] = UNSET
        if not isinstance(self.socket_stats, Unset):
            socket_stats = self.socket_stats.value

        source: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.source, Unset):
            source = self.source.to_dict()

        splice_auto: Union[Unset, str] = UNSET
        if not isinstance(self.splice_auto, Unset):
            splice_auto = self.splice_auto.value

        splice_request: Union[Unset, str] = UNSET
        if not isinstance(self.splice_request, Unset):
            splice_request = self.splice_request.value

        splice_response: Union[Unset, str] = UNSET
        if not isinstance(self.splice_response, Unset):
            splice_response = self.splice_response.value

        srvtcpka: Union[Unset, str] = UNSET
        if not isinstance(self.srvtcpka, Unset):
            srvtcpka = self.srvtcpka.value

        srvtcpka_cnt: Union[None, Unset, int]
        if isinstance(self.srvtcpka_cnt, Unset):
            srvtcpka_cnt = UNSET
        else:
            srvtcpka_cnt = self.srvtcpka_cnt

        srvtcpka_idle: Union[None, Unset, int]
        if isinstance(self.srvtcpka_idle, Unset):
            srvtcpka_idle = UNSET
        else:
            srvtcpka_idle = self.srvtcpka_idle

        srvtcpka_intvl: Union[None, Unset, int]
        if isinstance(self.srvtcpka_intvl, Unset):
            srvtcpka_intvl = UNSET
        else:
            srvtcpka_intvl = self.srvtcpka_intvl

        stats_options: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.stats_options, Unset):
            stats_options = self.stats_options.to_dict()

        tarpit_timeout: Union[None, Unset, int]
        if isinstance(self.tarpit_timeout, Unset):
            tarpit_timeout = UNSET
        else:
            tarpit_timeout = self.tarpit_timeout

        tcp_smart_accept: Union[Unset, str] = UNSET
        if not isinstance(self.tcp_smart_accept, Unset):
            tcp_smart_accept = self.tcp_smart_accept.value

        tcp_smart_connect: Union[Unset, str] = UNSET
        if not isinstance(self.tcp_smart_connect, Unset):
            tcp_smart_connect = self.tcp_smart_connect.value

        tcpka: Union[Unset, str] = UNSET
        if not isinstance(self.tcpka, Unset):
            tcpka = self.tcpka.value

        tcplog = self.tcplog

        transparent: Union[Unset, str] = UNSET
        if not isinstance(self.transparent, Unset):
            transparent = self.transparent.value

        tunnel_timeout: Union[None, Unset, int]
        if isinstance(self.tunnel_timeout, Unset):
            tunnel_timeout = UNSET
        else:
            tunnel_timeout = self.tunnel_timeout

        unique_id_format = self.unique_id_format

        unique_id_header = self.unique_id_header

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if abortonclose is not UNSET:
            field_dict["abortonclose"] = abortonclose
        if accept_invalid_http_request is not UNSET:
            field_dict["accept_invalid_http_request"] = accept_invalid_http_request
        if accept_invalid_http_response is not UNSET:
            field_dict["accept_invalid_http_response"] = accept_invalid_http_response
        if accept_unsafe_violations_in_http_request is not UNSET:
            field_dict["accept_unsafe_violations_in_http_request"] = accept_unsafe_violations_in_http_request
        if accept_unsafe_violations_in_http_response is not UNSET:
            field_dict["accept_unsafe_violations_in_http_response"] = accept_unsafe_violations_in_http_response
        if adv_check is not UNSET:
            field_dict["adv_check"] = adv_check
        if allbackups is not UNSET:
            field_dict["allbackups"] = allbackups
        if backlog is not UNSET:
            field_dict["backlog"] = backlog
        if balance is not UNSET:
            field_dict["balance"] = balance
        if check_timeout is not UNSET:
            field_dict["check_timeout"] = check_timeout
        if checkcache is not UNSET:
            field_dict["checkcache"] = checkcache
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
        if connect_timeout is not UNSET:
            field_dict["connect_timeout"] = connect_timeout
        if contstats is not UNSET:
            field_dict["contstats"] = contstats
        if cookie is not UNSET:
            field_dict["cookie"] = cookie
        if default_backend is not UNSET:
            field_dict["default_backend"] = default_backend
        if default_server is not UNSET:
            field_dict["default_server"] = default_server
        if disable_h2_upgrade is not UNSET:
            field_dict["disable_h2_upgrade"] = disable_h2_upgrade
        if disabled is not UNSET:
            field_dict["disabled"] = disabled
        if dontlog_normal is not UNSET:
            field_dict["dontlog_normal"] = dontlog_normal
        if dontlognull is not UNSET:
            field_dict["dontlognull"] = dontlognull
        if dynamic_cookie_key is not UNSET:
            field_dict["dynamic_cookie_key"] = dynamic_cookie_key
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
        if external_check is not UNSET:
            field_dict["external_check"] = external_check
        if external_check_command is not UNSET:
            field_dict["external_check_command"] = external_check_command
        if external_check_path is not UNSET:
            field_dict["external_check_path"] = external_check_path
        if forwardfor is not UNSET:
            field_dict["forwardfor"] = forwardfor
        if from_ is not UNSET:
            field_dict["from"] = from_
        if fullconn is not UNSET:
            field_dict["fullconn"] = fullconn
        if h1_case_adjust_bogus_client is not UNSET:
            field_dict["h1_case_adjust_bogus_client"] = h1_case_adjust_bogus_client
        if h1_case_adjust_bogus_server is not UNSET:
            field_dict["h1_case_adjust_bogus_server"] = h1_case_adjust_bogus_server
        if hash_balance_factor is not UNSET:
            field_dict["hash_balance_factor"] = hash_balance_factor
        if hash_preserve_affinity is not UNSET:
            field_dict["hash_preserve_affinity"] = hash_preserve_affinity
        if hash_type is not UNSET:
            field_dict["hash_type"] = hash_type
        if http_buffer_request is not UNSET:
            field_dict["http-buffer-request"] = http_buffer_request
        if http_drop_request_trailers is not UNSET:
            field_dict["http-drop-request-trailers"] = http_drop_request_trailers
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
        if http_pretend_keepalive is not UNSET:
            field_dict["http_pretend_keepalive"] = http_pretend_keepalive
        if http_request_timeout is not UNSET:
            field_dict["http_request_timeout"] = http_request_timeout
        if http_restrict_req_hdr_names is not UNSET:
            field_dict["http_restrict_req_hdr_names"] = http_restrict_req_hdr_names
        if http_reuse is not UNSET:
            field_dict["http_reuse"] = http_reuse
        if http_send_name_header is not UNSET:
            field_dict["http_send_name_header"] = http_send_name_header
        if http_use_proxy_header is not UNSET:
            field_dict["http_use_proxy_header"] = http_use_proxy_header
        if httpchk_params is not UNSET:
            field_dict["httpchk_params"] = httpchk_params
        if httplog is not UNSET:
            field_dict["httplog"] = httplog
        if httpslog is not UNSET:
            field_dict["httpslog"] = httpslog
        if idle_close_on_response is not UNSET:
            field_dict["idle_close_on_response"] = idle_close_on_response
        if independent_streams is not UNSET:
            field_dict["independent_streams"] = independent_streams
        if load_server_state_from_file is not UNSET:
            field_dict["load_server_state_from_file"] = load_server_state_from_file
        if log_format is not UNSET:
            field_dict["log_format"] = log_format
        if log_format_sd is not UNSET:
            field_dict["log_format_sd"] = log_format_sd
        if log_health_checks is not UNSET:
            field_dict["log_health_checks"] = log_health_checks
        if log_separate_errors is not UNSET:
            field_dict["log_separate_errors"] = log_separate_errors
        if log_steps is not UNSET:
            field_dict["log_steps"] = log_steps
        if log_tag is not UNSET:
            field_dict["log_tag"] = log_tag
        if logasap is not UNSET:
            field_dict["logasap"] = logasap
        if max_keep_alive_queue is not UNSET:
            field_dict["max_keep_alive_queue"] = max_keep_alive_queue
        if maxconn is not UNSET:
            field_dict["maxconn"] = maxconn
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if mode is not UNSET:
            field_dict["mode"] = mode
        if monitor_uri is not UNSET:
            field_dict["monitor_uri"] = monitor_uri
        if mysql_check_params is not UNSET:
            field_dict["mysql_check_params"] = mysql_check_params
        if name is not UNSET:
            field_dict["name"] = name
        if nolinger is not UNSET:
            field_dict["nolinger"] = nolinger
        if originalto is not UNSET:
            field_dict["originalto"] = originalto
        if persist is not UNSET:
            field_dict["persist"] = persist
        if persist_rule is not UNSET:
            field_dict["persist_rule"] = persist_rule
        if pgsql_check_params is not UNSET:
            field_dict["pgsql_check_params"] = pgsql_check_params
        if prefer_last_server is not UNSET:
            field_dict["prefer_last_server"] = prefer_last_server
        if queue_timeout is not UNSET:
            field_dict["queue_timeout"] = queue_timeout
        if redispatch is not UNSET:
            field_dict["redispatch"] = redispatch
        if retries is not UNSET:
            field_dict["retries"] = retries
        if retry_on is not UNSET:
            field_dict["retry_on"] = retry_on
        if server_fin_timeout is not UNSET:
            field_dict["server_fin_timeout"] = server_fin_timeout
        if server_timeout is not UNSET:
            field_dict["server_timeout"] = server_timeout
        if smtpchk_params is not UNSET:
            field_dict["smtpchk_params"] = smtpchk_params
        if socket_stats is not UNSET:
            field_dict["socket_stats"] = socket_stats
        if source is not UNSET:
            field_dict["source"] = source
        if splice_auto is not UNSET:
            field_dict["splice_auto"] = splice_auto
        if splice_request is not UNSET:
            field_dict["splice_request"] = splice_request
        if splice_response is not UNSET:
            field_dict["splice_response"] = splice_response
        if srvtcpka is not UNSET:
            field_dict["srvtcpka"] = srvtcpka
        if srvtcpka_cnt is not UNSET:
            field_dict["srvtcpka_cnt"] = srvtcpka_cnt
        if srvtcpka_idle is not UNSET:
            field_dict["srvtcpka_idle"] = srvtcpka_idle
        if srvtcpka_intvl is not UNSET:
            field_dict["srvtcpka_intvl"] = srvtcpka_intvl
        if stats_options is not UNSET:
            field_dict["stats_options"] = stats_options
        if tarpit_timeout is not UNSET:
            field_dict["tarpit_timeout"] = tarpit_timeout
        if tcp_smart_accept is not UNSET:
            field_dict["tcp_smart_accept"] = tcp_smart_accept
        if tcp_smart_connect is not UNSET:
            field_dict["tcp_smart_connect"] = tcp_smart_connect
        if tcpka is not UNSET:
            field_dict["tcpka"] = tcpka
        if tcplog is not UNSET:
            field_dict["tcplog"] = tcplog
        if transparent is not UNSET:
            field_dict["transparent"] = transparent
        if tunnel_timeout is not UNSET:
            field_dict["tunnel_timeout"] = tunnel_timeout
        if unique_id_format is not UNSET:
            field_dict["unique_id_format"] = unique_id_format
        if unique_id_header is not UNSET:
            field_dict["unique_id_header"] = unique_id_header

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.balance import Balance
        from ..models.compression import Compression
        from ..models.cookie import Cookie
        from ..models.email_alert import EmailAlert
        from ..models.errorfile import Errorfile
        from ..models.errorfiles import Errorfiles
        from ..models.errorloc import Errorloc
        from ..models.forwardfor import Forwardfor
        from ..models.hash_type import HashType
        from ..models.httpchk_params import HttpchkParams
        from ..models.mysql_check_params import MysqlCheckParams
        from ..models.originalto import Originalto
        from ..models.persist_rule import PersistRule
        from ..models.pgsql_check_params import PgsqlCheckParams
        from ..models.redispatch import Redispatch
        from ..models.server_params import ServerParams
        from ..models.smtpchk_params import SmtpchkParams
        from ..models.source import Source
        from ..models.stats_options import StatsOptions

        d = dict(src_dict)
        _abortonclose = d.pop("abortonclose", UNSET)
        abortonclose: Union[Unset, DefaultsBaseAbortonclose]
        if isinstance(_abortonclose, Unset):
            abortonclose = UNSET
        else:
            abortonclose = DefaultsBaseAbortonclose(_abortonclose)

        _accept_invalid_http_request = d.pop("accept_invalid_http_request", UNSET)
        accept_invalid_http_request: Union[Unset, DefaultsBaseAcceptInvalidHttpRequest]
        if isinstance(_accept_invalid_http_request, Unset):
            accept_invalid_http_request = UNSET
        else:
            accept_invalid_http_request = DefaultsBaseAcceptInvalidHttpRequest(_accept_invalid_http_request)

        _accept_invalid_http_response = d.pop("accept_invalid_http_response", UNSET)
        accept_invalid_http_response: Union[Unset, DefaultsBaseAcceptInvalidHttpResponse]
        if isinstance(_accept_invalid_http_response, Unset):
            accept_invalid_http_response = UNSET
        else:
            accept_invalid_http_response = DefaultsBaseAcceptInvalidHttpResponse(_accept_invalid_http_response)

        _accept_unsafe_violations_in_http_request = d.pop("accept_unsafe_violations_in_http_request", UNSET)
        accept_unsafe_violations_in_http_request: Union[Unset, DefaultsBaseAcceptUnsafeViolationsInHttpRequest]
        if isinstance(_accept_unsafe_violations_in_http_request, Unset):
            accept_unsafe_violations_in_http_request = UNSET
        else:
            accept_unsafe_violations_in_http_request = DefaultsBaseAcceptUnsafeViolationsInHttpRequest(
                _accept_unsafe_violations_in_http_request
            )

        _accept_unsafe_violations_in_http_response = d.pop("accept_unsafe_violations_in_http_response", UNSET)
        accept_unsafe_violations_in_http_response: Union[Unset, DefaultsBaseAcceptUnsafeViolationsInHttpResponse]
        if isinstance(_accept_unsafe_violations_in_http_response, Unset):
            accept_unsafe_violations_in_http_response = UNSET
        else:
            accept_unsafe_violations_in_http_response = DefaultsBaseAcceptUnsafeViolationsInHttpResponse(
                _accept_unsafe_violations_in_http_response
            )

        _adv_check = d.pop("adv_check", UNSET)
        adv_check: Union[Unset, DefaultsBaseAdvCheck]
        if isinstance(_adv_check, Unset):
            adv_check = UNSET
        else:
            adv_check = DefaultsBaseAdvCheck(_adv_check)

        _allbackups = d.pop("allbackups", UNSET)
        allbackups: Union[Unset, DefaultsBaseAllbackups]
        if isinstance(_allbackups, Unset):
            allbackups = UNSET
        else:
            allbackups = DefaultsBaseAllbackups(_allbackups)

        def _parse_backlog(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        backlog = _parse_backlog(d.pop("backlog", UNSET))

        _balance = d.pop("balance", UNSET)
        balance: Union[Unset, Balance]
        if isinstance(_balance, Unset):
            balance = UNSET
        else:
            balance = Balance.from_dict(_balance)

        def _parse_check_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        check_timeout = _parse_check_timeout(d.pop("check_timeout", UNSET))

        _checkcache = d.pop("checkcache", UNSET)
        checkcache: Union[Unset, DefaultsBaseCheckcache]
        if isinstance(_checkcache, Unset):
            checkcache = UNSET
        else:
            checkcache = DefaultsBaseCheckcache(_checkcache)

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
        clitcpka: Union[Unset, DefaultsBaseClitcpka]
        if isinstance(_clitcpka, Unset):
            clitcpka = UNSET
        else:
            clitcpka = DefaultsBaseClitcpka(_clitcpka)

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

        def _parse_connect_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        connect_timeout = _parse_connect_timeout(d.pop("connect_timeout", UNSET))

        _contstats = d.pop("contstats", UNSET)
        contstats: Union[Unset, DefaultsBaseContstats]
        if isinstance(_contstats, Unset):
            contstats = UNSET
        else:
            contstats = DefaultsBaseContstats(_contstats)

        _cookie = d.pop("cookie", UNSET)
        cookie: Union[Unset, Cookie]
        if isinstance(_cookie, Unset):
            cookie = UNSET
        else:
            cookie = Cookie.from_dict(_cookie)

        default_backend = d.pop("default_backend", UNSET)

        _default_server = d.pop("default_server", UNSET)
        default_server: Union[Unset, ServerParams]
        if isinstance(_default_server, Unset):
            default_server = UNSET
        else:
            default_server = ServerParams.from_dict(_default_server)

        _disable_h2_upgrade = d.pop("disable_h2_upgrade", UNSET)
        disable_h2_upgrade: Union[Unset, DefaultsBaseDisableH2Upgrade]
        if isinstance(_disable_h2_upgrade, Unset):
            disable_h2_upgrade = UNSET
        else:
            disable_h2_upgrade = DefaultsBaseDisableH2Upgrade(_disable_h2_upgrade)

        disabled = d.pop("disabled", UNSET)

        _dontlog_normal = d.pop("dontlog_normal", UNSET)
        dontlog_normal: Union[Unset, DefaultsBaseDontlogNormal]
        if isinstance(_dontlog_normal, Unset):
            dontlog_normal = UNSET
        else:
            dontlog_normal = DefaultsBaseDontlogNormal(_dontlog_normal)

        _dontlognull = d.pop("dontlognull", UNSET)
        dontlognull: Union[Unset, DefaultsBaseDontlognull]
        if isinstance(_dontlognull, Unset):
            dontlognull = UNSET
        else:
            dontlognull = DefaultsBaseDontlognull(_dontlognull)

        dynamic_cookie_key = d.pop("dynamic_cookie_key", UNSET)

        _email_alert = d.pop("email_alert", UNSET)
        email_alert: Union[Unset, EmailAlert]
        if isinstance(_email_alert, Unset):
            email_alert = UNSET
        else:
            email_alert = EmailAlert.from_dict(_email_alert)

        enabled = d.pop("enabled", UNSET)

        _error_files = d.pop("error_files", UNSET)
        error_files: Union[Unset, list[Errorfile]] = UNSET
        if not isinstance(_error_files, Unset):
            error_files = []
            for error_files_item_data in _error_files:
                error_files_item = Errorfile.from_dict(error_files_item_data)

                error_files.append(error_files_item)

        error_log_format = d.pop("error_log_format", UNSET)

        _errorfiles_from_http_errors = d.pop("errorfiles_from_http_errors", UNSET)
        errorfiles_from_http_errors: Union[Unset, list[Errorfiles]] = UNSET
        if not isinstance(_errorfiles_from_http_errors, Unset):
            errorfiles_from_http_errors = []
            for errorfiles_from_http_errors_item_data in _errorfiles_from_http_errors:
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

        _external_check = d.pop("external_check", UNSET)
        external_check: Union[Unset, DefaultsBaseExternalCheck]
        if isinstance(_external_check, Unset):
            external_check = UNSET
        else:
            external_check = DefaultsBaseExternalCheck(_external_check)

        external_check_command = d.pop("external_check_command", UNSET)

        external_check_path = d.pop("external_check_path", UNSET)

        _forwardfor = d.pop("forwardfor", UNSET)
        forwardfor: Union[Unset, Forwardfor]
        if isinstance(_forwardfor, Unset):
            forwardfor = UNSET
        else:
            forwardfor = Forwardfor.from_dict(_forwardfor)

        from_ = d.pop("from", UNSET)

        def _parse_fullconn(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        fullconn = _parse_fullconn(d.pop("fullconn", UNSET))

        _h1_case_adjust_bogus_client = d.pop("h1_case_adjust_bogus_client", UNSET)
        h1_case_adjust_bogus_client: Union[Unset, DefaultsBaseH1CaseAdjustBogusClient]
        if isinstance(_h1_case_adjust_bogus_client, Unset):
            h1_case_adjust_bogus_client = UNSET
        else:
            h1_case_adjust_bogus_client = DefaultsBaseH1CaseAdjustBogusClient(_h1_case_adjust_bogus_client)

        _h1_case_adjust_bogus_server = d.pop("h1_case_adjust_bogus_server", UNSET)
        h1_case_adjust_bogus_server: Union[Unset, DefaultsBaseH1CaseAdjustBogusServer]
        if isinstance(_h1_case_adjust_bogus_server, Unset):
            h1_case_adjust_bogus_server = UNSET
        else:
            h1_case_adjust_bogus_server = DefaultsBaseH1CaseAdjustBogusServer(_h1_case_adjust_bogus_server)

        def _parse_hash_balance_factor(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        hash_balance_factor = _parse_hash_balance_factor(d.pop("hash_balance_factor", UNSET))

        _hash_preserve_affinity = d.pop("hash_preserve_affinity", UNSET)
        hash_preserve_affinity: Union[Unset, DefaultsBaseHashPreserveAffinity]
        if isinstance(_hash_preserve_affinity, Unset):
            hash_preserve_affinity = UNSET
        else:
            hash_preserve_affinity = DefaultsBaseHashPreserveAffinity(_hash_preserve_affinity)

        _hash_type = d.pop("hash_type", UNSET)
        hash_type: Union[Unset, HashType]
        if isinstance(_hash_type, Unset):
            hash_type = UNSET
        else:
            hash_type = HashType.from_dict(_hash_type)

        _http_buffer_request = d.pop("http-buffer-request", UNSET)
        http_buffer_request: Union[Unset, DefaultsBaseHttpBufferRequest]
        if isinstance(_http_buffer_request, Unset):
            http_buffer_request = UNSET
        else:
            http_buffer_request = DefaultsBaseHttpBufferRequest(_http_buffer_request)

        _http_drop_request_trailers = d.pop("http-drop-request-trailers", UNSET)
        http_drop_request_trailers: Union[Unset, DefaultsBaseHttpDropRequestTrailers]
        if isinstance(_http_drop_request_trailers, Unset):
            http_drop_request_trailers = UNSET
        else:
            http_drop_request_trailers = DefaultsBaseHttpDropRequestTrailers(_http_drop_request_trailers)

        _http_drop_response_trailers = d.pop("http-drop-response-trailers", UNSET)
        http_drop_response_trailers: Union[Unset, DefaultsBaseHttpDropResponseTrailers]
        if isinstance(_http_drop_response_trailers, Unset):
            http_drop_response_trailers = UNSET
        else:
            http_drop_response_trailers = DefaultsBaseHttpDropResponseTrailers(_http_drop_response_trailers)

        _http_use_htx = d.pop("http-use-htx", UNSET)
        http_use_htx: Union[Unset, DefaultsBaseHttpUseHtx]
        if isinstance(_http_use_htx, Unset):
            http_use_htx = UNSET
        else:
            http_use_htx = DefaultsBaseHttpUseHtx(_http_use_htx)

        _http_connection_mode = d.pop("http_connection_mode", UNSET)
        http_connection_mode: Union[Unset, DefaultsBaseHttpConnectionMode]
        if isinstance(_http_connection_mode, Unset):
            http_connection_mode = UNSET
        else:
            http_connection_mode = DefaultsBaseHttpConnectionMode(_http_connection_mode)

        _http_ignore_probes = d.pop("http_ignore_probes", UNSET)
        http_ignore_probes: Union[Unset, DefaultsBaseHttpIgnoreProbes]
        if isinstance(_http_ignore_probes, Unset):
            http_ignore_probes = UNSET
        else:
            http_ignore_probes = DefaultsBaseHttpIgnoreProbes(_http_ignore_probes)

        def _parse_http_keep_alive_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        http_keep_alive_timeout = _parse_http_keep_alive_timeout(d.pop("http_keep_alive_timeout", UNSET))

        _http_no_delay = d.pop("http_no_delay", UNSET)
        http_no_delay: Union[Unset, DefaultsBaseHttpNoDelay]
        if isinstance(_http_no_delay, Unset):
            http_no_delay = UNSET
        else:
            http_no_delay = DefaultsBaseHttpNoDelay(_http_no_delay)

        _http_pretend_keepalive = d.pop("http_pretend_keepalive", UNSET)
        http_pretend_keepalive: Union[Unset, DefaultsBaseHttpPretendKeepalive]
        if isinstance(_http_pretend_keepalive, Unset):
            http_pretend_keepalive = UNSET
        else:
            http_pretend_keepalive = DefaultsBaseHttpPretendKeepalive(_http_pretend_keepalive)

        def _parse_http_request_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        http_request_timeout = _parse_http_request_timeout(d.pop("http_request_timeout", UNSET))

        _http_restrict_req_hdr_names = d.pop("http_restrict_req_hdr_names", UNSET)
        http_restrict_req_hdr_names: Union[Unset, DefaultsBaseHttpRestrictReqHdrNames]
        if isinstance(_http_restrict_req_hdr_names, Unset):
            http_restrict_req_hdr_names = UNSET
        else:
            http_restrict_req_hdr_names = DefaultsBaseHttpRestrictReqHdrNames(_http_restrict_req_hdr_names)

        _http_reuse = d.pop("http_reuse", UNSET)
        http_reuse: Union[Unset, DefaultsBaseHttpReuse]
        if isinstance(_http_reuse, Unset):
            http_reuse = UNSET
        else:
            http_reuse = DefaultsBaseHttpReuse(_http_reuse)

        def _parse_http_send_name_header(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        http_send_name_header = _parse_http_send_name_header(d.pop("http_send_name_header", UNSET))

        _http_use_proxy_header = d.pop("http_use_proxy_header", UNSET)
        http_use_proxy_header: Union[Unset, DefaultsBaseHttpUseProxyHeader]
        if isinstance(_http_use_proxy_header, Unset):
            http_use_proxy_header = UNSET
        else:
            http_use_proxy_header = DefaultsBaseHttpUseProxyHeader(_http_use_proxy_header)

        _httpchk_params = d.pop("httpchk_params", UNSET)
        httpchk_params: Union[Unset, HttpchkParams]
        if isinstance(_httpchk_params, Unset):
            httpchk_params = UNSET
        else:
            httpchk_params = HttpchkParams.from_dict(_httpchk_params)

        httplog = d.pop("httplog", UNSET)

        _httpslog = d.pop("httpslog", UNSET)
        httpslog: Union[Unset, DefaultsBaseHttpslog]
        if isinstance(_httpslog, Unset):
            httpslog = UNSET
        else:
            httpslog = DefaultsBaseHttpslog(_httpslog)

        _idle_close_on_response = d.pop("idle_close_on_response", UNSET)
        idle_close_on_response: Union[Unset, DefaultsBaseIdleCloseOnResponse]
        if isinstance(_idle_close_on_response, Unset):
            idle_close_on_response = UNSET
        else:
            idle_close_on_response = DefaultsBaseIdleCloseOnResponse(_idle_close_on_response)

        _independent_streams = d.pop("independent_streams", UNSET)
        independent_streams: Union[Unset, DefaultsBaseIndependentStreams]
        if isinstance(_independent_streams, Unset):
            independent_streams = UNSET
        else:
            independent_streams = DefaultsBaseIndependentStreams(_independent_streams)

        _load_server_state_from_file = d.pop("load_server_state_from_file", UNSET)
        load_server_state_from_file: Union[Unset, DefaultsBaseLoadServerStateFromFile]
        if isinstance(_load_server_state_from_file, Unset):
            load_server_state_from_file = UNSET
        else:
            load_server_state_from_file = DefaultsBaseLoadServerStateFromFile(_load_server_state_from_file)

        log_format = d.pop("log_format", UNSET)

        log_format_sd = d.pop("log_format_sd", UNSET)

        _log_health_checks = d.pop("log_health_checks", UNSET)
        log_health_checks: Union[Unset, DefaultsBaseLogHealthChecks]
        if isinstance(_log_health_checks, Unset):
            log_health_checks = UNSET
        else:
            log_health_checks = DefaultsBaseLogHealthChecks(_log_health_checks)

        _log_separate_errors = d.pop("log_separate_errors", UNSET)
        log_separate_errors: Union[Unset, DefaultsBaseLogSeparateErrors]
        if isinstance(_log_separate_errors, Unset):
            log_separate_errors = UNSET
        else:
            log_separate_errors = DefaultsBaseLogSeparateErrors(_log_separate_errors)

        _log_steps = d.pop("log_steps", UNSET)
        log_steps: Union[Unset, list[DefaultsBaseLogStepsItem]] = UNSET
        if not isinstance(_log_steps, Unset):
            log_steps = []
            for log_steps_item_data in _log_steps:
                log_steps_item = DefaultsBaseLogStepsItem(log_steps_item_data)

                log_steps.append(log_steps_item)

        log_tag = d.pop("log_tag", UNSET)

        _logasap = d.pop("logasap", UNSET)
        logasap: Union[Unset, DefaultsBaseLogasap]
        if isinstance(_logasap, Unset):
            logasap = UNSET
        else:
            logasap = DefaultsBaseLogasap(_logasap)

        def _parse_max_keep_alive_queue(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_keep_alive_queue = _parse_max_keep_alive_queue(d.pop("max_keep_alive_queue", UNSET))

        def _parse_maxconn(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        maxconn = _parse_maxconn(d.pop("maxconn", UNSET))

        metadata = d.pop("metadata", UNSET)

        _mode = d.pop("mode", UNSET)
        mode: Union[Unset, DefaultsBaseMode]
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = DefaultsBaseMode(_mode)

        monitor_uri = d.pop("monitor_uri", UNSET)

        _mysql_check_params = d.pop("mysql_check_params", UNSET)
        mysql_check_params: Union[Unset, MysqlCheckParams]
        if isinstance(_mysql_check_params, Unset):
            mysql_check_params = UNSET
        else:
            mysql_check_params = MysqlCheckParams.from_dict(_mysql_check_params)

        name = d.pop("name", UNSET)

        _nolinger = d.pop("nolinger", UNSET)
        nolinger: Union[Unset, DefaultsBaseNolinger]
        if isinstance(_nolinger, Unset):
            nolinger = UNSET
        else:
            nolinger = DefaultsBaseNolinger(_nolinger)

        _originalto = d.pop("originalto", UNSET)
        originalto: Union[Unset, Originalto]
        if isinstance(_originalto, Unset):
            originalto = UNSET
        else:
            originalto = Originalto.from_dict(_originalto)

        _persist = d.pop("persist", UNSET)
        persist: Union[Unset, DefaultsBasePersist]
        if isinstance(_persist, Unset):
            persist = UNSET
        else:
            persist = DefaultsBasePersist(_persist)

        _persist_rule = d.pop("persist_rule", UNSET)
        persist_rule: Union[Unset, PersistRule]
        if isinstance(_persist_rule, Unset):
            persist_rule = UNSET
        else:
            persist_rule = PersistRule.from_dict(_persist_rule)

        _pgsql_check_params = d.pop("pgsql_check_params", UNSET)
        pgsql_check_params: Union[Unset, PgsqlCheckParams]
        if isinstance(_pgsql_check_params, Unset):
            pgsql_check_params = UNSET
        else:
            pgsql_check_params = PgsqlCheckParams.from_dict(_pgsql_check_params)

        _prefer_last_server = d.pop("prefer_last_server", UNSET)
        prefer_last_server: Union[Unset, DefaultsBasePreferLastServer]
        if isinstance(_prefer_last_server, Unset):
            prefer_last_server = UNSET
        else:
            prefer_last_server = DefaultsBasePreferLastServer(_prefer_last_server)

        def _parse_queue_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        queue_timeout = _parse_queue_timeout(d.pop("queue_timeout", UNSET))

        _redispatch = d.pop("redispatch", UNSET)
        redispatch: Union[Unset, Redispatch]
        if isinstance(_redispatch, Unset):
            redispatch = UNSET
        else:
            redispatch = Redispatch.from_dict(_redispatch)

        def _parse_retries(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        retries = _parse_retries(d.pop("retries", UNSET))

        retry_on = d.pop("retry_on", UNSET)

        def _parse_server_fin_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        server_fin_timeout = _parse_server_fin_timeout(d.pop("server_fin_timeout", UNSET))

        def _parse_server_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        server_timeout = _parse_server_timeout(d.pop("server_timeout", UNSET))

        _smtpchk_params = d.pop("smtpchk_params", UNSET)
        smtpchk_params: Union[Unset, SmtpchkParams]
        if isinstance(_smtpchk_params, Unset):
            smtpchk_params = UNSET
        else:
            smtpchk_params = SmtpchkParams.from_dict(_smtpchk_params)

        _socket_stats = d.pop("socket_stats", UNSET)
        socket_stats: Union[Unset, DefaultsBaseSocketStats]
        if isinstance(_socket_stats, Unset):
            socket_stats = UNSET
        else:
            socket_stats = DefaultsBaseSocketStats(_socket_stats)

        _source = d.pop("source", UNSET)
        source: Union[Unset, Source]
        if isinstance(_source, Unset):
            source = UNSET
        else:
            source = Source.from_dict(_source)

        _splice_auto = d.pop("splice_auto", UNSET)
        splice_auto: Union[Unset, DefaultsBaseSpliceAuto]
        if isinstance(_splice_auto, Unset):
            splice_auto = UNSET
        else:
            splice_auto = DefaultsBaseSpliceAuto(_splice_auto)

        _splice_request = d.pop("splice_request", UNSET)
        splice_request: Union[Unset, DefaultsBaseSpliceRequest]
        if isinstance(_splice_request, Unset):
            splice_request = UNSET
        else:
            splice_request = DefaultsBaseSpliceRequest(_splice_request)

        _splice_response = d.pop("splice_response", UNSET)
        splice_response: Union[Unset, DefaultsBaseSpliceResponse]
        if isinstance(_splice_response, Unset):
            splice_response = UNSET
        else:
            splice_response = DefaultsBaseSpliceResponse(_splice_response)

        _srvtcpka = d.pop("srvtcpka", UNSET)
        srvtcpka: Union[Unset, DefaultsBaseSrvtcpka]
        if isinstance(_srvtcpka, Unset):
            srvtcpka = UNSET
        else:
            srvtcpka = DefaultsBaseSrvtcpka(_srvtcpka)

        def _parse_srvtcpka_cnt(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        srvtcpka_cnt = _parse_srvtcpka_cnt(d.pop("srvtcpka_cnt", UNSET))

        def _parse_srvtcpka_idle(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        srvtcpka_idle = _parse_srvtcpka_idle(d.pop("srvtcpka_idle", UNSET))

        def _parse_srvtcpka_intvl(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        srvtcpka_intvl = _parse_srvtcpka_intvl(d.pop("srvtcpka_intvl", UNSET))

        _stats_options = d.pop("stats_options", UNSET)
        stats_options: Union[Unset, StatsOptions]
        if isinstance(_stats_options, Unset):
            stats_options = UNSET
        else:
            stats_options = StatsOptions.from_dict(_stats_options)

        def _parse_tarpit_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        tarpit_timeout = _parse_tarpit_timeout(d.pop("tarpit_timeout", UNSET))

        _tcp_smart_accept = d.pop("tcp_smart_accept", UNSET)
        tcp_smart_accept: Union[Unset, DefaultsBaseTcpSmartAccept]
        if isinstance(_tcp_smart_accept, Unset):
            tcp_smart_accept = UNSET
        else:
            tcp_smart_accept = DefaultsBaseTcpSmartAccept(_tcp_smart_accept)

        _tcp_smart_connect = d.pop("tcp_smart_connect", UNSET)
        tcp_smart_connect: Union[Unset, DefaultsBaseTcpSmartConnect]
        if isinstance(_tcp_smart_connect, Unset):
            tcp_smart_connect = UNSET
        else:
            tcp_smart_connect = DefaultsBaseTcpSmartConnect(_tcp_smart_connect)

        _tcpka = d.pop("tcpka", UNSET)
        tcpka: Union[Unset, DefaultsBaseTcpka]
        if isinstance(_tcpka, Unset):
            tcpka = UNSET
        else:
            tcpka = DefaultsBaseTcpka(_tcpka)

        tcplog = d.pop("tcplog", UNSET)

        _transparent = d.pop("transparent", UNSET)
        transparent: Union[Unset, DefaultsBaseTransparent]
        if isinstance(_transparent, Unset):
            transparent = UNSET
        else:
            transparent = DefaultsBaseTransparent(_transparent)

        def _parse_tunnel_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        tunnel_timeout = _parse_tunnel_timeout(d.pop("tunnel_timeout", UNSET))

        unique_id_format = d.pop("unique_id_format", UNSET)

        unique_id_header = d.pop("unique_id_header", UNSET)

        defaults_base = cls(
            abortonclose=abortonclose,
            accept_invalid_http_request=accept_invalid_http_request,
            accept_invalid_http_response=accept_invalid_http_response,
            accept_unsafe_violations_in_http_request=accept_unsafe_violations_in_http_request,
            accept_unsafe_violations_in_http_response=accept_unsafe_violations_in_http_response,
            adv_check=adv_check,
            allbackups=allbackups,
            backlog=backlog,
            balance=balance,
            check_timeout=check_timeout,
            checkcache=checkcache,
            clflog=clflog,
            client_fin_timeout=client_fin_timeout,
            client_timeout=client_timeout,
            clitcpka=clitcpka,
            clitcpka_cnt=clitcpka_cnt,
            clitcpka_idle=clitcpka_idle,
            clitcpka_intvl=clitcpka_intvl,
            compression=compression,
            connect_timeout=connect_timeout,
            contstats=contstats,
            cookie=cookie,
            default_backend=default_backend,
            default_server=default_server,
            disable_h2_upgrade=disable_h2_upgrade,
            disabled=disabled,
            dontlog_normal=dontlog_normal,
            dontlognull=dontlognull,
            dynamic_cookie_key=dynamic_cookie_key,
            email_alert=email_alert,
            enabled=enabled,
            error_files=error_files,
            error_log_format=error_log_format,
            errorfiles_from_http_errors=errorfiles_from_http_errors,
            errorloc302=errorloc302,
            errorloc303=errorloc303,
            external_check=external_check,
            external_check_command=external_check_command,
            external_check_path=external_check_path,
            forwardfor=forwardfor,
            from_=from_,
            fullconn=fullconn,
            h1_case_adjust_bogus_client=h1_case_adjust_bogus_client,
            h1_case_adjust_bogus_server=h1_case_adjust_bogus_server,
            hash_balance_factor=hash_balance_factor,
            hash_preserve_affinity=hash_preserve_affinity,
            hash_type=hash_type,
            http_buffer_request=http_buffer_request,
            http_drop_request_trailers=http_drop_request_trailers,
            http_drop_response_trailers=http_drop_response_trailers,
            http_use_htx=http_use_htx,
            http_connection_mode=http_connection_mode,
            http_ignore_probes=http_ignore_probes,
            http_keep_alive_timeout=http_keep_alive_timeout,
            http_no_delay=http_no_delay,
            http_pretend_keepalive=http_pretend_keepalive,
            http_request_timeout=http_request_timeout,
            http_restrict_req_hdr_names=http_restrict_req_hdr_names,
            http_reuse=http_reuse,
            http_send_name_header=http_send_name_header,
            http_use_proxy_header=http_use_proxy_header,
            httpchk_params=httpchk_params,
            httplog=httplog,
            httpslog=httpslog,
            idle_close_on_response=idle_close_on_response,
            independent_streams=independent_streams,
            load_server_state_from_file=load_server_state_from_file,
            log_format=log_format,
            log_format_sd=log_format_sd,
            log_health_checks=log_health_checks,
            log_separate_errors=log_separate_errors,
            log_steps=log_steps,
            log_tag=log_tag,
            logasap=logasap,
            max_keep_alive_queue=max_keep_alive_queue,
            maxconn=maxconn,
            metadata=metadata,
            mode=mode,
            monitor_uri=monitor_uri,
            mysql_check_params=mysql_check_params,
            name=name,
            nolinger=nolinger,
            originalto=originalto,
            persist=persist,
            persist_rule=persist_rule,
            pgsql_check_params=pgsql_check_params,
            prefer_last_server=prefer_last_server,
            queue_timeout=queue_timeout,
            redispatch=redispatch,
            retries=retries,
            retry_on=retry_on,
            server_fin_timeout=server_fin_timeout,
            server_timeout=server_timeout,
            smtpchk_params=smtpchk_params,
            socket_stats=socket_stats,
            source=source,
            splice_auto=splice_auto,
            splice_request=splice_request,
            splice_response=splice_response,
            srvtcpka=srvtcpka,
            srvtcpka_cnt=srvtcpka_cnt,
            srvtcpka_idle=srvtcpka_idle,
            srvtcpka_intvl=srvtcpka_intvl,
            stats_options=stats_options,
            tarpit_timeout=tarpit_timeout,
            tcp_smart_accept=tcp_smart_accept,
            tcp_smart_connect=tcp_smart_connect,
            tcpka=tcpka,
            tcplog=tcplog,
            transparent=transparent,
            tunnel_timeout=tunnel_timeout,
            unique_id_format=unique_id_format,
            unique_id_header=unique_id_header,
        )

        return defaults_base
