from enum import Enum


class ACMEProviderChallenge(str, Enum):
    DNS_01 = "DNS-01"
    HTTP_01 = "HTTP-01"

    def __str__(self) -> str:
        return str(self.value)
