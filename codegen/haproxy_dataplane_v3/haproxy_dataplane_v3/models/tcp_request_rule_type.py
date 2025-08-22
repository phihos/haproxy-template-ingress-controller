from enum import Enum


class TCPRequestRuleType(str, Enum):
    CONNECTION = "connection"
    CONTENT = "content"
    INSPECT_DELAY = "inspect-delay"
    SESSION = "session"

    def __str__(self) -> str:
        return str(self.value)
