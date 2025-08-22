from enum import Enum


class RuntimeAddServerOnMarkedDown(str, Enum):
    SHUTDOWN_SESSIONS = "shutdown-sessions"

    def __str__(self) -> str:
        return str(self.value)
