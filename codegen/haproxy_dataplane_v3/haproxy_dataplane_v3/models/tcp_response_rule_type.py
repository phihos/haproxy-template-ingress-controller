from enum import Enum


class TCPResponseRuleType(str, Enum):
    CONTENT = "content"
    INSPECT_DELAY = "inspect-delay"

    def __str__(self) -> str:
        return str(self.value)
