from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..models.server_params_agent_check import ServerParamsAgentCheck
from ..models.server_params_backup import ServerParamsBackup
from ..models.server_params_check import ServerParamsCheck
from ..models.server_params_check_reuse_pool import ServerParamsCheckReusePool
from ..models.server_params_check_send_proxy import ServerParamsCheckSendProxy
from ..models.server_params_check_ssl import ServerParamsCheckSsl
from ..models.server_params_check_via_socks_4 import ServerParamsCheckViaSocks4
from ..models.server_params_force_sslv_3 import ServerParamsForceSslv3
from ..models.server_params_force_tlsv_10 import ServerParamsForceTlsv10
from ..models.server_params_force_tlsv_11 import ServerParamsForceTlsv11
from ..models.server_params_force_tlsv_12 import ServerParamsForceTlsv12
from ..models.server_params_force_tlsv_13 import ServerParamsForceTlsv13
from ..models.server_params_init_state import ServerParamsInitState
from ..models.server_params_log_proto import ServerParamsLogProto
from ..models.server_params_maintenance import ServerParamsMaintenance
from ..models.server_params_no_sslv_3 import ServerParamsNoSslv3
from ..models.server_params_no_tlsv_10 import ServerParamsNoTlsv10
from ..models.server_params_no_tlsv_11 import ServerParamsNoTlsv11
from ..models.server_params_no_tlsv_12 import ServerParamsNoTlsv12
from ..models.server_params_no_tlsv_13 import ServerParamsNoTlsv13
from ..models.server_params_no_verifyhost import ServerParamsNoVerifyhost
from ..models.server_params_observe import ServerParamsObserve
from ..models.server_params_on_error import ServerParamsOnError
from ..models.server_params_on_marked_down import ServerParamsOnMarkedDown
from ..models.server_params_on_marked_up import ServerParamsOnMarkedUp
from ..models.server_params_proxy_v2_options_item import ServerParamsProxyV2OptionsItem
from ..models.server_params_resolve_prefer import ServerParamsResolvePrefer
from ..models.server_params_send_proxy import ServerParamsSendProxy
from ..models.server_params_send_proxy_v2 import ServerParamsSendProxyV2
from ..models.server_params_send_proxy_v2_ssl import ServerParamsSendProxyV2Ssl
from ..models.server_params_send_proxy_v2_ssl_cn import ServerParamsSendProxyV2SslCn
from ..models.server_params_ssl import ServerParamsSsl
from ..models.server_params_ssl_max_ver import ServerParamsSslMaxVer
from ..models.server_params_ssl_min_ver import ServerParamsSslMinVer
from ..models.server_params_ssl_reuse import ServerParamsSslReuse
from ..models.server_params_sslv_3 import ServerParamsSslv3
from ..models.server_params_stick import ServerParamsStick
from ..models.server_params_tfo import ServerParamsTfo
from ..models.server_params_tls_tickets import ServerParamsTlsTickets
from ..models.server_params_tlsv_10 import ServerParamsTlsv10
from ..models.server_params_tlsv_11 import ServerParamsTlsv11
from ..models.server_params_tlsv_12 import ServerParamsTlsv12
from ..models.server_params_tlsv_13 import ServerParamsTlsv13
from ..models.server_params_verify import ServerParamsVerify
from ..models.server_params_ws import ServerParamsWs
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.server_params_set_proxy_v2_tlv_fmt import ServerParamsSetProxyV2TlvFmt


T = TypeVar("T", bound="ServerTemplate")


