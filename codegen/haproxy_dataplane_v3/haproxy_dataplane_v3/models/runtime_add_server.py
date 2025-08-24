from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.runtime_add_server_agent_check import RuntimeAddServerAgentCheck
from ..models.runtime_add_server_backup import RuntimeAddServerBackup
from ..models.runtime_add_server_check import RuntimeAddServerCheck
from ..models.runtime_add_server_check_send_proxy import RuntimeAddServerCheckSendProxy
from ..models.runtime_add_server_check_ssl import RuntimeAddServerCheckSsl
from ..models.runtime_add_server_check_via_socks_4 import RuntimeAddServerCheckViaSocks4
from ..models.runtime_add_server_force_sslv_3 import RuntimeAddServerForceSslv3
from ..models.runtime_add_server_force_tlsv_10 import RuntimeAddServerForceTlsv10
from ..models.runtime_add_server_force_tlsv_11 import RuntimeAddServerForceTlsv11
from ..models.runtime_add_server_force_tlsv_12 import RuntimeAddServerForceTlsv12
from ..models.runtime_add_server_force_tlsv_13 import RuntimeAddServerForceTlsv13
from ..models.runtime_add_server_maintenance import RuntimeAddServerMaintenance
from ..models.runtime_add_server_no_sslv_3 import RuntimeAddServerNoSslv3
from ..models.runtime_add_server_no_tlsv_10 import RuntimeAddServerNoTlsv10
from ..models.runtime_add_server_no_tlsv_11 import RuntimeAddServerNoTlsv11
from ..models.runtime_add_server_no_tlsv_12 import RuntimeAddServerNoTlsv12
from ..models.runtime_add_server_no_tlsv_13 import RuntimeAddServerNoTlsv13
from ..models.runtime_add_server_observe import RuntimeAddServerObserve
from ..models.runtime_add_server_on_error import RuntimeAddServerOnError
from ..models.runtime_add_server_on_marked_down import RuntimeAddServerOnMarkedDown
from ..models.runtime_add_server_on_marked_up import RuntimeAddServerOnMarkedUp
from ..models.runtime_add_server_proxy_v2_options_item import RuntimeAddServerProxyV2OptionsItem
from ..models.runtime_add_server_send_proxy import RuntimeAddServerSendProxy
from ..models.runtime_add_server_send_proxy_v2 import RuntimeAddServerSendProxyV2
from ..models.runtime_add_server_send_proxy_v2_ssl import RuntimeAddServerSendProxyV2Ssl
from ..models.runtime_add_server_send_proxy_v2_ssl_cn import RuntimeAddServerSendProxyV2SslCn
from ..models.runtime_add_server_ssl import RuntimeAddServerSsl
from ..models.runtime_add_server_ssl_max_ver import RuntimeAddServerSslMaxVer
from ..models.runtime_add_server_ssl_min_ver import RuntimeAddServerSslMinVer
from ..models.runtime_add_server_ssl_reuse import RuntimeAddServerSslReuse
from ..models.runtime_add_server_tfo import RuntimeAddServerTfo
from ..models.runtime_add_server_tls_tickets import RuntimeAddServerTlsTickets
from ..models.runtime_add_server_verify import RuntimeAddServerVerify
from ..models.runtime_add_server_ws import RuntimeAddServerWs
from ..types import UNSET, Unset

T = TypeVar("T", bound="RuntimeAddServer")


