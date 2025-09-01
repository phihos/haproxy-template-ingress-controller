from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.backend_base_abortonclose import BackendBaseAbortonclose
from ..models.backend_base_accept_invalid_http_response import BackendBaseAcceptInvalidHttpResponse
from ..models.backend_base_accept_unsafe_violations_in_http_response import (
    BackendBaseAcceptUnsafeViolationsInHttpResponse,
)
from ..models.backend_base_adv_check import BackendBaseAdvCheck
from ..models.backend_base_allbackups import BackendBaseAllbackups
from ..models.backend_base_checkcache import BackendBaseCheckcache
from ..models.backend_base_external_check import BackendBaseExternalCheck
from ..models.backend_base_h1_case_adjust_bogus_server import BackendBaseH1CaseAdjustBogusServer
from ..models.backend_base_hash_preserve_affinity import BackendBaseHashPreserveAffinity
from ..models.backend_base_http_buffer_request import BackendBaseHttpBufferRequest
from ..models.backend_base_http_connection_mode import BackendBaseHttpConnectionMode
from ..models.backend_base_http_drop_request_trailers import BackendBaseHttpDropRequestTrailers
from ..models.backend_base_http_no_delay import BackendBaseHttpNoDelay
from ..models.backend_base_http_pretend_keepalive import BackendBaseHttpPretendKeepalive
from ..models.backend_base_http_proxy import BackendBaseHttpProxy
from ..models.backend_base_http_restrict_req_hdr_names import BackendBaseHttpRestrictReqHdrNames
from ..models.backend_base_http_reuse import BackendBaseHttpReuse
from ..models.backend_base_http_use_htx import BackendBaseHttpUseHtx
from ..models.backend_base_independent_streams import BackendBaseIndependentStreams
from ..models.backend_base_load_server_state_from_file import BackendBaseLoadServerStateFromFile
from ..models.backend_base_log_health_checks import BackendBaseLogHealthChecks
from ..models.backend_base_mode import BackendBaseMode
from ..models.backend_base_nolinger import BackendBaseNolinger
from ..models.backend_base_persist import BackendBasePersist
from ..models.backend_base_prefer_last_server import BackendBasePreferLastServer
from ..models.backend_base_splice_auto import BackendBaseSpliceAuto
from ..models.backend_base_splice_request import BackendBaseSpliceRequest
from ..models.backend_base_splice_response import BackendBaseSpliceResponse
from ..models.backend_base_spop_check import BackendBaseSpopCheck
from ..models.backend_base_srvtcpka import BackendBaseSrvtcpka
from ..models.backend_base_tcp_smart_connect import BackendBaseTcpSmartConnect
from ..models.backend_base_tcpka import BackendBaseTcpka
from ..models.backend_base_transparent import BackendBaseTransparent
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.backend_base_force_persist import BackendBaseForcePersist
    from ..models.backend_base_force_persist_list_item import BackendBaseForcePersistListItem
    from ..models.backend_base_ignore_persist import BackendBaseIgnorePersist
    from ..models.backend_base_ignore_persist_list_item import BackendBaseIgnorePersistListItem
    from ..models.balance import Balance
    from ..models.compression import Compression
    from ..models.config_stick_table import ConfigStickTable
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


T = TypeVar("T", bound="BackendBase")


