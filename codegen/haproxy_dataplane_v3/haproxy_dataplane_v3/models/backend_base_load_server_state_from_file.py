from enum import Enum


class BackendBaseLoadServerStateFromFile(str, Enum):
    GLOBAL = "global"
    LOCAL = "local"
    NONE = "none"

    def __str__(self) -> str:
        return str(self.value)
