from enum import Enum


class BackendBaseMode(str, Enum):
    HTTP = "http"
    LOG = "log"
    TCP = "tcp"

    def __str__(self) -> str:
        return str(self.value)
