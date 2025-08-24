from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.bind_params_force_strict_sni import BindParamsForceStrictSni
from ..models.bind_params_level import BindParamsLevel
from ..models.bind_params_quic_cc_algo import BindParamsQuicCcAlgo
from ..models.bind_params_quic_socket import BindParamsQuicSocket
from ..models.bind_params_severity_output import BindParamsSeverityOutput
from ..models.bind_params_ssl_max_ver import BindParamsSslMaxVer
from ..models.bind_params_ssl_min_ver import BindParamsSslMinVer
from ..models.bind_params_sslv_3 import BindParamsSslv3
from ..models.bind_params_tls_tickets import BindParamsTlsTickets
from ..models.bind_params_tlsv_10 import BindParamsTlsv10
from ..models.bind_params_tlsv_11 import BindParamsTlsv11
from ..models.bind_params_tlsv_12 import BindParamsTlsv12
from ..models.bind_params_tlsv_13 import BindParamsTlsv13
from ..models.bind_params_verify import BindParamsVerify
from ..types import UNSET, Unset

T = TypeVar("T", bound="GlobalBaseRuntimeApisItem")


@_attrs_define
class GlobalBaseRuntimeApisItem:
    """
    Attributes:
        address (str):
        accept_netscaler_cip (Union[Unset, int]):
        accept_proxy (Union[Unset, bool]):
        allow_0rtt (Union[Unset, bool]):
        alpn (Union[Unset, str]):
        backlog (Union[Unset, str]):
        ca_ignore_err (Union[Unset, str]):
        ca_sign_file (Union[Unset, str]):
        ca_sign_pass (Union[Unset, str]):
        ca_verify_file (Union[Unset, str]):
        ciphers (Union[Unset, str]):
        ciphersuites (Union[Unset, str]):
        client_sigalgs (Union[Unset, str]):
        crl_file (Union[Unset, str]):
        crt_ignore_err (Union[Unset, str]):
        crt_list (Union[Unset, str]):
        curves (Union[Unset, str]):
        default_crt_list (Union[Unset, list[str]]):
        defer_accept (Union[Unset, bool]):
        ecdhe (Union[Unset, str]):
        expose_fd_listeners (Union[Unset, bool]):
        force_sslv3 (Union[Unset, bool]): This field is deprecated in favor of sslv3, and will be removed in a future
            release
        force_strict_sni (Union[Unset, BindParamsForceStrictSni]):
        force_tlsv10 (Union[Unset, bool]): This field is deprecated in favor of tlsv10, and will be removed in a future
            release
        force_tlsv11 (Union[Unset, bool]): This field is deprecated in favor of tlsv11, and will be removed in a future
            release
        force_tlsv12 (Union[Unset, bool]): This field is deprecated in favor of tlsv12, and will be removed in a future
            release
        force_tlsv13 (Union[Unset, bool]): This field is deprecated in favor of tlsv13, and will be removed in a future
            release
        generate_certificates (Union[Unset, bool]):
        gid (Union[Unset, int]):
        group (Union[Unset, str]):
        guid_prefix (Union[Unset, str]):
        id (Union[Unset, str]):
        idle_ping (Union[None, Unset, int]):
        interface (Union[Unset, str]):
        level (Union[Unset, BindParamsLevel]):  Example: user.
        maxconn (Union[Unset, int]):  Example: 1234.
        mode (Union[Unset, str]):
        mss (Union[Unset, str]):
        name (Union[Unset, str]):
        namespace (Union[Unset, str]):  Example: app.
        nbconn (Union[Unset, int]):
        nice (Union[Unset, int]):  Example: 1.
        no_alpn (Union[Unset, bool]):
        no_ca_names (Union[Unset, bool]):
        no_sslv3 (Union[Unset, bool]): This field is deprecated in favor of sslv3, and will be removed in a future
            release
        no_strict_sni (Union[Unset, bool]):
        no_tls_tickets (Union[Unset, bool]): This field is deprecated in favor of tls_tickets, and will be removed in a
            future release
        no_tlsv10 (Union[Unset, bool]): This field is deprecated in favor of tlsv10, and will be removed in a future
            release
        no_tlsv11 (Union[Unset, bool]): This field is deprecated in favor of tlsv11, and will be removed in a future
            release
        no_tlsv12 (Union[Unset, bool]): This field is deprecated in favor of tlsv12, and will be removed in a future
            release
        no_tlsv13 (Union[Unset, bool]): This field is deprecated in favor of tlsv13, and will be removed in a future
            release
        npn (Union[Unset, str]):
        prefer_client_ciphers (Union[Unset, bool]):
        proto (Union[Unset, str]):
        quic_cc_algo (Union[Unset, BindParamsQuicCcAlgo]):
        quic_force_retry (Union[Unset, bool]):
        quic_socket (Union[Unset, BindParamsQuicSocket]):
        quic_cc_algo_burst_size (Union[None, Unset, int]):
        quic_cc_algo_max_window (Union[None, Unset, int]):
        severity_output (Union[Unset, BindParamsSeverityOutput]):  Example: none.
        sigalgs (Union[Unset, str]):
        ssl (Union[Unset, bool]):
        ssl_cafile (Union[Unset, str]):
        ssl_certificate (Union[Unset, str]):
        ssl_max_ver (Union[Unset, BindParamsSslMaxVer]):
        ssl_min_ver (Union[Unset, BindParamsSslMinVer]):
        sslv3 (Union[Unset, BindParamsSslv3]):
        strict_sni (Union[Unset, bool]):
        tcp_user_timeout (Union[None, Unset, int]):
        tfo (Union[Unset, bool]):
        thread (Union[Unset, str]):
        tls_ticket_keys (Union[Unset, str]):
        tls_tickets (Union[Unset, BindParamsTlsTickets]):
        tlsv10 (Union[Unset, BindParamsTlsv10]):
        tlsv11 (Union[Unset, BindParamsTlsv11]):
        tlsv12 (Union[Unset, BindParamsTlsv12]):
        tlsv13 (Union[Unset, BindParamsTlsv13]):
        transparent (Union[Unset, bool]):
        uid (Union[Unset, str]):
        user (Union[Unset, str]):
        v4v6 (Union[Unset, bool]):
        v6only (Union[Unset, bool]):
        verify (Union[Unset, BindParamsVerify]):  Example: none.
    """

    address: str
    accept_netscaler_cip: Union[Unset, int] = UNSET
    accept_proxy: Union[Unset, bool] = UNSET
    allow_0rtt: Union[Unset, bool] = UNSET
    alpn: Union[Unset, str] = UNSET
    backlog: Union[Unset, str] = UNSET
    ca_ignore_err: Union[Unset, str] = UNSET
    ca_sign_file: Union[Unset, str] = UNSET
    ca_sign_pass: Union[Unset, str] = UNSET
    ca_verify_file: Union[Unset, str] = UNSET
    ciphers: Union[Unset, str] = UNSET
    ciphersuites: Union[Unset, str] = UNSET
    client_sigalgs: Union[Unset, str] = UNSET
    crl_file: Union[Unset, str] = UNSET
    crt_ignore_err: Union[Unset, str] = UNSET
    crt_list: Union[Unset, str] = UNSET
    curves: Union[Unset, str] = UNSET
    default_crt_list: Union[Unset, list[str]] = UNSET
    defer_accept: Union[Unset, bool] = UNSET
    ecdhe: Union[Unset, str] = UNSET
    expose_fd_listeners: Union[Unset, bool] = UNSET
    force_sslv3: Union[Unset, bool] = UNSET
    force_strict_sni: Union[Unset, BindParamsForceStrictSni] = UNSET
    force_tlsv10: Union[Unset, bool] = UNSET
    force_tlsv11: Union[Unset, bool] = UNSET
    force_tlsv12: Union[Unset, bool] = UNSET
    force_tlsv13: Union[Unset, bool] = UNSET
    generate_certificates: Union[Unset, bool] = UNSET
    gid: Union[Unset, int] = UNSET
    group: Union[Unset, str] = UNSET
    guid_prefix: Union[Unset, str] = UNSET
    id: Union[Unset, str] = UNSET
    idle_ping: Union[None, Unset, int] = UNSET
    interface: Union[Unset, str] = UNSET
    level: Union[Unset, BindParamsLevel] = UNSET
    maxconn: Union[Unset, int] = UNSET
    mode: Union[Unset, str] = UNSET
    mss: Union[Unset, str] = UNSET
    name: Union[Unset, str] = UNSET
    namespace: Union[Unset, str] = UNSET
    nbconn: Union[Unset, int] = UNSET
    nice: Union[Unset, int] = UNSET
    no_alpn: Union[Unset, bool] = UNSET
    no_ca_names: Union[Unset, bool] = UNSET
    no_sslv3: Union[Unset, bool] = UNSET
    no_strict_sni: Union[Unset, bool] = UNSET
    no_tls_tickets: Union[Unset, bool] = UNSET
    no_tlsv10: Union[Unset, bool] = UNSET
    no_tlsv11: Union[Unset, bool] = UNSET
    no_tlsv12: Union[Unset, bool] = UNSET
    no_tlsv13: Union[Unset, bool] = UNSET
    npn: Union[Unset, str] = UNSET
    prefer_client_ciphers: Union[Unset, bool] = UNSET
    proto: Union[Unset, str] = UNSET
    quic_cc_algo: Union[Unset, BindParamsQuicCcAlgo] = UNSET
    quic_force_retry: Union[Unset, bool] = UNSET
    quic_socket: Union[Unset, BindParamsQuicSocket] = UNSET
    quic_cc_algo_burst_size: Union[None, Unset, int] = UNSET
    quic_cc_algo_max_window: Union[None, Unset, int] = UNSET
    severity_output: Union[Unset, BindParamsSeverityOutput] = UNSET
    sigalgs: Union[Unset, str] = UNSET
    ssl: Union[Unset, bool] = UNSET
    ssl_cafile: Union[Unset, str] = UNSET
    ssl_certificate: Union[Unset, str] = UNSET
    ssl_max_ver: Union[Unset, BindParamsSslMaxVer] = UNSET
    ssl_min_ver: Union[Unset, BindParamsSslMinVer] = UNSET
    sslv3: Union[Unset, BindParamsSslv3] = UNSET
    strict_sni: Union[Unset, bool] = UNSET
    tcp_user_timeout: Union[None, Unset, int] = UNSET
    tfo: Union[Unset, bool] = UNSET
    thread: Union[Unset, str] = UNSET
    tls_ticket_keys: Union[Unset, str] = UNSET
    tls_tickets: Union[Unset, BindParamsTlsTickets] = UNSET
    tlsv10: Union[Unset, BindParamsTlsv10] = UNSET
    tlsv11: Union[Unset, BindParamsTlsv11] = UNSET
    tlsv12: Union[Unset, BindParamsTlsv12] = UNSET
    tlsv13: Union[Unset, BindParamsTlsv13] = UNSET
    transparent: Union[Unset, bool] = UNSET
    uid: Union[Unset, str] = UNSET
    user: Union[Unset, str] = UNSET
    v4v6: Union[Unset, bool] = UNSET
    v6only: Union[Unset, bool] = UNSET
    verify: Union[Unset, BindParamsVerify] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        address = self.address

        accept_netscaler_cip = self.accept_netscaler_cip

        accept_proxy = self.accept_proxy

        allow_0rtt = self.allow_0rtt

        alpn = self.alpn

        backlog = self.backlog

        ca_ignore_err = self.ca_ignore_err

        ca_sign_file = self.ca_sign_file

        ca_sign_pass = self.ca_sign_pass

        ca_verify_file = self.ca_verify_file

        ciphers = self.ciphers

        ciphersuites = self.ciphersuites

        client_sigalgs = self.client_sigalgs

        crl_file = self.crl_file

        crt_ignore_err = self.crt_ignore_err

        crt_list = self.crt_list

        curves = self.curves

        default_crt_list: Union[Unset, list[str]] = UNSET
        if not isinstance(self.default_crt_list, Unset):
            default_crt_list = self.default_crt_list

        defer_accept = self.defer_accept

        ecdhe = self.ecdhe

        expose_fd_listeners = self.expose_fd_listeners

        force_sslv3 = self.force_sslv3

        force_strict_sni: Union[Unset, str] = UNSET
        if not isinstance(self.force_strict_sni, Unset):
            force_strict_sni = self.force_strict_sni.value

        force_tlsv10 = self.force_tlsv10

        force_tlsv11 = self.force_tlsv11

        force_tlsv12 = self.force_tlsv12

        force_tlsv13 = self.force_tlsv13

        generate_certificates = self.generate_certificates

        gid = self.gid

        group = self.group

        guid_prefix = self.guid_prefix

        id = self.id

        idle_ping: Union[None, Unset, int]
        if isinstance(self.idle_ping, Unset):
            idle_ping = UNSET
        else:
            idle_ping = self.idle_ping

        interface = self.interface

        level: Union[Unset, str] = UNSET
        if not isinstance(self.level, Unset):
            level = self.level.value

        maxconn = self.maxconn

        mode = self.mode

        mss = self.mss

        name = self.name

        namespace = self.namespace

        nbconn = self.nbconn

        nice = self.nice

        no_alpn = self.no_alpn

        no_ca_names = self.no_ca_names

        no_sslv3 = self.no_sslv3

        no_strict_sni = self.no_strict_sni

        no_tls_tickets = self.no_tls_tickets

        no_tlsv10 = self.no_tlsv10

        no_tlsv11 = self.no_tlsv11

        no_tlsv12 = self.no_tlsv12

        no_tlsv13 = self.no_tlsv13

        npn = self.npn

        prefer_client_ciphers = self.prefer_client_ciphers

        proto = self.proto

        quic_cc_algo: Union[Unset, str] = UNSET
        if not isinstance(self.quic_cc_algo, Unset):
            quic_cc_algo = self.quic_cc_algo.value

        quic_force_retry = self.quic_force_retry

        quic_socket: Union[Unset, str] = UNSET
        if not isinstance(self.quic_socket, Unset):
            quic_socket = self.quic_socket.value

        quic_cc_algo_burst_size: Union[None, Unset, int]
        if isinstance(self.quic_cc_algo_burst_size, Unset):
            quic_cc_algo_burst_size = UNSET
        else:
            quic_cc_algo_burst_size = self.quic_cc_algo_burst_size

        quic_cc_algo_max_window: Union[None, Unset, int]
        if isinstance(self.quic_cc_algo_max_window, Unset):
            quic_cc_algo_max_window = UNSET
        else:
            quic_cc_algo_max_window = self.quic_cc_algo_max_window

        severity_output: Union[Unset, str] = UNSET
        if not isinstance(self.severity_output, Unset):
            severity_output = self.severity_output.value

        sigalgs = self.sigalgs

        ssl = self.ssl

        ssl_cafile = self.ssl_cafile

        ssl_certificate = self.ssl_certificate

        ssl_max_ver: Union[Unset, str] = UNSET
        if not isinstance(self.ssl_max_ver, Unset):
            ssl_max_ver = self.ssl_max_ver.value

        ssl_min_ver: Union[Unset, str] = UNSET
        if not isinstance(self.ssl_min_ver, Unset):
            ssl_min_ver = self.ssl_min_ver.value

        sslv3: Union[Unset, str] = UNSET
        if not isinstance(self.sslv3, Unset):
            sslv3 = self.sslv3.value

        strict_sni = self.strict_sni

        tcp_user_timeout: Union[None, Unset, int]
        if isinstance(self.tcp_user_timeout, Unset):
            tcp_user_timeout = UNSET
        else:
            tcp_user_timeout = self.tcp_user_timeout

        tfo = self.tfo

        thread = self.thread

        tls_ticket_keys = self.tls_ticket_keys

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

        transparent = self.transparent

        uid = self.uid

        user = self.user

        v4v6 = self.v4v6

        v6only = self.v6only

        verify: Union[Unset, str] = UNSET
        if not isinstance(self.verify, Unset):
            verify = self.verify.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "address": address,
            }
        )
        if accept_netscaler_cip is not UNSET:
            field_dict["accept_netscaler_cip"] = accept_netscaler_cip
        if accept_proxy is not UNSET:
            field_dict["accept_proxy"] = accept_proxy
        if allow_0rtt is not UNSET:
            field_dict["allow_0rtt"] = allow_0rtt
        if alpn is not UNSET:
            field_dict["alpn"] = alpn
        if backlog is not UNSET:
            field_dict["backlog"] = backlog
        if ca_ignore_err is not UNSET:
            field_dict["ca_ignore_err"] = ca_ignore_err
        if ca_sign_file is not UNSET:
            field_dict["ca_sign_file"] = ca_sign_file
        if ca_sign_pass is not UNSET:
            field_dict["ca_sign_pass"] = ca_sign_pass
        if ca_verify_file is not UNSET:
            field_dict["ca_verify_file"] = ca_verify_file
        if ciphers is not UNSET:
            field_dict["ciphers"] = ciphers
        if ciphersuites is not UNSET:
            field_dict["ciphersuites"] = ciphersuites
        if client_sigalgs is not UNSET:
            field_dict["client_sigalgs"] = client_sigalgs
        if crl_file is not UNSET:
            field_dict["crl_file"] = crl_file
        if crt_ignore_err is not UNSET:
            field_dict["crt_ignore_err"] = crt_ignore_err
        if crt_list is not UNSET:
            field_dict["crt_list"] = crt_list
        if curves is not UNSET:
            field_dict["curves"] = curves
        if default_crt_list is not UNSET:
            field_dict["default_crt_list"] = default_crt_list
        if defer_accept is not UNSET:
            field_dict["defer_accept"] = defer_accept
        if ecdhe is not UNSET:
            field_dict["ecdhe"] = ecdhe
        if expose_fd_listeners is not UNSET:
            field_dict["expose_fd_listeners"] = expose_fd_listeners
        if force_sslv3 is not UNSET:
            field_dict["force_sslv3"] = force_sslv3
        if force_strict_sni is not UNSET:
            field_dict["force_strict_sni"] = force_strict_sni
        if force_tlsv10 is not UNSET:
            field_dict["force_tlsv10"] = force_tlsv10
        if force_tlsv11 is not UNSET:
            field_dict["force_tlsv11"] = force_tlsv11
        if force_tlsv12 is not UNSET:
            field_dict["force_tlsv12"] = force_tlsv12
        if force_tlsv13 is not UNSET:
            field_dict["force_tlsv13"] = force_tlsv13
        if generate_certificates is not UNSET:
            field_dict["generate_certificates"] = generate_certificates
        if gid is not UNSET:
            field_dict["gid"] = gid
        if group is not UNSET:
            field_dict["group"] = group
        if guid_prefix is not UNSET:
            field_dict["guid_prefix"] = guid_prefix
        if id is not UNSET:
            field_dict["id"] = id
        if idle_ping is not UNSET:
            field_dict["idle_ping"] = idle_ping
        if interface is not UNSET:
            field_dict["interface"] = interface
        if level is not UNSET:
            field_dict["level"] = level
        if maxconn is not UNSET:
            field_dict["maxconn"] = maxconn
        if mode is not UNSET:
            field_dict["mode"] = mode
        if mss is not UNSET:
            field_dict["mss"] = mss
        if name is not UNSET:
            field_dict["name"] = name
        if namespace is not UNSET:
            field_dict["namespace"] = namespace
        if nbconn is not UNSET:
            field_dict["nbconn"] = nbconn
        if nice is not UNSET:
            field_dict["nice"] = nice
        if no_alpn is not UNSET:
            field_dict["no_alpn"] = no_alpn
        if no_ca_names is not UNSET:
            field_dict["no_ca_names"] = no_ca_names
        if no_sslv3 is not UNSET:
            field_dict["no_sslv3"] = no_sslv3
        if no_strict_sni is not UNSET:
            field_dict["no_strict_sni"] = no_strict_sni
        if no_tls_tickets is not UNSET:
            field_dict["no_tls_tickets"] = no_tls_tickets
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
        if prefer_client_ciphers is not UNSET:
            field_dict["prefer_client_ciphers"] = prefer_client_ciphers
        if proto is not UNSET:
            field_dict["proto"] = proto
        if quic_cc_algo is not UNSET:
            field_dict["quic-cc-algo"] = quic_cc_algo
        if quic_force_retry is not UNSET:
            field_dict["quic-force-retry"] = quic_force_retry
        if quic_socket is not UNSET:
            field_dict["quic-socket"] = quic_socket
        if quic_cc_algo_burst_size is not UNSET:
            field_dict["quic_cc_algo_burst_size"] = quic_cc_algo_burst_size
        if quic_cc_algo_max_window is not UNSET:
            field_dict["quic_cc_algo_max_window"] = quic_cc_algo_max_window
        if severity_output is not UNSET:
            field_dict["severity_output"] = severity_output
        if sigalgs is not UNSET:
            field_dict["sigalgs"] = sigalgs
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
        if sslv3 is not UNSET:
            field_dict["sslv3"] = sslv3
        if strict_sni is not UNSET:
            field_dict["strict_sni"] = strict_sni
        if tcp_user_timeout is not UNSET:
            field_dict["tcp_user_timeout"] = tcp_user_timeout
        if tfo is not UNSET:
            field_dict["tfo"] = tfo
        if thread is not UNSET:
            field_dict["thread"] = thread
        if tls_ticket_keys is not UNSET:
            field_dict["tls_ticket_keys"] = tls_ticket_keys
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
        if transparent is not UNSET:
            field_dict["transparent"] = transparent
        if uid is not UNSET:
            field_dict["uid"] = uid
        if user is not UNSET:
            field_dict["user"] = user
        if v4v6 is not UNSET:
            field_dict["v4v6"] = v4v6
        if v6only is not UNSET:
            field_dict["v6only"] = v6only
        if verify is not UNSET:
            field_dict["verify"] = verify

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        address = d.pop("address")

        accept_netscaler_cip = d.pop("accept_netscaler_cip", UNSET)

        accept_proxy = d.pop("accept_proxy", UNSET)

        allow_0rtt = d.pop("allow_0rtt", UNSET)

        alpn = d.pop("alpn", UNSET)

        backlog = d.pop("backlog", UNSET)

        ca_ignore_err = d.pop("ca_ignore_err", UNSET)

        ca_sign_file = d.pop("ca_sign_file", UNSET)

        ca_sign_pass = d.pop("ca_sign_pass", UNSET)

        ca_verify_file = d.pop("ca_verify_file", UNSET)

        ciphers = d.pop("ciphers", UNSET)

        ciphersuites = d.pop("ciphersuites", UNSET)

        client_sigalgs = d.pop("client_sigalgs", UNSET)

        crl_file = d.pop("crl_file", UNSET)

        crt_ignore_err = d.pop("crt_ignore_err", UNSET)

        crt_list = d.pop("crt_list", UNSET)

        curves = d.pop("curves", UNSET)

        default_crt_list = cast(list[str], d.pop("default_crt_list", UNSET))

        defer_accept = d.pop("defer_accept", UNSET)

        ecdhe = d.pop("ecdhe", UNSET)

        expose_fd_listeners = d.pop("expose_fd_listeners", UNSET)

        force_sslv3 = d.pop("force_sslv3", UNSET)

        _force_strict_sni = d.pop("force_strict_sni", UNSET)
        force_strict_sni: Union[Unset, BindParamsForceStrictSni]
        if isinstance(_force_strict_sni, Unset):
            force_strict_sni = UNSET
        else:
            force_strict_sni = BindParamsForceStrictSni(_force_strict_sni)

        force_tlsv10 = d.pop("force_tlsv10", UNSET)

        force_tlsv11 = d.pop("force_tlsv11", UNSET)

        force_tlsv12 = d.pop("force_tlsv12", UNSET)

        force_tlsv13 = d.pop("force_tlsv13", UNSET)

        generate_certificates = d.pop("generate_certificates", UNSET)

        gid = d.pop("gid", UNSET)

        group = d.pop("group", UNSET)

        guid_prefix = d.pop("guid_prefix", UNSET)

        id = d.pop("id", UNSET)

        def _parse_idle_ping(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        idle_ping = _parse_idle_ping(d.pop("idle_ping", UNSET))

        interface = d.pop("interface", UNSET)

        _level = d.pop("level", UNSET)
        level: Union[Unset, BindParamsLevel]
        if isinstance(_level, Unset):
            level = UNSET
        else:
            level = BindParamsLevel(_level)

        maxconn = d.pop("maxconn", UNSET)

        mode = d.pop("mode", UNSET)

        mss = d.pop("mss", UNSET)

        name = d.pop("name", UNSET)

        namespace = d.pop("namespace", UNSET)

        nbconn = d.pop("nbconn", UNSET)

        nice = d.pop("nice", UNSET)

        no_alpn = d.pop("no_alpn", UNSET)

        no_ca_names = d.pop("no_ca_names", UNSET)

        no_sslv3 = d.pop("no_sslv3", UNSET)

        no_strict_sni = d.pop("no_strict_sni", UNSET)

        no_tls_tickets = d.pop("no_tls_tickets", UNSET)

        no_tlsv10 = d.pop("no_tlsv10", UNSET)

        no_tlsv11 = d.pop("no_tlsv11", UNSET)

        no_tlsv12 = d.pop("no_tlsv12", UNSET)

        no_tlsv13 = d.pop("no_tlsv13", UNSET)

        npn = d.pop("npn", UNSET)

        prefer_client_ciphers = d.pop("prefer_client_ciphers", UNSET)

        proto = d.pop("proto", UNSET)

        _quic_cc_algo = d.pop("quic-cc-algo", UNSET)
        quic_cc_algo: Union[Unset, BindParamsQuicCcAlgo]
        if isinstance(_quic_cc_algo, Unset):
            quic_cc_algo = UNSET
        else:
            quic_cc_algo = BindParamsQuicCcAlgo(_quic_cc_algo)

        quic_force_retry = d.pop("quic-force-retry", UNSET)

        _quic_socket = d.pop("quic-socket", UNSET)
        quic_socket: Union[Unset, BindParamsQuicSocket]
        if isinstance(_quic_socket, Unset):
            quic_socket = UNSET
        else:
            quic_socket = BindParamsQuicSocket(_quic_socket)

        def _parse_quic_cc_algo_burst_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        quic_cc_algo_burst_size = _parse_quic_cc_algo_burst_size(d.pop("quic_cc_algo_burst_size", UNSET))

        def _parse_quic_cc_algo_max_window(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        quic_cc_algo_max_window = _parse_quic_cc_algo_max_window(d.pop("quic_cc_algo_max_window", UNSET))

        _severity_output = d.pop("severity_output", UNSET)
        severity_output: Union[Unset, BindParamsSeverityOutput]
        if isinstance(_severity_output, Unset):
            severity_output = UNSET
        else:
            severity_output = BindParamsSeverityOutput(_severity_output)

        sigalgs = d.pop("sigalgs", UNSET)

        ssl = d.pop("ssl", UNSET)

        ssl_cafile = d.pop("ssl_cafile", UNSET)

        ssl_certificate = d.pop("ssl_certificate", UNSET)

        _ssl_max_ver = d.pop("ssl_max_ver", UNSET)
        ssl_max_ver: Union[Unset, BindParamsSslMaxVer]
        if isinstance(_ssl_max_ver, Unset):
            ssl_max_ver = UNSET
        else:
            ssl_max_ver = BindParamsSslMaxVer(_ssl_max_ver)

        _ssl_min_ver = d.pop("ssl_min_ver", UNSET)
        ssl_min_ver: Union[Unset, BindParamsSslMinVer]
        if isinstance(_ssl_min_ver, Unset):
            ssl_min_ver = UNSET
        else:
            ssl_min_ver = BindParamsSslMinVer(_ssl_min_ver)

        _sslv3 = d.pop("sslv3", UNSET)
        sslv3: Union[Unset, BindParamsSslv3]
        if isinstance(_sslv3, Unset):
            sslv3 = UNSET
        else:
            sslv3 = BindParamsSslv3(_sslv3)

        strict_sni = d.pop("strict_sni", UNSET)

        def _parse_tcp_user_timeout(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        tcp_user_timeout = _parse_tcp_user_timeout(d.pop("tcp_user_timeout", UNSET))

        tfo = d.pop("tfo", UNSET)

        thread = d.pop("thread", UNSET)

        tls_ticket_keys = d.pop("tls_ticket_keys", UNSET)

        _tls_tickets = d.pop("tls_tickets", UNSET)
        tls_tickets: Union[Unset, BindParamsTlsTickets]
        if isinstance(_tls_tickets, Unset):
            tls_tickets = UNSET
        else:
            tls_tickets = BindParamsTlsTickets(_tls_tickets)

        _tlsv10 = d.pop("tlsv10", UNSET)
        tlsv10: Union[Unset, BindParamsTlsv10]
        if isinstance(_tlsv10, Unset):
            tlsv10 = UNSET
        else:
            tlsv10 = BindParamsTlsv10(_tlsv10)

        _tlsv11 = d.pop("tlsv11", UNSET)
        tlsv11: Union[Unset, BindParamsTlsv11]
        if isinstance(_tlsv11, Unset):
            tlsv11 = UNSET
        else:
            tlsv11 = BindParamsTlsv11(_tlsv11)

        _tlsv12 = d.pop("tlsv12", UNSET)
        tlsv12: Union[Unset, BindParamsTlsv12]
        if isinstance(_tlsv12, Unset):
            tlsv12 = UNSET
        else:
            tlsv12 = BindParamsTlsv12(_tlsv12)

        _tlsv13 = d.pop("tlsv13", UNSET)
        tlsv13: Union[Unset, BindParamsTlsv13]
        if isinstance(_tlsv13, Unset):
            tlsv13 = UNSET
        else:
            tlsv13 = BindParamsTlsv13(_tlsv13)

        transparent = d.pop("transparent", UNSET)

        uid = d.pop("uid", UNSET)

        user = d.pop("user", UNSET)

        v4v6 = d.pop("v4v6", UNSET)

        v6only = d.pop("v6only", UNSET)

        _verify = d.pop("verify", UNSET)
        verify: Union[Unset, BindParamsVerify]
        if isinstance(_verify, Unset):
            verify = UNSET
        else:
            verify = BindParamsVerify(_verify)

        global_base_runtime_apis_item = cls(
            address=address,
            accept_netscaler_cip=accept_netscaler_cip,
            accept_proxy=accept_proxy,
            allow_0rtt=allow_0rtt,
            alpn=alpn,
            backlog=backlog,
            ca_ignore_err=ca_ignore_err,
            ca_sign_file=ca_sign_file,
            ca_sign_pass=ca_sign_pass,
            ca_verify_file=ca_verify_file,
            ciphers=ciphers,
            ciphersuites=ciphersuites,
            client_sigalgs=client_sigalgs,
            crl_file=crl_file,
            crt_ignore_err=crt_ignore_err,
            crt_list=crt_list,
            curves=curves,
            default_crt_list=default_crt_list,
            defer_accept=defer_accept,
            ecdhe=ecdhe,
            expose_fd_listeners=expose_fd_listeners,
            force_sslv3=force_sslv3,
            force_strict_sni=force_strict_sni,
            force_tlsv10=force_tlsv10,
            force_tlsv11=force_tlsv11,
            force_tlsv12=force_tlsv12,
            force_tlsv13=force_tlsv13,
            generate_certificates=generate_certificates,
            gid=gid,
            group=group,
            guid_prefix=guid_prefix,
            id=id,
            idle_ping=idle_ping,
            interface=interface,
            level=level,
            maxconn=maxconn,
            mode=mode,
            mss=mss,
            name=name,
            namespace=namespace,
            nbconn=nbconn,
            nice=nice,
            no_alpn=no_alpn,
            no_ca_names=no_ca_names,
            no_sslv3=no_sslv3,
            no_strict_sni=no_strict_sni,
            no_tls_tickets=no_tls_tickets,
            no_tlsv10=no_tlsv10,
            no_tlsv11=no_tlsv11,
            no_tlsv12=no_tlsv12,
            no_tlsv13=no_tlsv13,
            npn=npn,
            prefer_client_ciphers=prefer_client_ciphers,
            proto=proto,
            quic_cc_algo=quic_cc_algo,
            quic_force_retry=quic_force_retry,
            quic_socket=quic_socket,
            quic_cc_algo_burst_size=quic_cc_algo_burst_size,
            quic_cc_algo_max_window=quic_cc_algo_max_window,
            severity_output=severity_output,
            sigalgs=sigalgs,
            ssl=ssl,
            ssl_cafile=ssl_cafile,
            ssl_certificate=ssl_certificate,
            ssl_max_ver=ssl_max_ver,
            ssl_min_ver=ssl_min_ver,
            sslv3=sslv3,
            strict_sni=strict_sni,
            tcp_user_timeout=tcp_user_timeout,
            tfo=tfo,
            thread=thread,
            tls_ticket_keys=tls_ticket_keys,
            tls_tickets=tls_tickets,
            tlsv10=tlsv10,
            tlsv11=tlsv11,
            tlsv12=tlsv12,
            tlsv13=tlsv13,
            transparent=transparent,
            uid=uid,
            user=user,
            v4v6=v4v6,
            v6only=v6only,
            verify=verify,
        )

        global_base_runtime_apis_item.additional_properties = d
        return global_base_runtime_apis_item

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
