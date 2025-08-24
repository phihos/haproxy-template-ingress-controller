from enum import Enum


class SourceUsesrc(str, Enum):
    ADDRESS = "address"
    CLIENT = "client"
    CLIENTIP = "clientip"
    HDR_IP = "hdr_ip"

    def __str__(self) -> str:
        return str(self.value)
