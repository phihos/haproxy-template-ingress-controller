from enum import Enum


class ServerParamsSendProxyV2Ssl(str, Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"

    def __str__(self) -> str:
        return str(self.value)
