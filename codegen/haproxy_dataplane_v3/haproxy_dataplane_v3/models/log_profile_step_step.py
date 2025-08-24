from enum import Enum


class LogProfileStepStep(str, Enum):
    ACCEPT = "accept"
    ANY = "any"
    CLOSE = "close"
    CONNECT = "connect"
    ERROR = "error"
    HTTP_AFTER_RES = "http-after-res"
    HTTP_REQ = "http-req"
    HTTP_RES = "http-res"
    QUIC_INIT = "quic-init"
    REQUEST = "request"
    RESPONSE = "response"
    TCP_REQ_CONN = "tcp-req-conn"
    TCP_REQ_CONT = "tcp-req-cont"
    TCP_REQ_SESS = "tcp-req-sess"

    def __str__(self) -> str:
        return str(self.value)
