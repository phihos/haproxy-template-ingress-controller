from enum import Enum


class DefaultsBaseContstats(str, Enum):
    ENABLED = "enabled"

    def __str__(self) -> str:
        return str(self.value)