@_attrs_define
class RuntimeAddServer:
    """Settable properties when adding a new server using HAProxy's runtime.

    Attributes:
        address (Union[Unset, str]):
        agent_addr (Union[Unset, str]):
        agent_check (Union[Unset, RuntimeAddServerAgentCheck]):
        agent_inter (Union[None, Unset, int]):
        agent_port (Union[None, Unset, int]):
        agent_send (Union[Unset, str]):
        allow_0rtt (Union[Unset, bool]):
        alpn (Union[Unset, str]):
        backup (Union[Unset, RuntimeAddServerBackup]):
        check (Union[Unset, RuntimeAddServerCheck]):
        check_send_proxy (Union[Unset, RuntimeAddServerCheckSendProxy]):
        check_sni (Union[Unset, str]):
        check_ssl (Union[Unset, RuntimeAddServerCheckSsl]):
        check_alpn (Union[Unset, str]):
        check_proto (Union[Unset, str]):
        check_via_socks4 (Union[Unset, RuntimeAddServerCheckViaSocks4]):
        ciphers (Union[Unset, str]):
        ciphersuites (Union[Unset, str]):
        crl_file (Union[Unset, str]):
        downinter (Union[None, Unset, int]):
        error_limit (Union[None, Unset, int]):
        fall (Union[None, Unset, int]):
        fastinter (Union[None, Unset, int]):
        force_sslv3 (Union[Unset, RuntimeAddServerForceSslv3]):
        force_tlsv10 (Union[Unset, RuntimeAddServerForceTlsv10]):
        force_tlsv11 (Union[Unset, RuntimeAddServerForceTlsv11]):
        force_tlsv12 (Union[Unset, RuntimeAddServerForceTlsv12]):
        force_tlsv13 (Union[Unset, RuntimeAddServerForceTlsv13]):
        health_check_address (Union[Unset, str]):
        health_check_port (Union[None, Unset, int]):
        id (Union[Unset, str]):
        inter (Union[None, Unset, int]):
        maintenance (Union[Unset, RuntimeAddServerMaintenance]):
        maxconn (Union[None, Unset, int]):
        maxqueue (Union[None, Unset, int]):
        minconn (Union[None, Unset, int]):
        name (Union[Unset, str]):
        no_sslv3 (Union[Unset, RuntimeAddServerNoSslv3]):
        no_tlsv10 (Union[Unset, RuntimeAddServerNoTlsv10]):
        no_tlsv11 (Union[Unset, RuntimeAddServerNoTlsv11]):
        no_tlsv12 (Union[Unset, RuntimeAddServerNoTlsv12]):
        no_tlsv13 (Union[Unset, RuntimeAddServerNoTlsv13]):
        npn (Union[Unset, str]):
        observe (Union[Unset, RuntimeAddServerObserve]):
        on_error (Union[Unset, RuntimeAddServerOnError]):
        on_marked_down (Union[Unset, RuntimeAddServerOnMarkedDown]):
        on_marked_up (Union[Unset, RuntimeAddServerOnMarkedUp]):
        pool_low_conn (Union[None, Unset, int]):
        pool_max_conn (Union[None, Unset, int]):
        pool_purge_delay (Union[None, Unset, int]):
        port (Union[None, Unset, int]):
        proto (Union[Unset, str]):
        proxy_v2_options (Union[Unset, list[RuntimeAddServerProxyV2OptionsItem]]):
        rise (Union[None, Unset, int]):
        send_proxy (Union[Unset, RuntimeAddServerSendProxy]):
        send_proxy_v2 (Union[Unset, RuntimeAddServerSendProxyV2]):
        send_proxy_v2_ssl (Union[Unset, RuntimeAddServerSendProxyV2Ssl]):
        send_proxy_v2_ssl_cn (Union[Unset, RuntimeAddServerSendProxyV2SslCn]):
        slowstart (Union[None, Unset, int]):
        sni (Union[Unset, str]):
        source (Union[Unset, str]):
        ssl (Union[Unset, RuntimeAddServerSsl]):
        ssl_cafile (Union[Unset, str]):
        ssl_certificate (Union[Unset, str]):
        ssl_max_ver (Union[Unset, RuntimeAddServerSslMaxVer]):
        ssl_min_ver (Union[Unset, RuntimeAddServerSslMinVer]):
        ssl_reuse (Union[Unset, RuntimeAddServerSslReuse]):
        tfo (Union[Unset, RuntimeAddServerTfo]):
        tls_tickets (Union[Unset, RuntimeAddServerTlsTickets]):
        track (Union[Unset, str]):
        verify (Union[Unset, RuntimeAddServerVerify]):
        verifyhost (Union[Unset, str]):
        weight (Union[None, Unset, int]):
        ws (Union[Unset, RuntimeAddServerWs]):
    """

    address: Union[Unset, str] = UNSET
    agent_addr: Union[Unset, str] = UNSET
    agent_check: Union[Unset, RuntimeAddServerAgentCheck] = UNSET
    agent_inter: Union[None, Unset, int] = UNSET
    agent_port: Union[None, Unset, int] = UNSET
    agent_send: Union[Unset, str] = UNSET
    allow_0rtt: Union[Unset, bool] = UNSET
    alpn: Union[Unset, str] = UNSET
    backup: Union[Unset, RuntimeAddServerBackup] = UNSET
    check: Union[Unset, RuntimeAddServerCheck] = UNSET
    check_send_proxy: Union[Unset, RuntimeAddServerCheckSendProxy] = UNSET
    check_sni: Union[Unset, str] = UNSET
    check_ssl: Union[Unset, RuntimeAddServerCheckSsl] = UNSET
    check_alpn: Union[Unset, str] = UNSET
    check_proto: Union[Unset, str] = UNSET
    check_via_socks4: Union[Unset, RuntimeAddServerCheckViaSocks4] = UNSET
    ciphers: Union[Unset, str] = UNSET
    ciphersuites: Union[Unset, str] = UNSET
    crl_file: Union[Unset, str] = UNSET
    downinter: Union[None, Unset, int] = UNSET
    error_limit: Union[None, Unset, int] = UNSET
    fall: Union[None, Unset, int] = UNSET
    fastinter: Union[None, Unset, int] = UNSET
    force_sslv3: Union[Unset, RuntimeAddServerForceSslv3] = UNSET
    force_tlsv10: Union[Unset, RuntimeAddServerForceTlsv10] = UNSET
    force_tlsv11: Union[Unset, RuntimeAddServerForceTlsv11] = UNSET
    force_tlsv12: Union[Unset, RuntimeAddServerForceTlsv12] = UNSET
    force_tlsv13: Union[Unset, RuntimeAddServerForceTlsv13] = UNSET
    health_check_address: Union[Unset, str] = UNSET
    health_check_port: Union[None, Unset, int] = UNSET
    id: Union[Unset, str] = UNSET
    inter: Union[None, Unset, int] = UNSET
    maintenance: Union[Unset, RuntimeAddServerMaintenance] = UNSET
    maxconn: Union[None, Unset, int] = UNSET
    maxqueue: Union[None, Unset, int] = UNSET
    minconn: Union[None, Unset, int] = UNSET
    name: Union[Unset, str] = UNSET
    no_sslv3: Union[Unset, RuntimeAddServerNoSslv3] = UNSET
    no_tlsv10: Union[Unset, RuntimeAddServerNoTlsv10] = UNSET
    no_tlsv11: Union[Unset, RuntimeAddServerNoTlsv11] = UNSET
    no_tlsv12: Union[Unset, RuntimeAddServerNoTlsv12] = UNSET
    no_tlsv13: Union[Unset, RuntimeAddServerNoTlsv13] = UNSET
    npn: Union[Unset, str] = UNSET
    observe: Union[Unset, RuntimeAddServerObserve] = UNSET
    on_error: Union[Unset, RuntimeAddServerOnError] = UNSET
    on_marked_down: Union[Unset, RuntimeAddServerOnMarkedDown] = UNSET
    on_marked_up: Union[Unset, RuntimeAddServerOnMarkedUp] = UNSET
    pool_low_conn: Union[None, Unset, int] = UNSET
    pool_max_conn: Union[None, Unset, int] = UNSET
    pool_purge_delay: Union[None, Unset, int] = UNSET
    port: Union[None, Unset, int] = UNSET
    proto: Union[Unset, str] = UNSET
    proxy_v2_options: Union[Unset, list[RuntimeAddServerProxyV2OptionsItem]] = UNSET
    rise: Union[None, Unset, int] = UNSET
    send_proxy: Union[Unset, RuntimeAddServerSendProxy] = UNSET
    send_proxy_v2: Union[Unset, RuntimeAddServerSendProxyV2] = UNSET
    send_proxy_v2_ssl: Union[Unset, RuntimeAddServerSendProxyV2Ssl] = UNSET
    send_proxy_v2_ssl_cn: Union[Unset, RuntimeAddServerSendProxyV2SslCn] = UNSET
    slowstart: Union[None, Unset, int] = UNSET
    sni: Union[Unset, str] = UNSET
    source: Union[Unset, str] = UNSET
    ssl: Union[Unset, RuntimeAddServerSsl] = UNSET
    ssl_cafile: Union[Unset, str] = UNSET
    ssl_certificate: Union[Unset, str] = UNSET
    ssl_max_ver: Union[Unset, RuntimeAddServerSslMaxVer] = UNSET
    ssl_min_ver: Union[Unset, RuntimeAddServerSslMinVer] = UNSET
    ssl_reuse: Union[Unset, RuntimeAddServerSslReuse] = UNSET
    tfo: Union[Unset, RuntimeAddServerTfo] = UNSET
    tls_tickets: Union[Unset, RuntimeAddServerTlsTickets] = UNSET
    track: Union[Unset, str] = UNSET
    verify: Union[Unset, RuntimeAddServerVerify] = UNSET
    verifyhost: Union[Unset, str] = UNSET
    weight: Union[None, Unset, int] = UNSET
    ws: Union[Unset, RuntimeAddServerWs] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        address = self.address

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

        crl_file = self.crl_file

        downinter: Union[None, Unset, int]
        if isinstance(self.downinter, Unset):
            downinter = UNSET
        else:
            downinter = self.downinter

        error_limit: Union[None, Unset, int]
        if isinstance(self.error_limit, Unset):
            error_limit = UNSET
        else:
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

        health_check_address = self.health_check_address

        health_check_port: Union[None, Unset, int]
        if isinstance(self.health_check_port, Unset):
            health_check_port = UNSET
        else:
            health_check_port = self.health_check_port

        id = self.id

        inter: Union[None, Unset, int]
        if isinstance(self.inter, Unset):
            inter = UNSET
        else:
            inter = self.inter

        maintenance: Union[Unset, str] = UNSET
        if not isinstance(self.maintenance, Unset):
            maintenance = self.maintenance.value

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

        name = self.name

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

        port: Union[None, Unset, int]
        if isinstance(self.port, Unset):
            port = UNSET
        else:
            port = self.port

        proto = self.proto

        proxy_v2_options: Union[Unset, list[str]] = UNSET
        if not isinstance(self.proxy_v2_options, Unset):
            proxy_v2_options = []
            for proxy_v2_options_item_data in self.proxy_v2_options:
                proxy_v2_options_item = proxy_v2_options_item_data.value
                proxy_v2_options.append(proxy_v2_options_item)

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

        slowstart: Union[None, Unset, int]
        if isinstance(self.slowstart, Unset):
            slowstart = UNSET
        else:
            slowstart = self.slowstart

        sni = self.sni

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

        tfo: Union[Unset, str] = UNSET
        if not isinstance(self.tfo, Unset):
            tfo = self.tfo.value

        tls_tickets: Union[Unset, str] = UNSET
        if not isinstance(self.tls_tickets, Unset):
            tls_tickets = self.tls_tickets.value

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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if address is not UNSET:
            field_dict["address"] = address
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
        if crl_file is not UNSET:
            field_dict["crl_file"] = crl_file
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
        if health_check_address is not UNSET:
            field_dict["health_check_address"] = health_check_address
        if health_check_port is not UNSET:
            field_dict["health_check_port"] = health_check_port
        if id is not UNSET:
            field_dict["id"] = id
        if inter is not UNSET:
            field_dict["inter"] = inter
        if maintenance is not UNSET:
            field_dict["maintenance"] = maintenance
        if maxconn is not UNSET:
            field_dict["maxconn"] = maxconn
        if maxqueue is not UNSET:
            field_dict["maxqueue"] = maxqueue
        if minconn is not UNSET:
            field_dict["minconn"] = minconn
        if name is not UNSET:
            field_dict["name"] = name
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
        if pool_low_conn is not UNSET:
            field_dict["pool_low_conn"] = pool_low_conn
        if pool_max_conn is not UNSET:
            field_dict["pool_max_conn"] = pool_max_conn
        if pool_purge_delay is not UNSET:
            field_dict["pool_purge_delay"] = pool_purge_delay
        if port is not UNSET:
            field_dict["port"] = port
        if proto is not UNSET:
            field_dict["proto"] = proto
        if proxy_v2_options is not UNSET:
            field_dict["proxy-v2-options"] = proxy_v2_options
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
        if slowstart is not UNSET:
            field_dict["slowstart"] = slowstart
        if sni is not UNSET:
            field_dict["sni"] = sni
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
        if tfo is not UNSET:
            field_dict["tfo"] = tfo
        if tls_tickets is not UNSET:
            field_dict["tls_tickets"] = tls_tickets
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        address = d.pop("address", UNSET)

        agent_addr = d.pop("agent-addr", UNSET)

        _agent_check = d.pop("agent-check", UNSET)
        agent_check: Union[Unset, RuntimeAddServerAgentCheck]
        if isinstance(_agent_check, Unset):
            agent_check = UNSET
        else:
            agent_check = RuntimeAddServerAgentCheck(_agent_check)

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
        backup: Union[Unset, RuntimeAddServerBackup]
        if isinstance(_backup, Unset):
            backup = UNSET
        else:
            backup = RuntimeAddServerBackup(_backup)

        _check = d.pop("check", UNSET)
        check: Union[Unset, RuntimeAddServerCheck]
        if isinstance(_check, Unset):
            check = UNSET
        else:
            check = RuntimeAddServerCheck(_check)

        _check_send_proxy = d.pop("check-send-proxy", UNSET)
        check_send_proxy: Union[Unset, RuntimeAddServerCheckSendProxy]
        if isinstance(_check_send_proxy, Unset):
            check_send_proxy = UNSET
        else:
            check_send_proxy = RuntimeAddServerCheckSendProxy(_check_send_proxy)

        check_sni = d.pop("check-sni", UNSET)

        _check_ssl = d.pop("check-ssl", UNSET)
        check_ssl: Union[Unset, RuntimeAddServerCheckSsl]
        if isinstance(_check_ssl, Unset):
            check_ssl = UNSET
        else:
            check_ssl = RuntimeAddServerCheckSsl(_check_ssl)

        check_alpn = d.pop("check_alpn", UNSET)

        check_proto = d.pop("check_proto", UNSET)

        _check_via_socks4 = d.pop("check_via_socks4", UNSET)
        check_via_socks4: Union[Unset, RuntimeAddServerCheckViaSocks4]
        if isinstance(_check_via_socks4, Unset):
            check_via_socks4 = UNSET
        else:
            check_via_socks4 = RuntimeAddServerCheckViaSocks4(_check_via_socks4)

        ciphers = d.pop("ciphers", UNSET)

        ciphersuites = d.pop("ciphersuites", UNSET)

        crl_file = d.pop("crl_file", UNSET)

        def _parse_downinter(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        downinter = _parse_downinter(d.pop("downinter", UNSET))

        def _parse_error_limit(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        error_limit = _parse_error_limit(d.pop("error_limit", UNSET))

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
        force_sslv3: Union[Unset, RuntimeAddServerForceSslv3]
        if isinstance(_force_sslv3, Unset):
            force_sslv3 = UNSET
        else:
            force_sslv3 = RuntimeAddServerForceSslv3(_force_sslv3)

        _force_tlsv10 = d.pop("force_tlsv10", UNSET)
        force_tlsv10: Union[Unset, RuntimeAddServerForceTlsv10]
        if isinstance(_force_tlsv10, Unset):
            force_tlsv10 = UNSET
        else:
            force_tlsv10 = RuntimeAddServerForceTlsv10(_force_tlsv10)

        _force_tlsv11 = d.pop("force_tlsv11", UNSET)
        force_tlsv11: Union[Unset, RuntimeAddServerForceTlsv11]
        if isinstance(_force_tlsv11, Unset):
            force_tlsv11 = UNSET
        else:
            force_tlsv11 = RuntimeAddServerForceTlsv11(_force_tlsv11)

        _force_tlsv12 = d.pop("force_tlsv12", UNSET)
        force_tlsv12: Union[Unset, RuntimeAddServerForceTlsv12]
        if isinstance(_force_tlsv12, Unset):
            force_tlsv12 = UNSET
        else:
            force_tlsv12 = RuntimeAddServerForceTlsv12(_force_tlsv12)

        _force_tlsv13 = d.pop("force_tlsv13", UNSET)
        force_tlsv13: Union[Unset, RuntimeAddServerForceTlsv13]
        if isinstance(_force_tlsv13, Unset):
            force_tlsv13 = UNSET
        else:
            force_tlsv13 = RuntimeAddServerForceTlsv13(_force_tlsv13)

        health_check_address = d.pop("health_check_address", UNSET)

        def _parse_health_check_port(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        health_check_port = _parse_health_check_port(d.pop("health_check_port", UNSET))

        id = d.pop("id", UNSET)

        def _parse_inter(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        inter = _parse_inter(d.pop("inter", UNSET))

        _maintenance = d.pop("maintenance", UNSET)
        maintenance: Union[Unset, RuntimeAddServerMaintenance]
        if isinstance(_maintenance, Unset):
            maintenance = UNSET
        else:
            maintenance = RuntimeAddServerMaintenance(_maintenance)

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

        name = d.pop("name", UNSET)

        _no_sslv3 = d.pop("no_sslv3", UNSET)
        no_sslv3: Union[Unset, RuntimeAddServerNoSslv3]
        if isinstance(_no_sslv3, Unset):
            no_sslv3 = UNSET
        else:
            no_sslv3 = RuntimeAddServerNoSslv3(_no_sslv3)

        _no_tlsv10 = d.pop("no_tlsv10", UNSET)
        no_tlsv10: Union[Unset, RuntimeAddServerNoTlsv10]
        if isinstance(_no_tlsv10, Unset):
            no_tlsv10 = UNSET
        else:
            no_tlsv10 = RuntimeAddServerNoTlsv10(_no_tlsv10)

        _no_tlsv11 = d.pop("no_tlsv11", UNSET)
        no_tlsv11: Union[Unset, RuntimeAddServerNoTlsv11]
        if isinstance(_no_tlsv11, Unset):
            no_tlsv11 = UNSET
        else:
            no_tlsv11 = RuntimeAddServerNoTlsv11(_no_tlsv11)

        _no_tlsv12 = d.pop("no_tlsv12", UNSET)
        no_tlsv12: Union[Unset, RuntimeAddServerNoTlsv12]
        if isinstance(_no_tlsv12, Unset):
            no_tlsv12 = UNSET
        else:
            no_tlsv12 = RuntimeAddServerNoTlsv12(_no_tlsv12)

        _no_tlsv13 = d.pop("no_tlsv13", UNSET)
        no_tlsv13: Union[Unset, RuntimeAddServerNoTlsv13]
        if isinstance(_no_tlsv13, Unset):
            no_tlsv13 = UNSET
        else:
            no_tlsv13 = RuntimeAddServerNoTlsv13(_no_tlsv13)

        npn = d.pop("npn", UNSET)

        _observe = d.pop("observe", UNSET)
        observe: Union[Unset, RuntimeAddServerObserve]
        if isinstance(_observe, Unset):
            observe = UNSET
        else:
            observe = RuntimeAddServerObserve(_observe)

        _on_error = d.pop("on-error", UNSET)
        on_error: Union[Unset, RuntimeAddServerOnError]
        if isinstance(_on_error, Unset):
            on_error = UNSET
        else:
            on_error = RuntimeAddServerOnError(_on_error)

        _on_marked_down = d.pop("on-marked-down", UNSET)
        on_marked_down: Union[Unset, RuntimeAddServerOnMarkedDown]
        if isinstance(_on_marked_down, Unset):
            on_marked_down = UNSET
        else:
            on_marked_down = RuntimeAddServerOnMarkedDown(_on_marked_down)

        _on_marked_up = d.pop("on-marked-up", UNSET)
        on_marked_up: Union[Unset, RuntimeAddServerOnMarkedUp]
        if isinstance(_on_marked_up, Unset):
            on_marked_up = UNSET
        else:
            on_marked_up = RuntimeAddServerOnMarkedUp(_on_marked_up)

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

        def _parse_port(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        port = _parse_port(d.pop("port", UNSET))

        proto = d.pop("proto", UNSET)

        proxy_v2_options = []
        _proxy_v2_options = d.pop("proxy-v2-options", UNSET)
        for proxy_v2_options_item_data in _proxy_v2_options or []:
            proxy_v2_options_item = RuntimeAddServerProxyV2OptionsItem(proxy_v2_options_item_data)

            proxy_v2_options.append(proxy_v2_options_item)

        def _parse_rise(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        rise = _parse_rise(d.pop("rise", UNSET))

        _send_proxy = d.pop("send-proxy", UNSET)
        send_proxy: Union[Unset, RuntimeAddServerSendProxy]
        if isinstance(_send_proxy, Unset):
            send_proxy = UNSET
        else:
            send_proxy = RuntimeAddServerSendProxy(_send_proxy)

        _send_proxy_v2 = d.pop("send-proxy-v2", UNSET)
        send_proxy_v2: Union[Unset, RuntimeAddServerSendProxyV2]
        if isinstance(_send_proxy_v2, Unset):
            send_proxy_v2 = UNSET
        else:
            send_proxy_v2 = RuntimeAddServerSendProxyV2(_send_proxy_v2)

        _send_proxy_v2_ssl = d.pop("send_proxy_v2_ssl", UNSET)
        send_proxy_v2_ssl: Union[Unset, RuntimeAddServerSendProxyV2Ssl]
        if isinstance(_send_proxy_v2_ssl, Unset):
            send_proxy_v2_ssl = UNSET
        else:
            send_proxy_v2_ssl = RuntimeAddServerSendProxyV2Ssl(_send_proxy_v2_ssl)

        _send_proxy_v2_ssl_cn = d.pop("send_proxy_v2_ssl_cn", UNSET)
        send_proxy_v2_ssl_cn: Union[Unset, RuntimeAddServerSendProxyV2SslCn]
        if isinstance(_send_proxy_v2_ssl_cn, Unset):
            send_proxy_v2_ssl_cn = UNSET
        else:
            send_proxy_v2_ssl_cn = RuntimeAddServerSendProxyV2SslCn(_send_proxy_v2_ssl_cn)

        def _parse_slowstart(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        slowstart = _parse_slowstart(d.pop("slowstart", UNSET))

        sni = d.pop("sni", UNSET)

        source = d.pop("source", UNSET)

        _ssl = d.pop("ssl", UNSET)
        ssl: Union[Unset, RuntimeAddServerSsl]
        if isinstance(_ssl, Unset):
            ssl = UNSET
        else:
            ssl = RuntimeAddServerSsl(_ssl)

        ssl_cafile = d.pop("ssl_cafile", UNSET)

        ssl_certificate = d.pop("ssl_certificate", UNSET)

        _ssl_max_ver = d.pop("ssl_max_ver", UNSET)
        ssl_max_ver: Union[Unset, RuntimeAddServerSslMaxVer]
        if isinstance(_ssl_max_ver, Unset):
            ssl_max_ver = UNSET
        else:
            ssl_max_ver = RuntimeAddServerSslMaxVer(_ssl_max_ver)

        _ssl_min_ver = d.pop("ssl_min_ver", UNSET)
        ssl_min_ver: Union[Unset, RuntimeAddServerSslMinVer]
        if isinstance(_ssl_min_ver, Unset):
            ssl_min_ver = UNSET
        else:
            ssl_min_ver = RuntimeAddServerSslMinVer(_ssl_min_ver)

        _ssl_reuse = d.pop("ssl_reuse", UNSET)
        ssl_reuse: Union[Unset, RuntimeAddServerSslReuse]
        if isinstance(_ssl_reuse, Unset):
            ssl_reuse = UNSET
        else:
            ssl_reuse = RuntimeAddServerSslReuse(_ssl_reuse)

        _tfo = d.pop("tfo", UNSET)
        tfo: Union[Unset, RuntimeAddServerTfo]
        if isinstance(_tfo, Unset):
            tfo = UNSET
        else:
            tfo = RuntimeAddServerTfo(_tfo)

        _tls_tickets = d.pop("tls_tickets", UNSET)
        tls_tickets: Union[Unset, RuntimeAddServerTlsTickets]
        if isinstance(_tls_tickets, Unset):
            tls_tickets = UNSET
        else:
            tls_tickets = RuntimeAddServerTlsTickets(_tls_tickets)

        track = d.pop("track", UNSET)

        _verify = d.pop("verify", UNSET)
        verify: Union[Unset, RuntimeAddServerVerify]
        if isinstance(_verify, Unset):
            verify = UNSET
        else:
            verify = RuntimeAddServerVerify(_verify)

        verifyhost = d.pop("verifyhost", UNSET)

        def _parse_weight(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        weight = _parse_weight(d.pop("weight", UNSET))

        _ws = d.pop("ws", UNSET)
        ws: Union[Unset, RuntimeAddServerWs]
        if isinstance(_ws, Unset):
            ws = UNSET
        else:
            ws = RuntimeAddServerWs(_ws)

        runtime_add_server = cls(
            address=address,
            agent_addr=agent_addr,
            agent_check=agent_check,
            agent_inter=agent_inter,
            agent_port=agent_port,
            agent_send=agent_send,
            allow_0rtt=allow_0rtt,
            alpn=alpn,
            backup=backup,
            check=check,
            check_send_proxy=check_send_proxy,
            check_sni=check_sni,
            check_ssl=check_ssl,
            check_alpn=check_alpn,
            check_proto=check_proto,
            check_via_socks4=check_via_socks4,
            ciphers=ciphers,
            ciphersuites=ciphersuites,
            crl_file=crl_file,
            downinter=downinter,
            error_limit=error_limit,
            fall=fall,
            fastinter=fastinter,
            force_sslv3=force_sslv3,
            force_tlsv10=force_tlsv10,
            force_tlsv11=force_tlsv11,
            force_tlsv12=force_tlsv12,
            force_tlsv13=force_tlsv13,
            health_check_address=health_check_address,
            health_check_port=health_check_port,
            id=id,
            inter=inter,
            maintenance=maintenance,
            maxconn=maxconn,
            maxqueue=maxqueue,
            minconn=minconn,
            name=name,
            no_sslv3=no_sslv3,
            no_tlsv10=no_tlsv10,
            no_tlsv11=no_tlsv11,
            no_tlsv12=no_tlsv12,
            no_tlsv13=no_tlsv13,
            npn=npn,
            observe=observe,
            on_error=on_error,
            on_marked_down=on_marked_down,
            on_marked_up=on_marked_up,
            pool_low_conn=pool_low_conn,
            pool_max_conn=pool_max_conn,
            pool_purge_delay=pool_purge_delay,
            port=port,
            proto=proto,
            proxy_v2_options=proxy_v2_options,
            rise=rise,
            send_proxy=send_proxy,
            send_proxy_v2=send_proxy_v2,
            send_proxy_v2_ssl=send_proxy_v2_ssl,
            send_proxy_v2_ssl_cn=send_proxy_v2_ssl_cn,
            slowstart=slowstart,
            sni=sni,
            source=source,
            ssl=ssl,
            ssl_cafile=ssl_cafile,
            ssl_certificate=ssl_certificate,
            ssl_max_ver=ssl_max_ver,
            ssl_min_ver=ssl_min_ver,
            ssl_reuse=ssl_reuse,
            tfo=tfo,
            tls_tickets=tls_tickets,
            track=track,
            verify=verify,
            verifyhost=verifyhost,
            weight=weight,
            ws=ws,
        )

        runtime_add_server.additional_properties = d
        return runtime_add_server

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
