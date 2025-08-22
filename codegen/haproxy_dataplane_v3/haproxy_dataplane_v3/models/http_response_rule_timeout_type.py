from enum import Enum


class HTTPResponseRuleTimeoutType(str, Enum):
    CLIENT = "client"
    SERVER = "server"
    TUNNEL = "tunnel"

    def __str__(self) -> str:
        return str(self.value)