@_attrs_define
class ServerTemplate:
    """Set a template to initialize servers with shared parameters.

    Example:
        {'fqdn': 'google.com', 'num_or_range': '1-3', 'port': 80, 'prefix': 'srv'}

    Attributes:
        fqdn (str):
        num_or_range (str):
        prefix (str):
        agent_addr (Union[Unset, str]):
        agent_check (Union[Unset, ServerParamsAgentCheck]):
        agent_inter (Union[None, Unset, int]):
        agent_port (Union[None, Unset, int]):
        agent_send (Union[Unset, str]):
        allow_0rtt (Union[Unset, bool]):
        alpn (Union[Unset, str]):
        backup (Union[Unset, ServerParamsBackup]):
        check (Union[Unset, ServerParamsCheck]):
        check_pool_conn_name (Union[Unset, str]):
        check_reuse_pool (Union[Unset, ServerParamsCheckReusePool]):
        check_send_proxy (Union[Unset, ServerParamsCheckSendProxy]):
        check_sni (Union[Unset, str]):
        check_ssl (Union[Unset, ServerParamsCheckSsl]):
        check_alpn (Union[Unset, str]):
        check_proto (Union[Unset, str]):
        check_via_socks4 (Union[Unset, ServerParamsCheckViaSocks4]):
        ciphers (Union[Unset, str]):
        ciphersuites (Union[Unset, str]):
        client_sigalgs (Union[Unset, str]):
        cookie (Union[Unset, str]):
        crl_file (Union[Unset, str]):
        curves (Union[Unset, str]):
        downinter (Union[None, Unset, int]):
        error_limit (Union[Unset, int]):
        fall (Union[None, Unset, int]):
        fastinter (Union[None, Unset, int]):
        force_sslv3 (Union[Unset, ServerParamsForceSslv3]): This field is deprecated in favor of sslv3, and will be
            removed in a future release
        force_tlsv10 (Union[Unset, ServerParamsForceTlsv10]): This field is deprecated in favor of tlsv10, and will be
            removed in a future release
        force_tlsv11 (Union[Unset, ServerParamsForceTlsv11]): This field is deprecated in favor of tlsv11, and will be
            removed in a future release
        force_tlsv12 (Union[Unset, ServerParamsForceTlsv12]): This field is deprecated in favor of tlsv12, and will be
            removed in a future release
        force_tlsv13 (Union[Unset, ServerParamsForceTlsv13]): This field is deprecated in favor of tlsv13, and will be
            removed in a future release
        guid (Union[Unset, str]):
        hash_key (Union[Unset, str]):
        health_check_address (Union[Unset, str]):
        health_check_port (Union[None, Unset, int]):
        idle_ping (Union[None, Unset, int]):
        init_addr (Union[None, Unset, str]):
        init_state (Union[Unset, ServerParamsInitState]):
        inter (Union[None, Unset, int]):
        log_bufsize (Union[None, Unset, int]):
        log_proto (Union[Unset, ServerParamsLogProto]):
        maintenance (Union[Unset, ServerParamsMaintenance]):
        max_reuse (Union[None, Unset, int]):
        maxconn (Union[None, Unset, int]):
        maxqueue (Union[None, Unset, int]):
        minconn (Union[None, Unset, int]):
        namespace (Union[Unset, str]):
        no_sslv3 (Union[Unset, ServerParamsNoSslv3]): This field is deprecated in favor of sslv3, and will be removed in
            a future release
        no_tlsv10 (Union[Unset, ServerParamsNoTlsv10]): This field is deprecated in favor of tlsv10, and will be removed
            in a future release
        no_tlsv11 (Union[Unset, ServerParamsNoTlsv11]): This field is deprecated in favor of tlsv11, and will be removed
            in a future release
        no_tlsv12 (Union[Unset, ServerParamsNoTlsv12]): This field is deprecated in favor of tlsv12, and will be removed
            in a future release
        no_tlsv13 (Union[Unset, ServerParamsNoTlsv13]): This field is deprecated in favor of force_tlsv13, and will be
            removed in a future release
        no_verifyhost (Union[Unset, ServerParamsNoVerifyhost]):
        npn (Union[Unset, str]):
        observe (Union[Unset, ServerParamsObserve]):
        on_error (Union[Unset, ServerParamsOnError]):
        on_marked_down (Union[Unset, ServerParamsOnMarkedDown]):
        on_marked_up (Union[Unset, ServerParamsOnMarkedUp]):
        pool_conn_name (Union[Unset, str]):
        pool_low_conn (Union[None, Unset, int]):
        pool_max_conn (Union[None, Unset, int]):
        pool_purge_delay (Union[None, Unset, int]):
        proto (Union[Unset, str]):
        proxy_v2_options (Union[Unset, list[ServerParamsProxyV2OptionsItem]]):
        redir (Union[Unset, str]):
        resolve_net (Union[Unset, str]):
        resolve_prefer (Union[Unset, ServerParamsResolvePrefer]):
        resolve_opts (Union[Unset, str]):
        resolvers (Union[Unset, str]):
        rise (Union[None, Unset, int]):
        send_proxy (Union[Unset, ServerParamsSendProxy]):
        send_proxy_v2 (Union[Unset, ServerParamsSendProxyV2]):
        send_proxy_v2_ssl (Union[Unset, ServerParamsSendProxyV2Ssl]):
        send_proxy_v2_ssl_cn (Union[Unset, ServerParamsSendProxyV2SslCn]):
        set_proxy_v2_tlv_fmt (Union[Unset, ServerParamsSetProxyV2TlvFmt]):
        shard (Union[Unset, int]):
        sigalgs (Union[Unset, str]):
        slowstart (Union[None, Unset, int]):
        sni (Union[Unset, str]):
        socks4 (Union[Unset, str]):
        source (Union[Unset, str]):
        ssl (Union[Unset, ServerParamsSsl]):
        ssl_cafile (Union[Unset, str]):
        ssl_certificate (Union[Unset, str]):
        ssl_max_ver (Union[Unset, ServerParamsSslMaxVer]):
        ssl_min_ver (Union[Unset, ServerParamsSslMinVer]):
        ssl_reuse (Union[Unset, ServerParamsSslReuse]):
        sslv3 (Union[Unset, ServerParamsSslv3]):
        stick (Union[Unset, ServerParamsStick]):
        strict_maxconn (Union[Unset, bool]):
        tcp_ut (Union[None, Unset, int]):
        tfo (Union[Unset, ServerParamsTfo]):
        tls_tickets (Union[Unset, ServerParamsTlsTickets]):
        tlsv10 (Union[Unset, ServerParamsTlsv10]):
        tlsv11 (Union[Unset, ServerParamsTlsv11]):
        tlsv12 (Union[Unset, ServerParamsTlsv12]):
        tlsv13 (Union[Unset, ServerParamsTlsv13]):
        track (Union[Unset, str]):
        verify (Union[Unset, ServerParamsVerify]):
        verifyhost (Union[Unset, str]):
        weight (Union[None, Unset, int]):
        ws (Union[Unset, ServerParamsWs]):
        id (Union[None, Unset, int]):
        metadata (Union[Unset, Any]):
        port (Union[None, Unset, int]):
    """

    fqdn: str
    num_or_range: str
    prefix: str
    agent_addr: Union[Unset, str] = UNSET
    agent_check: Union[Unset, ServerParamsAgentCheck] = UNSET
    agent_inter: Union[None, Unset, int] = UNSET
    agent_port: Union[None, Unset, int] = UNSET
    agent_send: Union[Unset, str] = UNSET
    allow_0rtt: Union[Unset, bool] = UNSET
    alpn: Union[Unset, str] = UNSET
    backup: Union[Unset, ServerParamsBackup] = UNSET
    check: Union[Unset, ServerParamsCheck] = UNSET
    check_pool_conn_name: Union[Unset, str] = UNSET
    check_reuse_pool: Union[Unset, ServerParamsCheckReusePool] = UNSET
    check_send_proxy: Union[Unset, ServerParamsCheckSendProxy] = UNSET
    check_sni: Union[Unset, str] = UNSET
    check_ssl: Union[Unset, ServerParamsCheckSsl] = UNSET
    check_alpn: Union[Unset, str] = UNSET
    check_proto: Union[Unset, str] = UNSET
    check_via_socks4: Union[Unset, ServerParamsCheckViaSocks4] = UNSET
    ciphers: Union[Unset, str] = UNSET
    ciphersuites: Union[Unset, str] = UNSET
    client_sigalgs: Union[Unset, str] = UNSET
    cookie: Union[Unset, str] = UNSET
    crl_file: Union[Unset, str] = UNSET
    curves: Union[Unset, str] = UNSET
    downinter: Union[None, Unset, int] = UNSET
    error_limit: Union[Unset, int] = UNSET
    fall: Union[None, Unset, int] = UNSET
    fastinter: Union[None, Unset, int] = UNSET
    force_sslv3: Union[Unset, ServerParamsForceSslv3] = UNSET
    force_tlsv10: Union[Unset, ServerParamsForceTlsv10] = UNSET
    force_tlsv11: Union[Unset, ServerParamsForceTlsv11] = UNSET
    force_tlsv12: Union[Unset, ServerParamsForceTlsv12] = UNSET
    force_tlsv13: Union[Unset, ServerParamsForceTlsv13] = UNSET
    guid: Union[Unset, str] = UNSET
    hash_key: Union[Unset, str] = UNSET
    health_check_address: Union[Unset, str] = UNSET
    health_check_port: Union[None, Unset, int] = UNSET
    idle_ping: Union[None, Unset, int] = UNSET
    init_addr: Union[None, Unset, str] = UNSET
    init_state: Union[Unset, ServerParamsInitState] = UNSET
    inter: Union[None, Unset, int] = UNSET
    log_bufsize: Union[None, Unset, int] = UNSET
    log_proto: Union[Unset, ServerParamsLogProto] = UNSET
    maintenance: Union[Unset, ServerParamsMaintenance] = UNSET
    max_reuse: Union[None, Unset, int] = UNSET
    maxconn: Union[None, Unset, int] = UNSET
    maxqueue: Union[None, Unset, int] = UNSET
    minconn: Union[None, Unset, int] = UNSET
    namespace: Union[Unset, str] = UNSET
    no_sslv3: Union[Unset, ServerParamsNoSslv3] = UNSET
    no_tlsv10: Union[Unset, ServerParamsNoTlsv10] = UNSET
    no_tlsv11: Union[Unset, ServerParamsNoTlsv11] = UNSET
    no_tlsv12: Union[Unset, ServerParamsNoTlsv12] = UNSET
    no_tlsv13: Union[Unset, ServerParamsNoTlsv13] = UNSET
    no_verifyhost: Union[Unset, ServerParamsNoVerifyhost] = UNSET
    npn: Union[Unset, str] = UNSET
    observe: Union[Unset, ServerParamsObserve] = UNSET
    on_error: Union[Unset, ServerParamsOnError] = UNSET
    on_marked_down: Union[Unset, ServerParamsOnMarkedDown] = UNSET
    on_marked_up: Union[Unset, ServerParamsOnMarkedUp] = UNSET
    pool_conn_name: Union[Unset, str] = UNSET
    pool_low_conn: Union[None, Unset, int] = UNSET
    pool_max_conn: Union[None, Unset, int] = UNSET
    pool_purge_delay: Union[None, Unset, int] = UNSET
    proto: Union[Unset, str] = UNSET
    proxy_v2_options: Union[Unset, list[ServerParamsProxyV2OptionsItem]] = UNSET
    redir: Union[Unset, str] = UNSET
    resolve_net: Union[Unset, str] = UNSET
    resolve_prefer: Union[Unset, ServerParamsResolvePrefer] = UNSET
    resolve_opts: Union[Unset, str] = UNSET
    resolvers: Union[Unset, str] = UNSET
    rise: Union[None, Unset, int] = UNSET
    send_proxy: Union[Unset, ServerParamsSendProxy] = UNSET
    send_proxy_v2: Union[Unset, ServerParamsSendProxyV2] = UNSET
    send_proxy_v2_ssl: Union[Unset, ServerParamsSendProxyV2Ssl] = UNSET
    send_proxy_v2_ssl_cn: Union[Unset, ServerParamsSendProxyV2SslCn] = UNSET
    set_proxy_v2_tlv_fmt: Union[Unset, "ServerParamsSetProxyV2TlvFmt"] = UNSET
    shard: Union[Unset, int] = UNSET
    sigalgs: Union[Unset, str] = UNSET
    slowstart: Union[None, Unset, int] = UNSET
    sni: Union[Unset, str] = UNSET
    socks4: Union[Unset, str] = UNSET
    source: Union[Unset, str] = UNSET
    ssl: Union[Unset, ServerParamsSsl] = UNSET
    ssl_cafile: Union[Unset, str] = UNSET
    ssl_certificate: Union[Unset, str] = UNSET
    ssl_max_ver: Union[Unset, ServerParamsSslMaxVer] = UNSET
    ssl_min_ver: Union[Unset, ServerParamsSslMinVer] = UNSET
    ssl_reuse: Union[Unset, ServerParamsSslReuse] = UNSET
    sslv3: Union[Unset, ServerParamsSslv3] = UNSET
    stick: Union[Unset, ServerParamsStick] = UNSET
    strict_maxconn: Union[Unset, bool] = UNSET
    tcp_ut: Union[None, Unset, int] = UNSET
    tfo: Union[Unset, ServerParamsTfo] = UNSET
    tls_tickets: Union[Unset, ServerParamsTlsTickets] = UNSET
    tlsv10: Union[Unset, ServerParamsTlsv10] = UNSET
    tlsv11: Union[Unset, ServerParamsTlsv11] = UNSET
    tlsv12: Union[Unset, ServerParamsTlsv12] = UNSET
    tlsv13: Union[Unset, ServerParamsTlsv13] = UNSET
    track: Union[Unset, str] = UNSET
    verify: Union[Unset, ServerParamsVerify] = UNSET
    verifyhost: Union[Unset, str] = UNSET
    weight: Union[None, Unset, int] = UNSET
    ws: Union[Unset, ServerParamsWs] = UNSET
    id: Union[None, Unset, int] = UNSET
    metadata: Union[Unset, Any] = UNSET
    port: Union[None, Unset, int] = UNSET

    def to_dict(self) -> dict[str, Any]:
        fqdn = self.fqdn

        num_or_range = self.num_or_range

        prefix = self.prefix

        agent_addr = self.agent_addr

        agent_check: Union[Unset, str] = UNSET
        if not isinstance(self.agent_check, Unset):
            agent_check = self.agent_check.value

        agent_inter: Union[None, Unset, int]
        if isinstance(self.agent_inter, Unset):
            agent_inter = UNSET
        else:
            agent_inter = self.agent_inter

        agent_port: Union[None, Unset, int]
        if isinstance(self.agent_port, Unset):
            agent_port = UNSET
        else:
            agent_port = self.agent_port

        agent_send = self.agent_send

        allow_0rtt = self.allow_0rtt

        alpn = self.alpn

        backup: Union[Unset, str] = UNSET
        if not isinstance(self.backup, Unset):
            backup = self.backup.value

        check: Union[Unset, str] = UNSET
        if not isinstance(self.check, Unset):
            check = self.check.value

        check_pool_conn_name = self.check_pool_conn_name

        check_reuse_pool: Union[Unset, str] = UNSET
        if not isinstance(self.check_reuse_pool, Unset):
            check_reuse_pool = self.check_reuse_pool.value

        check_send_proxy: Union[Unset, str] = UNSET
        if not isinstance(self.check_send_proxy, Unset):
            check_send_proxy = self.check_send_proxy.value

        check_sni = self.check_sni

        check_ssl: Union[Unset, str] = UNSET
        if not isinstance(self.check_ssl, Unset):
            check_ssl = self.check_ssl.value

        check_alpn = self.check_alpn

        check_proto = self.check_proto

        check_via_socks4: Union[Unset, str] = UNSET
        if not isinstance(self.check_via_socks4, Unset):
            check_via_socks4 = self.check_via_socks4.value

        ciphers = self.ciphers

        ciphersuites = self.ciphersuites

        client_sigalgs = self.client_sigalgs

        cookie = self.cookie

        crl_file = self.crl_file

        curves = self.curves

        downinter: Union[None, Unset, int]
        if isinstance(self.downinter, Unset):
            downinter = UNSET
        else:
            downinter = self.downinter

        error_limit = self.error_limit

        fall: Union[None, Unset, int]
        if isinstance(self.fall, Unset):
            fall = UNSET
        else:
            fall = self.fall

        fastinter: Union[None, Unset, int]
        if isinstance(self.fastinter, Unset):
            fastinter = UNSET
        else:
            fastinter = self.fastinter

        force_sslv3: Union[Unset, str] = UNSET
        if not isinstance(self.force_sslv3, Unset):
            force_sslv3 = self.force_sslv3.value

        force_tlsv10: Union[Unset, str] = UNSET
        if not isinstance(self.force_tlsv10, Unset):
            force_tlsv10 = self.force_tlsv10.value

        force_tlsv11: Union[Unset, str] = UNSET
        if not isinstance(self.force_tlsv11, Unset):
            force_tlsv11 = self.force_tlsv11.value

        force_tlsv12: Union[Unset, str] = UNSET
        if not isinstance(self.force_tlsv12, Unset):
            force_tlsv12 = self.force_tlsv12.value

        force_tlsv13: Union[Unset, str] = UNSET
        if not isinstance(self.force_tlsv13, Unset):
            force_tlsv13 = self.force_tlsv13.value

        guid = self.guid

        hash_key = self.hash_key

        health_check_address = self.health_check_address

        health_check_port: Union[None, Unset, int]
        if isinstance(self.health_check_port, Unset):
            health_check_port = UNSET
        else:
            health_check_port = self.health_check_port

        idle_ping: Union[None, Unset, int]
        if isinstance(self.idle_ping, Unset):
            idle_ping = UNSET
        else:
            idle_ping = self.idle_ping

        init_addr: Union[None, Unset, str]
        if isinstance(self.init_addr, Unset):
            init_addr = UNSET
        else:
            init_addr = self.init_addr

        init_state: Union[Unset, str] = UNSET
        if not isinstance(self.init_state, Unset):
            init_state = self.init_state.value

        inter: Union[None, Unset, int]
        if isinstance(self.inter, Unset):
            inter = UNSET
        else:
            inter = self.inter

        log_bufsize: Union[None, Unset, int]
        if isinstance(self.log_bufsize, Unset):
            log_bufsize = UNSET
        else:
            log_bufsize = self.log_bufsize

        log_proto: Union[Unset, str] = UNSET
        if not isinstance(self.log_proto, Unset):
            log_proto = self.log_proto.value

        maintenance: Union[Unset, str] = UNSET
        if not isinstance(self.maintenance, Unset):
            maintenance = self.maintenance.value

        max_reuse: Union[None, Unset, int]
        if isinstance(self.max_reuse, Unset):
            max_reuse = UNSET
        else:
            max_reuse = self.max_reuse

        maxconn: Union[None, Unset, int]
        if isinstance(self.maxconn, Unset):
            maxconn = UNSET
        else:
            maxconn = self.maxconn

        maxqueue: Union[None, Unset, int]
        if isinstance(self.maxqueue, Unset):
            maxqueue = UNSET
        else:
            maxqueue = self.maxqueue

        minconn: Union[None, Unset, int]
        if isinstance(self.minconn, Unset):
            minconn = UNSET
        else:
            minconn = self.minconn

        namespace = self.namespace

        no_sslv3: Union[Unset, str] = UNSET
        if not isinstance(self.no_sslv3, Unset):
            no_sslv3 = self.no_sslv3.value

        no_tlsv10: Union[Unset, str] = UNSET
        if not isinstance(self.no_tlsv10, Unset):
            no_tlsv10 = self.no_tlsv10.value

        no_tlsv11: Union[Unset, str] = UNSET
        if not isinstance(self.no_tlsv11, Unset):
            no_tlsv11 = self.no_tlsv11.value

        no_tlsv12: Union[Unset, str] = UNSET
        if not isinstance(self.no_tlsv12, Unset):
            no_tlsv12 = self.no_tlsv12.value

        no_tlsv13: Union[Unset, str] = UNSET
        if not isinstance(self.no_tlsv13, Unset):
            no_tlsv13 = self.no_tlsv13.value

        no_verifyhost: Union[Unset, str] = UNSET
        if not isinstance(self.no_verifyhost, Unset):
            no_verifyhost = self.no_verifyhost.value

        npn = self.npn

        observe: Union[Unset, str] = UNSET
        if not isinstance(self.observe, Unset):
            observe = self.observe.value

        on_error: Union[Unset, str] = UNSET
        if not isinstance(self.on_error, Unset):
            on_error = self.on_error.value

        on_marked_down: Union[Unset, str] = UNSET
        if not isinstance(self.on_marked_down, Unset):
            on_marked_down = self.on_marked_down.value

        on_marked_up: Union[Unset, str] = UNSET
        if not isinstance(self.on_marked_up, Unset):
            on_marked_up = self.on_marked_up.value

        pool_conn_name = self.pool_conn_name

        pool_low_conn: Union[None, Unset, int]
        if isinstance(self.pool_low_conn, Unset):
            pool_low_conn = UNSET
        else:
            pool_low_conn = self.pool_low_conn

        pool_max_conn: Union[None, Unset, int]
        if isinstance(self.pool_max_conn, Unset):
            pool_max_conn = UNSET
        else:
            pool_max_conn = self.pool_max_conn

        pool_purge_delay: Union[None, Unset, int]
        if isinstance(self.pool_purge_delay, Unset):
            pool_purge_delay = UNSET
        else:
            pool_purge_delay = self.pool_purge_delay

        proto = self.proto

        proxy_v2_options: Union[Unset, list[str]] = UNSET
        if not isinstance(self.proxy_v2_options, Unset):
            proxy_v2_options = []
            for proxy_v2_options_item_data in self.proxy_v2_options:
                proxy_v2_options_item = proxy_v2_options_item_data.value
                proxy_v2_options.append(proxy_v2_options_item)

        redir = self.redir

        resolve_net = self.resolve_net

        resolve_prefer: Union[Unset, str] = UNSET
        if not isinstance(self.resolve_prefer, Unset):
            resolve_prefer = self.resolve_prefer.value

        resolve_opts = self.resolve_opts

        resolvers = self.resolvers

        rise: Union[None, Unset, int]
        if isinstance(self.rise, Unset):
            rise = UNSET
        else:
            rise = self.rise

        send_proxy: Union[Unset, str] = UNSET
        if not isinstance(self.send_proxy, Unset):
            send_proxy = self.send_proxy.value

        send_proxy_v2: Union[Unset, str] = UNSET
        if not isinstance(self.send_proxy_v2, Unset):
            send_proxy_v2 = self.send_proxy_v2.value

        send_proxy_v2_ssl: Union[Unset, str] = UNSET
        if not isinstance(self.send_proxy_v2_ssl, Unset):
            send_proxy_v2_ssl = self.send_proxy_v2_ssl.value

        send_proxy_v2_ssl_cn: Union[Unset, str] = UNSET
        if not isinstance(self.send_proxy_v2_ssl_cn, Unset):
            send_proxy_v2_ssl_cn = self.send_proxy_v2_ssl_cn.value

        set_proxy_v2_tlv_fmt: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.set_proxy_v2_tlv_fmt, Unset):
            set_proxy_v2_tlv_fmt = self.set_proxy_v2_tlv_fmt.to_dict()

        shard = self.shard

        sigalgs = self.sigalgs

        slowstart: Union[None, Unset, int]
        if isinstance(self.slowstart, Unset):
            slowstart = UNSET
        else:
            slowstart = self.slowstart

        sni = self.sni

        socks4 = self.socks4

        source = self.source

        ssl: Union[Unset, str] = UNSET
        if not isinstance(self.ssl, Unset):
            ssl = self.ssl.value

        ssl_cafile = self.ssl_cafile

        ssl_certificate = self.ssl_certificate

        ssl_max_ver: Union[Unset, str] = UNSET
        if not isinstance(self.ssl_max_ver, Unset):
            ssl_max_ver = self.ssl_max_ver.value

        ssl_min_ver: Union[Unset, str] = UNSET
        if not isinstance(self.ssl_min_ver, Unset):
            ssl_min_ver = self.ssl_min_ver.value

        ssl_reuse: Union[Unset, str] = UNSET
        if not isinstance(self.ssl_reuse, Unset):
            ssl_reuse = self.ssl_reuse.value

        sslv3: Union[Unset, str] = UNSET
        if not isinstance(self.sslv3, Unset):
            sslv3 = self.sslv3.value

        stick: Union[Unset, str] = UNSET
        if not isinstance(self.stick, Unset):
            stick = self.stick.value

        strict_maxconn = self.strict_maxconn

        tcp_ut: Union[None, Unset, int]
        if isinstance(self.tcp_ut, Unset):
            tcp_ut = UNSET
        else:
            tcp_ut = self.tcp_ut

        tfo: Union[Unset, str] = UNSET
        if not isinstance(self.tfo, Unset):
            tfo = self.tfo.value

        tls_tickets: Union[Unset, str] = UNSET
        if not isinstance(self.tls_tickets, Unset):
            tls_tickets = self.tls_tickets.value

        tlsv10: Union[Unset, str] = UNSET
        if not isinstance(self.tlsv10, Unset):
            tlsv10 = self.tlsv10.value

        tlsv11: Union[Unset, str] = UNSET
        if not isinstance(self.tlsv11, Unset):
            tlsv11 = self.tlsv11.value

        tlsv12: Union[Unset, str] = UNSET
        if not isinstance(self.tlsv12, Unset):
            tlsv12 = self.tlsv12.value

        tlsv13: Union[Unset, str] = UNSET
        if not isinstance(self.tlsv13, Unset):
            tlsv13 = self.tlsv13.value

        track = self.track

        verify: Union[Unset, str] = UNSET
        if not isinstance(self.verify, Unset):
            verify = self.verify.value

        verifyhost = self.verifyhost

        weight: Union[None, Unset, int]
        if isinstance(self.weight, Unset):
            weight = UNSET
        else:
            weight = self.weight

        ws: Union[Unset, str] = UNSET
        if not isinstance(self.ws, Unset):
            ws = self.ws.value

        id: Union[None, Unset, int]
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        metadata = self.metadata

        port: Union[None, Unset, int]
        if isinstance(self.port, Unset):
            port = UNSET
        else:
            port = self.port

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "fqdn": fqdn,
                "num_or_range": num_or_range,
                "prefix": prefix,
            }
        )
        if agent_addr is not UNSET:
            field_dict["agent-addr"] = agent_addr
        if agent_check is not UNSET:
            field_dict["agent-check"] = agent_check
        if agent_inter is not UNSET:
            field_dict["agent-inter"] = agent_inter
        if agent_port is not UNSET:
            field_dict["agent-port"] = agent_port
        if agent_send is not UNSET:
            field_dict["agent-send"] = agent_send
        if allow_0rtt is not UNSET:
            field_dict["allow_0rtt"] = allow_0rtt
        if alpn is not UNSET:
            field_dict["alpn"] = alpn
        if backup is not UNSET:
            field_dict["backup"] = backup
        if check is not UNSET:
            field_dict["check"] = check
        if check_pool_conn_name is not UNSET:
            field_dict["check-pool-conn-name"] = check_pool_conn_name
        if check_reuse_pool is not UNSET:
            field_dict["check-reuse-pool"] = check_reuse_pool
        if check_send_proxy is not UNSET:
            field_dict["check-send-proxy"] = check_send_proxy
        if check_sni is not UNSET:
            field_dict["check-sni"] = check_sni
        if check_ssl is not UNSET:
            field_dict["check-ssl"] = check_ssl
        if check_alpn is not UNSET:
            field_dict["check_alpn"] = check_alpn
        if check_proto is not UNSET:
            field_dict["check_proto"] = check_proto
        if check_via_socks4 is not UNSET:
            field_dict["check_via_socks4"] = check_via_socks4
        if ciphers is not UNSET:
            field_dict["ciphers"] = ciphers
        if ciphersuites is not UNSET:
            field_dict["ciphersuites"] = ciphersuites
        if client_sigalgs is not UNSET:
            field_dict["client_sigalgs"] = client_sigalgs
        if cookie is not UNSET:
            field_dict["cookie"] = cookie
        if crl_file is not UNSET:
            field_dict["crl_file"] = crl_file
        if curves is not UNSET:
            field_dict["curves"] = curves
        if downinter is not UNSET:
            field_dict["downinter"] = downinter
        if error_limit is not UNSET:
            field_dict["error_limit"] = error_limit
        if fall is not UNSET:
            field_dict["fall"] = fall
        if fastinter is not UNSET:
            field_dict["fastinter"] = fastinter
        if force_sslv3 is not UNSET:
            field_dict["force_sslv3"] = force_sslv3
        if force_tlsv10 is not UNSET:
            field_dict["force_tlsv10"] = force_tlsv10
        if force_tlsv11 is not UNSET:
            field_dict["force_tlsv11"] = force_tlsv11
        if force_tlsv12 is not UNSET:
            field_dict["force_tlsv12"] = force_tlsv12
        if force_tlsv13 is not UNSET:
            field_dict["force_tlsv13"] = force_tlsv13
        if guid is not UNSET:
            field_dict["guid"] = guid
        if hash_key is not UNSET:
            field_dict["hash_key"] = hash_key
        if health_check_address is not UNSET:
            field_dict["health_check_address"] = health_check_address
        if health_check_port is not UNSET:
            field_dict["health_check_port"] = health_check_port
        if idle_ping is not UNSET:
            field_dict["idle_ping"] = idle_ping
        if init_addr is not UNSET:
            field_dict["init-addr"] = init_addr
        if init_state is not UNSET:
            field_dict["init-state"] = init_state
        if inter is not UNSET:
            field_dict["inter"] = inter
        if log_bufsize is not UNSET:
            field_dict["log-bufsize"] = log_bufsize
        if log_proto is not UNSET:
            field_dict["log_proto"] = log_proto
        if maintenance is not UNSET:
            field_dict["maintenance"] = maintenance
        if max_reuse is not UNSET:
            field_dict["max_reuse"] = max_reuse
        if maxconn is not UNSET:
            field_dict["maxconn"] = maxconn
        if maxqueue is not UNSET:
            field_dict["maxqueue"] = maxqueue
        if minconn is not UNSET:
            field_dict["minconn"] = minconn
        if namespace is not UNSET:
            field_dict["namespace"] = namespace
        if no_sslv3 is not UNSET:
            field_dict["no_sslv3"] = no_sslv3
        if no_tlsv10 is not UNSET:
            field_dict["no_tlsv10"] = no_tlsv10
        if no_tlsv11 is not UNSET:
            field_dict["no_tlsv11"] = no_tlsv11
        if no_tlsv12 is not UNSET:
            field_dict["no_tlsv12"] = no_tlsv12
        if no_tlsv13 is not UNSET:
            field_dict["no_tlsv13"] = no_tlsv13
        if no_verifyhost is not UNSET:
            field_dict["no_verifyhost"] = no_verifyhost
        if npn is not UNSET:
            field_dict["npn"] = npn
        if observe is not UNSET:
            field_dict["observe"] = observe
        if on_error is not UNSET:
            field_dict["on-error"] = on_error
        if on_marked_down is not UNSET:
            field_dict["on-marked-down"] = on_marked_down
        if on_marked_up is not UNSET:
            field_dict["on-marked-up"] = on_marked_up
        if pool_conn_name is not UNSET:
            field_dict["pool_conn_name"] = pool_conn_name
        if pool_low_conn is not UNSET:
            field_dict["pool_low_conn"] = pool_low_conn
        if pool_max_conn is not UNSET:
            field_dict["pool_max_conn"] = pool_max_conn
        if pool_purge_delay is not UNSET:
            field_dict["pool_purge_delay"] = pool_purge_delay
        if proto is not UNSET:
            field_dict["proto"] = proto
        if proxy_v2_options is not UNSET:
            field_dict["proxy-v2-options"] = proxy_v2_options
        if redir is not UNSET:
            field_dict["redir"] = redir
        if resolve_net is not UNSET:
            field_dict["resolve-net"] = resolve_net
        if resolve_prefer is not UNSET:
            field_dict["resolve-prefer"] = resolve_prefer
        if resolve_opts is not UNSET:
            field_dict["resolve_opts"] = resolve_opts
        if resolvers is not UNSET:
            field_dict["resolvers"] = resolvers
        if rise is not UNSET:
            field_dict["rise"] = rise
        if send_proxy is not UNSET:
            field_dict["send-proxy"] = send_proxy
        if send_proxy_v2 is not UNSET:
            field_dict["send-proxy-v2"] = send_proxy_v2
        if send_proxy_v2_ssl is not UNSET:
            field_dict["send_proxy_v2_ssl"] = send_proxy_v2_ssl
        if send_proxy_v2_ssl_cn is not UNSET:
            field_dict["send_proxy_v2_ssl_cn"] = send_proxy_v2_ssl_cn
        if set_proxy_v2_tlv_fmt is not UNSET:
            field_dict["set-proxy-v2-tlv-fmt"] = set_proxy_v2_tlv_fmt
        if shard is not UNSET:
            field_dict["shard"] = shard
        if sigalgs is not UNSET:
            field_dict["sigalgs"] = sigalgs
        if slowstart is not UNSET:
            field_dict["slowstart"] = slowstart
        if sni is not UNSET:
            field_dict["sni"] = sni
        if socks4 is not UNSET:
            field_dict["socks4"] = socks4
        if source is not UNSET:
            field_dict["source"] = source
        if ssl is not UNSET:
            field_dict["ssl"] = ssl
        if ssl_cafile is not UNSET:
            field_dict["ssl_cafile"] = ssl_cafile
        if ssl_certificate is not UNSET:
            field_dict["ssl_certificate"] = ssl_certificate
        if ssl_max_ver is not UNSET:
            field_dict["ssl_max_ver"] = ssl_max_ver
        if ssl_min_ver is not UNSET:
            field_dict["ssl_min_ver"] = ssl_min_ver
        if ssl_reuse is not UNSET:
            field_dict["ssl_reuse"] = ssl_reuse
        if sslv3 is not UNSET:
            field_dict["sslv3"] = sslv3
        if stick is not UNSET:
            field_dict["stick"] = stick
        if strict_maxconn is not UNSET:
            field_dict["strict-maxconn"] = strict_maxconn
        if tcp_ut is not UNSET:
            field_dict["tcp_ut"] = tcp_ut
        if tfo is not UNSET:
            field_dict["tfo"] = tfo
        if tls_tickets is not UNSET:
            field_dict["tls_tickets"] = tls_tickets
        if tlsv10 is not UNSET:
            field_dict["tlsv10"] = tlsv10
        if tlsv11 is not UNSET:
            field_dict["tlsv11"] = tlsv11
        if tlsv12 is not UNSET:
            field_dict["tlsv12"] = tlsv12
        if tlsv13 is not UNSET:
            field_dict["tlsv13"] = tlsv13
        if track is not UNSET:
            field_dict["track"] = track
        if verify is not UNSET:
            field_dict["verify"] = verify
        if verifyhost is not UNSET:
            field_dict["verifyhost"] = verifyhost
        if weight is not UNSET:
            field_dict["weight"] = weight
        if ws is not UNSET:
            field_dict["ws"] = ws
        if id is not UNSET:
            field_dict["id"] = id
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if port is not UNSET:
            field_dict["port"] = port

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.server_params_set_proxy_v2_tlv_fmt import ServerParamsSetProxyV2TlvFmt

        d = dict(src_dict)
        fqdn = d.pop("fqdn")

        num_or_range = d.pop("num_or_range")

        prefix = d.pop("prefix")

        agent_addr = d.pop("agent-addr", UNSET)

        _agent_check = d.pop("agent-check", UNSET)
        agent_check: Union[Unset, ServerParamsAgentCheck]
        if isinstance(_agent_check, Unset):
            agent_check = UNSET
        else:
            agent_check = ServerParamsAgentCheck(_agent_check)

        def _parse_agent_inter(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        agent_inter = _parse_agent_inter(d.pop("agent-inter", UNSET))

        def _parse_agent_port(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        agent_port = _parse_agent_port(d.pop("agent-port", UNSET))

        agent_send = d.pop("agent-send", UNSET)

        allow_0rtt = d.pop("allow_0rtt", UNSET)

        alpn = d.pop("alpn", UNSET)

        _backup = d.pop("backup", UNSET)
        backup: Union[Unset, ServerParamsBackup]
        if isinstance(_backup, Unset):
            backup = UNSET
        else:
            backup = ServerParamsBackup(_backup)

        _check = d.pop("check", UNSET)
        check: Union[Unset, ServerParamsCheck]
        if isinstance(_check, Unset):
            check = UNSET
        else:
            check = ServerParamsCheck(_check)

        check_pool_conn_name = d.pop("check-pool-conn-name", UNSET)

        _check_reuse_pool = d.pop("check-reuse-pool", UNSET)
        check_reuse_pool: Union[Unset, ServerParamsCheckReusePool]
        if isinstance(_check_reuse_pool, Unset):
            check_reuse_pool = UNSET
        else:
            check_reuse_pool = ServerParamsCheckReusePool(_check_reuse_pool)

        _check_send_proxy = d.pop("check-send-proxy", UNSET)
        check_send_proxy: Union[Unset, ServerParamsCheckSendProxy]
        if isinstance(_check_send_proxy, Unset):
            check_send_proxy = UNSET
        else:
            check_send_proxy = ServerParamsCheckSendProxy(_check_send_proxy)

        check_sni = d.pop("check-sni", UNSET)

        _check_ssl = d.pop("check-ssl", UNSET)
        check_ssl: Union[Unset, ServerParamsCheckSsl]
        if isinstance(_check_ssl, Unset):
            check_ssl = UNSET
        else:
            check_ssl = ServerParamsCheckSsl(_check_ssl)

        check_alpn = d.pop("check_alpn", UNSET)

        check_proto = d.pop("check_proto", UNSET)

        _check_via_socks4 = d.pop("check_via_socks4", UNSET)
        check_via_socks4: Union[Unset, ServerParamsCheckViaSocks4]
        if isinstance(_check_via_socks4, Unset):
            check_via_socks4 = UNSET
        else:
            check_via_socks4 = ServerParamsCheckViaSocks4(_check_via_socks4)

        ciphers = d.pop("ciphers", UNSET)

        ciphersuites = d.pop("ciphersuites", UNSET)

        client_sigalgs = d.pop("client_sigalgs", UNSET)

        cookie = d.pop("cookie", UNSET)

        crl_file = d.pop("crl_file", UNSET)

        curves = d.pop("curves", UNSET)

        def _parse_downinter(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        downinter = _parse_downinter(d.pop("downinter", UNSET))

        error_limit = d.pop("error_limit", UNSET)

        def _parse_fall(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        fall = _parse_fall(d.pop("fall", UNSET))

        def _parse_fastinter(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        fastinter = _parse_fastinter(d.pop("fastinter", UNSET))

        _force_sslv3 = d.pop("force_sslv3", UNSET)
        force_sslv3: Union[Unset, ServerParamsForceSslv3]
        if isinstance(_force_sslv3, Unset):
            force_sslv3 = UNSET
        else:
            force_sslv3 = ServerParamsForceSslv3(_force_sslv3)

        _force_tlsv10 = d.pop("force_tlsv10", UNSET)
        force_tlsv10: Union[Unset, ServerParamsForceTlsv10]
        if isinstance(_force_tlsv10, Unset):
            force_tlsv10 = UNSET
        else:
            force_tlsv10 = ServerParamsForceTlsv10(_force_tlsv10)

        _force_tlsv11 = d.pop("force_tlsv11", UNSET)
        force_tlsv11: Union[Unset, ServerParamsForceTlsv11]
        if isinstance(_force_tlsv11, Unset):
            force_tlsv11 = UNSET
        else:
            force_tlsv11 = ServerParamsForceTlsv11(_force_tlsv11)

        _force_tlsv12 = d.pop("force_tlsv12", UNSET)
        force_tlsv12: Union[Unset, ServerParamsForceTlsv12]
        if isinstance(_force_tlsv12, Unset):
            force_tlsv12 = UNSET
        else:
            force_tlsv12 = ServerParamsForceTlsv12(_force_tlsv12)

        _force_tlsv13 = d.pop("force_tlsv13", UNSET)
        force_tlsv13: Union[Unset, ServerParamsForceTlsv13]
        if isinstance(_force_tlsv13, Unset):
            force_tlsv13 = UNSET
        else:
            force_tlsv13 = ServerParamsForceTlsv13(_force_tlsv13)

        guid = d.pop("guid", UNSET)

        hash_key = d.pop("hash_key", UNSET)

        health_check_address = d.pop("health_check_address", UNSET)

        def _parse_health_check_port(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        health_check_port = _parse_health_check_port(d.pop("health_check_port", UNSET))

        def _parse_idle_ping(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        idle_ping = _parse_idle_ping(d.pop("idle_ping", UNSET))

        def _parse_init_addr(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        init_addr = _parse_init_addr(d.pop("init-addr", UNSET))

        _init_state = d.pop("init-state", UNSET)
        init_state: Union[Unset, ServerParamsInitState]
        if isinstance(_init_state, Unset):
            init_state = UNSET
        else:
            init_state = ServerParamsInitState(_init_state)

        def _parse_inter(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        inter = _parse_inter(d.pop("inter", UNSET))

        def _parse_log_bufsize(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        log_bufsize = _parse_log_bufsize(d.pop("log-bufsize", UNSET))

        _log_proto = d.pop("log_proto", UNSET)
        log_proto: Union[Unset, ServerParamsLogProto]
        if isinstance(_log_proto, Unset):
            log_proto = UNSET
        else:
            log_proto = ServerParamsLogProto(_log_proto)

        _maintenance = d.pop("maintenance", UNSET)
        maintenance: Union[Unset, ServerParamsMaintenance]
        if isinstance(_maintenance, Unset):
            maintenance = UNSET
        else:
            maintenance = ServerParamsMaintenance(_maintenance)

        def _parse_max_reuse(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_reuse = _parse_max_reuse(d.pop("max_reuse", UNSET))

        def _parse_maxconn(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        maxconn = _parse_maxconn(d.pop("maxconn", UNSET))

        def _parse_maxqueue(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        maxqueue = _parse_maxqueue(d.pop("maxqueue", UNSET))

        def _parse_minconn(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        minconn = _parse_minconn(d.pop("minconn", UNSET))

        namespace = d.pop("namespace", UNSET)

        _no_sslv3 = d.pop("no_sslv3", UNSET)
        no_sslv3: Union[Unset, ServerParamsNoSslv3]
        if isinstance(_no_sslv3, Unset):
            no_sslv3 = UNSET
        else:
            no_sslv3 = ServerParamsNoSslv3(_no_sslv3)

        _no_tlsv10 = d.pop("no_tlsv10", UNSET)
        no_tlsv10: Union[Unset, ServerParamsNoTlsv10]
        if isinstance(_no_tlsv10, Unset):
            no_tlsv10 = UNSET
        else:
            no_tlsv10 = ServerParamsNoTlsv10(_no_tlsv10)

        _no_tlsv11 = d.pop("no_tlsv11", UNSET)
        no_tlsv11: Union[Unset, ServerParamsNoTlsv11]
        if isinstance(_no_tlsv11, Unset):
            no_tlsv11 = UNSET
        else:
            no_tlsv11 = ServerParamsNoTlsv11(_no_tlsv11)

        _no_tlsv12 = d.pop("no_tlsv12", UNSET)
        no_tlsv12: Union[Unset, ServerParamsNoTlsv12]
        if isinstance(_no_tlsv12, Unset):
            no_tlsv12 = UNSET
        else:
            no_tlsv12 = ServerParamsNoTlsv12(_no_tlsv12)

        _no_tlsv13 = d.pop("no_tlsv13", UNSET)
        no_tlsv13: Union[Unset, ServerParamsNoTlsv13]
        if isinstance(_no_tlsv13, Unset):
            no_tlsv13 = UNSET
        else:
            no_tlsv13 = ServerParamsNoTlsv13(_no_tlsv13)

        _no_verifyhost = d.pop("no_verifyhost", UNSET)
        no_verifyhost: Union[Unset, ServerParamsNoVerifyhost]
        if isinstance(_no_verifyhost, Unset):
            no_verifyhost = UNSET
        else:
            no_verifyhost = ServerParamsNoVerifyhost(_no_verifyhost)

        npn = d.pop("npn", UNSET)

        _observe = d.pop("observe", UNSET)
        observe: Union[Unset, ServerParamsObserve]
        if isinstance(_observe, Unset):
            observe = UNSET
        else:
            observe = ServerParamsObserve(_observe)

        _on_error = d.pop("on-error", UNSET)
        on_error: Union[Unset, ServerParamsOnError]
        if isinstance(_on_error, Unset):
            on_error = UNSET
        else:
            on_error = ServerParamsOnError(_on_error)

        _on_marked_down = d.pop("on-marked-down", UNSET)
        on_marked_down: Union[Unset, ServerParamsOnMarkedDown]
        if isinstance(_on_marked_down, Unset):
            on_marked_down = UNSET
        else:
            on_marked_down = ServerParamsOnMarkedDown(_on_marked_down)

        _on_marked_up = d.pop("on-marked-up", UNSET)
        on_marked_up: Union[Unset, ServerParamsOnMarkedUp]
        if isinstance(_on_marked_up, Unset):
            on_marked_up = UNSET
        else:
            on_marked_up = ServerParamsOnMarkedUp(_on_marked_up)

        pool_conn_name = d.pop("pool_conn_name", UNSET)

        def _parse_pool_low_conn(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        pool_low_conn = _parse_pool_low_conn(d.pop("pool_low_conn", UNSET))

        def _parse_pool_max_conn(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        pool_max_conn = _parse_pool_max_conn(d.pop("pool_max_conn", UNSET))

        def _parse_pool_purge_delay(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        pool_purge_delay = _parse_pool_purge_delay(d.pop("pool_purge_delay", UNSET))

        proto = d.pop("proto", UNSET)

        proxy_v2_options = []
        _proxy_v2_options = d.pop("proxy-v2-options", UNSET)
        for proxy_v2_options_item_data in _proxy_v2_options or []:
            proxy_v2_options_item = ServerParamsProxyV2OptionsItem(proxy_v2_options_item_data)

            proxy_v2_options.append(proxy_v2_options_item)

        redir = d.pop("redir", UNSET)

        resolve_net = d.pop("resolve-net", UNSET)

        _resolve_prefer = d.pop("resolve-prefer", UNSET)
        resolve_prefer: Union[Unset, ServerParamsResolvePrefer]
        if isinstance(_resolve_prefer, Unset):
            resolve_prefer = UNSET
        else:
            resolve_prefer = ServerParamsResolvePrefer(_resolve_prefer)

        resolve_opts = d.pop("resolve_opts", UNSET)

        resolvers = d.pop("resolvers", UNSET)

        def _parse_rise(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        rise = _parse_rise(d.pop("rise", UNSET))

        _send_proxy = d.pop("send-proxy", UNSET)
        send_proxy: Union[Unset, ServerParamsSendProxy]
        if isinstance(_send_proxy, Unset):
            send_proxy = UNSET
        else:
            send_proxy = ServerParamsSendProxy(_send_proxy)

        _send_proxy_v2 = d.pop("send-proxy-v2", UNSET)
        send_proxy_v2: Union[Unset, ServerParamsSendProxyV2]
        if isinstance(_send_proxy_v2, Unset):
            send_proxy_v2 = UNSET
        else:
            send_proxy_v2 = ServerParamsSendProxyV2(_send_proxy_v2)

        _send_proxy_v2_ssl = d.pop("send_proxy_v2_ssl", UNSET)
        send_proxy_v2_ssl: Union[Unset, ServerParamsSendProxyV2Ssl]
        if isinstance(_send_proxy_v2_ssl, Unset):
            send_proxy_v2_ssl = UNSET
        else:
            send_proxy_v2_ssl = ServerParamsSendProxyV2Ssl(_send_proxy_v2_ssl)

        _send_proxy_v2_ssl_cn = d.pop("send_proxy_v2_ssl_cn", UNSET)
        send_proxy_v2_ssl_cn: Union[Unset, ServerParamsSendProxyV2SslCn]
        if isinstance(_send_proxy_v2_ssl_cn, Unset):
            send_proxy_v2_ssl_cn = UNSET
        else:
            send_proxy_v2_ssl_cn = ServerParamsSendProxyV2SslCn(_send_proxy_v2_ssl_cn)

        _set_proxy_v2_tlv_fmt = d.pop("set-proxy-v2-tlv-fmt", UNSET)
        set_proxy_v2_tlv_fmt: Union[Unset, ServerParamsSetProxyV2TlvFmt]
        if isinstance(_set_proxy_v2_tlv_fmt, Unset):
            set_proxy_v2_tlv_fmt = UNSET
        else:
            set_proxy_v2_tlv_fmt = ServerParamsSetProxyV2TlvFmt.from_dict(_set_proxy_v2_tlv_fmt)

        shard = d.pop("shard", UNSET)

        sigalgs = d.pop("sigalgs", UNSET)

        def _parse_slowstart(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        slowstart = _parse_slowstart(d.pop("slowstart", UNSET))

        sni = d.pop("sni", UNSET)

        socks4 = d.pop("socks4", UNSET)

        source = d.pop("source", UNSET)

        _ssl = d.pop("ssl", UNSET)
        ssl: Union[Unset, ServerParamsSsl]
        if isinstance(_ssl, Unset):
            ssl = UNSET
        else:
            ssl = ServerParamsSsl(_ssl)

        ssl_cafile = d.pop("ssl_cafile", UNSET)

        ssl_certificate = d.pop("ssl_certificate", UNSET)

        _ssl_max_ver = d.pop("ssl_max_ver", UNSET)
        ssl_max_ver: Union[Unset, ServerParamsSslMaxVer]
        if isinstance(_ssl_max_ver, Unset):
            ssl_max_ver = UNSET
        else:
            ssl_max_ver = ServerParamsSslMaxVer(_ssl_max_ver)

        _ssl_min_ver = d.pop("ssl_min_ver", UNSET)
        ssl_min_ver: Union[Unset, ServerParamsSslMinVer]
        if isinstance(_ssl_min_ver, Unset):
            ssl_min_ver = UNSET
        else:
            ssl_min_ver = ServerParamsSslMinVer(_ssl_min_ver)

        _ssl_reuse = d.pop("ssl_reuse", UNSET)
        ssl_reuse: Union[Unset, ServerParamsSslReuse]
        if isinstance(_ssl_reuse, Unset):
            ssl_reuse = UNSET
        else:
            ssl_reuse = ServerParamsSslReuse(_ssl_reuse)

        _sslv3 = d.pop("sslv3", UNSET)
        sslv3: Union[Unset, ServerParamsSslv3]
        if isinstance(_sslv3, Unset):
            sslv3 = UNSET
        else:
            sslv3 = ServerParamsSslv3(_sslv3)

        _stick = d.pop("stick", UNSET)
        stick: Union[Unset, ServerParamsStick]
        if isinstance(_stick, Unset):
            stick = UNSET
        else:
            stick = ServerParamsStick(_stick)

        strict_maxconn = d.pop("strict-maxconn", UNSET)

        def _parse_tcp_ut(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        tcp_ut = _parse_tcp_ut(d.pop("tcp_ut", UNSET))

        _tfo = d.pop("tfo", UNSET)
        tfo: Union[Unset, ServerParamsTfo]
        if isinstance(_tfo, Unset):
            tfo = UNSET
        else:
            tfo = ServerParamsTfo(_tfo)

        _tls_tickets = d.pop("tls_tickets", UNSET)
        tls_tickets: Union[Unset, ServerParamsTlsTickets]
        if isinstance(_tls_tickets, Unset):
            tls_tickets = UNSET
        else:
            tls_tickets = ServerParamsTlsTickets(_tls_tickets)

        _tlsv10 = d.pop("tlsv10", UNSET)
        tlsv10: Union[Unset, ServerParamsTlsv10]
        if isinstance(_tlsv10, Unset):
            tlsv10 = UNSET
        else:
            tlsv10 = ServerParamsTlsv10(_tlsv10)

        _tlsv11 = d.pop("tlsv11", UNSET)
        tlsv11: Union[Unset, ServerParamsTlsv11]
        if isinstance(_tlsv11, Unset):
            tlsv11 = UNSET
        else:
            tlsv11 = ServerParamsTlsv11(_tlsv11)

        _tlsv12 = d.pop("tlsv12", UNSET)
        tlsv12: Union[Unset, ServerParamsTlsv12]
        if isinstance(_tlsv12, Unset):
            tlsv12 = UNSET
        else:
            tlsv12 = ServerParamsTlsv12(_tlsv12)

        _tlsv13 = d.pop("tlsv13", UNSET)
        tlsv13: Union[Unset, ServerParamsTlsv13]
        if isinstance(_tlsv13, Unset):
            tlsv13 = UNSET
        else:
            tlsv13 = ServerParamsTlsv13(_tlsv13)

        track = d.pop("track", UNSET)

        _verify = d.pop("verify", UNSET)
        verify: Union[Unset, ServerParamsVerify]
        if isinstance(_verify, Unset):
            verify = UNSET
        else:
            verify = ServerParamsVerify(_verify)

        verifyhost = d.pop("verifyhost", UNSET)

        def _parse_weight(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        weight = _parse_weight(d.pop("weight", UNSET))

        _ws = d.pop("ws", UNSET)
        ws: Union[Unset, ServerParamsWs]
        if isinstance(_ws, Unset):
            ws = UNSET
        else:
            ws = ServerParamsWs(_ws)

        def _parse_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        id = _parse_id(d.pop("id", UNSET))

        metadata = d.pop("metadata", UNSET)

        def _parse_port(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        port = _parse_port(d.pop("port", UNSET))

        server_template = cls(
            fqdn=fqdn,
            num_or_range=num_or_range,
            prefix=prefix,
            agent_addr=agent_addr,
            agent_check=agent_check,
            agent_inter=agent_inter,
            agent_port=agent_port,
            agent_send=agent_send,
            allow_0rtt=allow_0rtt,
            alpn=alpn,
            backup=backup,
            check=check,
            check_pool_conn_name=check_pool_conn_name,
            check_reuse_pool=check_reuse_pool,
            check_send_proxy=check_send_proxy,
            check_sni=check_sni,
            check_ssl=check_ssl,
            check_alpn=check_alpn,
            check_proto=check_proto,
            check_via_socks4=check_via_socks4,
            ciphers=ciphers,
            ciphersuites=ciphersuites,
            client_sigalgs=client_sigalgs,
            cookie=cookie,
            crl_file=crl_file,
            curves=curves,
            downinter=downinter,
            error_limit=error_limit,
            fall=fall,
            fastinter=fastinter,
            force_sslv3=force_sslv3,
            force_tlsv10=force_tlsv10,
            force_tlsv11=force_tlsv11,
            force_tlsv12=force_tlsv12,
            force_tlsv13=force_tlsv13,
            guid=guid,
            hash_key=hash_key,
            health_check_address=health_check_address,
            health_check_port=health_check_port,
            idle_ping=idle_ping,
            init_addr=init_addr,
            init_state=init_state,
            inter=inter,
            log_bufsize=log_bufsize,
            log_proto=log_proto,
            maintenance=maintenance,
            max_reuse=max_reuse,
            maxconn=maxconn,
            maxqueue=maxqueue,
            minconn=minconn,
            namespace=namespace,
            no_sslv3=no_sslv3,
            no_tlsv10=no_tlsv10,
            no_tlsv11=no_tlsv11,
            no_tlsv12=no_tlsv12,
            no_tlsv13=no_tlsv13,
            no_verifyhost=no_verifyhost,
            npn=npn,
            observe=observe,
            on_error=on_error,
            on_marked_down=on_marked_down,
            on_marked_up=on_marked_up,
            pool_conn_name=pool_conn_name,
            pool_low_conn=pool_low_conn,
            pool_max_conn=pool_max_conn,
            pool_purge_delay=pool_purge_delay,
            proto=proto,
            proxy_v2_options=proxy_v2_options,
            redir=redir,
            resolve_net=resolve_net,
            resolve_prefer=resolve_prefer,
            resolve_opts=resolve_opts,
            resolvers=resolvers,
            rise=rise,
            send_proxy=send_proxy,
            send_proxy_v2=send_proxy_v2,
            send_proxy_v2_ssl=send_proxy_v2_ssl,
            send_proxy_v2_ssl_cn=send_proxy_v2_ssl_cn,
            set_proxy_v2_tlv_fmt=set_proxy_v2_tlv_fmt,
            shard=shard,
            sigalgs=sigalgs,
            slowstart=slowstart,
            sni=sni,
            socks4=socks4,
            source=source,
            ssl=ssl,
            ssl_cafile=ssl_cafile,
            ssl_certificate=ssl_certificate,
            ssl_max_ver=ssl_max_ver,
            ssl_min_ver=ssl_min_ver,
            ssl_reuse=ssl_reuse,
            sslv3=sslv3,
            stick=stick,
            strict_maxconn=strict_maxconn,
            tcp_ut=tcp_ut,
            tfo=tfo,
            tls_tickets=tls_tickets,
            tlsv10=tlsv10,
            tlsv11=tlsv11,
            tlsv12=tlsv12,
            tlsv13=tlsv13,
            track=track,
            verify=verify,
            verifyhost=verifyhost,
            weight=weight,
            ws=ws,
            id=id,
            metadata=metadata,
            port=port,
        )

        return server_template
