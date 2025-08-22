from enum import Enum


class TuneLuaOptionsLogStderr(str, Enum):
    AUTO = "auto"
    DISABLED = "disabled"
    ENABLED = "enabled"

    def __str__(self) -> str:
        return str(self.value)
