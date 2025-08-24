from enum import Enum


class SiteServiceHttpConnectionMode(str, Enum):
    FORCED_CLOSE = "forced-close"
    HTTPCLOSE = "httpclose"
    HTTP_KEEP_ALIVE = "http-keep-alive"
    HTTP_SERVER_CLOSE = "http-server-close"
    HTTP_TUNNEL = "http-tunnel"

    def __str__(self) -> str:
        return str(self.value)