@_attrs_define
class BackendBase:
    """HAProxy backend configuration

    Example:
        {'adv_check': 'httpchk', 'balance': {'algorithm': 'roundrobin'}, 'forwardfor': {'enabled': 'enabled'},
            'httpchk_params': {'method': 'GET', 'uri': '/check', 'version': 'HTTP/1.1'}, 'mode': 'http', 'name':
            'test_backend'}

    Attributes:
        name (str):
        abortonclose (Union[Unset, BackendBaseAbortonclose]):
        accept_invalid_http_response (Union[Unset, BackendBaseAcceptInvalidHttpResponse]):
        accept_unsafe_violations_in_http_response (Union[Unset, BackendBaseAcceptUnsafeViolationsInHttpResponse]):
        adv_check (Union[Unset, BackendBaseAdvCheck]):
        allbackups (Union[Unset, BackendBaseAllbackups]):
        balance (Union[Unset, Balance]):
        check_timeout (Union[None, Unset, int]):
        checkcache (Union[Unset, BackendBaseCheckcache]):
        compression (Union[Unset, Compression]):
        connect_timeout (Union[None, Unset, int]):
        cookie (Union[Unset, Cookie]):
        default_server (Union[Unset, ServerParams]):
        description (Union[Unset, str]):
        disabled (Union[Unset, bool]):
        dynamic_cookie_key (Union[Unset, str]):
        email_alert (Union[Unset, EmailAlert]): Send emails for important log messages.
        enabled (Union[Unset, bool]):
        error_files (Union[Unset, list['Errorfile']]):
        errorfiles_from_http_errors (Union[Unset, list['Errorfiles']]):
        errorloc302 (Union[Unset, Errorloc]):
        errorloc303 (Union[Unset, Errorloc]):
        external_check (Union[Unset, BackendBaseExternalCheck]):
        external_check_command (Union[Unset, str]):
        external_check_path (Union[Unset, str]):
        force_persist (Union[Unset, BackendBaseForcePersist]): This field is deprecated in favor of force_persist_list,
            and will be removed in a future release
        force_persist_list (Union[Unset, list['BackendBaseForcePersistListItem']]):
        forwardfor (Union[Unset, Forwardfor]):
        from_ (Union[Unset, str]):
        fullconn (Union[None, Unset, int]):
        guid (Union[Unset, str]):
        h1_case_adjust_bogus_server (Union[Unset, BackendBaseH1CaseAdjustBogusServer]):
        hash_balance_factor (Union[None, Unset, int]):
        hash_preserve_affinity (Union[Unset, BackendBaseHashPreserveAffinity]):
        hash_type (Union[Unset, HashType]):
        http_buffer_request (Union[Unset, BackendBaseHttpBufferRequest]):
        http_drop_request_trailers (Union[Unset, BackendBaseHttpDropRequestTrailers]):
        http_no_delay (Union[Unset, BackendBaseHttpNoDelay]):
        http_use_htx (Union[Unset, BackendBaseHttpUseHtx]):
        http_connection_mode (Union[Unset, BackendBaseHttpConnectionMode]):
        http_keep_alive_timeout (Union[None, Unset, int]):
        http_pretend_keepalive (Union[Unset, BackendBaseHttpPretendKeepalive]):
        http_proxy (Union[Unset, BackendBaseHttpProxy]):
        http_request_timeout (Union[None, Unset, int]):
        http_restrict_req_hdr_names (Union[Unset, BackendBaseHttpRestrictReqHdrNames]):
        http_reuse (Union[Unset, BackendBaseHttpReuse]):
        http_send_name_header (Union[None, Unset, str]):
        httpchk_params (Union[Unset, HttpchkParams]):
        id (Union[None, Unset, int]):
        ignore_persist (Union[Unset, BackendBaseIgnorePersist]): This field is deprecated in favor of
            ignore_persist_list, and will be removed in a future release
        ignore_persist_list (Union[Unset, list['BackendBaseIgnorePersistListItem']]):
        independent_streams (Union[Unset, BackendBaseIndependentStreams]):
        load_server_state_from_file (Union[Unset, BackendBaseLoadServerStateFromFile]):
        log_health_checks (Union[Unset, BackendBaseLogHealthChecks]):
        log_tag (Union[Unset, str]):
        max_keep_alive_queue (Union[None, Unset, int]):
        metadata (Union[Unset, Any]):
        mode (Union[Unset, BackendBaseMode]):
        mysql_check_params (Union[Unset, MysqlCheckParams]):
        nolinger (Union[Unset, BackendBaseNolinger]):
        originalto (Union[Unset, Originalto]):
        persist (Union[Unset, BackendBasePersist]):
        persist_rule (Union[Unset, PersistRule]):
        pgsql_check_params (Union[Unset, PgsqlCheckParams]):
        prefer_last_server (Union[Unset, BackendBasePreferLastServer]):
        queue_timeout (Union[None, Unset, int]):
        redispatch (Union[Unset, Redispatch]):
        retries (Union[None, Unset, int]):
        retry_on (Union[Unset, str]):
        server_fin_timeout (Union[None, Unset, int]):
        server_state_file_name (Union[Unset, str]):
        server_timeout (Union[None, Unset, int]):
        smtpchk_params (Union[Unset, SmtpchkParams]):
        source (Union[Unset, Source]):
        splice_auto (Union[Unset, BackendBaseSpliceAuto]):
        splice_request (Union[Unset, BackendBaseSpliceRequest]):
        splice_response (Union[Unset, BackendBaseSpliceResponse]):
        spop_check (Union[Unset, BackendBaseSpopCheck]):
        srvtcpka (Union[Unset, BackendBaseSrvtcpka]):
        srvtcpka_cnt (Union[None, Unset, int]):
        srvtcpka_idle (Union[None, Unset, int]):
        srvtcpka_intvl (Union[None, Unset, int]):
        stats_options (Union[Unset, StatsOptions]):
        stick_table (Union[Unset, ConfigStickTable]):
        tarpit_timeout (Union[None, Unset, int]):
        tcp_smart_connect (Union[Unset, BackendBaseTcpSmartConnect]):
        tcpka (Union[Unset, BackendBaseTcpka]):
        transparent (Union[Unset, BackendBaseTransparent]):
        tunnel_timeout (Union[None, Unset, int]):
        use_fcgi_app (Union[Unset, str]):
    """

    name: str
    abortonclose: Union[Unset, BackendBaseAbortonclose] = UNSET
    accept_invalid_http_response: Union[Unset, BackendBaseAcceptInvalidHttpResponse] = UNSET
    accept_unsafe_violations_in_http_response: Union[Unset, BackendBaseAcceptUnsafeViolationsInHttpResponse] = UNSET
    adv_check: Union[Unset, BackendBaseAdvCheck] = UNSET
    allbackups: Union[Unset, BackendBaseAllbackups] = UNSET
    balance: Union[Unset, "Balance"] = UNSET
    check_timeout: Union[None, Unset, int] = UNSET
    checkcache: Union[Unset, BackendBaseCheckcache] = UNSET
    compression: Union[Unset, "Compression"] = UNSET
    connect_timeout: Union[None, Unset, int] = UNSET
    cookie: Union[Unset, "Cookie"] = UNSET
    default_server: Union[Unset, "ServerParams"] = UNSET
    description: Union[Unset, str] = UNSET
    disabled: Union[Unset, bool] = UNSET
    dynamic_cookie_key: Union[Unset, str] = UNSET
    email_alert: Union[Unset, "EmailAlert"] = UNSET
    enabled: Union[Unset, bool] = UNSET
    error_files: Union[Unset, list["Errorfile"]] = UNSET
    errorfiles_from_http_errors: Union[Unset, list["Errorfiles"]] = UNSET
    errorloc302: Union[Unset, "Errorloc"] = UNSET
    errorloc303: Union[Unset, "Errorloc"] = UNSET
    external_check: Union[Unset, BackendBaseExternalCheck] = UNSET
    external_check_command: Union[Unset, str] = UNSET
    external_check_path: Union[Unset, str] = UNSET
    force_persist: Union[Unset, "BackendBaseForcePersist"] = UNSET
    force_persist_list: Union[Unset, list["BackendBaseForcePersistListItem"]] = UNSET
    forwardfor: Union[Unset, "Forwardfor"] = UNSET
    from_: Union[Unset, str] = UNSET
    fullconn: Union[None, Unset, int] = UNSET
    guid: Union[Unset, str] = UNSET
    h1_case_adjust_bogus_server: Union[Unset, BackendBaseH1CaseAdjustBogusServer] = UNSET
    hash_balance_factor: Union[None, Unset, int] = UNSET
    hash_preserve_affinity: Union[Unset, BackendBaseHashPreserveAffinity] = UNSET
    hash_type: Union[Unset, "HashType"] = UNSET
    http_buffer_request: Union[Unset, BackendBaseHttpBufferRequest] = UNSET
    http_drop_request_trailers: Union[Unset, BackendBaseHttpDropRequestTrailers] = UNSET
    http_no_delay: Union[Unset, BackendBaseHttpNoDelay] = UNSET
    http_use_htx: Union[Unset, BackendBaseHttpUseHtx] = UNSET
    http_connection_mode: Union[Unset, BackendBaseHttpConnectionMode] = UNSET
    http_keep_alive_timeout: Union[None, Unset, int] = UNSET
    http_pretend_keepalive: Union[Unset, BackendBaseHttpPretendKeepalive] = UNSET
    http_proxy: Union[Unset, BackendBaseHttpProxy] = UNSET
    http_request_timeout: Union[None, Unset, int] = UNSET
    http_restrict_req_hdr_names: Union[Unset, BackendBaseHttpRestrictReqHdrNames] = UNSET
    http_reuse: Union[Unset, BackendBaseHttpReuse] = UNSET
    http_send_name_header: Union[None, Unset, str] = UNSET
    httpchk_params: Union[Unset, "HttpchkParams"] = UNSET
    id: Union[None, Unset, int] = UNSET
    ignore_persist: Union[Unset, "BackendBaseIgnorePersist"] = UNSET
    ignore_persist_list: Union[Unset, list["BackendBaseIgnorePersistListItem"]] = UNSET
    independent_streams: Union[Unset, BackendBaseIndependentStreams] = UNSET
    load_server_state_from_file: Union[Unset, BackendBaseLoadServerStateFromFile] = UNSET
    log_health_checks: Union[Unset, BackendBaseLogHealthChecks] = UNSET
    log_tag: Union[Unset, str] = UNSET
    max_keep_alive_queue: Union[None, Unset, int] = UNSET
    metadata: Union[Unset, Any] = UNSET
    mode: Union[Unset, BackendBaseMode] = UNSET
    mysql_check_params: Union[Unset, "MysqlCheckParams"] = UNSET
    nolinger: Union[Unset, BackendBaseNolinger] = UNSET
    originalto: Union[Unset, "Originalto"] = UNSET
    persist: Union[Unset, BackendBasePersist] = UNSET
    persist_rule: Union[Unset, "PersistRule"] = UNSET
    pgsql_check_params: Union[Unset, "PgsqlCheckParams"] = UNSET
    prefer_last_server: Union[Unset, BackendBasePreferLastServer] = UNSET
    queue_timeout: Union[None, Unset, int] = UNSET
    redispatch: Union[Unset, "Redispatch"] = UNSET
    retries: Union[None, Unset, int] = UNSET
    retry_on: Union[Unset, str] = UNSET
    server_fin_timeout: Union[None, Unset, int] = UNSET
    server_state_file_name: Union[Unset, str] = UNSET
    server_timeout: Union[None, Unset, int] = UNSET
    smtpchk_params: Union[Unset, "SmtpchkParams"] = UNSET
    source: Union[Unset, "Source"] = UNSET
    splice_auto: Union[Unset, BackendBaseSpliceAuto] = UNSET
    splice_request: Union[Unset, BackendBaseSpliceRequest] = UNSET
    splice_response: Union[Unset, BackendBaseSpliceResponse] = UNSET
    spop_check: Union[Unset, BackendBaseSpopCheck] = UNSET
    srvtcpka: Union[Unset, BackendBaseSrvtcpka] = UNSET
    srvtcpka_cnt: Union[None, Unset, int] = UNSET
    srvtcpka_idle: Union[None, Unset, int] = UNSET
    srvtcpka_intvl: Union[None, Unset, int] = UNSET
    stats_options: Union[Unset, "StatsOptions"] = UNSET
    stick_table: Union[Unset, "ConfigStickTable"] = UNSET
    tarpit_timeout: Union[None, Unset, int] = UNSET
    tcp_smart_connect: Union[Unset, BackendBaseTcpSmartConnect] = UNSET
    tcpka: Union[Unset, BackendBaseTcpka] = UNSET
    transparent: Union[Unset, BackendBaseTransparent] = UNSET
    tunnel_timeout: Union[None, Unset, int] = UNSET
    use_fcgi_app: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        abortonclose: Union[Unset, str] = UNSET
        if not isinstance(self.abortonclose, Unset):
            abortonclose = self.abortonclose.value

        accept_invalid_http_response: Union[Unset, str] = UNSET
        if not isinstance(self.accept_invalid_http_response, Unset):
            accept_invalid_http_response = self.accept_invalid_http_response.value

        accept_unsafe_violations_in_http_response: Union[Unset, str] = UNSET
        if not isinstance(self.accept_unsafe_violations_in_http_response, Unset):
            accept_unsafe_violations_in_http_response = self.accept_unsafe_violations_in_http_response.value

        adv_check: Union[Unset, str] = UNSET
        if not isinstance(self.adv_check, Unset):
            adv_check = self.adv_check.value

        allbackups: Union[Unset, str] = UNSET
        if not isinstance(self.allbackups, Unset):
            allbackups = self.allbackups.value

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

        compression: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.compression, Unset):
            compression = self.compression.to_dict()

        connect_timeout: Union[None, Unset, int]
        if isinstance(self.connect_timeout, Unset):
            connect_timeout = UNSET
        else:
            connect_timeout = self.connect_timeout

        cookie: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.cookie, Unset):
            cookie = self.cookie.to_dict()

        default_server: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.default_server, Unset):
            default_server = self.default_server.to_dict()

        description = self.description

        disabled = self.disabled

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

        force_persist: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.force_persist, Unset):
            force_persist = self.force_persist.to_dict()

        force_persist_list: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.force_persist_list, Unset):
            force_persist_list = []
            for force_persist_list_item_data in self.force_persist_list:
                force_persist_list_item = force_persist_list_item_data.to_dict()
                force_persist_list.append(force_persist_list_item)

        forwardfor: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.forwardfor, Unset):
            forwardfor = self.forwardfor.to_dict()

        from_ = self.from_

        fullconn: Union[None, Unset, int]
        if isinstance(self.fullconn, Unset):
            fullconn = UNSET
        else:
            fullconn = self.fullconn

        guid = self.guid

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

        http_no_delay: Union[Unset, str] = UNSET
        if not isinstance(self.http_no_delay, Unset):
            http_no_delay = self.http_no_delay.value

        http_use_htx: Union[Unset, str] = UNSET
        if not isinstance(self.http_use_htx, Unset):
            http_use_htx = self.http_use_htx.value

        http_connection_mode: Union[Unset, str] = UNSET
        if not isinstance(self.http_connection_mode, Unset):
            http_connection_mode = self.http_connection_mode.value

        http_keep_alive_timeout: Union[None, Unset, int]
        if isinstance(self.http_keep_alive_timeout, Unset):
            http_keep_alive_timeout = UNSET
        else:
            http_keep_alive_timeout = self.http_keep_alive_timeout

        http_pretend_keepalive: Union[Unset, str] = UNSET
        if not isinstance(self.http_pretend_keepalive, Unset):
            http_pretend_keepalive = self.http_pretend_keepalive.value

        http_proxy: Union[Unset, str] = UNSET
        if not isinstance(self.http_proxy, Unset):
            http_proxy = self.http_proxy.value

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

        httpchk_params: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.httpchk_params, Unset):
            httpchk_params = self.httpchk_params.to_dict()

        id: Union[None, Unset, int]
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        ignore_persist: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.ignore_persist, Unset):
            ignore_persist = self.ignore_persist.to_dict()

        ignore_persist_list: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.ignore_persist_list, Unset):
            ignore_persist_list = []
            for ignore_persist_list_item_data in self.ignore_persist_list:
                ignore_persist_list_item = ignore_persist_list_item_data.to_dict()
                ignore_persist_list.append(ignore_persist_list_item)

        independent_streams: Union[Unset, str] = UNSET
        if not isinstance(self.independent_streams, Unset):
            independent_streams = self.independent_streams.value

        load_server_state_from_file: Union[Unset, str] = UNSET
        if not isinstance(self.load_server_state_from_file, Unset):
            load_server_state_from_file = self.load_server_state_from_file.value

        log_health_checks: Union[Unset, str] = UNSET
        if not isinstance(self.log_health_checks, Unset):
            log_health_checks = self.log_health_checks.value

        log_tag = self.log_tag

        max_keep_alive_queue: Union[None, Unset, int]
        if isinstance(self.max_keep_alive_queue, Unset):
            max_keep_alive_queue = UNSET
        else:
            max_keep_alive_queue = self.max_keep_alive_queue

        metadata = self.metadata

        mode: Union[Unset, str] = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        mysql_check_params: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.mysql_check_params, Unset):
            mysql_check_params = self.mysql_check_params.to_dict()

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

        server_state_file_name = self.server_state_file_name

        server_timeout: Union[None, Unset, int]
        if isinstance(self.server_timeout, Unset):
            server_timeout = UNSET
        else:
            server_timeout = self.server_timeout

        smtpchk_params: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.smtpchk_params, Unset):
            smtpchk_params = self.smtpchk_params.to_dict()

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

        spop_check: Union[Unset, str] = UNSET
        if not isinstance(self.spop_check, Unset):
            spop_check = self.spop_check.value

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

        stick_table: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.stick_table, Unset):
            stick_table = self.stick_table.to_dict()

        tarpit_timeout: Union[None, Unset, int]
        if isinstance(self.tarpit_timeout, Unset):
            tarpit_timeout = UNSET
        else:
            tarpit_timeout = self.tarpit_timeout

        tcp_smart_connect: Union[Unset, str] = UNSET
        if not isinstance(self.tcp_smart_connect, Unset):
            tcp_smart_connect = self.tcp_smart_connect.value

        tcpka: Union[Unset, str] = UNSET
        if not isinstance(self.tcpka, Unset):
            tcpka = self.tcpka.value

        transparent: Union[Unset, str] = UNSET
        if not isinstance(self.transparent, Unset):
            transparent = self.transparent.value

        tunnel_timeout: Union[None, Unset, int]
        if isinstance(self.tunnel_timeout, Unset):
            tunnel_timeout = UNSET
        else:
            tunnel_timeout = self.tunnel_timeout

        use_fcgi_app = self.use_fcgi_app

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )
        if abortonclose is not UNSET:
            field_dict["abortonclose"] = abortonclose
        if accept_invalid_http_response is not UNSET:
            field_dict["accept_invalid_http_response"] = accept_invalid_http_response
        if accept_unsafe_violations_in_http_response is not UNSET:
            field_dict["accept_unsafe_violations_in_http_response"] = accept_unsafe_violations_in_http_response
        if adv_check is not UNSET:
            field_dict["adv_check"] = adv_check
        if allbackups is not UNSET:
            field_dict["allbackups"] = allbackups
        if balance is not UNSET:
            field_dict["balance"] = balance
        if check_timeout is not UNSET:
            field_dict["check_timeout"] = check_timeout
        if checkcache is not UNSET:
            field_dict["checkcache"] = checkcache
        if compression is not UNSET:
            field_dict["compression"] = compression
        if connect_timeout is not UNSET:
            field_dict["connect_timeout"] = connect_timeout
        if cookie is not UNSET:
            field_dict["cookie"] = cookie
        if default_server is not UNSET:
            field_dict["default_server"] = default_server
        if description is not UNSET:
            field_dict["description"] = description
        if disabled is not UNSET:
            field_dict["disabled"] = disabled
        if dynamic_cookie_key is not UNSET:
            field_dict["dynamic_cookie_key"] = dynamic_cookie_key
        if email_alert is not UNSET:
            field_dict["email_alert"] = email_alert
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if error_files is not UNSET:
            field_dict["error_files"] = error_files
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
        if force_persist is not UNSET:
            field_dict["force_persist"] = force_persist
        if force_persist_list is not UNSET:
            field_dict["force_persist_list"] = force_persist_list
        if forwardfor is not UNSET:
            field_dict["forwardfor"] = forwardfor
        if from_ is not UNSET:
            field_dict["from"] = from_
        if fullconn is not UNSET:
            field_dict["fullconn"] = fullconn
        if guid is not UNSET:
            field_dict["guid"] = guid
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
        if http_no_delay is not UNSET:
            field_dict["http-no-delay"] = http_no_delay
        if http_use_htx is not UNSET:
            field_dict["http-use-htx"] = http_use_htx
        if http_connection_mode is not UNSET:
            field_dict["http_connection_mode"] = http_connection_mode
        if http_keep_alive_timeout is not UNSET:
            field_dict["http_keep_alive_timeout"] = http_keep_alive_timeout
        if http_pretend_keepalive is not UNSET:
            field_dict["http_pretend_keepalive"] = http_pretend_keepalive
        if http_proxy is not UNSET:
            field_dict["http_proxy"] = http_proxy
        if http_request_timeout is not UNSET:
            field_dict["http_request_timeout"] = http_request_timeout
        if http_restrict_req_hdr_names is not UNSET:
            field_dict["http_restrict_req_hdr_names"] = http_restrict_req_hdr_names
        if http_reuse is not UNSET:
            field_dict["http_reuse"] = http_reuse
        if http_send_name_header is not UNSET:
            field_dict["http_send_name_header"] = http_send_name_header
        if httpchk_params is not UNSET:
            field_dict["httpchk_params"] = httpchk_params
        if id is not UNSET:
            field_dict["id"] = id
        if ignore_persist is not UNSET:
            field_dict["ignore_persist"] = ignore_persist
        if ignore_persist_list is not UNSET:
            field_dict["ignore_persist_list"] = ignore_persist_list
        if independent_streams is not UNSET:
            field_dict["independent_streams"] = independent_streams
        if load_server_state_from_file is not UNSET:
            field_dict["load_server_state_from_file"] = load_server_state_from_file
        if log_health_checks is not UNSET:
            field_dict["log_health_checks"] = log_health_checks
        if log_tag is not UNSET:
            field_dict["log_tag"] = log_tag
        if max_keep_alive_queue is not UNSET:
            field_dict["max_keep_alive_queue"] = max_keep_alive_queue
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if mode is not UNSET:
            field_dict["mode"] = mode
        if mysql_check_params is not UNSET:
            field_dict["mysql_check_params"] = mysql_check_params
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
        if server_state_file_name is not UNSET:
            field_dict["server_state_file_name"] = server_state_file_name
        if server_timeout is not UNSET:
            field_dict["server_timeout"] = server_timeout
        if smtpchk_params is not UNSET:
            field_dict["smtpchk_params"] = smtpchk_params
        if source is not UNSET:
            field_dict["source"] = source
        if splice_auto is not UNSET:
            field_dict["splice_auto"] = splice_auto
        if splice_request is not UNSET:
            field_dict["splice_request"] = splice_request
        if splice_response is not UNSET:
            field_dict["splice_response"] = splice_response
        if spop_check is not UNSET:
            field_dict["spop_check"] = spop_check
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
        if stick_table is not UNSET:
            field_dict["stick_table"] = stick_table
        if tarpit_timeout is not UNSET:
            field_dict["tarpit_timeout"] = tarpit_timeout
        if tcp_smart_connect is not UNSET:
            field_dict["tcp_smart_connect"] = tcp_smart_connect
        if tcpka is not UNSET:
            field_dict["tcpka"] = tcpka
        if transparent is not UNSET:
            field_dict["transparent"] = transparent
        if tunnel_timeout is not UNSET:
            field_dict["tunnel_timeout"] = tunnel_timeout
        if use_fcgi_app is not UNSET:
            field_dict["use_fcgi_app"] = use_fcgi_app

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.backend_base_force_persist import BackendBaseForcePersist
        from ..models.backend_base_force_persist_list_item import BackendBaseForcePersistListItem
        from ..models.backend_base_ignore_persist import BackendBaseIgnorePersist
        from ..models.backend_base_ignore_persist_list_item import BackendBaseIgnorePersistListItem
        from ..models.balance import Balance
        from ..models.compression import Compression
        from ..models.config_stick_table import ConfigStickTable
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
        name = d.pop("name")

        _abortonclose = d.pop("abortonclose", UNSET)
        abortonclose: Union[Unset, BackendBaseAbortonclose]
        if isinstance(_abortonclose, Unset):
            abortonclose = UNSET
        else:
            abortonclose = BackendBaseAbortonclose(_abortonclose)

        _accept_invalid_http_response = d.pop("accept_invalid_http_response", UNSET)
        accept_invalid_http_response: Union[Unset, BackendBaseAcceptInvalidHttpResponse]
        if isinstance(_accept_invalid_http_response, Unset):
            accept_invalid_http_response = UNSET
        else:
            accept_invalid_http_response = BackendBaseAcceptInvalidHttpResponse(_accept_invalid_http_response)

        _accept_unsafe_violations_in_http_response = d.pop("accept_unsafe_violations_in_http_response", UNSET)
        accept_unsafe_violations_in_http_response: Union[Unset, BackendBaseAcceptUnsafeViolationsInHttpResponse]
        if isinstance(_accept_unsafe_violations_in_http_response, Unset):
            accept_unsafe_violations_in_http_response = UNSET
        else:
            accept_unsafe_violations_in_http_response = BackendBaseAcceptUnsafeViolationsInHttpResponse(
                _accept_unsafe_violations_in_http_response
            )

        _adv_check = d.pop("adv_check", UNSET)
        adv_check: Union[Unset, BackendBaseAdvCheck]
        if isinstance(_adv_check, Unset):
            adv_check = UNSET
        else:
            adv_check = BackendBaseAdvCheck(_adv_check)

        _allbackups = d.pop("allbackups", UNSET)
        allbackups: Union[Unset, BackendBaseAllbackups]
        if isinstance(_allbackups, Unset):
            allbackups = UNSET
        else:
            allbackups = BackendBaseAllbackups(_allbackups)

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
        checkcache: Union[Unset, BackendBaseCheckcache]
        if isinstance(_checkcache, Unset):
            checkcache = UNSET
        else:
            checkcache = BackendBaseCheckcache(_checkcache)

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

        _cookie = d.pop("cookie", UNSET)
        cookie: Union[Unset, Cookie]
        if isinstance(_cookie, Unset):
            cookie = UNSET
        else:
            cookie = Cookie.from_dict(_cookie)

        _default_server = d.pop("default_server", UNSET)
        default_server: Union[Unset, ServerParams]
        if isinstance(_default_server, Unset):
            default_server = UNSET
        else:
            default_server = ServerParams.from_dict(_default_server)

        description = d.pop("description", UNSET)

        disabled = d.pop("disabled", UNSET)

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
        external_check: Union[Unset, BackendBaseExternalCheck]
        if isinstance(_external_check, Unset):
            external_check = UNSET
        else:
            external_check = BackendBaseExternalCheck(_external_check)

        external_check_command = d.pop("external_check_command", UNSET)

        external_check_path = d.pop("external_check_path", UNSET)

        _force_persist = d.pop("force_persist", UNSET)
        force_persist: Union[Unset, BackendBaseForcePersist]
        if isinstance(_force_persist, Unset):
            force_persist = UNSET
        else:
            force_persist = BackendBaseForcePersist.from_dict(_force_persist)

        _force_persist_list = d.pop("force_persist_list", UNSET)
        force_persist_list: Union[Unset, list[BackendBaseForcePersistListItem]] = UNSET
        if not isinstance(_force_persist_list, Unset):
            force_persist_list = []
            for force_persist_list_item_data in _force_persist_list:
                force_persist_list_item = BackendBaseForcePersistListItem.from_dict(force_persist_list_item_data)

                force_persist_list.append(force_persist_list_item)

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

        guid = d.pop("guid", UNSET)

        _h1_case_adjust_bogus_server = d.pop("h1_case_adjust_bogus_server", UNSET)
        h1_case_adjust_bogus_server: Union[Unset, BackendBaseH1CaseAdjustBogusServer]
        if isinstance(_h1_case_adjust_bogus_server, Unset):
            h1_case_adjust_bogus_server = UNSET
        else:
            h1_case_adjust_bogus_server = BackendBaseH1CaseAdjustBogusServer(_h1_case_adjust_bogus_server)

        def _parse_hash_balance_factor(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        hash_balance_factor = _parse_hash_balance_factor(d.pop("hash_balance_factor", UNSET))

        _hash_preserve_affinity = d.pop("hash_preserve_affinity", UNSET)
        hash_preserve_affinity: Union[Unset, BackendBaseHashPreserveAffinity]
        if isinstance(_hash_preserve_affinity, Unset):
            hash_preserve_affinity = UNSET
        else:
            hash_preserve_affinity = BackendBaseHashPreserveAffinity(_hash_preserve_affinity)

        _hash_type = d.pop("hash_type", UNSET)
        hash_type: Union[Unset, HashType]
        if isinstance(_hash_type, Unset):
            hash_type = UNSET
        else:
            hash_type = HashType.from_dict(_hash_type)

        _http_buffer_request = d.pop("http-buffer-request", UNSET)
        http_buffer_request: Union[Unset, BackendBaseHttpBufferRequest]
        if isinstance(_http_buffer_request, Unset):
            http_buffer_request = UNSET
        else:
            http_buffer_request = BackendBaseHttpBufferRequest(_http_buffer_request)

        _http_drop_request_trailers = d.pop("http-drop-request-trailers", UNSET)
        http_drop_request_trailers: Union[Unset, BackendBaseHttpDropRequestTrailers]
        if isinstance(_http_drop_request_trailers, Unset):
            http_drop_request_trailers = UNSET
        else:
            http_drop_request_trailers = BackendBaseHttpDropRequestTrailers(_http_drop_request_trailers)

        _http_no_delay = d.pop("http-no-delay", UNSET)
        http_no_delay: Union[Unset, BackendBaseHttpNoDelay]
        if isinstance(_http_no_delay, Unset):
            http_no_delay = UNSET
        else:
            http_no_delay = BackendBaseHttpNoDelay(_http_no_delay)

        _http_use_htx = d.pop("http-use-htx", UNSET)
        http_use_htx: Union[Unset, BackendBaseHttpUseHtx]
        if isinstance(_http_use_htx, Unset):
            http_use_htx = UNSET
        else:
            http_use_htx = BackendBaseHttpUseHtx(_http_use_htx)

        _http_connection_mode = d.pop("http_connection_mode", UNSET)
        http_connection_mode: Union[Unset, BackendBaseHttpConnectionMode]
        if isinstance(_http_connection_mode, Unset):
            http_connection_mode = UNSET
        else:
            http_connection_mode = BackendBaseHttpConnectionMode(_http_connection_mode)

        def _parse_http_keep_alive_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        http_keep_alive_timeout = _parse_http_keep_alive_timeout(d.pop("http_keep_alive_timeout", UNSET))

        _http_pretend_keepalive = d.pop("http_pretend_keepalive", UNSET)
        http_pretend_keepalive: Union[Unset, BackendBaseHttpPretendKeepalive]
        if isinstance(_http_pretend_keepalive, Unset):
            http_pretend_keepalive = UNSET
        else:
            http_pretend_keepalive = BackendBaseHttpPretendKeepalive(_http_pretend_keepalive)

        _http_proxy = d.pop("http_proxy", UNSET)
        http_proxy: Union[Unset, BackendBaseHttpProxy]
        if isinstance(_http_proxy, Unset):
            http_proxy = UNSET
        else:
            http_proxy = BackendBaseHttpProxy(_http_proxy)

        def _parse_http_request_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        http_request_timeout = _parse_http_request_timeout(d.pop("http_request_timeout", UNSET))

        _http_restrict_req_hdr_names = d.pop("http_restrict_req_hdr_names", UNSET)
        http_restrict_req_hdr_names: Union[Unset, BackendBaseHttpRestrictReqHdrNames]
        if isinstance(_http_restrict_req_hdr_names, Unset):
            http_restrict_req_hdr_names = UNSET
        else:
            http_restrict_req_hdr_names = BackendBaseHttpRestrictReqHdrNames(_http_restrict_req_hdr_names)

        _http_reuse = d.pop("http_reuse", UNSET)
        http_reuse: Union[Unset, BackendBaseHttpReuse]
        if isinstance(_http_reuse, Unset):
            http_reuse = UNSET
        else:
            http_reuse = BackendBaseHttpReuse(_http_reuse)

        def _parse_http_send_name_header(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        http_send_name_header = _parse_http_send_name_header(d.pop("http_send_name_header", UNSET))

        _httpchk_params = d.pop("httpchk_params", UNSET)
        httpchk_params: Union[Unset, HttpchkParams]
        if isinstance(_httpchk_params, Unset):
            httpchk_params = UNSET
        else:
            httpchk_params = HttpchkParams.from_dict(_httpchk_params)

        def _parse_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        id = _parse_id(d.pop("id", UNSET))

        _ignore_persist = d.pop("ignore_persist", UNSET)
        ignore_persist: Union[Unset, BackendBaseIgnorePersist]
        if isinstance(_ignore_persist, Unset):
            ignore_persist = UNSET
        else:
            ignore_persist = BackendBaseIgnorePersist.from_dict(_ignore_persist)

        _ignore_persist_list = d.pop("ignore_persist_list", UNSET)
        ignore_persist_list: Union[Unset, list[BackendBaseIgnorePersistListItem]] = UNSET
        if not isinstance(_ignore_persist_list, Unset):
            ignore_persist_list = []
            for ignore_persist_list_item_data in _ignore_persist_list:
                ignore_persist_list_item = BackendBaseIgnorePersistListItem.from_dict(ignore_persist_list_item_data)

                ignore_persist_list.append(ignore_persist_list_item)

        _independent_streams = d.pop("independent_streams", UNSET)
        independent_streams: Union[Unset, BackendBaseIndependentStreams]
        if isinstance(_independent_streams, Unset):
            independent_streams = UNSET
        else:
            independent_streams = BackendBaseIndependentStreams(_independent_streams)

        _load_server_state_from_file = d.pop("load_server_state_from_file", UNSET)
        load_server_state_from_file: Union[Unset, BackendBaseLoadServerStateFromFile]
        if isinstance(_load_server_state_from_file, Unset):
            load_server_state_from_file = UNSET
        else:
            load_server_state_from_file = BackendBaseLoadServerStateFromFile(_load_server_state_from_file)

        _log_health_checks = d.pop("log_health_checks", UNSET)
        log_health_checks: Union[Unset, BackendBaseLogHealthChecks]
        if isinstance(_log_health_checks, Unset):
            log_health_checks = UNSET
        else:
            log_health_checks = BackendBaseLogHealthChecks(_log_health_checks)

        log_tag = d.pop("log_tag", UNSET)

        def _parse_max_keep_alive_queue(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_keep_alive_queue = _parse_max_keep_alive_queue(d.pop("max_keep_alive_queue", UNSET))

        metadata = d.pop("metadata", UNSET)

        _mode = d.pop("mode", UNSET)
        mode: Union[Unset, BackendBaseMode]
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = BackendBaseMode(_mode)

        _mysql_check_params = d.pop("mysql_check_params", UNSET)
        mysql_check_params: Union[Unset, MysqlCheckParams]
        if isinstance(_mysql_check_params, Unset):
            mysql_check_params = UNSET
        else:
            mysql_check_params = MysqlCheckParams.from_dict(_mysql_check_params)

        _nolinger = d.pop("nolinger", UNSET)
        nolinger: Union[Unset, BackendBaseNolinger]
        if isinstance(_nolinger, Unset):
            nolinger = UNSET
        else:
            nolinger = BackendBaseNolinger(_nolinger)

        _originalto = d.pop("originalto", UNSET)
        originalto: Union[Unset, Originalto]
        if isinstance(_originalto, Unset):
            originalto = UNSET
        else:
            originalto = Originalto.from_dict(_originalto)

        _persist = d.pop("persist", UNSET)
        persist: Union[Unset, BackendBasePersist]
        if isinstance(_persist, Unset):
            persist = UNSET
        else:
            persist = BackendBasePersist(_persist)

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
        prefer_last_server: Union[Unset, BackendBasePreferLastServer]
        if isinstance(_prefer_last_server, Unset):
            prefer_last_server = UNSET
        else:
            prefer_last_server = BackendBasePreferLastServer(_prefer_last_server)

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

        server_state_file_name = d.pop("server_state_file_name", UNSET)

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

        _source = d.pop("source", UNSET)
        source: Union[Unset, Source]
        if isinstance(_source, Unset):
            source = UNSET
        else:
            source = Source.from_dict(_source)

        _splice_auto = d.pop("splice_auto", UNSET)
        splice_auto: Union[Unset, BackendBaseSpliceAuto]
        if isinstance(_splice_auto, Unset):
            splice_auto = UNSET
        else:
            splice_auto = BackendBaseSpliceAuto(_splice_auto)

        _splice_request = d.pop("splice_request", UNSET)
        splice_request: Union[Unset, BackendBaseSpliceRequest]
        if isinstance(_splice_request, Unset):
            splice_request = UNSET
        else:
            splice_request = BackendBaseSpliceRequest(_splice_request)

        _splice_response = d.pop("splice_response", UNSET)
        splice_response: Union[Unset, BackendBaseSpliceResponse]
        if isinstance(_splice_response, Unset):
            splice_response = UNSET
        else:
            splice_response = BackendBaseSpliceResponse(_splice_response)

        _spop_check = d.pop("spop_check", UNSET)
        spop_check: Union[Unset, BackendBaseSpopCheck]
        if isinstance(_spop_check, Unset):
            spop_check = UNSET
        else:
            spop_check = BackendBaseSpopCheck(_spop_check)

        _srvtcpka = d.pop("srvtcpka", UNSET)
        srvtcpka: Union[Unset, BackendBaseSrvtcpka]
        if isinstance(_srvtcpka, Unset):
            srvtcpka = UNSET
        else:
            srvtcpka = BackendBaseSrvtcpka(_srvtcpka)

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

        _tcp_smart_connect = d.pop("tcp_smart_connect", UNSET)
        tcp_smart_connect: Union[Unset, BackendBaseTcpSmartConnect]
        if isinstance(_tcp_smart_connect, Unset):
            tcp_smart_connect = UNSET
        else:
            tcp_smart_connect = BackendBaseTcpSmartConnect(_tcp_smart_connect)

        _tcpka = d.pop("tcpka", UNSET)
        tcpka: Union[Unset, BackendBaseTcpka]
        if isinstance(_tcpka, Unset):
            tcpka = UNSET
        else:
            tcpka = BackendBaseTcpka(_tcpka)

        _transparent = d.pop("transparent", UNSET)
        transparent: Union[Unset, BackendBaseTransparent]
        if isinstance(_transparent, Unset):
            transparent = UNSET
        else:
            transparent = BackendBaseTransparent(_transparent)

        def _parse_tunnel_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        tunnel_timeout = _parse_tunnel_timeout(d.pop("tunnel_timeout", UNSET))

        use_fcgi_app = d.pop("use_fcgi_app", UNSET)

        backend_base = cls(
            name=name,
            abortonclose=abortonclose,
            accept_invalid_http_response=accept_invalid_http_response,
            accept_unsafe_violations_in_http_response=accept_unsafe_violations_in_http_response,
            adv_check=adv_check,
            allbackups=allbackups,
            balance=balance,
            check_timeout=check_timeout,
            checkcache=checkcache,
            compression=compression,
            connect_timeout=connect_timeout,
            cookie=cookie,
            default_server=default_server,
            description=description,
            disabled=disabled,
            dynamic_cookie_key=dynamic_cookie_key,
            email_alert=email_alert,
            enabled=enabled,
            error_files=error_files,
            errorfiles_from_http_errors=errorfiles_from_http_errors,
            errorloc302=errorloc302,
            errorloc303=errorloc303,
            external_check=external_check,
            external_check_command=external_check_command,
            external_check_path=external_check_path,
            force_persist=force_persist,
            force_persist_list=force_persist_list,
            forwardfor=forwardfor,
            from_=from_,
            fullconn=fullconn,
            guid=guid,
            h1_case_adjust_bogus_server=h1_case_adjust_bogus_server,
            hash_balance_factor=hash_balance_factor,
            hash_preserve_affinity=hash_preserve_affinity,
            hash_type=hash_type,
            http_buffer_request=http_buffer_request,
            http_drop_request_trailers=http_drop_request_trailers,
            http_no_delay=http_no_delay,
            http_use_htx=http_use_htx,
            http_connection_mode=http_connection_mode,
            http_keep_alive_timeout=http_keep_alive_timeout,
            http_pretend_keepalive=http_pretend_keepalive,
            http_proxy=http_proxy,
            http_request_timeout=http_request_timeout,
            http_restrict_req_hdr_names=http_restrict_req_hdr_names,
            http_reuse=http_reuse,
            http_send_name_header=http_send_name_header,
            httpchk_params=httpchk_params,
            id=id,
            ignore_persist=ignore_persist,
            ignore_persist_list=ignore_persist_list,
            independent_streams=independent_streams,
            load_server_state_from_file=load_server_state_from_file,
            log_health_checks=log_health_checks,
            log_tag=log_tag,
            max_keep_alive_queue=max_keep_alive_queue,
            metadata=metadata,
            mode=mode,
            mysql_check_params=mysql_check_params,
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
            server_state_file_name=server_state_file_name,
            server_timeout=server_timeout,
            smtpchk_params=smtpchk_params,
            source=source,
            splice_auto=splice_auto,
            splice_request=splice_request,
            splice_response=splice_response,
            spop_check=spop_check,
            srvtcpka=srvtcpka,
            srvtcpka_cnt=srvtcpka_cnt,
            srvtcpka_idle=srvtcpka_idle,
            srvtcpka_intvl=srvtcpka_intvl,
            stats_options=stats_options,
            stick_table=stick_table,
            tarpit_timeout=tarpit_timeout,
            tcp_smart_connect=tcp_smart_connect,
            tcpka=tcpka,
            transparent=transparent,
            tunnel_timeout=tunnel_timeout,
            use_fcgi_app=use_fcgi_app,
        )

        return backend_base
