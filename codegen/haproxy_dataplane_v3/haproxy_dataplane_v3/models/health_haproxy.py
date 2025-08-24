from enum import Enum


class HealthHaproxy(str, Enum):
    DOWN = "down"
    UNKNOWN = "unknown"
    UP = "up"

    def __str__(self) -> str:
        return str(self.value)
