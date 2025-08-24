from enum import Enum


class ServerParamsResolvePrefer(str, Enum):
    IPV4 = "ipv4"
    IPV6 = "ipv6"

    def __str__(self) -> str:
        return str(self.value)
