from enum import Enum


class BackendBaseTcpSmartConnect(str, Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"

    def __str__(self) -> str:
        return str(self.value)
