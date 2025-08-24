from enum import Enum


class QUICInitialType(str, Enum):
    ACCEPT = "accept"
    DGRAM_DROP = "dgram-drop"
    REJECT = "reject"
    SEND_RETRY = "send-retry"

    def __str__(self) -> str:
        return str(self.value)
