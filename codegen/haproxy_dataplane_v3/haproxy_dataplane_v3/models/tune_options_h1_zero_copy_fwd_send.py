from enum import Enum


class TuneOptionsH1ZeroCopyFwdSend(str, Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"

    def __str__(self) -> str:
        return str(self.value)
