from enum import Enum


class BalanceAlgorithm(str, Enum):
    FIRST = "first"
    HASH = "hash"
    HDR = "hdr"
    LEASTCONN = "leastconn"
    RANDOM = "random"
    RDP_COOKIE = "rdp-cookie"
    ROUNDROBIN = "roundrobin"
    SOURCE = "source"
    STATIC_RR = "static-rr"
    URI = "uri"
    URL_PARAM = "url_param"

    def __str__(self) -> str:
        return str(self.value)
