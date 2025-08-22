from enum import Enum


class NativeStatStatsStatus(str, Enum):
    DOWN = "DOWN"
    MAINT = "MAINT"
    NOLB = "NOLB"
    NO_CHECK = "no check"
    UP = "UP"

    def __str__(self) -> str:
        return str(self.value)
