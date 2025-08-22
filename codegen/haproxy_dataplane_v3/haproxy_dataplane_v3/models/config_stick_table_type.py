from enum import Enum


class ConfigStickTableType(str, Enum):
    BINARY = "binary"
    INTEGER = "integer"
    IP = "ip"
    IPV6 = "ipv6"
    STRING = "string"

    def __str__(self) -> str:
        return str(self.value)
