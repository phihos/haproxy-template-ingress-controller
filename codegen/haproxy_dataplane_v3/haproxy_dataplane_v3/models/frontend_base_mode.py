from enum import Enum


class FrontendBaseMode(str, Enum):
    HTTP = "http"
    TCP = "tcp"

    def __str__(self) -> str:
        return str(self.value)
