from enum import Enum


class RuntimeAddServerOnMarkedUp(str, Enum):
    SHUTDOWN_BACKUP_SESSIONS = "shutdown-backup-sessions"

    def __str__(self) -> str:
        return str(self.value)
