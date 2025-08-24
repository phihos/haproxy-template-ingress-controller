from enum import Enum


class DefaultsBaseHttpConnectionMode(str, Enum):
    HTTPCLOSE = "httpclose"
    HTTP_KEEP_ALIVE = "http-keep-alive"
    HTTP_SERVER_CLOSE = "http-server-close"

    def __str__(self) -> str:
        return str(self.value)
