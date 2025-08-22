from enum import Enum


class NativeStatStatsMode(str, Enum):
    HEALTH = "health"
    HTTP = "http"
    TCP = "tcp"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return str(self.value)
