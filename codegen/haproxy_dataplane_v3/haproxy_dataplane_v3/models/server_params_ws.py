from enum import Enum


class ServerParamsWs(str, Enum):
    AUTO = "auto"
    H1 = "h1"
    H2 = "h2"

    def __str__(self) -> str:
        return str(self.value)
