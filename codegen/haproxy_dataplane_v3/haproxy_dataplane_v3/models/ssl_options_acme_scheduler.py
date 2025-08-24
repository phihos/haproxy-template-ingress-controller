from enum import Enum


class SslOptionsAcmeScheduler(str, Enum):
    AUTO = "auto"
    OFF = "off"

    def __str__(self) -> str:
        return str(self.value)
